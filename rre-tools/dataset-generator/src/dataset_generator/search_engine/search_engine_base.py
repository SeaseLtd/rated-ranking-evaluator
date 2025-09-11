import json
from abc import ABC, abstractmethod
from json import JSONDecodeError
from pathlib import Path
from typing import List, Dict, Any, Union
from pydantic import HttpUrl
from commons.model.document import Document

class BaseSearchEngine(ABC):
    def __init__(self, endpoint: HttpUrl):
        self.endpoint = HttpUrl(endpoint)
        self.QUERY_PLACEHOLDER = "$query"
        self.UNIQUE_KEY = 'id'


    def parse_query_template(self, path: Path) -> Dict[str, Any]:
        """Return the payload"""
        try:
            with path.open() as f:
                return json.load(f)
        except JSONDecodeError as e:
            raise ValueError(f"Invalid JSON query_template: {e}")

    def replace_placeholders(self, obj, placeholder, keyword):
        if isinstance(obj, str):
            return obj.replace(placeholder, keyword)
        elif isinstance(obj, dict):
            return {k: self.replace_placeholders(v, placeholder, keyword) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.replace_placeholders(x, placeholder, keyword) for x in obj]
        else:
            return obj

    @abstractmethod
    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   doc_number: int,
                                   doc_fields: List[str]) \
            -> List[Document]:
        """Extract documents for generating queries."""
        raise NotImplementedError

    @abstractmethod
    def fetch_for_evaluation(self,
                             query_template_path: Path,
                             doc_fields: List[str],
                             keyword: str="*:*") \
            -> List[Document]:
        """Search for documents based on a keyword and a query template to evaluate the system."""
        raise NotImplementedError

    @abstractmethod
    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        raise NotImplementedError
