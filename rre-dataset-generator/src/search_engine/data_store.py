from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.model.document import Document
from src.model.query_rating_context import QueryRatingContext

log = logging.getLogger(__name__)

class DataStore:
    """
    Stores/retrieves documents, queries, and rating scores.
    """

    def __init__(self):
        self._documents: Dict[str, Document] = {}                # doc_id -> Document
        self._queries_by_id: Dict[str, QueryRatingContext] = {}  # query_id → QueryRatingContext
        self._query_text_to_query_id: Dict[str, str] = {}        # query_text -> query_id

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

    
    def save_queries_and_docs(self, filepath: str | Path) -> None:
        """
        Saves all query contexts (query_id, text, doc_ids) to a JSON file.
        """
        data = [
            {
                "query_id": ctx.get_query_id(),
                "query_text": ctx.get_query(),
                "doc_ids": ctx.get_doc_ids()
            }
            for ctx in self._queries_by_id.values()
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


    def load_queries_and_docs(self, filepath: str | Path) -> None:
        """
        Loads query contexts from a JSON file. Reconstructs query_id, query text, and associated doc_ids.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            context = QueryRatingContext(item["query_text"], doc_id=None)
            context._id = item["query_id"] 
            for doc_id in item["doc_ids"]:
                context.add_doc_id(doc_id)
            self._queries_by_id[context.get_query_id()] = context
            self._query_text_to_query_id[context.get_query()] = context.get_query_id()


    def save_rating_triples(self, filepath: str | Path) -> None:
        """
        Saves all (query_id, doc_id, score) triples to a JSON file.
        """
        triples = []
        for _context in self._queries_by_id.values():
            query_id = _context.get_query_id()
            for doc_id in _context.get_doc_ids():
                try:
                    score = _context.get_rating_score(doc_id)
                    triples.append({
                        "query_id": query_id,
                        "doc_id": doc_id,
                        "score": score
                    })
                except KeyError:
                    continue
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(triples, f, indent=2)


    def load_rating_triples(self, filepath: str | Path) -> None:
        """
        Loads rating triples from a JSON file and updates existing QueryRatingContext entries.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            triples = json.load(f)

        for triple in triples:
            query_id = triple["query_id"]
            doc_id = triple["doc_id"]
            score = triple["score"]
            if query_id not in self._queries_by_id:
                raise ValueError(f"Query ID {query_id} not found when loading triples.")
            self._queries_by_id[query_id].add_rating_score(doc_id, score)


