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
        """
        Fetches a set of documents from Elasticsearch for query generation purposes.

        Args:
            documents_filter (Union[None, List[Dict[str, List[str]]]]): Optional list of field filters to apply.
                Each filter is a dictionary mapping field names to allowed values.
            doc_number (int): Number of documents to retrieve.
            doc_fields (List[str]): List of field names to include in the output.

        Returns:
            List[Document]: A list of documents formatted as `Document` instances.
        """
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
        """
        Executes a search for evaluation using a query template with an optional keyword substitution.

        Args:
            query_template (str): A JSON-formatted string representing the Elasticsearch query,
                possibly containing a placeholder for a keyword.
            doc_fields (List[str]): List of field names to include in the response.
            keyword (str, optional): A keyword to replace the placeholder in the query.
                If not provided, a default match_all query is used.

        Returns:
            List[Document]: A list of documents matching the query.
        """
        if keyword:
             payload = json.loads(query_template.replace(self.PLACEHOLDER, keyword))
        else:
            payload = {
            "query": {"match_all": {}}
            }
        payload["_source"] = doc_fields
        return self._search(payload)

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """
        Executes the search request to the Elasticsearch `_search` endpoint and parses the response.

        Args:
            payload (Dict[str, Any]): JSON payload representing the Elasticsearch query.

        Returns:
            List[Document]: A list of retrieved documents as `Document` instances.

        Raises:
            ConnectionError: If the connection to the Elasticsearch endpoint fails.
            Timeout: If the request times out.
            RequestException: If an unexpected error occurs during the request.
            HTTPError: If Elasticsearch returns a non-200 HTTP status code.
        """
        search_url = urljoin(self.endpoint.encoded_string(), '_search')

        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload, allow_redirects=False)
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
                data = response.json()
                raw_docs = (data.get('hits') or {}).get('hits') or []
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
