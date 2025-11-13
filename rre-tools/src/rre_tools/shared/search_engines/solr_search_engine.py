from pathlib import Path
from urllib.parse import urljoin
import requests
from pydantic import HttpUrl
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from typing import List, Dict, Any, Union

from rre_tools.shared.search_engines.search_engine_base import BaseSearchEngine
from rre_tools.shared.models.document import Document
from rre_tools.shared.utils import clean_text

import logging
import json

log = logging.getLogger(__name__)


class SolrSearchEngine(BaseSearchEngine):
    """
    Solr implementation to search into a given collection
    """

    def __init__(self, endpoint: HttpUrl):
        super().__init__(endpoint)
        self.HEADERS = {'Content-Type': 'application/json'}
        log.debug(f"Working on endpoint: {self.endpoint}")
        self.UNIQUE_KEY = requests.get(urljoin(self.endpoint.encoded_string(), 'schema/uniquekey')).json()['uniqueKey']
        log.debug(f"uniqueKey found: {self.UNIQUE_KEY}")

    @property
    def _fetch_all_payload(self) -> Dict[str, Any]:
        return {
            'q': '*:*',
        }

    def _unify_fields(self, doc_fields: List[str]) -> str:
        fields = doc_fields if self.UNIQUE_KEY in doc_fields else doc_fields + [self.UNIQUE_KEY]
        return ','.join(fields)

    def _get_total_hits(self, payload: Dict[str, Any]) -> int:
        search_url = urljoin(self.endpoint.encoded_string(), 'select')

        # Force Solr to return a JSON formatted response
        payload['wt'] = 'json'

        log.debug("Retrieving all docs to count them")
        log.debug(f"Search url: {search_url}")
        log.debug(f"Solr payload (showing payload 500 first chars): {str(payload)[:500]}")

        try:
            response = requests.get(search_url, headers=self.HEADERS, params=payload)
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException, HTTPError) as e:
            log.error(f"Solr query failed: {e}\n")
            raise

        return int(response.json().get('response', {}).get('numFound', 0))

    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   number_of_docs: int, doc_fields: List[str], start: int = 0) \
            -> List[Document]:
        """
        Fetches a set of documents from Solr for the purpose of query generation.

        Args:
            documents_filter (Union[None, List[Dict[str, List[str]]]]): Optional filter constraints for fields and their allowed values.
            number_of_docs (int): Number of documents to retrieve.
            doc_fields (List[str]): List of field names to include in the output.
            start (int, optional): Starting index of the query. Defaults to 0.

        Returns:
            List[Document]: A list of retrieved documents as `Document` objects.
        """
        log.info(f"Fetching {number_of_docs} documents (rows) from the search engine for query generation")

        payload: Dict[str, Any] = self._fetch_all_payload
        payload['rows'] = number_of_docs
        payload['start'] = start
        payload['fl'] = self._unify_fields(doc_fields)

        if documents_filter is not None:
            payload['fq'] = []
            for dict_field in documents_filter:
                for field, values in dict_field.items():
                    if not values:
                        continue  # skip empty lists
                    if len(values) == 1:
                        clause = f'{field}:{values[0]}'
                    else:
                        or_values = ' OR '.join(f'{v}' for v in values)
                        clause = f'{field}:({or_values})'
                    payload['fq'].append(clause)

        return self._search(payload)

    def fetch_for_evaluation(self, query_template: Path | str, doc_fields: List[str], keyword: str="*:*") -> List[Document]:
        """
        Executes a search using a query template for evaluation purposes.

        Args:
            query_template (Path): Path variable pointing to the file with the payload a placeholder for the keyword.
            doc_fields (List[str]): List of fields to include in the response.
            keyword (str, optional): Keyword to inject into the query template. Defaults to "*:*".

        Returns:
            List[Document]: A list of documents matching the query.
        """
        log.info("Fetching documents (rows) based on query template for query evaluation")

        query_template = Path(query_template)
        payload: Dict[str, Any] = self._parse_query_template(query_template)
        payload = self._replace_placeholder(payload, self.QUERY_PLACEHOLDER, self.escape(keyword))
        payload['fl'] = self._unify_fields(doc_fields)

        return self._search(payload)

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """
        Executes a Solr search using a JSON payload and parses the results.

        Args:
            payload (Dict[str, Any]): The JSON payload to send in the POST request to Solr.

        Returns:
            List[Document]: A list of documents formatted as `Document` instances.
        """
        search_url = urljoin(self.endpoint.encoded_string(), 'select')

        # Force Solr to return a JSON formatted response
        payload['wt'] = 'json'

        log.debug(f"Search url: {search_url}")
        log.debug(f"Solr payload (showing payload 500 first chars): {str(payload)[:500]}")

        try:
            response = requests.get(search_url, headers=self.HEADERS, params=payload)
            log.debug(f"URL: {response.request.url}")
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException, HTTPError) as e:
            log.error(f"Solr query failed: {e}\n")
            raise

        hits = response.json().get('response', {}).get('docs', [])
        result = []
        for hit in hits:
            doc_id = hit.get(self.UNIQUE_KEY)
            fields = {
                key: self._normalize(value)
                for key, value in hit.items()
                if key != self.UNIQUE_KEY
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
