from __future__ import annotations
from typing import Dict, Optional, Tuple, Set, List
from collections import defaultdict
from pathlib import Path
import json, os, logging
from uuid import uuid4

from pydantic import ValidationError
from src.model import Document, Query, Rating

log = logging.getLogger(__name__)

TMP_FILE = Path("./tmp/datastore.json")

class DataStore:
    def __init__(self, path: Path = TMP_FILE, ignore_saved_data: bool = False):
        self.path = path

        # Primary Storage (O(1) access)
        # id  ─>  Pydantic-validated object 
        self.docs: Dict[str, Document] = {}
        self.queries: Dict[str, Query] = {}
        self.ratings: Dict[str, Rating] = {}

        # Secondary Storage (O(1) access)
        # Fast access: avoid re-looping + checks over primary storage
        self.rating_index: Dict[Tuple[str, str], str] = {}               # (query_id, doc_id) -> rating_id
        self.ratings_by_query: Dict[str, Set[str]] = defaultdict(set)    # query_id -> [rating_ids]
        self.docs_by_query: Dict[str, Set[str]] = defaultdict(set)       # query_id -> [doc_ids] 

        if not ignore_saved_data:
            self.load()

    # ---------- checks - O(1) ----------
    def has_doc(self, doc_id: str) -> bool: return doc_id in self.docs
    def has_query(self, query_id: str) -> bool: return query_id in self.queries
    def has_rating(self, rating_id: str) -> bool: return rating_id in self.ratings
    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        return (query_id, doc_id) in self.rating_index

    # ---------- getters - O(1) ----------
    def get_doc(self, doc_id: str) -> Document: return self.docs[doc_id]
    def get_docs(self) -> List[Document]: return list(self.docs.values())
    def get_query(self, query_id: str) -> Query: return self.queries[query_id]
    def get_queries(self) -> List[Query]: return list(self.queries.values())
    def get_rating(self, rating_id: str) -> Rating: return self.ratings[rating_id]
    def get_ratings(self) -> List[Rating]: return list(self.ratings.values())

    # Used in the Abstract Writer
    def get_rating_score(self, query_id: str, doc_id: str) -> Optional[int]:
        if query_id not in self.queries:
            log.debug(f"[get_rating_score] query_not_found query_id={query_id}")  
            return None
        if doc_id not in self.docs:
            log.debug(f"[get_rating_score] doc_not_found doc_id={doc_id}")  
            return None
        rid = self.rating_index.get((query_id, doc_id))
        return self.ratings[rid].score if rid else None

    # ---------- getters - O(k) ----------

    def get_ratings_for_query(self, query_id: str) -> List[Rating]:
        """List ratings of a query (O(k log k)) in a deterministic order (by rating_id)."""
        if query_id not in self.queries:
            log.debug(f"[get_ratings_for_query] query_not_found query_id={query_id}")  
            raise KeyError(f"Query {query_id} not found")
        ids = self.ratings_by_query.get(query_id, set())
        # sort by rating_id (deterministic) 
        return [self.ratings[rid] for rid in sorted(ids)]

    def get_doc_ids_for_query(self, query_id: str) -> List[str]:
        """Retrieve doc_ids associated to the query_id"""
        if query_id not in self.queries:
            log.debug(f"[get_doc_ids_for_query] query_not_found query_id={query_id}")  
            raise KeyError(f"Query {query_id} not found")
        via_ratings = set(self.ratings[rid].doc_id for rid in self.ratings_by_query.get(query_id, set()))
        via_links = set(self.docs_by_query.get(query_id, set()))
        return sorted(via_ratings | via_links)

    # ---------- commands ----------
    def add_doc(self, doc: Document) -> None:
        if doc.id in self.docs:
            log.debug(f"[add_doc] exists doc_id={doc.id}")
            return
        self.docs[doc.id] = doc
        log.debug(f"[add_doc] added doc_id={doc.id}")  

    def add_query(self, query: Query) -> None:
        if query.id in self.queries:
            log.debug(f"[add_query] exists query_id={query.id}")
            return
        self.queries[query.id] = query
        log.debug(f"[add_query] added query_id={query.id}")  

    def add_doc_to_query(self, query_id: str, doc_id: str) -> None:
        """Maintains an index of all documents ever associated with a query."""
        if query_id not in self.queries:
            log.warning(f"[add_doc_to_query] query_not_found query_id={query_id}")
            return
        if doc_id not in self.docs:
            log.warning(f"[add_doc_to_query] doc_not_found doc_id={doc_id}")
            return
        self.docs_by_query[query_id].add(doc_id)
        log.debug(f"[add_doc_to_query] linked query_id={query_id} doc_id={doc_id}")  

    def add_rating(self, rating: Rating) -> None:
        """Creates a rating if no other exists for (query, doc). Maintains indices."""
        if rating.id in self.ratings:
            log.debug(f"[add_rating] rating_exists rating_id={rating.id}")
            return
        if rating.query_id not in self.queries:
            log.warning(f"[add_rating] query_not_found query_id={rating.query_id}")
            return
        if rating.doc_id not in self.docs:
            log.warning(f"[add_rating] doc_not_found doc_id={rating.doc_id}")
            return

        key = (rating.query_id, rating.doc_id)
        if key in self.rating_index:
            log.debug(f"[add_rating] rating_for_pair_exists q={rating.query_id} d={rating.doc_id}")
            return

        # Update in-memory references for fast access
        self.ratings[rating.id] = rating
        self.rating_index[key] = rating.id
        self.ratings_by_query[rating.query_id].add(rating.id)
        log.debug(f"[add_rating] added rating_id={rating.id} q={rating.query_id} d={rating.doc_id}")  
        

    def create_rating_score(self, query_id: str, doc_id: str, score: int) -> Optional[Rating]:
        """Create a rating score if no other exists for (query_id, doc_id)."""
        if query_id not in self.queries:
            log.debug(f"[create_rating_score] query_not_found query_id={query_id}")  
            return None
        if doc_id not in self.docs:
            log.debug(f"[create_rating_score] doc_not_found doc_id={doc_id}")  
            return None

        key = (query_id, doc_id)
        rid = self.rating_index.get(key)
        if rid:
            log.debug(f"[create_rating_score] rating_for_pair_exists q={query_id} d={doc_id} rating_id={rid}")  
            return self.ratings[rid]
        
        # Create rating object with validation (NonNegativeInt)
        try:
            rating = Rating(doc_id=doc_id, query_id=query_id, score=score)
            # Add rating to in-memory dict
            self.add_rating(rating)
            # Add doc to query in-memory dict
            self.add_doc_to_query(*key)
            return rating
        except ValidationError as e:
            log.debug(f"[create_rating_score] validation_failed q={query_id} d={doc_id} score={score} error={e}")
            return None

    # ---------- persistence ----------
    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + f".{uuid4().hex}.tmp")
        payload = {
            "docs":    [d.model_dump() for d in self.docs.values()],
            "queries": [q.model_dump() for q in self.queries.values()],
            "ratings": [r.model_dump() for r in self.ratings.values()],
        }
        try:  
            tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            os.replace(tmp_path, self.path)  # atomic
            log.info(f"[save] ok path={self.path} n_docs={len(self.docs)} n_queries={len(self.queries)} n_ratings={len(self.ratings)}")  
        except Exception as e:  
            # cleanup tmp
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
            log.exception(f"[save] fail path={self.path} err={e}")  

    def load(self) -> None:
        """Load JSON file and rebuild transient indices."""
        if not self.path.exists():
            log.debug(f"[load] skip_missing path={self.path}")  
            return

        # Clean object lists
        self.docs.clear()
        self.queries.clear()
        self.ratings.clear()

        # Clean in-memory dicts
        self.rating_index.clear()
        self.ratings_by_query.clear()
        self.docs_by_query.clear()

        try:
            raw = self.path.read_text()
            data = json.loads(raw)
        except json.JSONDecodeError as e:  
            log.error(f"[load] corrupt_json path={self.path} pos={getattr(e, 'pos', None)} msg={e}")
            return
        except Exception as e:  
            log.exception(f"[load] io_error path={self.path} err={e}")
            return

        for d in data.get("docs", []):
            self.docs[d["id"]] = Document.model_validate(d)
        for q in data.get("queries", []):
            self.queries[q["id"]] = Query.model_validate(q)

        # Load valid ratings and rebuild in-memory dicts
        seen_pairs = set()
        for r in data.get("ratings", []):
            
            robj = Rating.model_validate(r)

            if robj.query_id not in self.queries or robj.doc_id not in self.docs:
                log.debug(f"[load] skip_rating_broken_ref rating_id={robj.id} q={robj.query_id} d={robj.doc_id}")  
                continue

            pair = (robj.query_id, robj.doc_id)
            if pair in seen_pairs:
                log.debug(f"[load] skip_rating_duplicate_pair rating_id={robj.id} q={robj.query_id} d={robj.doc_id}")  
                continue

            # Keep Track of seen pairs
            seen_pairs.add(pair)
            #  Update in-memory indices
            self.add_rating(robj)
            self.add_doc_to_query(*pair)

        log.info(f"[load] ok path={self.path} n_docs={len(self.docs)} n_queries={len(self.queries)} n_ratings={len(self.ratings)}")  
