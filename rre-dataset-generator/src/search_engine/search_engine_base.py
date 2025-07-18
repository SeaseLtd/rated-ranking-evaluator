from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from pydantic import HttpUrl, BaseModel
from src.model.document import Document

class EndpointValidator(BaseModel):
    endpoint: HttpUrl

class BaseSearchEngine(ABC):
    def __init__(self, endpoint: str):
        validated = EndpointValidator(endpoint=endpoint)
        self.endpoint = validated.endpoint
        self.PLACEHOLDER = "#$query##"
        self.UNIQUE_KEY = 'id'

    @abstractmethod
    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   doc_number: int,
                                   doc_fields: List[str]) \
            -> List[Document]:
        """Extract documents for generating queries."""
        pass

    @abstractmethod
    def fetch_for_evaluation(self,
                             query_template: str,
                             doc_fields: List[str],
                             keyword: str="*:*") \
            -> List[Document]:
        """Search for documents based on a keyword and a query template to evaluate the system."""
        pass

    @abstractmethod
    def search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        pass
