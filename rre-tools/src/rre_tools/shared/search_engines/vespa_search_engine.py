import re
import logging
import requests
import json
from requests.exceptions import ConnectionError, Timeout, RequestException
from typing import List, Dict, Any, Union, Optional
from collections import defaultdict
from pathlib import Path
from pydantic import HttpUrl

from rre_tools.shared.search_engines.search_engine_base import BaseSearchEngine
from rre_tools.shared.models.document import Document
from rre_tools.shared.utils import clean_text


log = logging.getLogger(__name__)

# Timeout (in seconds) for outbound HTTP calls.
DEFAULT_TIMEOUT = 10

# Simple field name validation to prevent injection / unvalid strings - valid field names must start with a letter or underscore, followed by alphanumerics or underscores.
_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$") 


class VespaSearchEngine(BaseSearchEngine):
    """
    Thin HTTP wrapper around the Vespa Query API.
    Assumes an already deployed a schema called `doc`.
    """
    def __init__(self, endpoint: HttpUrl):
        super().__init__(endpoint)
        # Extract schema from endpoint path: http://host:port/schema_name/
        endpoint_str = str(endpoint).rstrip('/')
        path_parts = endpoint_str.split('/')
        if len(path_parts) > 3:
            self.schema = path_parts[-1]  # Last part of the path
        else:
            self.schema = "doc"  # Fallback to default
        self.HEADERS = {"Content-Type": "application/json"}

    # ------------------------------------------------------------------
    # Helpers / internal utils
    # ------------------------------------------------------------------

    @property
    def _fetch_all_payload(self) -> Dict[str, Any]:
        return {
            'yql': f"select * from {self.schema}"
        }

    def _get_total_hits(self, payload: Dict[str, Any]) -> int:
        base = str(self.endpoint).rstrip("/")
        search_url = f"{base}/search/"
        log.debug(f"Search url: {search_url}")
        log.debug(f"Vespa payload (showing payload 500 first chars): {str(payload)[:500]}")

        try:
            response = requests.post(
                search_url,
                headers=self.HEADERS,
                json=payload,
                timeout=DEFAULT_TIMEOUT,  # added timeout to avoid blocking calls
                allow_redirects=False,  # added allow_redirects
            )
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException) as e:
            log.error(f"Request to {search_url} failed: {e}")
            raise

        return int(response.json().get("root", {}).get("fields", {}).get("totalCount", 0))

    def _build_yql(self, select_fields: List[str], where_clause: str = "true") -> str:
        fields = ", ".join(select_fields) if select_fields else "*"
        return f"select {fields} from {self.schema} where {where_clause}"

    @staticmethod
    def _escape_filter_value(s: str) -> str:
        """Simple escaping for filter values in YQL."""
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        s = re.sub(r"[\x00-\x1F\x7F]", " ", s)
        return f'"{s}"'


    def _validate_filters(self, filters: Union[None, List[Dict[str, List[str]]]]) -> None:
        """
        Validate filter field names.

        Args:
            filters: A list of filter dictionaries where keys are field names.

        Notes:
            This is a debugging aid only. It does not affect query execution.
        """

        if not filters:
            return

        for f in filters:
            for field in f.keys():
                if not _FIELD_RE.match(field):
                    log.debug(f"Filter field '{field}' is not a valid identifier.")


    @staticmethod
    def _normalize_field_value(v: Any) -> List[str]:
        """
        Normalize field values for `Document.fields` to List[str], matching Solr behavior:
        - None -> []
        - str -> [clean_text(str)]
        - list -> each element cleaned if str, else cast to str
        - dict -> JSON-dumped with string values cleaned
        - other -> [str(value)]
        """

        if v is None:
            return []

        if isinstance(v, str):
            return [clean_text(v)]

        if isinstance(v, list):
            return [clean_text(i) if isinstance(i, str) else str(i) for i in v]

        if isinstance(v, dict):
            cleaned_dict = {k: (clean_text(val) if isinstance(val, str) else val) for k, val in v.items()}
            return [json.dumps(cleaned_dict)]

        return [str(v)]


    # ---- public API ------------------------------------------------------

    def fetch_for_query_generation(
        self,
        documents_filter: Union[None, List[Dict[str, List[str]]]],
        number_of_docs: int,
        doc_fields: Optional[List[str]],
        start: int  = 0,
    ) -> List[Document]:
        """
        Fetch documents from Vespa for the purpose of query generation.

        Args:
            documents_filter: Optional list of filter dictionaries for query restriction.
            number_of_docs: Number of documents to retrieve.
            doc_fields: Optional list of fields to include in the response.
            start: Optional start index to retrieve documents from.

        Returns:
            A list of `Document` instances parsed from the response.
        """
        log.info(f"Fetching {number_of_docs} documents (hits) from the search engine for query generation")

        payload: Dict[str, Any] = self._fetch_all_payload

        self._validate_filters(documents_filter)
        where = self._filter_to_where(documents_filter)
        yql = self._build_yql(doc_fields or [], where)

        payload["yql"] = yql
        payload["hits"] = int(number_of_docs)
        payload["presentation.format"] =  "json"
        payload['offset'] = start

        log.debug(f"Vespa payload (showing payload 500 first chars): {str(payload)[:500]}")
        return self._search(payload)

    def fetch_for_evaluation(
        self,
        query_template: Path | str,
        doc_fields: Optional[List[str]],
        keyword: str = "*"
    ) -> List[Document]:
        """
        Fetch documents from Vespa using a provided YQL template file and keyword.

        Args:
            query_template: Path to YQL template file with userInput(@kw) for parameter substitution.
            doc_fields: Optional list of fields to retrieve. -- NOT USED NOW
            keyword: The term to substitute into the query. Defaults to '*'.

        Returns:
            A list of `Document` instances retrieved from the engine.
        """

        log.info("Fetching documents (hits) based on query template for query evaluation")

        # Read the YQL template from file (following the same pattern as other engines)
        if isinstance(query_template, Path):
            template_str = query_template.read_text(encoding='utf-8').strip()
        else:
            template_str = query_template.strip()

        # Use parameter substitution instead of string replacement for security
        # Template should contain userInput(@kw) with {allowEmpty:true} for empty queries
        kw_param = "" if keyword == "*" else keyword

        payload = {
            "yql": template_str,  # Template contains userInput(@kw)
            "kw": kw_param,      # Parameter substitution
            "presentation.format": "json",
        }
        log.debug(f"Vespa payload (evaluation): {str(payload)[:1000]}")
        return self._search(payload)


    # ---- low‑level call --------------------------------------------------

    def _search(self, payload: Dict[str, Any]) -> List[Document]:
        """
        Execute a low-level HTTP POST request to the Vespa search endpoint.

        Args:
            payload: Dictionary containing the Vespa query in JSON format.

        Returns:
            A list of `Document` instances parsed from the response.

        Raises:
            ConnectionError, Timeout, RequestException: If the search request fails.
        """

        base = str(self.endpoint).rstrip("/")
        search_url = f"{base}/search/"

        try:
            response = requests.post(
                search_url,
                headers=self.HEADERS,
                json=payload,
                timeout=DEFAULT_TIMEOUT, # added timeout to avoid blocking calls
                allow_redirects=False,   # added allow_redirects
            )
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException) as e:
            log.error(f"Request to {search_url} failed: {e}")
            raise

        raw_response = response.json()
        hits = (raw_response.get("root") or {}).get("children") or []
        docs: List[Document] = []
        for hit in hits:
            doc_id = hit.get("id")
            if not doc_id:
                log.debug(f"Potential corrupted entry without id in Vespa _search: {hit}")
                continue
            fields = hit.get("fields", {}) or {}

            normalized_fields = {k: self._normalize_field_value(v) for k, v in fields.items()}
            docs.append(Document(id=doc_id, fields=normalized_fields))
        log.info(f"Fetched {len(docs)} documents from the engine")
        return docs

    @staticmethod
    def _filter_to_where(filters: Union[None, List[Dict[str, List[str]]]]) -> str:
        """
        Convert a list of filter dictionaries into a Vespa YQL predicate string.

        Each dictionary maps a field to a list of values:
            - One value: field contains "value"
            - Multiple values: (field contains "v1" OR field contains "v2" ...)

        Different fields are combined with AND logic.

        Args:
            filters: List of dictionaries, each mapping a field name to a list of values.

        Returns:
            A YQL-compatible predicate string. If no filters, returns "true".

        Example:
            Input:
                [{"title": ["Helicopter"]}, {"description": ["BOGOTA", "Colombia"]}]
            Output:
                'title contains "Helicopter" AND (description contains "BOGOTA" OR description contains "Colombia")'
        """

        if not filters:
            # Vespa requires a WHERE clause (mandatory)
            # > return "true" if no filters are provided.
            return "true"

        # 1. Aggregate values by field so that multiple entries for the same field
        #    are merged together. This prevents logical errors such as
        #    `(field contains "a" OR field contains "b") AND (field contains "c")`

        aggregated: Dict[str, List[str]] = defaultdict(list)

        for f in filters:
            for field, values in f.items():
                # Validate field names and values
                if not values or not isinstance(values, list):
                    continue
                if not _FIELD_RE.match(field):
                    log.warning(f"Skipping invalid field name '{field}' in filters.")
                    continue

                # Filter out None values and convert to strings
                valid_values = []
                for v in values:
                    if v is not None:
                        valid_values.append(str(v))
                    else:
                        log.debug(f"Skipping None value in field '{field}' filters.")
                
                # Append valid values, deduplicating later
                aggregated[field].extend(valid_values)

        # 2. Build YQL clauses per field
        clauses: List[str] = []
        for field, values in aggregated.items():
            seen = set()
            unique_vals = []
            for v in values:
                if v not in seen:
                    seen.add(v)
                    unique_vals.append(v)

            if not unique_vals:
                continue

            safe_vals = [VespaSearchEngine._escape_filter_value(v) for v in unique_vals]

            if len(safe_vals) == 1:
                clauses.append(f"{field} contains {safe_vals[0]}")
            else:
                ors = " OR ".join(f"{field} contains {sv}" for sv in safe_vals)
                clauses.append(f"({ors})")

        if len(clauses) == 1:
            # if there's only one clause, return it
            return clauses[0]
        elif len(clauses) > 1:
            # if there are multiple clauses, join them with AND
            return " AND ".join(clauses)
        else:
            # if there are no clauses, return true
            return "true"
