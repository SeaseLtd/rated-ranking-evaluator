from urllib.parse import urljoin
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
from typing import List, Dict, Any, Union, Optional

from src.utils import clean_text
from src.search_engine.search_engine_base import BaseSearchEngine
from src.model.document import Document
import logging

log = logging.getLogger(__name__)

class VespaSearchEngine(BaseSearchEngine):
    """
    Thin HTTP wrapper around the Vespa Query API.
    Assumes an already deployed a schema called `doc`.
    """
    def __init__(self, endpoint: str, schema: str = "doc"):
        super().__init__(endpoint)
        self.schema = schema
        self.HEADERS = {"Content-Type": "application/json"}

    def _build_yql(self, select_fields: List[str], where_clause: str = "true") -> str:
        fields = ", ".join(select_fields) if select_fields else "*"
        return f"select {fields} from {self.schema} where {where_clause}"



    @staticmethod
    def _filter_to_where(filters: Union[None, List[Dict[str, List[str]]]]) -> str:
        """
        Convert a list of filter dictionaries into a Vespa YQL predicate string.

        Each filter dictionary should map field names to a list of values to match.
        - For a single value: 'field contains "value"'
        - For multiple values: '(field contains "value1" OR field contains "value2" OR ...)'

        Different fields are combined with AND.

        Example:
            Input:
                [
                    {"title": ["Helicopter"]},
                    {"description": ["BOGOTA", "Colombia"]}
                ]
            Output:
                'title contains "Helicopter" AND (description contains "BOGOTA" OR description contains "Colombia")'

        If filters is None or empty, returns "true".
        """
        if not filters:
            return "true"
        clauses = []
        for f in filters:
            for field, values in f.items():
                if not values: 
                    # skip empty lists                  
                    continue
                if len(values) == 1:
                    clauses.append(f'{field} contains "{values[0]}"')
                else:
                    ors = " OR ".join(f'{field} contains "{v}"' for v in values)
                    clauses.append(f"({ors})")
        return " AND ".join(clauses) or "true"

    # ---- public API ------------------------------------------------------

    def fetch_for_query_generation(
        self,
        documents_filter: Union[None, List[Dict[str, List[str]]]],
        doc_number: int,
        doc_fields: Optional[List[str]]
    ) -> List[Document]:

        where = self._filter_to_where(documents_filter)
        yql   = self._build_yql(doc_fields, where)
        payload = {
            "yql": yql,
            "hits": doc_number,
            "presentation.format": "json"
        }
        print("Payload:", payload)
        # response = requests.post(search_url, headers=self.HEADERS, json=payload)

        return self._search(payload)

    def fetch_for_evaluation(
        self,
        query_template: str,      # e.g. "select * from doc where userQuery()"
        doc_fields: Optional[List[str]],
        keyword: str = "*"
    ) -> List[Document]:
        yql = query_template.replace(self.PLACEHOLDER, keyword)
        payload = {
            "yql": yql,
            "hits": 10
        }
        return self._search(payload)

    # ---- low‑level call --------------------------------------------------

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        search_url = urljoin(str(self.endpoint), "search/")
        try:
            response = requests.post(search_url, headers=self.HEADERS, json=payload)
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException) as e:
            log.error(f"Request to {search_url} failed: {e}")
            raise

        raw = response.json().get("root", {}).get("children", [])
        docs = []
        for hit in raw:
            doc_id = hit.get("id")
            fields = hit.get("fields", {})
            cleaned = {k: [clean_text(vv) for vv in v] if isinstance(v, list) else v
                       for k, v in fields.items()}
            docs.append(Document(id=doc_id, fields=cleaned))
        return docs
