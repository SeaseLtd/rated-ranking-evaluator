import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Union

import requests
from pydantic import HttpUrl
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException

from rre_tools.shared.models.document import Document
from rre_tools.shared.search_engines.search_engine_base import BaseSearchEngine
from rre_tools.shared.utils import clean_text

log = logging.getLogger(__name__)


class OpenSearchEngine(BaseSearchEngine):
    """
    OpenSearch implementation to search in a given index.
    """

    def __init__(self, endpoint: HttpUrl):
        super().__init__(endpoint)
        self.HEADERS = {'Content-Type': 'application/json'}
        self.UNIQUE_KEY = "id"

    def _get_total_hits(self, payload: Dict[str, Any]) -> int:
        search_url = f"{self.endpoint}/_search"
        log.debug(f"User-specified fields: {payload.get('_source')}")
        log.debug(f"Search url: {search_url}")
        log.debug(f"OpenSearch payload (showing payload 500 first chars): {str(payload)[:500]}")
        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload)
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException, HTTPError) as e:
            log.error(f"OpenSearch query failed: {e}")
            raise

        return int(response.json().get('hits', {}).get('total', {}).get('value', 0))

    @property
    def _fetch_all_payload(self) -> Dict[str, Any]:
        return {"match_all": {}}

    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   number_of_docs: int,
                                   doc_fields: List[str],
                                   start: int = 0) -> List[Document]:
        """Fetches a list of documents for query generation based on optional filters."""
        log.info(f"Fetching {number_of_docs} documents (size) from the search engine for query generation")

        filters: List[Dict[str, Any]] = []
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

        query: Dict[str, Any] = {}
        if filters:
            query = {
                "bool": {
                    "filter": filters
                }
            }
        else:
            query = self._fetch_all_payload

        payload = {
            "query": query,
            "_source": fields,
            "from": start,
            "size": number_of_docs
        }

        return self._search(payload)

    def fetch_for_evaluation(self, query_template: Path | str, doc_fields: List[str], keyword: str = "*") -> List[Document]:
        """Fetches documents for evaluation by executing a query built from a template."""

        log.info("Fetching documents (size) based on query template for query evaluation")

        query_template = Path(query_template)
        payload: Dict[str, Any] = self._parse_query_template(query_template)
        payload = self._replace_placeholder(payload, self.QUERY_PLACEHOLDER, keyword)

        fields = doc_fields if self.UNIQUE_KEY in doc_fields else doc_fields + [self.UNIQUE_KEY]
        payload["_source"] = fields

        return self._search(payload)

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Perform a search to OpenSearch and return matching documents based on the given payload."""
        search_url = f"{self.endpoint}/_search"
        log.debug(f"User-specified fields: {payload.get('_source')}")
        log.debug(f"Search url: {search_url}")
        log.debug(f"OpenSearch payload (showing payload 500 first chars): {str(payload)[:500]}")
        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload)
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException, HTTPError) as e:
            log.error(f"OpenSearch query failed: {e}")
            raise

        hits = response.json().get("hits", {}).get("hits", [])
        result = []

        for hit in hits:
            source = hit.get("_source", {})
            log.debug(f"Opensearch returns fields based on payload: {list(source.items())}")
            doc_id = source.get("id", hit.get("_id"))

            fields = {
                key: self._normalize(value)
                for key, value in source.items()
                if key != "id"
            }

            result.append(Document(id=doc_id, fields=fields))
        log.info(f"Fetched {len(result)} documents from the engine")
        return result

    @staticmethod
    def _normalize(value: Any) -> List[str]:
        """Normalize a field value into a list of cleaned strings or throws an exception."""
        try:
            if value is None:
                return []

            if isinstance(value, str):
                return [clean_text(value)]

            if isinstance(value, list):
                return [clean_text(v) if isinstance(v, str) else str(v) for v in value]

            if isinstance(value, dict):
                cleaned_dict = {
                    k: clean_text(v) if isinstance(v, str) else v
                    for k, v in value.items()
                }
                return [json.dumps(cleaned_dict)]

            return [str(value)]

        except Exception as e:
            raise ValueError(f"Failed to normalize value: {value}") from e

