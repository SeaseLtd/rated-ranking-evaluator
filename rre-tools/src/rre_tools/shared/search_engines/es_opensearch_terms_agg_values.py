"""Parse Elasticsearch/OpenSearch `_search` terms-aggregation responses for value discovery."""

from __future__ import annotations

from typing import Any, List

from rre_tools.shared.utils import normalize_discovered_field_values


def list_values_from_terms_aggregations(aggregations: Any, field: str) -> List[str]:
    """Return normalized distinct values from ``aggregations[field].buckets[*].key``.

    Convention: the aggregation result key under the response's ``aggregations`` object must
    equal ``field`` (the request body still uses ``aggs``). Keyed-bucket form
    (``\"keyed\": true``) is unsupported.
    """
    if not isinstance(aggregations, dict):
        aggregations = {}
    agg_entry = aggregations.get(field)
    if not isinstance(agg_entry, dict) or "buckets" not in agg_entry:
        raise ValueError(
            f"ES/OS value-discovery: expected aggregations.{field}.buckets in response. "
            f"Convention: the aggregation result key must equal fields[0] ('{field}'); "
            f"the aggregation's internal terms.field can be a keyword subfield "
            f"(e.g. '{field}.keyword') without affecting this convention."
        )
    buckets = agg_entry["buckets"]
    if not isinstance(buckets, list):
        raise ValueError(
            f"ES/OS value-discovery: aggregations.{field}.buckets must be a list. "
            f"Keyed-bucket aggregations (`'keyed': true`) are not supported."
        )
    return normalize_discovered_field_values(b.get("key") for b in buckets)
