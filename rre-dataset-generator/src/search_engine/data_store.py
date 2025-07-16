from __future__ import annotations

import logging
from typing import Dict, List, Literal
from src.schemas import Document, Query, Score
from src.logger import configure_logging

configure_logging(level=logging.INFO)
log = logging.getLogger(__name__)

EntityType = Literal['document', 'query']

class DataStore:
    """
    Public API for storing, managing documents, queries, and relevance scores.
    """

    def __init__(self):
        self.documents_dict: Dict[str, Document] = {}  # doc_id → document
        self.queries_dict: Dict[str, Query] = {}  # query_id → query

    def _validate_entity_exists(self, entity_id: str, entity_type: EntityType) -> None:
        """Centralized validation for entity existence."""
        if entity_type == 'document' and entity_id not in self.documents_dict:
            error_msg = f"Document '{entity_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)
        elif entity_type == 'query' and entity_id not in self.queries_dict:
            error_msg = f"Query '{entity_id}' not found in DataStore"
            log.error(error_msg)
            raise KeyError(error_msg)

    def _get_query_object(self, query_id: str) -> Query:
        """Get query object with validation."""
        self._validate_entity_exists(query_id, 'query')
        return self.queries_dict[query_id]

    def _get_document(self, doc_id: str) -> Document:
        """Get document with validation."""
        self._validate_entity_exists(doc_id, 'document')
        return self.documents_dict[doc_id]

    def add_document(self, doc_id: str, document: Document) -> None:
        """Add a document to the store."""
        self.documents_dict[doc_id] = document

    def get_document(self, doc_id: str) -> Document:
        """Returns a document or raises KeyError if the doc_id is not found."""
        return self._get_document(doc_id)

    def add_query(self, query_text: str, doc_id: str) -> str:
        """
        Creates a new query with a default score for the given document.
        Returns the generated query id.
        """
        self._validate_entity_exists(doc_id, 'document')
        score = Score(doc_id=doc_id)
        query_ = Query(text=query_text, scores={doc_id: score})
        self.queries_dict[query_.id] = query_
        return query_.id

    def get_queries(self) -> List[Query]:
        """Returns a list of all Query objects."""
        return list(self.queries_dict.values())

    def get_query(self, query_id: str) -> Query:
        """Returns a Query object or raises KeyError if the query_id is not found."""
        return self._get_query_object(query_id)

    def add_score(self, query_id: str, doc_id: str, score_value: int) -> None:
        """
        Adds or updates a relevance score for a document-query pair.
        Raises KeyError if query_id or doc_id is not found.
        """
        self._validate_entity_exists(query_id, 'query')
        self._validate_entity_exists(doc_id, 'document')
        
        query_ = self.queries_dict[query_id]
        query_.scores[doc_id] = Score(doc_id=doc_id, value=score_value)

    def get_score(self, query_id: str, doc_id: str) -> int:
        """
        Returns the score for the given (query_id, doc_id) pair.
        Raises KeyError if query_id is not found, doc_id is not found,
        or the doc_id is not associated with the query.
        """
        self._validate_entity_exists(query_id, 'query')
        self._validate_entity_exists(doc_id, 'document')
        
        query_ = self.queries_dict[query_id]
        if doc_id not in query_.scores:
            raise KeyError(f"Document id '{doc_id}' not found for query id '{query_id}'")
        return query_.scores[doc_id].value

    def has_score(self, query_id: str, doc_id: str) -> bool:
        """
        Returns True if the (query_id, doc_id) pair has a real score (i.e. != -1).
        Raises KeyError if query_id or doc_id isn't found/linked.
        """
        try:
            score_value = self.get_score(query_id, doc_id)
            return score_value != -1
        except KeyError:
            return False
