from typing import List
import requests

class MockResponseElasticsearchEngine:
    def __init__(self, json_data: List, total_hits: int = 100, status_code: int =200):
        self._json_data = json_data
        self.status_code = status_code
        self.total_hits = total_hits

    def json(self):
        return {
            "hits": {
                "hits": self._json_data,
                "total": {
                    "value": self.total_hits
                }
            }
        }

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")
