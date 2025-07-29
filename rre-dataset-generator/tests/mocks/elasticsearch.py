from typing import List

class MockResponseElasticsearchEngine:
    def __init__(self, json_data: List, status_code: int =200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return {
            "hits": {
                "hits": self._json_data
            }
        }
