import os
import requests
from typing import List, Dict, Any, Union
from urllib.parse import parse_qs

from src.search_engine.interface import BaseSearchEngine

class SolrSearchEngine(BaseSearchEngine):
    """
    Solr implementation to search into a given collection
    """
    def __init__(self, endpoint: str):
        super().__init__(endpoint)
        self.HEADERS = {'Content-Type': 'application/json'}

    @staticmethod
    def template_to_json_body(template_payload: str) -> dict:
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

    def extract_documents_to_generate_queries(self,
                                             documents_filter: Union[None, List[Dict[str, List[str]]]],
                                             doc_number: int) \
            -> List[Dict[str, Any]]:
        payload = {
            'query': '*:*',
            'params': {
                'rows': doc_number
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

        return self.search(payload)

    def extract_documents_to_evaluate_system(self, query_template: str, keyword: str="*:*") -> List[Dict[str, Any]]:
        """Search for documents using a query."""
        template = query_template.replace(self.PLACEHOLDER, keyword)
        payload = self.template_to_json_body(template)
        return self.search(payload)

    def search(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for documents using a query."""
        search_url = os.path.join(str(self.endpoint), "select")

        response = requests.post(search_url, headers=self.HEADERS, json=payload)
        if response.status_code == 200:
            return response.json()['response']['docs']
        else:
            raise ValueError()
