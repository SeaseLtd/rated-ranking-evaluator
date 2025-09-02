from typing import List, Dict, Union, Any

import requests


class MockResponseOpenSearchEngine:
    def __init__(self, hits_data: Union[Dict[str, Any], List[Dict[str, Any]]], status_code: int = 200):
        if isinstance(hits_data, dict):
            self._hits_data = [hits_data]
        elif isinstance(hits_data, list):
            self._hits_data = hits_data
        else:
            raise ValueError("hits_data must be a dict or a list of dicts")

        if not isinstance(status_code, int):
            raise TypeError("status_code must be an int")

        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return {
            "hits": {
                "total": {"value": len(self._hits_data), "relation": "eq"},
                "max_score": 1.0,
                "hits": self._hits_data
            }
        }
