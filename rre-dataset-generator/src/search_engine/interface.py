from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from pydantic import HttpUrl, BaseModel

class EndpointValidator(BaseModel):
    endpoint: HttpUrl

class BaseSearchEngine(ABC):
    def __init__(self, endpoint: str):
        validated = EndpointValidator(endpoint=endpoint)
        self.endpoint = validated.endpoint
        self.PLACEHOLDER = "#$query##"

    @abstractmethod
    def extract_documents_to_generate_queries(self,
                                             documents_filter: Union[None, List[Dict[str, List[str]]]],
                                             doc_number: int) \
            -> List[Dict[str, Any]]:
        """Extract documents for evaluating the search system."""
        pass

    @abstractmethod
    def extract_documents_to_evaluate_system(self, query_template: str, keyword: str="*:*") -> List[Dict[str, Any]]:
        """Search for documents based on a keyword and a query template."""
        pass

    @abstractmethod
    def search(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for documents using a query."""
        pass
