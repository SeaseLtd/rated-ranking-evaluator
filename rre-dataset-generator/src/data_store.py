from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple, List

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
    - A (query_id, doc_id) pair is unique within `rating_by_pair`.
    - `has_rating_score` is True only if a `Rating` object exists for the pair (query_id, document_id).
    """

    def __init__(self, path: Path = TMP_FILE, ignore_saved_data: bool = False):
        self.path = path

        # Primary (id → object)
        self.docs: Dict[str, Document] = {}
        self.queries: Dict[str, Query] = {}

        # Ratings storage
        self.rating_by_pair: Dict[Tuple[str, str], Rating] = {}    # (query_id, doc_id) → Rating 

        # Text based deduplication for queries
        self.query_text_to_query_id: Dict[str, str] = {}           # query_text → query_id 
        # TODO: add normalizing function to text for query_text_to_query_id (strip, lower, etc).
        ### Proposal: refactor utils clean_text() and import / reuse here

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

    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        """Checks for a rating by (query, doc) pair. Complexity: O(1)."""
        return (query_id, doc_id) in self.rating_by_pair

    def has_rating(self, rating_id: str) -> bool:
        """Checks for rating existence by rating_id. O(P)"""
        return any(r.id == rating_id for r in self.rating_by_pair.values())

    # ────────────────────────────────────────────
    # Getters
    # ────────────────────────────────────────────
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Gets a single document by its ID, or None if not found."""
        return self.docs.get(doc_id)

    def get_documents(self) -> List[Document]:
        """Gets all documents. Complexity: O(N) where N is the number of docs."""
        return list(self.docs.values())

    def get_query(self, query_id: str) -> Optional[Query]:
        """Gets a single query by its ID, or None if not found."""
        return self.queries.get(query_id)

    def get_queries(self) -> List[Query]:
        """Gets all queries. Complexity: O(M) where M is the number of queries."""
        return list(self.queries.values())

    def get_ratings(self) -> List[Rating]:
        """Gets all ratings. Complexity: O(P) where P is the number of ratings."""
        return list(self.rating_by_pair.values())


    # ────────────────────────────────────────────
    # Mutators (all O(1) on average)
    # ────────────────────────────────────────────
    def add_document(self, doc: Document) -> None:
        """Adds a document. Complexity: O(1)."""
        if self.has_document(doc.id):
            log.warning(f"[add_document] exists doc_id={doc.id}")
            return
        self.docs[doc.id] = doc
        log.debug(f"[add_document] added doc_id={doc.id}")

    def add_query(self, query: Query) -> str:
        """Adds a new query only if the Query.text is not already cached. 
        If the query text is already cached, return the existing query ID. O(1)."""
        key = query.text
        if (existing_id := self.query_text_to_query_id.get(key)):
            log.warning(f"[add_query] exists text='{query.text}' existing_id={existing_id}")
            return existing_id

        self.queries[query.id] = query
        self.query_text_to_query_id[key] = query.id
        log.debug(f"[add_query] added query_id={query.id}")
        return query.id

    def _add_rating(self, rating: Rating) -> None:
        """Adds a rating. Complexity: O(1)."""
        if not self.has_query(rating.query_id):
            log.warning(f"[add_rating] query_not_found query_id={rating.query_id}")
            return
        if not self.has_document(rating.doc_id):
            log.warning(f"[add_rating] doc_not_found doc_id={rating.doc_id}")
            return

        key = (rating.query_id, rating.doc_id)
        if key in self.rating_by_pair:
            log.warning(f"[add_rating] exists q={rating.query_id} d={rating.doc_id}")
            return

        self.rating_by_pair[key] = rating 
        log.debug(f"[add_rating] added q={rating.query_id} d={rating.doc_id}")

    def create_rating_score(
        self, query_id: str, doc_id: str, score: int, explanation: Optional[str] = None
    ) -> Optional[Rating]:
        """Create rating (if not exists) and add via `add_rating`. Complexity: O(1)."""
        if not self.has_query(query_id):
            log.warning(f"[create_rating_score] query_not_found query_id={query_id}")
            return None
        if not self.has_document(doc_id):
            log.warning(f"[create_rating_score] doc_not_found doc_id={doc_id}")
            return None

        key = (query_id, doc_id)
        if (existing_rating := self.rating_by_pair.get(key)):
            log.warning(f"[create_rating_score] existing q={query_id} d={doc_id}")
            return existing_rating

        try:
            rating = Rating(doc_id=doc_id, query_id=query_id, score=score, explanation=explanation)
            self._add_rating(rating)
            return rating
        except ValidationError as e:
            log.warning(f"[create_rating_score] validation_failed q={query_id} d={doc_id} score={score} error={e}")
            return None

    # ────────────────────────────────────────────
    # Persistence
    # ────────────────────────────────────────────
    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "docs": [d.model_dump() for d in self.docs.values()],
            "queries": [q.model_dump() for q in self.queries.values()],
            "ratings": [r.model_dump() for r in self.rating_by_pair.values()],
        }
        tmp_path = self.path.with_name(self.path.name + f".{uuid4().hex}.tmp")
        tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding=ENCODING)
        os.replace(tmp_path, self.path)
        log.info("[save] ok path=%s n_docs=%d n_queries=%d n_ratings=%d",
                self.path, len(self.docs), len(self.queries), len(self.rating_by_pair))

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding=ENCODING))
        except json.JSONDecodeError as e:
            log.warning("Could not read datastore %s (JSON). Starting clean. Error: %s", self.path, e)
            self._clear_all_data()
            return

        self._clear_all_data()

        # docs
        for d in data.get("docs", []):
            try:
                self.add_document(Document.model_validate(d))
            except ValidationError as e:
                log.warning("[load] skip_doc_invalid data=%s error=%s", d, e)

        # queries
        for q in data.get("queries", []):
            try:
                self.add_query(Query.model_validate(q))
            except ValidationError as e:
                log.warning("[load] skip_query_invalid data=%s error=%s", q, e)

        # ratings
        for r in data.get("ratings", []):
            try:
                robj = Rating.model_validate(r)
            except ValidationError as e:
                log.warning("[load] skip_rating_invalid data=%s error=%s", r, e)
                continue
            self._add_rating(robj)  # verifies refs and creates query→doc link


    def _clear_all_data(self) -> None:
        """Reset state."""
        self.docs.clear()
        self.queries.clear()
        self.rating_by_pair.clear()
        self.query_text_to_query_id.clear()


    def export_all_records_with_explanation(self, output_path: str | Path) -> None:
        """Export (query_text, doc_id, rating, explanation) to JSON."""
        records = []
        for r in self.rating_by_pair.values():
            # Guard against dangling references (defensive)
            q = self.queries.get(r.query_id)
            if not q:
                continue
            records.append({
                "query": q.text,
                "doc_id": r.doc_id,
                "rating": r.score,
                "explanation": r.explanation or ""
            })

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output_path.open("w", encoding=ENCODING) as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            log.info("[export] ok path=%s records=%d", output_path, len(records))
        except Exception as e:
            log.warning("[export] fail path=%s err=%s", output_path, e)
