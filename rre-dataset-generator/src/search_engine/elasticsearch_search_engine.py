import json
from urllib.parse import urljoin
from pydantic import HttpUrl
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
            "_source": doc_fields,
            "query": query
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

    def _extract_docs(self, response: Response) -> List[Document]:
        raw_docs = response.json()['hits']['hits']
        reformat_raw_doc = []
        for doc in raw_docs:
            clean_doc = dict()
            clean_doc['id'] = doc[self.UNIQUE_KEY]
            clean_doc['fields'] = doc['_source']
            reformat_raw_doc.append(Document(**clean_doc))
        return reformat_raw_doc

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """Search for documents using a query."""
        search_url = urljoin(self.endpoint.encoded_string(), '_search')

        response = self._deal_with_request_post_exception(search_url=search_url,
                                                          headers=self.HEADERS,
                                                          json=payload)

        reformat_raw_docs = self._deal_with_response_status_code(response=response,
                                                                 extract_docs=self._extract_docs)
        return reformat_raw_docs
