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
                                   doc_number: int,
                                   doc_fields: List[str]) \
            -> List[Document]:
        """Extract documents for generating queries."""
        raise NotImplementedError

    @abstractmethod
    def fetch_for_evaluation(self,
                             query_template: Path | str,
                             doc_fields: List[str],
                             keyword: str="*:*") \
            -> List[Document]:
        """Search for documents based on a keyword and a query template to evaluate the system."""
        raise NotImplementedError

    @abstractmethod
    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        raise NotImplementedError
