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
        # TODO: add normalizing function for the text keys (strip, lower, etc).
        ### Proposal: refactor utils clean_text() and import / reuse here

        if not ignore_saved_data:
            self.load()

    # ────────────────────────────────────────────
    # Existence checks
    # ────────────────────────────────────────────
    def has_document(self, doc_id: str) -> bool:
        """Checks for document existence."""
        return doc_id in self.docs

    def has_query(self, query_id: str) -> bool:
        """Checks for query existence."""
        return query_id in self.queries

    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        """Checks for a rating by (query, doc) pair."""
        return (query_id, doc_id) in self.rating_by_pair

    # ────────────────────────────────────────────
    # Getters
    # ────────────────────────────────────────────
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Gets a single document by its ID, or None if not found."""
        return self.docs.get(doc_id)

    def get_documents(self) -> List[Document]:
        """Gets all documents."""
        return list(self.docs.values())

    def get_query(self, query_id: str) -> Optional[Query]:
        """Gets a single query by its ID, or None if not found."""
        return self.queries.get(query_id)

    def get_queries(self) -> List[Query]:
        """Gets all queries."""
        return list(self.queries.values())

    def get_ratings(self) -> List[Rating]:
        """Gets all ratings."""
        return list(self.rating_by_pair.values())


    # ────────────────────────────────────────────
    # Mutators (all O(1) on average)
    # ────────────────────────────────────────────
    def add_document(self, doc: Document) -> None:
        """Adds a document."""
        if self.has_document(doc.id):
            log.warning(f"[add_document] exists doc_id={doc.id}")
            return
        self.docs[doc.id] = doc
        log.debug(f"[add_document] added doc_id={doc.id}")

    def add_query(self, query_text_str: str, id: Optional[str] = None) -> Query:
        """Adds a new query. If text is cached, returns existing Query. If id is given, it's used."""
        if (existing_id := self.query_text_to_query_id.get(query_text_str)):
            log.warning(f"[add_query] exists text='{query_text_str}' existing_id={existing_id}")
            return self.queries[existing_id]

        query = Query(id=id, text=query_text_str) if id else Query(text=query_text_str)
        self.queries[query.id] = query
        self.query_text_to_query_id[query_text_str] = query.id
        log.debug(f"[add_query] added query_id={query.id}")
        return query

    def _add_rating(self, rating: Rating) -> None:
        """Adds a rating."""
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
        """Create rating (if not exists) and add via `add_rating`."""

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
        
    def load(self) -> None:
        if not self.path.exists():
            return

        # Clear previous data
        self._clear_all_data()

        try:
            data = json.loads(self.path.read_text(encoding=ENCODING))
        except json.JSONDecodeError as e:
            log.warning(f"Could not read datastore {self.path} (JSON). Starting clean. Error: {e}")
            return

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
                self.add_query(query_text_str=tmp_query.text, id=tmp_query.id) # Pass (text, ID) values to keep ID consistent
            except ValidationError as e:
                log.warning(f"[load] skip_query_invalid data={query_as_dict} error={e}")

        # ratings
        for rating_as_dict in data.get("ratings", []):
            try:
                robj = Rating.model_validate(rating_as_dict)
                self._add_rating(robj)
            except ValidationError as e:
                log.warning(f"[load] skip_rating_invalid data={rating_as_dict} error={e}")

    def _clear_all_data(self) -> None:
        """Reset state."""
        self.docs.clear()
        self.queries.clear()
        self.rating_by_pair.clear()
        self.query_text_to_query_id.clear()


    def export_all_records_with_explanation(self, output_path: str | Path) -> None:
        """Export (query_text, doc_id, rating, explanation) to JSON."""
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
