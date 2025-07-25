import requests


class MockResponseOpenSearchEngine:
    def __init__(self, hits_data, status_code=200):
        self._hits_data = hits_data if isinstance(hits_data, list) else [hits_data]
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")

    def json(self):
        return {
            "hits": {
                "total": {"value": len(self._hits_data), "relation": "eq"},
                "max_score": 1.0,
                "hits": self._hits_data
            }
        }
