from __future__ import annotations

import logging
from typing import Dict, List
from src.schemas import Document, Query, Score
from src.logger import configure_logging

configure_logging(level=logging.INFO)
log = logging.getLogger(__name__)


class DataStore:
    """
    Public API for storing, managing documents, queries, and relevance scores.
    """

    def __init__(self):
        self.documents_dict: Dict[str, Document] = {}  # doc_id → document
        self.queries_dict: Dict[str, Query] = {}  # query_id → query

    def _get_query_object(self, query_id: str) -> Query:
        if query_id not in self.queries_dict:
            error_msg = f"Query id '{query_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)
        return self.queries_dict[query_id]

    def _get_document(self, doc_id: str) -> Document:
        if doc_id not in self.documents_dict:
            error_msg = f"Document id '{doc_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)
        return self.documents_dict[doc_id]

    def add_document(self, doc_id: str, document: Document) -> None:
        self.documents_dict[doc_id] = document

    def get_document(self, doc_id: str) -> Document:
        """
        Returns a document text or raises KeyError if the doc_id is not found.
        """
        return self._get_document(doc_id)

    def add_query(self, query_text: str, doc_id: str) -> str:
        """
        Returns the generated query id
        """
        score = Score(doc_id=doc_id)
        query_ = Query(text=query_text, scores={doc_id: score})
        self.queries_dict[query_.id] = query_
        return query_.id

    def get_queries(self) -> List[Query]:
        """
        Returns a list of all Query objects.
        """
        return list(self.queries_dict.values())

    def get_query(self, query_id: str) -> Query:
        """
        Returns a Query object or raises KeyError if the query_id is not found.
        """
        return self._get_query_object(query_id)

    def add_score(self, query_id: str, doc_id: str, score_value: int) -> None:
        """
        Adds relevance score associated with the given doc_id and query_id or raises KeyError
        if the query_id or doc_id is not found.
        """
        if query_id not in self.queries_dict:
            error_msg = f"Query '{query_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)

        if doc_id not in self.documents_dict:
            error_msg = f"Document '{doc_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)

        query_ = self.queries_dict[query_id]
        if doc_id in query_.scores:
            query_.scores[doc_id].value = score_value
        else:
            query_.scores[doc_id] = Score(doc_id=doc_id, value=score_value)

    def get_score(self, query_id: str, doc_id: str) -> int:
        """
        Returns the score for the given (query_id, doc_id) pair or raises KeyError if the query_id is not found
        or the doc_id is not associated with the query.
        """
        if query_id not in self.queries_dict:
            error_msg = f"Query '{query_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)

        if doc_id not in self.documents_dict:
            error_msg = f"Document '{doc_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)

        query_ = self.queries_dict[query_id]
        if doc_id in query_.scores:
            return query_.scores[doc_id].value
        raise KeyError(f"Document id '{doc_id}' not found for query id '{query_id}'")

    def has_score(self, query_id: str, doc_id: str) -> bool:
        """
        Returns True if the (query_id, doc_id) pair has a real score (i.e. != -1) or raises KeyError
        if query_id or doc_id isn’t found/linked.
        """
        if query_id not in self.queries_dict:
            error_msg = f"Query '{query_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)

        if doc_id not in self.documents_dict:
            error_msg = f"Document '{doc_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)

        score_value = self.get_score(query_id, doc_id)
        return score_value != -1
