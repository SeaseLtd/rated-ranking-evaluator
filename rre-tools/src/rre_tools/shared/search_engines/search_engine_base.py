import json
from abc import ABC, abstractmethod
from json import JSONDecodeError
from pathlib import Path
from typing import List, Dict, Any, Union, Iterator
from pydantic import HttpUrl
from rre_tools.shared.models.document import Document

NUMBER_OF_DOCS_EACH_FETCH = 100

class BaseSearchEngine(ABC):
    def __init__(self, endpoint: HttpUrl):
        self.endpoint = HttpUrl(endpoint)
        self.QUERY_PLACEHOLDER = "$query"
        self.UNIQUE_KEY = 'id'

    def fetch_all(self, doc_fields: List[str]) -> Iterator[Document]:
        """Extract all documents from search engine in batches.

        Yields batches of documents instead of loading everything in memory.

        Args:
            doc_fields: Fields to extract from documents

        Yields:
            List[Document]: Batch of documents
        """
        # Now this is relying on fetch_for_query_generation to avoid duplicate code. Might be changed in the future
        start: int = 0
        total_hits: int = self._get_total_hits(self._fetch_all_payload)
        while start < total_hits:
            batch = self.fetch_for_query_generation(
                documents_filter=None,
                number_of_docs=NUMBER_OF_DOCS_EACH_FETCH,
                doc_fields=doc_fields,
                start=start
                )
            if not batch:
                break
            for doc in batch:
                yield doc
            # if we didn't reach the end of the docs, then len(batch) == NUMBER_OF_DOCS_EACH_FETCH if we reached the
            # end of the docs. then len(batch) <= NUMBER_OF_DOCS_EACH_FETCH -> next iteration we exit the loop since
            # we are adding NUMBER_OF_DOCS_EACH_FETCH (not len(batch)) and start becomes greater than total_hits
            start += NUMBER_OF_DOCS_EACH_FETCH


    def _parse_query_template(self, path: Path | str) -> Dict[str, Any]:
        """Return the payload"""
        path = Path(path)
        try:
            with path.open() as f:
                data: Dict[str, Any] = json.load(f)
                return data
        except JSONDecodeError as e:
            raise ValueError(f"Invalid JSON query_template: {e}")

    def _replace_placeholder(self, obj: Any, placeholder: str, keyword: str | None) -> Any:
        if keyword is None:
            return obj

        if isinstance(obj, str):
            return obj.replace(placeholder, keyword)
        elif isinstance(obj, dict):
            return {k: self._replace_placeholder(v, placeholder, keyword) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_placeholder(x, placeholder, keyword) for x in obj]
        else:
            return obj


    @abstractmethod
    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   number_of_docs: int,
                                   doc_fields: List[str],
                                   start: int = 0) \
            -> List[Document]:
        """Extract documents for generating queries."""
        pass

    @abstractmethod
    def fetch_for_evaluation(self,
                             query_template: Path | str,
                             doc_fields: List[str],
                             keyword: str="*:*") \
            -> List[Document]:
        """Search for documents based on a keyword and a query template to evaluate the system."""
        pass

    @abstractmethod
    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        pass

    @abstractmethod
    def _get_total_hits(self, payload: Dict[str, Any]) -> int:
        """Get the total number of documents returned by a query."""
        pass

    @property
    @abstractmethod
    def _fetch_all_payload(self) -> Dict[str, Any]:
        """Payload to fetch all documents from the search engine."""
        pass

