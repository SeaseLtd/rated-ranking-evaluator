from typing import List, Dict, Any, Union
from src.model.document import Document


class MockResponseHealth:
    """Mock a successful call to /state/v1/health"""
    def __init__(self, status_code: int = 200):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("Healthcheck failed")


class MockResponseVespaSearch:
    """Mock Vespa /search response.

    The payload structure mirrors the real Vespa JSON structure that the
    VespaSearchEngine expects: {"root": {"children": [...]}}
    """
    def __init__(self, docs: Union[Document, List[Document]], status_code: int = 200):
        # `docs` could be a list of Docs or a single Doc
        self._docs = docs if isinstance(docs, list) else [docs]
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"Status {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return {
            "root": {
                "children": self._docs,
            }
        }
