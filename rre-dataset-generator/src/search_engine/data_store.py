from __future__ import annotations

import logging
import uuid
from typing import Dict, Tuple, List

from src.logger import configure_logging

configure_logging(level=logging.INFO)
log = logging.getLogger(__name__)


class DataStore:
    """
    Public API for storing, managing documents, queries, and relevance scores.
    """

    def __init__(self):
        self.documents: Dict[str, str] = {}  # doc_id → document text
        self.queries: Dict[str, QueryObject] = {}  # query_id → QueryObject

    def _get_query_object(self, query_id: str) -> QueryObject:
        if query_id not in self.queries:
            log.error("Query id %s not found in DataStore", query_id)
            raise KeyError(f"Query id '{query_id}' not found in DataStore")
        return self.queries[query_id]

    def _get_document(self, doc_id: str) -> str:
        if doc_id not in self.documents:
            log.error("Document id %s not found in DataStore", doc_id)
            raise KeyError(f"Document id '{doc_id}' not found in DataStore")
        return self.documents[doc_id]

    def add_document(self, doc_id: str, document: str) -> None:
        self.documents[doc_id] = document

    def get_document(self, doc_id: str) -> str:
        """
        Returns a document text or raises KeyError if the doc_id is not found.
        """
        return self._get_document(doc_id)

    def add_query(self, query: str, doc_id: str) -> str:
        """
        Returns generated query id
        """
        query_obj = QueryObject(query, doc_id)
        self.queries[query_obj.id] = query_obj
        return query_obj.id

    def get_queries(self) -> List[Tuple[str, List[str]]]:
        """
        Returns a list of all (query, doc_ids)
        """
        return [(query_obj.query, list(query_obj.doc_id_to_score.keys())) for query_obj in self.queries.values()]

    def get_query(self, query_id: str) -> Tuple[str, List[str]]:
        """
        Returns a tuple of (query, doc_ids) or raises KeyError if the query_id is not found.
        """
        query_obj = self._get_query_object(query_id)
        return query_obj.query, list(query_obj.doc_id_to_score.keys())

    def add_score(self, query_id: str, doc_id: str, score: float) -> None:
        """
        Adds relevance score associated with the given doc_id and query_id or raises KeyError
        if the query_id or doc_id is not found.
        """
        query_obj = self._get_query_object(query_id)

        self._get_document(doc_id)

        query_obj.add_score_for_query(doc_id, score)
        self.queries[query_id] = query_obj

    def get_score(self, query_id: str, doc_id: str) -> float:
        """
        Returns the score for the given (query_id, doc_id) pair or raises KeyError if the query_id is not found.
        """
        query_obj = self._get_query_object(query_id)
        return query_obj.doc_id_to_score[doc_id]

    def has_score(self, query_id: str, doc_id: str) -> bool:
        """
        Returns True if the (query_id, doc_id) pair has a real score (i.e. != -1) or raises KeyError
        if query_id or doc_id isn’t found/linked.
        """
        query_obj = self._get_query_object(query_id)
        return query_obj.has_score_for_query(doc_id)


class QueryObject:
    """
    QueryObject: holds the query text, its doc id → score mapping, and a generated unique id.
    """

    def __init__(self, query: str, doc_id: str):
        self.id: str = str(uuid.uuid4())
        self.query: str = query
        # mapping doc_id → score; score=-1 means doc is “not scored yet”
        self.doc_id_to_score: Dict[str, float] = {doc_id: -1.0}

    def add_score_for_query(self, doc_id: str, score: float) -> None:
        self.doc_id_to_score[doc_id] = score

    def has_score_for_query(self, doc_id: str) -> bool:
        """
        Returns True if this query has been scored for doc_id (i.e. score != -1) or raises KeyError
        if the doc_id is not linked to this query.
        """
        if doc_id not in self.doc_id_to_score:
            log.error("Document id %s is not associated with this query", doc_id)
            raise KeyError(f"Document id '{doc_id}' is not associated with this query")
        return self.doc_id_to_score[doc_id] != -1.0

