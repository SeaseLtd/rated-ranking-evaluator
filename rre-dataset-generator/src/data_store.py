from pathlib import Path
import json
from typing import Dict
from src.model import Document, Query, Rating
import logging
from uuid import uuid4
import os

log = logging.getLogger(__name__)

TMP_FILE = Path("./tmp/datastore.json")

class DataStore:
    def __init__(self, path: Path = TMP_FILE, ignore_saved_data: bool = False):
        self.path = path
        self.docs: Dict[str, Document] = {}
        self.queries: Dict[str, Query] = {}
        self.ratings: Dict[str, Rating] = {} 
        
        self.rating_index: Dict[tuple[str, str], str] = {}
        # (query_id, doc_id) -> rating_id - cache for quick access / deduplication

        if not ignore_saved_data:
            self.load()

    # ---------- checks ----------
    def has_doc(self, doc_id: str) -> bool: return doc_id in self.docs
    def has_query(self, query_id: str) -> bool: return query_id in self.queries
    def has_rating(self, rating_id: str) -> bool: return rating_id in self.ratings

    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        return self.get_rating_score(query_id, doc_id) is not None

    # ---------- getters ----------
    def get_doc(self, doc_id: str) -> Document: return self.docs[doc_id]
    def get_docs(self) -> list[Document]: return list(self.docs.values())
    
    def get_query(self, query_id: str) -> Query: return self.queries[query_id]
    def get_queries(self)   -> list[Query]: return list(self.queries.values())
    
    def get_rating(self, rating_id: str) -> Rating: return self.ratings[rating_id]
    def get_ratings(self) -> list[Rating]: return list(self.ratings.values())

    def get_rating_score(self, query_id: str, doc_id: str) -> int | None:
        if query_id not in self.queries:
            log.error(f"Query {query_id} not found")
            return 
        if doc_id not in self.docs:
            log.error(f"Document {doc_id} not found")
            return 
        for rating_id in self.queries[query_id].related_ratings_ids:
            rating = self.ratings[rating_id]
            if rating.doc_id == doc_id:
                return rating.score
        return None
    
    # ---------- commands ----------
    def add_doc(self, doc: Document) -> None:
        if doc.id in self.docs:
            log.error(f"Document {doc.id} already exists")
            return 
        self.docs[doc.id] = doc

    def add_query(self, query: Query) -> None:
        if query.id in self.queries:
            log.error(f"Query {query.id} already exists")
            return 
        self.queries[query.id] = query

    def add_rating(self, rating: Rating) -> None:
        if rating.id in self.ratings:
            log.error(f"Rating {rating.id} already exists")
            return 
        self.ratings[rating.id] = rating
        # maintain rating index for quick access / deduplication
        self.rating_index[(rating.query_id, rating.doc_id)] = rating.id

    def add_doc_to_query(self, query_id: str, doc_id: str) -> None:
        if query_id not in self.queries:
            log.error(f"Query {query_id} not found")
            return 
        if doc_id not in self.docs:
            log.error(f"Document {doc_id} not found")
            return 
        self.queries[query_id].add_doc(self.docs[doc_id])
    
    def add_rating_score(self, query_id: str, doc_id: str, score: int) -> str:
        if query_id not in self.queries: 
            raise KeyError(f"Query {query_id} not found")
        if doc_id not in self.docs: 
            raise KeyError(f"Document {doc_id} not found")

        key = (query_id, doc_id)
        rating_id = self.rating_index.get(key)
        if rating_id:
            self.ratings[rating_id].score = score
            return rating_id

        rating = Rating(doc_id=doc_id, query_id=query_id, score=score)
        self.add_rating(rating)
        self.queries[query_id].add_rating(rating)
        # optional: assure doc<->query
        if doc_id not in self.queries[query_id].doc_ids:
            self.queries[query_id].doc_ids.append(doc_id)
        return rating.id
    

    # ---------- persistance ----------
    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + f".{uuid4().hex}.tmp")
        payload = {
            "docs": [d.model_dump() for d in self.docs.values()],
            "queries": [q.model_dump() for q in self.queries.values()],
            "ratings": [r.model_dump() for r in self.ratings.values()],
        }
        tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        os.replace(tmp_path, self.path)  # better practice - avoid being hanged

    def load(self) -> None:
        if not self.path.exists(): return
        self.docs.clear(); self.queries.clear(); self.ratings.clear(); self.rating_index.clear()

        data = json.loads(self.path.read_text())
        for d in data.get("docs", []):
            self.docs[d["id"]] = Document.model_validate(d)
        for q in data.get("queries", []):
            self.queries[q["id"]] = Query.model_validate(q)
        for r in data.get("ratings", []):
            robj = Rating.model_validate(r)
            self.ratings[robj.id] = robj
            # populate rating index for loaded data
            self.rating_index[(robj.query_id, robj.doc_id)] = robj.id

