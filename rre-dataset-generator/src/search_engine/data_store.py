from __future__ import annotations
import os 
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.model.document import Document
from src.model.query_rating_context import QueryRatingContext

log = logging.getLogger(__name__)

# FILE TO ROOT RRE-DATASET-GENERATOR/TMP DIRECTORY
TMP_FILE = "./tmp/datastore.json"

class DataStore:
    """
    Stores/retrieves documents, queries, and rating scores.
    """
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._queries_by_id: Dict[str, QueryRatingContext] = {}
        self._query_text_to_query_id: Dict[str, str] = {}

        # Load from default file if present
        if os.path.exists(TMP_FILE):
            try:
                self.load_tmp_file_content(TMP_FILE)
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

    
    @staticmethod
    def query_context_docs_to_dict(query: QueryRatingContext, documents: List[Document], save_documents: bool = False) -> dict:
        return {
            "query_id": query.get_query_id(),
            "query_text": query.get_query(),
            "doc_ratings": query._doc_id_to_rating_score.copy(), # save the queries as nested dict
            "documents": [doc.model_dump() for doc in documents if doc is not None] if save_documents else []
        }

    @staticmethod
    def dict_to_query_context_docs(dict_: dict) -> tuple[str, str, dict[str, int], list[dict]]:
        query_id = dict_["query_id"]
        query_text = dict_["query_text"]
        doc_ratings = dict_["doc_ratings"]
        documents = dict_.get("documents", [])
        return query_id, query_text, doc_ratings, documents

    @staticmethod
    def check_tmp_file(filepath: str | Path = None) -> None:
        if filepath is None:
            filepath = TMP_FILE

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)  # ensure ./tmp/ exists
        if not filepath.exists():
            log.debug(f'Tmp file with previous data not found in DataStore: {filepath}')
            raise FileNotFoundError(f"Data file not found: {filepath}")
        return filepath

    def save_tmp_file_content(self, filepath: str | Path = None) -> None:
        """
        Save queries, ratings, and documents to a unified JSON file on disk.
        """
        filepath = self.check_tmp_file(filepath)

        all_content = []
        # Serialize all queries and documents
        for query_ctx in self._queries_by_id.values():
            docs_ = [self.get_document(doc_id) for doc_id in query_ctx.get_doc_ids()]
            data = self.query_context_docs_to_dict(query_ctx, docs_, save_documents=True)
            all_content.append(data)

        # Dumps JSON to memory file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_content, f, indent=2)



    def load_tmp_file_content(self, filepath: str | Path = None) -> None:
        """
        Load queries, ratings, and documents from a unified JSON file on disk.
        """
        filepath = self.check_tmp_file(filepath)

        with filepath.open("r", encoding="utf-8") as f:
            all_content = json.load(f)

        for entry in all_content:
            query_id, query_text, doc_ratings, documents = self.dict_to_query_context_docs(entry)

            for doc_data in documents:
                document = Document.model_validate(doc_data)
                self.add_document(document.id, document)

            # Instanciate QueryRatingContext from fields
            context = QueryRatingContext.from_serialized(query_id, query_text, doc_ratings)

            # Add QueryRatingContext to in-memory dict
            self._queries_by_id[query_id] = context

            # Add query text-id to in-memory dict
            self._query_text_to_query_id[query_text] = query_id
