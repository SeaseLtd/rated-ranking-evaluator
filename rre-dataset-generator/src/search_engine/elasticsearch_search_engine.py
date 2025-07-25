import json
import requests
from urllib.parse import urljoin
from pydantic import HttpUrl
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from typing import List, Dict, Any, Union

from requests import Response

from src.utils import clean_text
import logging

log = logging.getLogger(__name__)

from src.search_engine.search_engine_base import BaseSearchEngine
from src.model.document import Document

class ElasticsearchSearchEngine(BaseSearchEngine):
    """
    Elasticsearch implementation to search into a given collection
    """
    def __init__(self, endpoint: HttpUrl | str):
        super().__init__(endpoint)
        self.HEADERS = {'Content-Type': 'application/json'}
        log.debug(f"Working on endpoint: {self.endpoint}")
        self.UNIQUE_KEY = "_id"

    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   doc_number: int,
                                   doc_fields: List[str]) -> List[Document]:

        # Build base query
        query = {"match_all": {}}

        # Add filters, if provided
        filter_clauses = []
        if documents_filter is not None:
            for dict_field in documents_filter:
                for field, values in dict_field.items():
                    if not values:
                        continue
                    if len(values) == 1:
                        filter_clauses.append({"term": {field: values[0]}})
                    else:
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
            "size": doc_number,
            "query": query,
            "_source": doc_fields
        }

        return self._search(payload)

    def fetch_for_evaluation(self, query_template: str, doc_fields: List[str], keyword: str=None) -> List[Document]:
        """Search for documents using a query."""
        if keyword:
             payload = json.loads(query_template.replace(self.PLACEHOLDER, keyword))
        else:
            payload = {
            "query": {"match_all": {}}
            }
        payload["_source"] = doc_fields
        return self._search(payload)

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        search_url = urljoin(self.endpoint.encoded_string(), '_search')

        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload)
        except ConnectionError as e:
            log.error(f"Connection failed while accessing {search_url}\nError: {e}")
            raise ConnectionError(f"Connection failed while accessing {search_url}\nError: {e}")
        except Timeout as e:
            log.error(f"Request to {search_url} timed out\nError: {e}")
            raise Timeout(f"Request to {search_url} timed out\nError: {e}")
        except RequestException as e:
            log.error(f"Unexpected error during request to {search_url}\nError: {e}")
            raise RequestException(f"Unexpected error during request to {search_url}\nError: {e}")

        match response.status_code:
            case 200:
                log.debug("Elasticsearch query successful.")
                log.debug(f"URL: {search_url}")
                log.debug(f"Payload: {payload}")
                raw_docs = response.json()['hits']['hits']
                reformat_raw_doc = []
                for doc in raw_docs:
                    clean_doc = dict()
                    clean_doc['id'] = doc[self.UNIQUE_KEY]
                    clean_doc['fields'] = doc['_source']
                    reformat_raw_doc.append(Document(**clean_doc))
                return reformat_raw_doc
            case 400:
                error_msg = f"400 Bad Request: The request was invalid.\nURL: {search_url}\nPayload: {payload}"
            case 401:
                error_msg = f"401 Unauthorized: Authentication is required.\nURL: {search_url}"
            case 403:
                error_msg = f"403 Forbidden: Access is denied.\nURL: {search_url}"
            case 404:
                error_msg = f"404 Not Found: The Elasticsearch endpoint was not found.\nURL: {search_url}"
            case 500:
                error_msg = f"500 Internal Server Error: Elasticsearch encountered a problem.\nURL: {search_url}"
            case _:
                error_msg = f"Unexpected status code {response.status_code}.\nURL: {search_url}\nPayload: {payload}"
        log.error(error_msg)
        raise HTTPError(error_msg)
