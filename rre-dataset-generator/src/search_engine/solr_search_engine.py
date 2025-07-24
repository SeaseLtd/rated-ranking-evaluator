from urllib.parse import urljoin
import requests
from pydantic import HttpUrl
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from typing import List, Dict, Any, Union
from urllib.parse import parse_qs

from src.utils import clean_text
import logging

log = logging.getLogger(__name__)

from src.search_engine.search_engine_base import BaseSearchEngine
from src.model.document import Document

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

    def _template_to_json_payload(self, template_payload: str) -> Dict[str, Any]:
        """
        Converts a Solr query string into a structured JSON body.

        Args:
            template_payload (str): The Solr query string, e.g., 'q=ghosts&fq=genre:horror&wt=json'.

        Returns:
            dict: A dictionary representing the query parameters.
        """
        # Parse the query string into a dictionary
        json_body = parse_qs(template_payload)

        defaults = {
            'q': '*:*',
            'wt': 'json'
        }

        # Substitute missing parameters with default values
        for key, default_value in defaults.items():
            if key not in json_body or not json_body[key]:
                json_body[key] = [default_value]

        return {
            'query': json_body.get('q')[0],
            'params': {k: v[0] for k, v in json_body.items() if k != 'q'}
        }

    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   doc_number: int, doc_fields: List[str]) \
            -> List[Document]:
        payload = {
            'query': '*:*',
            'params': {
                'rows': doc_number,
                'fl' : doc_fields if self.UNIQUE_KEY in doc_fields else doc_fields + [self.UNIQUE_KEY]
            }
        }

        if documents_filter is not None:
            payload['params']['fq'] = []
            for dict_field in documents_filter:
                for field, values in dict_field.items():
                    if not values:
                        continue  # skip empty lists
                    if len(values) == 1:
                        clause = f'{field}:{values[0]}'
                    else:
                        or_values = ' OR '.join(f'{v}' for v in values)
                        clause = f'{field}:({or_values})'
                    payload['params']['fq'].append(clause)

        return self._search(payload)

    def fetch_for_evaluation(self, query_template: str, doc_fields: List[str], keyword: str="*:*") -> List[Document]:
        """Search for documents using a query."""
        template = query_template.replace(self.PLACEHOLDER, keyword)
        payload = self._template_to_json_payload(template)
        # here fl is overwritten, even if in the template there are other fields in the 'fl' key
        payload['params']['fl'] = doc_fields if self.UNIQUE_KEY in doc_fields else doc_fields + [self.UNIQUE_KEY]
        return self._search(payload)

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        search_url = urljoin(self.endpoint.encoded_string(), 'select')

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
                log.debug("Solr query successful.")
                log.debug(f"URL: {search_url}")
                log.debug(f"Payload: {payload}")
                # log.debug(f"Response: {response.json()}")
                raw_docs = response.json()['response']['docs']
                reformat_raw_doc = []
                for doc in raw_docs:
                     clean_doc = dict()
                     clean_doc['id'] = doc[self.UNIQUE_KEY]
                     clean_doc['fields'] = dict()
                     for k, v in doc.items():
                        if k != self.UNIQUE_KEY:
                            if isinstance(v, list):
                                if v:
                                    if isinstance(v[0], str):
                                        clean_doc['fields'][k] = [clean_text(text) for text in v]
                                    else:
                                        clean_doc['fields'][k] = v
                                else:
                                    log.warning(f"The field {k} is empty, skipped.")
                            else:
                                clean_doc['fields'][k] = v
                     reformat_raw_doc.append(Document(**clean_doc))
                return reformat_raw_doc
            case 400:
                error_msg = f"400 Bad Request: The request was invalid.\nURL: {search_url}\nPayload: {payload}"
            case 401:
                error_msg = f"401 Unauthorized: Authentication is required.\nURL: {search_url}"
            case 403:
                error_msg = f"403 Forbidden: Access is denied.\nURL: {search_url}"
            case 404:
                error_msg = f"404 Not Found: The Solr endpoint was not found.\nURL: {search_url}"
            case 500:
                error_msg = f"500 Internal Server Error: Solr encountered a problem.\nURL: {search_url}"
            case _:
                error_msg = f"Unexpected status code {response.status_code}.\nURL: {search_url}\nPayload: {payload}"
        log.error(error_msg)
        raise HTTPError(error_msg)
