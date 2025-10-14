from typing import List
import requests


class MockRequest:
    """Mock for the requests.Response object"""
    def __init__(self, url: str, method: str = "GET", body: str = None):
        self.url = url
        self.method = method
        self.body = body

class MockResponseSolrEngine:
    def __init__(self, json_data: List, total_hits: int = 100, status_code: int = 200, url: str = "http://mock-solr.com/select"):
        self._json_data = json_data
        self.status_code = status_code
        self.total_hits = total_hits
        self.url = url
        self.request = MockRequest(url)

    def json(self):
        return {
            "response": {
                "docs": self._json_data,
                "numFound": self.total_hits,
            }
        }

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")


class MockResponseUniqueKey:
    def __init__(self, ident, url: str = "http://mock-solr.com/admin/schema"):
        self._id = ident
        self.url = url
        self.request = MockRequest(url)

    def json(self):
        return {
            "responseHeader":
                {
                    "status":0,
                    "QTime":2
                },
            "uniqueKey": self._id
        }
