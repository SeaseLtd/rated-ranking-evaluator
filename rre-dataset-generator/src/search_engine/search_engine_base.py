from abc import ABC
from typing import List, Dict, Any, Union
from pydantic import HttpUrl
from src.model.document import Document

class BaseSearchEngine:
    def __init__(self, endpoint: HttpUrl):
        self.endpoint = HttpUrl(endpoint)
        self.PLACEHOLDER = "#$query##"
        self.UNIQUE_KEY = 'id'

    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   doc_number: int,
                                   doc_fields: List[str]) \
            -> List[Document]:
        """Extract documents for generating queries."""
        raise NotImplementedError

    def fetch_for_evaluation(self,
                             query_template: str,
                             doc_fields: List[str],
                             keyword: str="*:*") \
            -> List[Document]:
        """Search for documents based on a keyword and a query template to evaluate the system."""
        raise NotImplementedError

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        raise NotImplementedError
