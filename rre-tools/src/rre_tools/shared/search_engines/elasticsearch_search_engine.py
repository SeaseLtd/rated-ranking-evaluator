import json
from pathlib import Path

import requests
from urllib.parse import urljoin
from pydantic import HttpUrl
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from typing import List, Dict, Any, Union, Optional

from rre_tools.shared.search_engines.search_engine_base import BaseSearchEngine
from rre_tools.shared.models.document import Document
from rre_tools.shared.utils import clean_text

import logging
log = logging.getLogger(__name__)


class ElasticsearchSearchEngine(BaseSearchEngine):
    """
    Elasticsearch implementation to search into a given collection
    """
    def __init__(self, endpoint: HttpUrl):
        super().__init__(endpoint)
        self.HEADERS = {'Content-Type': 'application/json'}
        log.debug(f"Working on endpoint: {self.endpoint}")
        self.UNIQUE_KEY = "_id"

    def _get_total_hits(self, payload: Dict[str, Any]) -> int:
        search_url = urljoin(self.endpoint.encoded_string(), '_search')

        log.debug(f"Search url: {search_url}")
        log.debug(f"Payload: {payload}")

        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload)
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException, HTTPError) as e:
            log.error(f"ElasticSearch query failed: {e}")
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
        """
        Fetches a set of documents from Elasticsearch for query generation purposes.

        Args:
            documents_filter (Union[None, List[Dict[str, List[str]]]]): Optional list of field filters to apply.
                Each filter is a dictionary mapping field names to allowed values.
            number_of_docs (int): Number of documents to retrieve.
            doc_fields (List[str]): List of field names to include in the output.
            start (int, optional): Starting index. Defaults to 0.

        Returns:
            List[Document]: A list of documents formatted as `Document` instances.
        """
        # Build base query
        query: Dict[str, Any] = self._fetch_all_payload

        # Add filters, if provided
        filter_clauses = []
        if documents_filter is not None:
            for dict_field in documents_filter:
                for field, values in dict_field.items():
                    if not values:
                        continue
                    filter_clauses.append({"terms": {field: values}})

        # Wrap in a bool query if there are any filters
        if filter_clauses:
            query = {
                "bool": {
                    "must": {"match_all": {}},
                    "filter": filter_clauses
                }
            }

        # Construct the payload (Elasticsearch query body)
        payload = {
            "size": number_of_docs,
            "query": query,
            "from": start,
            "_source": doc_fields
        }

        return self._search(payload)

    def fetch_for_evaluation(self, query_template: Path | str, doc_fields: List[str], keyword: Optional[str] = None) -> List[Document]:
        """
        Executes a search for evaluation using a query template with an optional keyword substitution.

        Args:
            query_template (Path): Path variable pointing to the file with the payload a placeholder for the keyword.
            doc_fields (List[str]): List of field names to include in the response.
            keyword (str, optional): A keyword to replace the placeholder in the query.
                If not provided, a default match_all query is used.

        Returns:
            List[Document]: A list of documents matching the query.
        """
        query_template = Path(query_template)
        payload: Dict[str, Any] = self._parse_query_template(query_template)
        payload = self._replace_placeholder(payload, self.QUERY_PLACEHOLDER, keyword)

        fields = doc_fields if self.UNIQUE_KEY in doc_fields else doc_fields + [self.UNIQUE_KEY]
        payload["_source"] = fields
        return self._search(payload)

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """
        Executes the search request to the Elasticsearch `_search` endpoint and parses the response.

        Args:
            payload (Dict[str, Any]): JSON payload representing the Elasticsearch query.

        Returns:
            List[Document]: A list of retrieved documents as `Document` instances.
        """
        search_url = urljoin(self.endpoint.encoded_string(), '_search')

        log.debug(f"Search url: {search_url}")
        log.debug(f"Payload: {payload}")

        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload)
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException, HTTPError) as e:
            log.error(f"ElasticSearch query failed: {e}")
            raise

        hits = response.json().get('hits', {}).get('hits', [])
        result = []
        for hit in hits:
            source = hit.get("_source", {})
            doc_id = source.get("id", hit.get(self.UNIQUE_KEY))

            fields = {
                key: self._normalize(value)
                for key, value in source.items()
                if key != "id"
            }

            result.append(Document(id=doc_id, fields=fields))
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
