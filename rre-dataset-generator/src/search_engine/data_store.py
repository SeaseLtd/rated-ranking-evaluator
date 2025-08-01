from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.model.document import Document
from src.model.query_rating_context import QueryRatingContext

log = logging.getLogger(__name__)


TMP_FILE = "./tmp/datastore.json"

class DataStore:
    """
    Stores/retrieves documents, queries, and rating scores.
    """
    def __init__(self, ignore_saved_data: bool = False):
        self._documents: Dict[str, Document] = {}
        self._queries_by_id: Dict[str, QueryRatingContext] = {}
        self._query_text_to_query_id: Dict[str, str] = {}

        # Load from default file if present
        if not ignore_saved_data and os.path.exists(TMP_FILE):
            try:
                self.load_tmp_file_content()
                log.debug(f"Loaded DataStore from default file: {TMP_FILE}")
            except Exception as e:
                log.error(f"Could not load default datastore file '{TMP_FILE}': {e}")

    def _get_query_rating_context_by_id(self, query_id: str) -> QueryRatingContext:
        if query_id not in self._queries_by_id:
            _error_msg = f"Query id {query_id} not found in DataStore"
            log.error(_error_msg)
            raise KeyError(_error_msg)
        return self._queries_by_id[query_id]

    def _get_document(self, doc_id: str) -> Optional[Document]:
        if doc_id not in self._documents:
            _warning_msg = f"Detected an error when retrieving a document from the data store. Document {doc_id} not found in DataStore"
            log.warning(_warning_msg)
            return None
        return self._documents[doc_id]

    def add_document(self, doc_id: str, document: Document) -> None:
        if doc_id in self._documents:
            _error_msg = f"Detected an error when adding document to the data store. Document {doc_id} already present."
            log.error(_error_msg)
            raise KeyError(_error_msg)
        self._documents[doc_id] = document

    def has_document(self, doc_id: str) -> bool:
        """
        Returns True if Document with the given id exists, False otherwise.
        """
        return doc_id in self._documents

    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Returns the Document with the given ID, or None if not found.
        """
        return self._get_document(doc_id)

    def get_documents(self) -> List[Document]:
        """
        Returns a list of Document objects."
        """
        return list(self._documents.values())

    def add_query(self, query: str, doc_id: str | None = None) -> str:
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
        context = QueryRatingContext(query=query, doc_id=doc_id)
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
        context: QueryRatingContext = self._get_query_rating_context_by_id(query_id)
        context.add_rating_score(doc_id, rating_score)
        self._queries_by_id[query_id] = context

    def get_rating_score(self, query_id: str, doc_id: str) -> int:
        """
        Returns the rating score for the given (query_id, doc_id) pair or raises KeyError if the query_id is not found.
        """
        context: QueryRatingContext = self._get_query_rating_context_by_id(query_id)
        return context.get_rating_score(doc_id)

    def has_rating_score(self, query_id: str, doc_id: str) -> bool:
        """
        Returns True if the (query_id, doc_id) pair has a rating score (i.e. != -1) or raises KeyError
        if query_id is not found.
        """
        context: QueryRatingContext = self._get_query_rating_context_by_id(query_id)
        return context.has_rating_score(doc_id)


    @staticmethod
    def ensure_tmp_file_exists() -> Path:
        """Checks if a file exists on disk and returns its path or create the parent folder.
        Resolves a given path and logs a warning if the file does not exist.

        Returns:
            The resolved path as a Path object.
        """
        path = Path(TMP_FILE)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            log.debug(f'Previous file not found in DataStore: {path}')
        return path

    def save_tmp_file_content(self) -> None:
        """Saves the current state to a file on disk serializing queries, ratings, and optionally documents.

        Args:
            filepath: The path to the file where the data will be saved.
                      If None, a default path is used.
        """
        path = self.ensure_tmp_file_exists()

        def default_serializer(obj):
            """Default function to handle non-serializable objects"""
            if isinstance(obj, QueryRatingContext):
                return obj.to_dict()
            elif isinstance(obj, Document):
                return obj.model_dump()
            else:
                # Convert to string as fallback
                return str(obj)

        data = {
            "queries": self._queries_by_id,
            "documents": self._documents,
        }

        # save the content to a file
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=default_serializer)


    def load_tmp_file_content(self) -> None:
        """Loads state from a file on disk loading queries, ratings, and documents from a unified
        JSON file on disk.

        Args:
            filepath: The path to the file to load data from. If None, a
                      default path is used.
            clear: If True, clears existing data before loading.
                   Defaults to None.
        """

        self._documents.clear()
        self._queries_by_id.clear()
        self._query_text_to_query_id.clear()
        
        filepath = self.ensure_tmp_file_exists()

        with filepath.open("r", encoding="utf-8") as f:
            file_content = json.load(f)

        queries: Dict[str, Dict[str, Any]] = file_content.get("queries", {})
        for query_id, context_dict in queries.items():
            context: QueryRatingContext = QueryRatingContext.from_dict(context_dict)
            self._queries_by_id[query_id] = context
            self._query_text_to_query_id[context.get_query()] = query_id

        documents = file_content.get("documents", {})
        for doc_id, doc_data in documents.items():
            self.add_document(doc_id, Document.model_validate(doc_data))

