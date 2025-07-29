from urllib.parse import urljoin  # mantenido aunque ya no dependemos de su semántica
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
from typing import List, Dict, Any, Union, Optional
import re
import logging

from src.utils import clean_text
from src.search_engine.search_engine_base import BaseSearchEngine
from src.model.document import Document

log = logging.getLogger(__name__)

# Default timeout (in seconds) for outbound HTTP calls. Can be overridden via monkey-patching in tests.
DEFAULT_TIMEOUT = 10

# Defensive cap on results per call (can be adjusted via config if preferred)
MAX_HITS = 100

# Basic field name validation to prevent injection through identifiers
_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$") #this only allows starting with a letter or underscore, and then any number of letters, numbers, or underscores. Not ., " , /..


class VespaSearchEngine(BaseSearchEngine):
    """
    Thin HTTP wrapper around the Vespa Query API.
    Assumes an already deployed a schema called `doc`.
    """
    def __init__(self, endpoint: str, schema: str = "doc"):
        super().__init__(endpoint)
        self.schema = schema
        self.HEADERS = {"Content-Type": "application/json"}
        # Will be populated by `_load_schema_fields` to allow validation of user provided filters.
        self.schema_fields: set[str] = set()
        # Lazy loading of schema field names. If the endpoint is not reachable we continue gracefully.
        self._load_schema_fields()

    def _build_yql(self, select_fields: List[str], where_clause: str = "true") -> str:
        fields = ", ".join(select_fields) if select_fields else "*"
        return f"select {fields} from {self.schema} where {where_clause}"

    # ------------------------------------------------------------------
    # Helper / internal utils
    # ------------------------------------------------------------------

    def _load_schema_fields(self) -> None:
        """
        Populate `self.schema_fields` by querying the Vespa `schema/fields` endpoint.

        The loaded information is later used to warn the user when they attempt to
        filter on a field that is not part of the deployed schema.

        Exceptions:
            All exceptions are caught and logged at debug level. The schema list is set to empty on failure.
        """
        # Robust URL construction (preserving final path)
        base = str(self.endpoint).rstrip("/")
        schema_url = f"{base}/schema/fields"
        try:
            schema_resp = requests.get(schema_url, timeout=DEFAULT_TIMEOUT, allow_redirects=False)
            schema_resp.raise_for_status()
            payload = schema_resp.json()
            self.schema_fields = {field["name"] for field in payload.get("fields", []) if "name" in field}
        except Exception as exc:  # noqa: BLE001 – we intentionally catch everything in schema loader
            log.debug(
                "Schema fields endpoint did not return expected payload: %s; defaulting to empty schema list",
                exc,
            )
            self.schema_fields = set()

        log.debug("Schema fields loaded: %d fields found.", len(self.schema_fields))

    @staticmethod
    def _yql_escape(s: str) -> str:
        """
        Minimal and basic escaping for YQL literals: escapes quotes and backslashes
        and removes problematic control characters.
        """
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        s = re.sub(r"[\x00-\x1F\x7F]", " ", s)
        return s

    @staticmethod
    def _safe_literal(s: str) -> str:
        """Returns a quoted and escaped YQL literal."""
        return f'"{VespaSearchEngine._yql_escape(s)}"'

    @staticmethod
    def _sanitize_value(value: str) -> str:
        """
        Sanitize a string value before embedding it in a YQL query.

        Instead of fragile blacklists, we apply escaping and treat it as a literal.
        (The method name is kept for compatibility with the original structure.)
        """
        return VespaSearchEngine._yql_escape(value)

    def _validate_filters(self, filters: Union[None, List[Dict[str, List[str]]]]) -> None:
        """
        Warn if any filter references an unknown field from the schema.

        Args:
            filters: A list of filter dictionaries where keys are field names.

        Notes:
            This is a debugging aid only. It does not affect query execution.
        """
        if not filters or not self.schema_fields:
            # Either no filters were supplied or the schema could not be loaded –
            # nothing to validate.
            return

        for f in filters:
            for field in f.keys():
                if not _FIELD_RE.match(field):
                    log.warning("Filter field '%s' is not a valid identifier.", field)
                elif field not in self.schema_fields:
                    log.warning("Filter field '%s' not present in schema.", field)

    @staticmethod
    def _normalize_field_value(v: Any) -> Any:
        """
        Normalize field values for `Document.fields`:
        - str -> [clean_text(str)]
        - list[str] -> [clean_text(...) ...]
        - other -> returned as-is (lax contract, same as other current implementations)
        """
        if isinstance(v, str):
            return [clean_text(v)]
        if isinstance(v, list) and all(isinstance(i, str) for i in v):
            return [clean_text(i) for i in v]
        return v

    # ---- public API ------------------------------------------------------

    def fetch_for_query_generation(
        self,
        documents_filter: Union[None, List[Dict[str, List[str]]]],
        doc_number: int,
        doc_fields: Optional[List[str]]
    ) -> List[Document]:
        """
        Fetch documents from Vespa for the purpose of query generation.

        Args:
            documents_filter: Optional list of filter dictionaries for query restriction.
            doc_number: Number of documents to retrieve.
            doc_fields: Optional list of fields to include in the response.

        Returns:
            A list of `Document` instances parsed from the response.
        """
        # Sanity-check filters against schema and build WHERE clause
        self._validate_filters(documents_filter)
        where = self._filter_to_where(documents_filter)
        yql = self._build_yql(doc_fields or [], where)

        payload = {
            "yql": yql,
            # Defensive result limit (signature and flow remain unchanged, just capped)
            "hits": min(max(0, int(doc_number)), MAX_HITS),
            "presentation.format": "json",
        }
        log.debug("Vespa payload (generation): %s", str(payload)[:1000])
        return self._search(payload)

    def fetch_for_evaluation(
        self,
        query_template: str,
        doc_fields: Optional[List[str]],
        keyword: str = "*"
    ) -> List[Document]:
        """
        Fetch documents from Vespa using a provided YQL template and keyword.

        Args:
            query_template: YQL string with a placeholder to inject the keyword.
            doc_fields: Optional list of fields to retrieve.
            keyword: The term to substitute into the query. Defaults to '*'.

        Returns:
            A list of `Document` instances retrieved from the engine.
        """
        # Prevent YQL injection: the placeholder is replaced with an escaped literal
        safe_kw = "*" if keyword == "*" else self._safe_literal(keyword)
        yql = query_template.replace(self.PLACEHOLDER, safe_kw)

        # If the template includes a select clause with fields, doc_fields may be redundant.
        # We keep it as a parameter for consistency but don't inject it here
        # (Vespa uses the fields declared in the YQL).
        payload = {
            "yql": yql,
            "hits": min(10, MAX_HITS),
            "presentation.format": "json",
        }
        log.debug("Vespa payload (evaluation): %s", str(payload)[:1000])
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
        # Robust URL construction
        base = str(self.endpoint).rstrip("/")
        search_url = f"{base}/search/"

        try:
            response = requests.post(
                search_url,
                headers=self.HEADERS,
                json=payload,
                timeout=DEFAULT_TIMEOUT,
                allow_redirects=False,
            )
            response.raise_for_status()
        except (ConnectionError, Timeout, RequestException) as e:
            log.error("Request to %s failed: %s", search_url, e)
            raise

        raw = response.json()
        hits = (raw.get("root") or {}).get("children") or []
        docs: List[Document] = []
        for hit in hits:
            doc_id = hit.get("id")
            if not doc_id:
                # skip entries without id
                continue
            fields = hit.get("fields", {}) or {}
            cleaned = {k: self._normalize_field_value(v) for k, v in fields.items()}
            docs.append(Document(id=doc_id, fields=cleaned))
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
            return "true"

        clauses: List[str] = []
        for f in filters:
            for field, values in f.items():
                # Validate field identifier; skip if invalid or empty list
                if not values or not isinstance(values, list):
                    continue
                if not _FIELD_RE.match(field):
                    log.warning("Skipping invalid field name '%s' in filters.", field)
                    continue

                # Escape each value embedded as a literal " "
                if len(values) == 1:
                    safe_val = VespaSearchEngine._safe_literal(values[0])
                    clauses.append(f'{field} contains {safe_val}')
                else:
                    safe_vals = [VespaSearchEngine._safe_literal(v) for v in values]
                    ors = " OR ".join(f'{field} contains {sv}' for sv in safe_vals)
                    clauses.append(f"({ors})")

        return " AND ".join(clauses) if clauses else "true"
