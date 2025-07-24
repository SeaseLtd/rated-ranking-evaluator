from __future__ import annotations

import logging
from typing import Dict, List, Optional

from src.model.document import Document
from src.model.query_rating_context import QueryRatingContext

log = logging.getLogger(__name__)


class DataStore:
    """
    Stores/retrieves documents, queries, and rating scores.
    """

    def __init__(self):
        self._documents: Dict[str, Document] = {}  # doc_id -> Document
        self._queries_by_id: Dict[str, QueryRatingContext] = {}  # query_id → QueryRatingContext
        self._query_text_to_query_id: Dict[str, str] = {}  # query_text -> query_id

    def _get_query_rating_context_by_id(self, query_id: str) -> QueryRatingContext:
        if query_id not in self._queries_by_id:
            log.error("Query id %s not found in DataStore", query_id)
            raise KeyError(f"Query id '{query_id}' not found in DataStore")
        return self._queries_by_id[query_id]

    def _get_document(self, doc_id: str) -> Optional[Document]:
        if doc_id not in self._documents:
            log.warning("Document id %s not found in DataStore", doc_id)
            return None
        return self._documents[doc_id]

    def add_document(self, doc_id: str, document: Document) -> None:
        if doc_id in self._documents:
            log.error("Document  id %s found in DataStore", doc_id)
            raise KeyError(f"Document id '{doc_id}' found in DataStore")
        self._documents[doc_id] = document

    def has_document(self, doc_id: str) -> bool:
        """
        Returns True if Document with the given id exists, False otherwise.
        """
        return doc_id in self._documents

    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Returns Document or None.
        """
        return self._get_document(doc_id)

    def get_documents(self) -> List[Document]:
        """
        Returns a list of Document.
        """
        return list(self._documents.values())

    def add_query(self, query: str, doc_id: str = None) -> str:
        """
        If `query` already exists, just adds `doc_id` to it.
        Otherwise, creates a new QueryRatingContext.
        Returns the query_id.
        """
        if query in self._query_text_to_query_id:
            query_id = self._query_text_to_query_id[query]
            context = self._queries_by_id[query_id]
            if doc_id is not None:
                context.add_doc_id(doc_id)
            return query_id

        # new query rating context
        context = QueryRatingContext(query, doc_id)
        query_id = context.get_query_id()
        self._queries_by_id[query_id] = context
        self._query_text_to_query_id[query] = query_id
        return query_id

    def get_queries(self) -> List[QueryRatingContext]:
        """
        Returns a list of all QueryRatingContext objects.
        """
        return list(self._queries_by_id.values())

    def get_query(self, query_id: str) -> QueryRatingContext:
        """
        Returns QueryRatingContext object or raises KeyError if the query_id is not found.
        """
        return self._get_query_rating_context_by_id(query_id)

    def add_rating_score(self, query_id: str, doc_id: str, rating_score: int) -> None:
        """
        Adds rating score associated with the given doc_id and query_id or raises KeyError
        if the query_id is not found.
        """
        context = self._get_query_rating_context_by_id(query_id)

        context.add_rating_score(doc_id, rating_score)
        self._queries_by_id[query_id] = context

    def get_rating_score(self, query_id: str, doc_id: str) -> int:
        """
        Returns the rating score for the given (query_id, doc_id) pair or raises KeyError if the query_id is not found.
        """
        context = self._get_query_rating_context_by_id(query_id)
        return context.get_rating_score(doc_id)

    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        """
        Returns True if the (query_id, doc_id) pair has a rating score (i.e. != -1) or raises KeyError
        if query_id is not found.
        """
        context = self._get_query_rating_context_by_id(query_id)
        return context.has_rating_score(doc_id)

