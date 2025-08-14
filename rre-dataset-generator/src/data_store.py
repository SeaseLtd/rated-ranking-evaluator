from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional, Tuple, Set, List

import json
import logging
import os
from uuid import uuid4

from pydantic import ValidationError
from src.model import Document, Query, Rating

log = logging.getLogger(__name__)

TMP_FILE = Path("./tmp/datastore.json")
ENCODING = "utf-8"


class DataStore:
    """In-memory store for documents, queries, and ratings with O(1) indices.

    Invariants:
    - A (query_id, doc_id) pair is unique within the `rating_index`.
    - An entry in `docs_by_query` (a link) does not imply a rating exists.
    - `has_rating_score` is True only if a `Rating` object exists for the pair (query_id, document_id).
    """

    def __init__(self, path: Path = TMP_FILE, ignore_saved_data: bool = False):
        self.path = path

        # Primary (id → object)
        self.docs: Dict[str, Document] = {}
        self.queries: Dict[str, Query] = {}
        self.ratings: Dict[str, Rating] = {}

        # Secondary
        self.rating_index: Dict[Tuple[str, str], str] = {}               # (query_id, doc_id) → rating_id
        self.ratings_by_query: Dict[str, Set[str]] = defaultdict(set)    # query_id → rating_ids
        self.docs_by_query: Dict[str, Set[str]] = defaultdict(set)       # query_id → doc_ids
        self.query_text_to_query_id: Dict[str, str] = {}                 # text-based deduplication

        if not ignore_saved_data:
            self.load()

    # ────────────────────────────────────────────
    # Existence checks
    # ────────────────────────────────────────────
    def has_document(self, doc_id: str) -> bool:
        """Checks for document existence. Complexity: O(1)."""
        return doc_id in self.docs

    def has_query(self, query_id: str) -> bool:
        """Checks for query existence. Complexity: O(1)."""
        return query_id in self.queries

    def has_rating(self, rating_id: str) -> bool:
        """Checks for rating existence. Complexity: O(1)."""
        return rating_id in self.ratings

    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        """Checks for a rating by (query, doc) pair. Complexity: O(1)."""
        return (query_id, doc_id) in self.rating_index

    # ────────────────────────────────────────────
    # Getters
    # ────────────────────────────────────────────
    def get_document(self, doc_id: str) -> Document:
        """Gets a document by ID. Complexity: O(1)."""
        return self.docs[doc_id]

    def get_documents(self) -> List[Document]:
        """Gets all documents. Complexity: O(N) where N is the number of docs."""
        return list(self.docs.values())

    def get_query(self, query_id: str) -> Query:
        """Gets a query by ID. Complexity: O(1)."""
        return self.queries[query_id]

    def get_queries(self) -> List[Query]:
        """Gets all queries. Complexity: O(M) where M is the number of queries."""
        return list(self.queries.values())

    def get_rating(self, rating_id: str) -> Rating:
        """Gets a rating by ID. Complexity: O(1)."""
        return self.ratings[rating_id]

    def get_ratings(self) -> List[Rating]:
        """Gets all ratings. Complexity: O(P) where P is the number of ratings."""
        return list(self.ratings.values())

    def get_rating_score(self, query_id: str, doc_id: str) -> Optional[int]:
        """Returns the score of a (query, doc) pair. Complexity: O(1)."""
        if not self.has_query(query_id):
            log.debug(f"[get_rating_score] query_not_found query_id={query_id}")
            return None
        if not self.has_document(doc_id):
            log.debug(f"[get_rating_score] doc_not_found doc_id={doc_id}")
            return None
        rid = self.rating_index.get((query_id, doc_id))
        return self.ratings[rid].score if rid else None

    def get_ratings_for_query(self, query_id: str) -> List[Rating]:
        """Returns ratings for a query, sorted by rating_id. Complexity: O(K log K) where K is ratings per query."""
        if not self.has_query(query_id):
            log.debug(f"[get_ratings_for_query] query_not_found query_id={query_id}")
            raise KeyError(f"Query '{query_id}' not found")
        ids = self.ratings_by_query.get(query_id, set())
        return [self.ratings[rid] for rid in sorted(ids)]

    def get_doc_ids_for_query(self, query_id: str) -> List[str]:
        """Returns doc IDs for a query, sorted. Complexity: O(L log L) where L is docs linked to the query."""
        if not self.has_query(query_id):
            log.debug(f"[get_doc_ids_for_query] query_not_found query_id={query_id}")
            raise KeyError(f"Query '{query_id}' not found")
        via_ratings = {self.ratings[rid].doc_id for rid in self.ratings_by_query.get(query_id, set())}
        via_links = self.docs_by_query.get(query_id, set())
        return sorted(via_ratings | via_links)

    # ────────────────────────────────────────────
    # Mutators (all O(1) on average)
    # ────────────────────────────────────────────
    def add_document(self, doc: Document) -> None:
        """Adds a document. Complexity: O(1)."""
        if self.has_document(doc.id):
            log.debug(f"[add_document] exists doc_id={doc.id}")
            return
        self.docs[doc.id] = doc
        log.debug(f"[add_document] added doc_id={doc.id}")

    def add_query(self, query: Query) -> str:
        """Adds a query, handling text-based deduplication. Complexity: O(1).

        If a query with the same text exists, it links the new query's source
        document (if any) to the existing query and returns the existing ID.
        Otherwise, it adds the new query and returns its new ID.

        Returns:
            The query_id of the new or existing query.
        """


        if self.has_query(query.id):
            log.debug(f"[add_query] ignored_existing query_id={query.id}")
            return query.id

        # If a query with the same text already exists, link metadata and return its ID.
        if (existing_id := self.query_text_to_query_id.get(query.text)):
            log.debug(f"[add_query] duplicate_text text='{query.text}' existing_id={existing_id}")
            if query.generated_from_doc_id:
                self.add_document_to_query(existing_id, query.generated_from_doc_id)
            return existing_id

        # Otherwise, add the new query.
        self.queries[query.id] = query
        self.query_text_to_query_id[query.text] = query.id
        log.debug(f"[add_query] added query_id={query.id}")
        return query.id

    def add_document_to_query(self, query_id: str, doc_id: str) -> None:
        """Idempotently links a document to a query. Complexity: O(1).

        This records an association between a query and a document, which does not
        require a rating to exist. It's used to track all documents that are
        potentially relevant for a query.
        """
        if not self.has_query(query_id):
            log.warning(f"[add_document_to_query] query_not_found query_id={query_id}")
            return
        if not self.has_document(doc_id):
            log.warning(f"[add_document_to_query] doc_not_found doc_id={doc_id}")
            return
        if doc_id in self.docs_by_query.get(query_id, set()):
            log.debug(f"[add_document_to_query] already_linked q={query_id} d={doc_id}")
            return

        self.docs_by_query[query_id].add(doc_id)
        log.debug(f"[add_document_to_query] linked q={query_id} d={doc_id}")

    def add_rating(self, rating: Rating) -> None:
        """Add rating and maintain indices; avoid duplicate (q,d) pair. Complexity: O(1)."""
        if self.has_rating(rating.id):
            log.debug(f"[add_rating] rating_exists rating_id={rating.id}")
            return
        if not self.has_query(rating.query_id):
            log.warning(f"[add_rating] query_not_found query_id={rating.query_id}")
            return
        if not self.has_document(rating.doc_id):
            log.warning(f"[add_rating] doc_not_found doc_id={rating.doc_id}")
            return

        key = (rating.query_id, rating.doc_id)
        if key in self.rating_index:
            log.debug(f"[add_rating] duplicate_pair q={rating.query_id} d={rating.doc_id}")
            return

        self.ratings[rating.id] = rating
        self.rating_index[key] = rating.id
        self.ratings_by_query[rating.query_id].add(rating.id)
        self.add_document_to_query(*key)  # asegura enlace lógico
        log.debug(f"[add_rating] added rating_id={rating.id} q={rating.query_id} d={rating.doc_id}")

    def create_rating_score(
        self, query_id: str, doc_id: str, score: int, explanation: Optional[str] = None
    ) -> Optional[Rating]:
        """Create rating (if not exists) and add via `add_rating`. Complexity: O(1)."""
        if not self.has_query(query_id):
            log.debug(f"[create_rating_score] query_not_found query_id={query_id}")
            return None
        if not self.has_document(doc_id):
            log.debug(f"[create_rating_score] doc_not_found doc_id={doc_id}")
            return None

        rid = self.rating_index.get((query_id, doc_id))
        if rid:
            log.debug(f"[create_rating_score] existing q={query_id} d={doc_id} rating_id={rid}")
            return self.ratings[rid]

        try:
            rating = Rating(doc_id=doc_id, query_id=query_id, score=score, explanation=explanation)
            self.add_rating(rating)
            return rating
        except ValidationError as e:
            log.warning(f"[create_rating_score] validation_failed q={query_id} d={doc_id} score={score} error={e}")
            return None

    # ────────────────────────────────────────────
    # Persistence
    # ────────────────────────────────────────────
    def save(self) -> None:
        """Saves the entire DataStore to JSON. Complexity: O(N+M+P)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.parent / f"{self.path.name}.{uuid4().hex}.tmp"
        payload = {
            "docs":    [d.model_dump() for d in self.docs.values()],
            "queries": [q.model_dump() for q in self.queries.values()],
            "ratings": [r.model_dump() for r in self.ratings.values()],
        }
        try:
            tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding=ENCODING) # segmented on the temp 
            os.replace(tmp_path, self.path) # atomic operation on the prod. file
            log.info(f"[save] ok path={self.path} n_docs={len(self.docs)} n_queries={len(self.queries)} n_ratings={len(self.ratings)}")
        except Exception as e:
            log.exception(f"[save] fail path={self.path} err={e}")
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError as cleanup_error:
                    log.error(f"[save] cleanup_fail tmp_path={tmp_path} err={cleanup_error}")

    def load(self) -> None:
        """Loads from JSON and rebuilds indices. Complexity: O(N+M+P)."""
        if not self.path.exists():
            log.debug(f"[load] skip_missing path={self.path}")
            return

        self._clear_all_data()

        try:
            data = json.loads(self.path.read_text(encoding=ENCODING))
        except json.JSONDecodeError as e:
            log.error(f"[load] corrupt_json path={self.path} pos={getattr(e, 'pos', None)} msg={e}")
            return
        except Exception as e:
            log.exception(f"[load] io_error path={self.path} err={e}")
            return

        self.docs = {d["id"]: Document.model_validate(d) for d in data.get("docs", [])}
        self.queries = {q["id"]: Query.model_validate(q) for q in data.get("queries", [])}
        self._rebuild_indices(data.get("ratings", []))

        log.info(f"[load] ok path={self.path} n_docs={len(self.docs)} n_queries={len(self.queries)} n_ratings={len(self.ratings)}")

    def _clear_all_data(self) -> None:
        """Reset state."""
        self.docs.clear()
        self.queries.clear()
        self.ratings.clear()
        self.rating_index.clear()
        self.ratings_by_query.clear()
        self.docs_by_query.clear()
        self.query_text_to_query_id.clear()

    def _rebuild_indices(self, ratings_data: List[Dict]) -> None:
        """Rebuild secondary indices from loaded data."""
        
        # text-based deduplication index
        for q in self.queries.values():
            self.query_text_to_query_id[q.text] = q.id

        seen_pairs: Set[Tuple[str, str]] = set()
        for r in ratings_data:
            try:
                robj = Rating.model_validate(r)
                if not self.has_query(robj.query_id) or not self.has_document(robj.doc_id):
                    log.warning(f"[load] skip_rating_broken_ref rating_id={robj.id} q={robj.query_id} d={robj.doc_id}")
                    continue
                pair = (robj.query_id, robj.doc_id)
                if pair in seen_pairs:
                    log.warning(f"[load] skip_rating_duplicate_pair q={robj.query_id} d={robj.doc_id}")
                    continue
                seen_pairs.add(pair)
                self.add_rating(robj)  # update all indexes
            except ValidationError as e:
                log.warning(f"[load] skip_rating_invalid data={r} error={e}")

    def export_all_records_with_explanation(self, output_path: str | Path) -> None:
        """Export (query_text, doc_id, rating, explanation) to JSON."""
        records = [
            {
                "query": self.queries[r.query_id].text,
                "doc_id": r.doc_id,
                "rating": r.score,
                "explanation": r.explanation or ""
            }
            for r in self.ratings.values()
        ]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output_path.open("w", encoding=ENCODING) as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            log.info(f"[export] ok path={output_path} records={len(records)}")
        except Exception as e:
            log.exception(f"[export] fail path={output_path} err={e}")
