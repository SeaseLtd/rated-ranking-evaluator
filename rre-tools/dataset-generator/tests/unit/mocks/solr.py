from typing import List
import requests

class MockResponseSolrEngine:
    def __init__(self, json_data: List, status_code: int =200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return {
            "response": {
                "docs": self._json_data
            }
        }


    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")


class MockResponseUniqueKey:
    def __init__(self, ident):
        self._id = ident

    def json(self):
        return {
            "responseHeader":
                {
                    "status":0,
                    "QTime":2
                },
            "uniqueKey": self._id
        }
