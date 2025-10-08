from typing import List, Dict, Any


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
    def __init__(self, json_data: List, total_hits: int = 100, status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.total_hits = total_hits

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"Status {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return {
            "root": {
                "children": self.json_data,
                "fields": {
                    "totalCount": self.total_hits,
                }
            }
        }