import logging
from typing import List, Dict, Any, Union

import requests
from pydantic import HttpUrl
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException

from src.model.document import Document
from src.search_engine.search_engine_base import BaseSearchEngine
from src.utils import clean_text

log = logging.getLogger(__name__)


class OpenSearchEngine(BaseSearchEngine):
    """
    OpenSearch implementation to search in a given index.
    """

    def __init__(self, endpoint: HttpUrl):
        super().__init__(endpoint)
        self.HEADERS = {'Content-Type': 'application/json'}
        self.UNIQUE_KEY = "id"

    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   doc_number: int,
                                   doc_fields: List[str]) -> List[Document]:
        filters = []
        if documents_filter:
            for field_values in documents_filter:
                for field, values in field_values.items():
                    if not values:
                        continue
                    if len(values) == 1:
                        filters.append({"term": {field: values[0]}})
                    else:
                        filters.append({"terms": {field: values}})

        fields = doc_fields if self.UNIQUE_KEY in doc_fields else doc_fields + [self.UNIQUE_KEY]

        if filters:
            query = {
                "bool": {
                    "filter": filters
                }
            }
        else:
            query = {
                "match_all": {}
            }

        payload = {
            "query": query,
            "_source": fields,
            "size": doc_number
        }

        return self._search(payload)

    def fetch_for_evaluation(self, query_template: str, doc_fields: List[str], keyword: str = "*") -> List[Document]:
        query = query_template.replace(self.PLACEHOLDER, keyword)
        fields = doc_fields if self.UNIQUE_KEY in doc_fields else doc_fields + [self.UNIQUE_KEY]

        payload = {
            "query": {
                "query_string": {
                    "query": query
                }
            },
            "_source": fields
        }
        return self._search(payload)

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        search_url = f"{self.endpoint}/_search"
        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload)
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException, HTTPError) as e:
            log.error(f"OpenSearch query failed: {e}\nPayload: {payload}")
            raise

        hits = response.json().get("hits", {}).get("hits", [])
        result = []

        for hit in hits:
            source = hit.get("_source", {})
            doc_id = source.get("id", hit.get("_id"))

            fields = {
                key: self._normalize(value)
                for key, value in source.items()
                if key != "id"
            }

            result.append(Document(id=doc_id, fields=fields))

        return result

    @staticmethod
    def _normalize(value: Any) -> Any:
        """
        Normalize a field value:
        - string → return [cleaned string]
        - list of strings → return [cleaned strings]
        - else → return as it is
        """
        if isinstance(value, str):
            return [clean_text(value)]
        if isinstance(value, list) and all(isinstance(i, str) for i in value):
            return [clean_text(i) for i in value]
        return value
