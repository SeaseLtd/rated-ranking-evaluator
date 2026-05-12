from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import json
import logging
from uuid import uuid4
from pydantic import ValidationError
from rre_tools.shared.models.document import Document
from rre_tools.shared.models.query import Query, QuerySource, SOURCE_PRIORITY
from rre_tools.shared.models.rating import Rating
from rre_tools.shared.utils import clean_text

log = logging.getLogger(__name__)

TMP_FILE = Path("resources/tmp/datastore.json")
ENCODING = "utf-8"


class DataStore:
    """In-memory store for documents, queries, and ratings with O(1) indices.

    Invariants
    ----------
    - A ``(query_id, doc_id)`` pair is unique within ``rating_by_pair``.
    - ``has_rating_score`` is True only if a ``Rating`` object exists for the
      pair ``(query_id, doc_id)``.

    Thread safety
    -------------
    Public methods are safe to call concurrently. State is protected by a
    single ``threading.RLock`` (``self._lock``) acquired by every public
    method that touches the four backing dicts (``docs``, ``queries``,
    ``rating_by_pair``, ``query_text_to_query_id``) — mutators, bulk getters
    (the ``list(...values())`` materialization is the snapshot point),
    existence checks, ``save()``, ``load()``, and
    ``export_all_records_with_explanation``.

    Why RLock specifically: ``create_rating_score`` would have to re-enter the
    lock through ``_add_rating`` if the latter took its own lock, and a plain
    ``Lock`` would deadlock on the second acquisition.

    What is NOT atomic: the ``has_rating_score`` → ``create_rating_score``
    read-then-act idiom doesn't extend across the two calls. Two workers can
    both pass ``has_rating_score`` and both call ``create_rating_score``;
    the second writer is a no-op because ``create_rating_score`` is idempotent
    on the ``(query_id, doc_id)`` key. The cost is at most one wasted LLM call.

    Autosave pattern (read before adding a new mutator)
    --------------------------------------------------
    Mutators that change persistent state follow this shape::

        def add_X(self, ...) -> ...:
            snapshot: Optional[Dict[str, Any]] = None
            with self._lock:
                # ... validate, dedupe, mutate the backing dict ...
                snapshot = self._capture_autosave_snapshot_if_due()
            self._persist_autosave(snapshot)

    The split — capture the snapshot under the lock, write it to disk after
    the lock is released — is what keeps autosave I/O off the worker hot
    path. Folding ``save()`` back inside the ``with self._lock:`` block (e.g.
    by calling ``save()`` from a mutator helper) reintroduces the bug where
    every concurrent worker serializes behind ``tmp_path.write_text()`` /
    ``tmp_path.replace()``. Don't.

    Private helpers used by the pattern:

    - ``_capture_autosave_snapshot_if_due``: bumps the counter; if the
      threshold is crossed, builds a JSON-ready snapshot and resets the
      counter. Caller must hold ``self._lock``.
    - ``_persist_autosave``: writes a captured snapshot to disk (best-effort,
      logs on failure). Safe to call without the lock. No-op on ``None``.
    - ``_add_rating``: returns the snapshot instead of persisting itself, so
      ``create_rating_score`` can do the persist call after its own lock is
      released.

    ``load()`` runs the replay through the same mutators but with autosave
    temporarily suppressed (the threshold is swapped to ``None`` for the
    duration). Without that suppression, crossing the threshold mid-replay
    would overwrite the on-disk cache with a partial snapshot.

    Autosave durability limitation
    ------------------------------
    Under concurrent autosave, on-disk progress is NOT strictly monotonic.
    Captures release the lock before the file I/O, so two autosaves race
    on ``tmp_path.replace()`` — whichever I/O finishes last wins, even if
    its snapshot was captured earlier. Both snapshots are internally
    consistent (each was captured under the lock) so the file is never
    corrupt, but the recovery point can move backwards.

    How far backwards: there is no hard bound. If an early capture's write
    stalls (slow disk, fsync contention, networked filesystem) while
    several newer captures complete in the meantime, the stalled write
    eventually replaces the file with its older snapshot. The practical
    rollback equals "how many newer captures finished while my write was
    stalled" — usually zero on a fast local filesystem, potentially more
    on slower / contended storage.

    The final ``save()`` at end of run is the authoritative state;
    autosave is a partial-progress convenience, not a contract. If a
    monotonic guarantee is needed later, the lightest fix is a monotonic
    ``_autosave_seq`` plus a separate I/O lock that skips writes whose
    seq is older than the latest persisted (~15 lines).
    """

    def __init__(self, path: Path = TMP_FILE, ignore_saved_data: bool = False, autosave_every_n_updates: Optional[int] = None):
        # ORDER MATTERS: assign self._lock BEFORE calling self.load(). load()
        # invokes add_document / add_query / _add_rating, each of which
        # acquires self._lock — moving this line below self.load() makes the
        # first record loaded raise `AttributeError: 'DataStore' object has
        # no attribute '_lock'`. Guarded by
        # test_data_store__load_called_inside_init__lock_already_initialized.
        self._lock = threading.RLock()
        self.path = path
        # Autosave configuration: when >0, save to disk every N successful mutations
        self._autosave_every_n_updates: Optional[int] = (
            autosave_every_n_updates if isinstance(autosave_every_n_updates, int) and autosave_every_n_updates > 0 else None
        )
        self._updates_since_last_save: int = 0

        # Primary (id → object)
        self.docs: Dict[str, Document] = {}
        self.queries: Dict[str, Query] = {}

        # Ratings storage
        self.rating_by_pair: Dict[Tuple[str, str], Rating] = {}    # (query_id, doc_id) → Rating

        # Text based deduplication for queries
        self.query_text_to_query_id: Dict[str, str] = {}           # query_text → query_id

        if not ignore_saved_data:
            log.info(f"Loading data from {path}")
            self.load()

    # ────────────────────────────────────────────
    # Existence checks
    # ────────────────────────────────────────────
    def has_document(self, doc_id: str) -> bool:
        """Checks for document existence."""
        with self._lock:
            return doc_id in self.docs

    def has_query(self, query_id: str) -> bool:
        """Checks for query existence."""
        with self._lock:
            return query_id in self.queries

    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        """Checks for a rating by (query, doc) pair."""
        with self._lock:
            return (query_id, doc_id) in self.rating_by_pair

    # ────────────────────────────────────────────
    # Getters
    # ────────────────────────────────────────────
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Gets a single document by its ID, or None if not found."""
        with self._lock:
            return self.docs.get(doc_id)

    def get_documents(self) -> List[Document]:
        """Gets all documents."""
        with self._lock:
            return list(self.docs.values())

    def get_cartesian_prod_docs(self) -> List[Document]:
        """Gets only documents used to generate queries."""
        with self._lock:
            return [doc for doc in self.docs.values() if doc.is_used_to_generate_queries]

    def get_query(self, query_id: str) -> Optional[Query]:
        """Gets a single query by its ID, or None if not found."""
        with self._lock:
            return self.queries.get(query_id)

    def get_queries(self) -> List[Query]:
        """Gets all queries."""
        with self._lock:
            return list(self.queries.values())

    def get_ratings(self) -> List[Rating]:
        """Gets all ratings."""
        with self._lock:
            return list(self.rating_by_pair.values())


    # ────────────────────────────────────────────
    # Mutators (all O(1) on average)
    # ────────────────────────────────────────────
    def add_document(self, doc: Document) -> None:
        """Adds a document."""
        snapshot: Optional[Dict[str, Any]] = None
        with self._lock:
            if doc.id in self.docs:
                log.debug(f"[add_document] exists doc_id={doc.id}")
                return
            self.docs[doc.id] = doc
            log.debug(f"[add_document] added doc_id={doc.id}")
            snapshot = self._capture_autosave_snapshot_if_due()
        self._persist_autosave(snapshot)

    def mark_document_as_query_seed(self, doc_id: str) -> None:
        """Flag an already-stored document as a cartesian seed.

        Required because add_document() returns early when doc_id already
        exists, so a re-fetched doc cannot update the stored object's
        is_used_to_generate_queries flag through that path.
        """
        snapshot: Optional[Dict[str, Any]] = None
        with self._lock:
            doc = self.docs.get(doc_id)
            if doc is None:
                log.warning(f"[mark_document_as_query_seed] doc_not_found doc_id={doc_id}")
                return
            if not doc.is_used_to_generate_queries:
                doc.is_used_to_generate_queries = True
                snapshot = self._capture_autosave_snapshot_if_due()
        self._persist_autosave(snapshot)

    def add_query(self, query_text_str: str, query_id: Optional[str] = None,
                  source: Optional[QuerySource] = None) -> Query:
        """Adds a new query. If text is cached, returns existing Query. If id is given, it's used.

        `source` records how the query was asserted in this run. On a dedup hit the existing
        query is *promoted* if the incoming source has higher priority than the stored one
        (cached < llm < user/category) — so re-asserting a previously-cached query as e.g. a
        user-supplied query updates its label.
        """
        key = clean_text(query_text_str) # Apply general filtering
        snapshot: Optional[Dict[str, Any]] = None
        with self._lock:
            if existing_id := self.query_text_to_query_id.get(key):
                log.debug(f"[add_query] exists text='{query_text_str}' key='{key}' existing_id={existing_id}")
                query = self.queries[existing_id]
                if source is not None and SOURCE_PRIORITY[source] < SOURCE_PRIORITY[query.source]:
                    log.debug(f"[add_query] promote source {query.source}->{source} for query_id={query.id}")
                    query.source = source
            else:
                kwargs: Dict[str, str] = {"text": query_text_str}
                if query_id:
                    kwargs["id"] = query_id
                if source is not None:
                    kwargs["source"] = source
                query = Query(**kwargs)
                self.queries[query.id] = query
                self.query_text_to_query_id[key] = query.id
                log.debug(f"[add_query] added query_id={query.id} source={query.source}")
                snapshot = self._capture_autosave_snapshot_if_due()

        self._persist_autosave(snapshot)
        return query

    def _add_rating(self, rating: Rating) -> Optional[Dict[str, Any]]:
        """Add a rating; return an autosave snapshot if one is due.

        Caller must hold ``self._lock`` AND, after releasing it, pass the
        return value to :meth:`_persist_autosave`. Splitting the snapshot
        capture from the file I/O is what keeps mutators from serializing
        worker writes behind disk I/O when the caller's lock is still held.
        """
        if rating.query_id not in self.queries:
            log.warning(f"[add_rating] query_not_found query_id={rating.query_id}")
            return None
        if rating.doc_id not in self.docs:
            log.warning(f"[add_rating] doc_not_found doc_id={rating.doc_id}")
            return None

        key = (rating.query_id, rating.doc_id)
        if key in self.rating_by_pair:
            log.warning(f"[add_rating] exists q={rating.query_id} d={rating.doc_id}")
            return None

        self.rating_by_pair[key] = rating
        log.debug(f"[add_rating] added q={rating.query_id} d={rating.doc_id}")
        return self._capture_autosave_snapshot_if_due()

    def create_rating_score(
        self, query_id: str, doc_id: str, score: int, explanation: Optional[str] = None
    ) -> Optional[Rating]:
        """Create rating (if not exists) and add via ``_add_rating``.

        The ``rating_by_pair`` check + ``_add_rating`` insert pair runs under
        the same RLock acquisition so a concurrent caller can't slip in between
        and double-insert. The autosave file write happens AFTER the lock is
        released — ``_add_rating`` only captures a snapshot, ``_persist_autosave``
        writes it.
        """
        snapshot: Optional[Dict[str, Any]] = None
        rating: Optional[Rating] = None
        with self._lock:
            key = (query_id, doc_id)
            if (existing_rating := self.rating_by_pair.get(key)):
                log.warning(f"[create_rating_score] existing q={query_id} d={doc_id}")
                return existing_rating

            try:
                rating = Rating(doc_id=doc_id, query_id=query_id, score=score, explanation=explanation)
                snapshot = self._add_rating(rating)
            except ValidationError as e:
                log.warning(f"[create_rating_score] validation_failed q={query_id} d={doc_id} score={score} error={e}")
                return None

        self._persist_autosave(snapshot)
        return rating

    # ────────────────────────────────────────────
    # Autosave helpers
    # ────────────────────────────────────────────
    def _capture_autosave_snapshot_if_due(self) -> Optional[Dict[str, Any]]:
        """Bump the mutation counter; if the autosave threshold is reached,
        return a JSON-ready snapshot of current state (and reset the counter).

        Caller must hold ``self._lock``. The returned dict is then written
        to disk OUTSIDE the lock via :meth:`_persist_autosave`. This split
        is what keeps autosave I/O off the mutator hot path — without it,
        the outer mutator's ``with self._lock:`` block would serialize
        worker writes behind ``tmp_path.write_text()`` / ``replace()``.

        The counter is reset *before* the I/O, not after success, so a
        failed write doesn't pin every subsequent mutation into another
        autosave attempt. The next autosave runs after the next N mutations
        regardless.
        """
        if self._autosave_every_n_updates is None:
            return None
        self._updates_since_last_save += 1
        if self._updates_since_last_save < self._autosave_every_n_updates:
            return None
        self._updates_since_last_save = 0
        return self._build_snapshot_unlocked()

    def _build_snapshot_unlocked(self) -> Dict[str, Any]:
        """Materialize a JSON-ready snapshot of the store. Caller must hold ``self._lock``."""
        return {
            "docs": [d.model_dump() for d in self.docs.values()],
            "queries": [q.model_dump() for q in self.queries.values()],
            "ratings": [r.model_dump() for r in self.rating_by_pair.values()],
        }

    def _write_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Atomically write a snapshot to ``self.path``. Lock-free by design.

        Each write uses a uuid-suffixed tmp path so concurrent autosave
        writers don't collide on the tmp filename; ``Path.replace()`` is
        atomic per-FS, so whichever writer finishes last wins — both
        snapshots are internally consistent (they were captured under the
        lock) so either is a valid recovery point.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_name(self.path.name + f".{uuid4().hex}.tmp")
        tmp_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding=ENCODING)
        tmp_path.replace(self.path)

    def _persist_autosave(self, snapshot: Optional[Dict[str, Any]]) -> None:
        """Best-effort write a captured autosave snapshot. No-op if None.

        Errors are logged, not raised — autosave is a durability convenience,
        not part of the mutator's contract. The final ``save()`` at end of run
        still has to succeed for the run to be considered successful.
        """
        if snapshot is None:
            return
        try:
            self._write_snapshot(snapshot)
            log.debug(f"[autosave] ok path={self.path}")
        except Exception as e:
            log.error(
                f"[autosave] failed to save {self.path}. Error: {e}",
                exc_info=True,
            )

    # ────────────────────────────────────────────
    # Persistence
    # ────────────────────────────────────────────
    def save(self) -> None:
        """Persist the current state to disk.

        Holds ``self._lock`` only for the dump-to-dict step; file I/O is done
        outside the lock so workers aren't serialized behind disk writes.
        """
        with self._lock:
            snapshot = self._build_snapshot_unlocked()
        self._write_snapshot(snapshot)

    def load(self) -> None:
        """Replay a persisted store from disk.

        Autosave is suppressed for the duration of the replay: mutators called
        during load otherwise bump the same counter the user's run uses, and
        crossing the threshold mid-replay would overwrite the on-disk cache
        with a partial snapshot. On exit the counter is reset so the user's
        first real mutation accounts from a clean state.
        """
        with self._lock:
            if not self.path.exists():
                return

            # Clear previous data
            self._clear_all_data()

            try:
                data = json.loads(self.path.read_text(encoding=ENCODING))
            except json.JSONDecodeError as e:
                log.warning(f"Could not read datastore {self.path} (JSON). Starting clean. Error: {e}")
                return

            saved_threshold = self._autosave_every_n_updates
            self._autosave_every_n_updates = None
            try:
                # docs
                for doc_as_dict in data.get("docs", []):
                    try:
                        self.add_document(Document.model_validate(doc_as_dict))
                    except ValidationError as e:
                        log.warning(f"[load] skip_doc_invalid data={doc_as_dict} error={e}")

                # queries
                for query_as_dict in data.get("queries", []):
                    try:
                        tmp_query = Query.model_validate(query_as_dict)                # Create a new tmp query with loaded dict
                        self.add_query(query_text_str=tmp_query.text, query_id=tmp_query.id) # Pass (text, ID) values to keep ID consistent
                    except ValidationError as e:
                        log.warning(f"[load] skip_query_invalid data={query_as_dict} error={e}")

                # ratings
                for rating_as_dict in data.get("ratings", []):
                    try:
                        robj = Rating.model_validate(rating_as_dict)
                        self._add_rating(robj)
                    except ValidationError as e:
                        log.warning(f"[load] skip_rating_invalid data={rating_as_dict} error={e}")
            finally:
                self._autosave_every_n_updates = saved_threshold
                self._updates_since_last_save = 0

    def _clear_all_data(self) -> None:
        """Reset state. Caller must hold ``self._lock``."""
        self.docs.clear()
        self.queries.clear()
        self.rating_by_pair.clear()
        self.query_text_to_query_id.clear()


    def export_all_records_with_explanation(self, output_path: str | Path) -> None:
        """Export (query_text, doc_id, rating, explanation) to JSON."""
        with self._lock:
            records = []
            for rating_obj in self.rating_by_pair.values():
                # Guard against dangling references (defensive)
                query_obj = self.queries.get(rating_obj.query_id)
                if not query_obj:
                    continue
                records.append({
                    "query": query_obj.text,
                    "doc_id": rating_obj.doc_id,
                    "rating": rating_obj.score,
                    "explanation": rating_obj.explanation or ""
                })

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output_path.open("w", encoding=ENCODING) as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            log.info(f"[export] ok path={output_path} records={len(records)}")
        except Exception as e:
            log.warning(f"[export] fail path={output_path} err={e}")