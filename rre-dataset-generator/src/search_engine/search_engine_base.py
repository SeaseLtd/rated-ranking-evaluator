from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Mapping, Callable

import requests
import logging
import json
from pydantic import HttpUrl
from requests import Timeout, RequestException, HTTPError
from requests import Response

from src.model.document import Document

log = logging.getLogger(__name__)

class BaseSearchEngine(ABC):
    def __init__(self, endpoint: HttpUrl):
        self.endpoint = HttpUrl(endpoint)
        self.PLACEHOLDER = "#$query##"
        self.UNIQUE_KEY = '_id'

    @abstractmethod
    def fetch_for_query_generation(self,
                                   documents_filter: Union[None, List[Dict[str, List[str]]]],
                                   doc_number: int,
                                   doc_fields: List[str]) \
            -> List[Document]:
        """Extract documents for generating queries."""
        pass

    @abstractmethod
    def fetch_for_evaluation(self,
                             query_template: str,
                             doc_fields: List[str],
                             keyword: str="*:*") \
            -> List[Document]:
        """Search for documents based on a keyword and a query template to evaluate the system."""
        pass

    @abstractmethod
    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        pass

    def _deal_with_request_post_exception(self,
                                          search_url: str,
                                          headers: Mapping[str, str | bytes | None] | None,
                                          json: Any | None) -> Response:
        try:
            return requests.post(search_url, headers=headers, json=json)
        except ConnectionError as e:
            log.error(f"Connection failed while accessing {search_url}\nError: {e}")
            raise ConnectionError(f"Connection failed while accessing {search_url}\nError: {e}")
        except Timeout as e:
            log.error(f"Request to {search_url} timed out\nError: {e}")
            raise Timeout(f"Request to {search_url} timed out\nError: {e}")
        except RequestException as e:
            log.error(f"Unexpected error during request to {search_url}\nError: {e}")
            raise RequestException(f"Unexpected error during request to {search_url}\nError: {e}")

    def _deal_with_response_status_code(self,
                                        response: Response,
                                        extract_docs: Callable[[Response], List[Document]])\
            -> List[Document]:
        search_url = response.url
        payload = json.loads(response.request.body)
        match response.status_code:
            case 200:
                log.debug("Query successful.")
                log.debug(f"URL: {search_url}")
                log.debug(f"Payload: {payload}")
                # log.debug(f"Response: {response.json()}")
                return extract_docs(response)
            case 400:
                error_msg = f"400 Bad Request: The request was invalid.\nURL: {search_url}\nPayload: {payload}"
            case 401:
                error_msg = f"401 Unauthorized: Authentication is required.\nURL: {search_url}"
            case 403:
                error_msg = f"403 Forbidden: Access is denied.\nURL: {search_url}"
            case 404:
                error_msg = f"404 Not Found: Search engine endpoint was not found.\nURL: {search_url}"
            case 500:
                error_msg = f"500 Internal Server Error: Search engine encountered a problem.\nURL: {search_url}"
            case _:
                error_msg = f"Unexpected status code {response.status_code}.\nURL: {search_url}\nPayload: {payload}"
        log.error(error_msg)
        raise HTTPError(error_msg)
