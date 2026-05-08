"""Per-engine `fetch_field_values` tests (engine-driven value discovery).

Each engine's `fetch_field_values` is a separate code path from `_search` (different
return type, different transport, raw response navigation), so these tests stub
`requests.get` (Solr) or `requests.post` (ES/OS/Vespa) directly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests
from requests.exceptions import HTTPError

from rre_tools.shared.search_engines import (
    ElasticsearchSearchEngine,
    OpenSearchEngine,
    SolrSearchEngine,
    VespaSearchEngine,
)


# ─────────────── shared HTTP-stub helpers ───────────────

class _Resp:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(f"status {self.status_code}")

    @property
    def request(self):
        # Used by Solr code path's debug log; not asserted on.
        return type("_Req", (), {"url": "stubbed"})()


def _capture_get(monkeypatch, body, status_code=200):
    calls = {}

    def _get(url, headers=None, params=None, **kwargs):
        calls["url"] = url
        calls["headers"] = headers
        calls["params"] = params
        calls["kwargs"] = kwargs
        return _Resp(body, status_code)

    monkeypatch.setattr(requests, "get", _get)
    return calls


def _capture_post(monkeypatch, body, status_code=200):
    calls = {}

    def _post(url, headers=None, json=None, **kwargs):
        calls["url"] = url
        calls["headers"] = headers
        calls["json"] = json
        calls["kwargs"] = kwargs
        return _Resp(body, status_code)

    monkeypatch.setattr(requests, "post", _post)
    return calls


# Solr engine `__init__` issues a GET to fetch the unique key. Avoid hitting the network.
@pytest.fixture
def solr_engine(monkeypatch):
    monkeypatch.setattr(
        requests, "get",
        lambda *a, **kw: _Resp({"uniqueKey": "id"}),
    )
    return SolrSearchEngine("http://fake-solr/collection/")


# ───────────────── Solr ─────────────────


def _write_solr_facet_template(tmp_path: Path) -> Path:
    p = tmp_path / "facet_solr.json"
    p.write_text(
        json.dumps({"q": "*:*", "facet": "true", "facet.field": "genres", "facet.limit": 5, "rows": 0}),
        encoding="utf-8",
    )
    return p


def test_solr_fetch_field_values__alternating_array_drops_counts_preserves_order(solr_engine, monkeypatch, tmp_path):
    body = {"facet_counts": {"facet_fields": {"genres": ["comedy", 12, "action", 4, "drama", 1]}}}
    calls = _capture_get(monkeypatch, body)
    template = _write_solr_facet_template(tmp_path)

    values = solr_engine.fetch_field_values(template, "genres")

    assert values == ["comedy", "action", "drama"]
    assert calls["url"].endswith("/select")
    assert calls["params"]["wt"] == "json"
    assert calls["params"]["facet.field"] == "genres"


def test_solr_fetch_field_values__numeric_values_coerce_and_whitespace_dropped(solr_engine, monkeypatch, tmp_path):
    body = {"facet_counts": {"facet_fields": {"year": [2020, 9, 2021, 4, "  ", 1, "   2022 ", 1]}}}
    _capture_get(monkeypatch, body)
    template = _write_solr_facet_template(tmp_path)

    values = solr_engine.fetch_field_values(template, "year")

    assert values == ["2020", "2021", "2022"]


def test_solr_fetch_field_values__missing_facet_counts_raises(solr_engine, monkeypatch, tmp_path):
    _capture_get(monkeypatch, {"response": {"docs": []}})
    template = _write_solr_facet_template(tmp_path)
    with pytest.raises(ValueError, match="facet_counts"):
        solr_engine.fetch_field_values(template, "genres")


def test_solr_fetch_field_values__wrong_field_key_raises(solr_engine, monkeypatch, tmp_path):
    _capture_get(monkeypatch, {"facet_counts": {"facet_fields": {"category": ["x", 1]}}})
    template = _write_solr_facet_template(tmp_path)
    with pytest.raises(ValueError, match="genres"):
        solr_engine.fetch_field_values(template, "genres")


def test_solr_fetch_field_values__field_not_a_list_raises(solr_engine, monkeypatch, tmp_path):
    _capture_get(monkeypatch, {"facet_counts": {"facet_fields": {"genres": "comedy,action"}}})
    template = _write_solr_facet_template(tmp_path)
    with pytest.raises(ValueError, match="must be a list"):
        solr_engine.fetch_field_values(template, "genres")


def test_solr_fetch_field_values__odd_length_array_raises(solr_engine, monkeypatch, tmp_path):
    _capture_get(monkeypatch, {"facet_counts": {"facet_fields": {"genres": ["comedy", 1, "action"]}}})
    template = _write_solr_facet_template(tmp_path)
    with pytest.raises(ValueError, match="even length"):
        solr_engine.fetch_field_values(template, "genres")


def test_solr_fetch_field_values__empty_array_returns_empty_list_silently(solr_engine, monkeypatch, tmp_path, caplog):
    _capture_get(monkeypatch, {"facet_counts": {"facet_fields": {"genres": []}}})
    template = _write_solr_facet_template(tmp_path)
    with caplog.at_level("WARNING"):
        values = solr_engine.fetch_field_values(template, "genres")
    assert values == []
    # No engine-side warning — the single warning lives in add_category_queries.
    assert not [r for r in caplog.records if "no values" in r.getMessage()]


def test_solr_fetch_field_values__http_error_propagates(solr_engine, monkeypatch, tmp_path):
    _capture_get(monkeypatch, {}, status_code=500)
    template = _write_solr_facet_template(tmp_path)
    with pytest.raises(HTTPError):
        solr_engine.fetch_field_values(template, "genres")


def test_solr_fetch_field_values__does_not_route_through_search(solr_engine, monkeypatch, tmp_path):
    """fetch_field_values must not call self._search() (which parses hits and discards
    facet_counts). Greppable contract from the plan."""
    body = {"facet_counts": {"facet_fields": {"genres": ["comedy", 1]}}}
    _capture_get(monkeypatch, body)

    sentinel = {"called": False}

    def _spy_search(*a, **kw):
        sentinel["called"] = True
        raise AssertionError("_search should not be called")

    monkeypatch.setattr(solr_engine, "_search", _spy_search)
    template = _write_solr_facet_template(tmp_path)
    solr_engine.fetch_field_values(template, "genres")
    assert sentinel["called"] is False


# ───────────────── Elasticsearch ─────────────────


def _write_es_agg_template(tmp_path: Path) -> Path:
    p = tmp_path / "facet_es.json"
    p.write_text(
        json.dumps({
            "size": 0,
            "aggs": {"genres": {"terms": {"field": "genres.keyword", "size": 5}}}
        }),
        encoding="utf-8",
    )
    return p


def test_es_fetch_field_values__buckets_returned_in_order(monkeypatch, tmp_path):
    body = {
        "aggregations": {
            "genres": {"buckets": [
                {"key": "comedy", "doc_count": 12},
                {"key": "action", "doc_count": 4},
            ]}
        }
    }
    calls = _capture_post(monkeypatch, body)
    engine = ElasticsearchSearchEngine("http://fake-es/index/")
    template = _write_es_agg_template(tmp_path)

    values = engine.fetch_field_values(template, "genres")

    assert values == ["comedy", "action"]
    assert calls["url"].endswith("/_search")
    # The internal terms.field stays `genres.keyword` (convention navigates by result key).
    assert calls["json"]["aggs"]["genres"]["terms"]["field"] == "genres.keyword"


def test_es_fetch_field_values__numeric_and_boolean_keys_coerce(monkeypatch, tmp_path):
    body = {"aggregations": {"is_premium": {"buckets": [
        {"key": True, "doc_count": 9},
        {"key": False, "doc_count": 1},
    ]}}}
    _capture_post(monkeypatch, body)
    engine = ElasticsearchSearchEngine("http://fake-es/index/")
    template = _write_es_agg_template(tmp_path)

    assert engine.fetch_field_values(template, "is_premium") == ["True", "False"]


def test_es_fetch_field_values__mismatched_agg_key_raises_with_convention_message(monkeypatch, tmp_path):
    body = {"aggregations": {"category": {"buckets": [{"key": "comedy"}]}}}  # named 'category', not 'genres'
    _capture_post(monkeypatch, body)
    engine = ElasticsearchSearchEngine("http://fake-es/index/")
    template = _write_es_agg_template(tmp_path)

    with pytest.raises(ValueError, match="aggregation result key must equal"):
        engine.fetch_field_values(template, "genres")


def test_es_fetch_field_values__keyed_buckets_form_raises(monkeypatch, tmp_path):
    """`"keyed": true` returns buckets as a dict; unsupported."""
    body = {"aggregations": {"genres": {"buckets": {"comedy": {"doc_count": 12}}}}}
    _capture_post(monkeypatch, body)
    engine = ElasticsearchSearchEngine("http://fake-es/index/")
    template = _write_es_agg_template(tmp_path)

    with pytest.raises(ValueError, match="Keyed-bucket"):
        engine.fetch_field_values(template, "genres")


def test_es_fetch_field_values__empty_buckets_returns_empty_list_silently(monkeypatch, tmp_path):
    body = {"aggregations": {"genres": {"buckets": []}}}
    _capture_post(monkeypatch, body)
    engine = ElasticsearchSearchEngine("http://fake-es/index/")
    template = _write_es_agg_template(tmp_path)
    assert engine.fetch_field_values(template, "genres") == []


def test_es_fetch_field_values__http_error_propagates(monkeypatch, tmp_path):
    _capture_post(monkeypatch, {}, status_code=500)
    engine = ElasticsearchSearchEngine("http://fake-es/index/")
    template = _write_es_agg_template(tmp_path)
    with pytest.raises(HTTPError):
        engine.fetch_field_values(template, "genres")


def test_es_agg_keyword_subfield_does_not_require_keyword_in_doc_fields(monkeypatch, tmp_path):
    """Convention test: aggregating on `genres.keyword` while naming the agg `genres` is supported.
    The result-key convention navigates by the agg's name, not its internal terms.field.
    `doc_fields=[genres]` (no `.keyword`) is fine — no engine-level coupling exists between
    the aggregation's internal field and Config.doc_fields.
    """
    body = {"aggregations": {"genres": {"buckets": [{"key": "comedy"}]}}}
    _capture_post(monkeypatch, body)
    engine = ElasticsearchSearchEngine("http://fake-es/index/")
    template = _write_es_agg_template(tmp_path)
    assert engine.fetch_field_values(template, "genres") == ["comedy"]


# ───────────────── OpenSearch ─────────────────


def test_opensearch_fetch_field_values__mirrors_es_behaviour(monkeypatch, tmp_path):
    body = {"aggregations": {"genres": {"buckets": [{"key": "drama"}, {"key": "horror"}]}}}
    _capture_post(monkeypatch, body)
    engine = OpenSearchEngine("http://fake-os/index/")
    template = _write_es_agg_template(tmp_path)
    assert engine.fetch_field_values(template, "genres") == ["drama", "horror"]


def test_opensearch_fetch_field_values__keyed_buckets_form_raises(monkeypatch, tmp_path):
    body = {"aggregations": {"genres": {"buckets": {"drama": {"doc_count": 1}}}}}
    _capture_post(monkeypatch, body)
    engine = OpenSearchEngine("http://fake-os/index/")
    template = _write_es_agg_template(tmp_path)
    with pytest.raises(ValueError, match="Keyed-bucket"):
        engine.fetch_field_values(template, "genres")


# ───────────────── Vespa ─────────────────


def _write_vespa_yql(tmp_path: Path) -> Path:
    p = tmp_path / "facet_vespa.yql"
    p.write_text(
        "select * from sources * where true | all(group(genres) max(5) each(output(count())))\n",
        encoding="utf-8",
    )
    return p


def _vespa_grouping_response(field: str, values_with_counts):
    """Build a canonical Vespa grouping response shape."""
    bucket_children = [
        {
            "id": f"group:string:{v}",
            "value": v,
            "fields": {"count()": c},
        }
        for v, c in values_with_counts
    ]
    return {
        "root": {
            "id": "toplevel",
            "children": [
                {
                    "id": "group:root:0",
                    "children": [
                        {
                            "id": f"grouplist:{field}",
                            "label": field,
                            "children": bucket_children,
                        }
                    ],
                }
            ],
        }
    }


def test_vespa_fetch_field_values__canonical_response_returns_values(monkeypatch, tmp_path):
    body = _vespa_grouping_response("genres", [("comedy", 12), ("action", 4)])
    calls = _capture_post(monkeypatch, body)
    engine = VespaSearchEngine("http://fake-vespa/movie/")
    template = _write_vespa_yql(tmp_path)

    values = engine.fetch_field_values(template, "genres")

    assert values == ["comedy", "action"]
    assert calls["url"].endswith("/search/")
    assert calls["json"]["hits"] == 0
    assert calls["json"]["presentation.format"] == "json"
    assert "group(genres)" in calls["json"]["yql"]


def test_vespa_fetch_field_values__missing_grouplist_raises_with_seen_nodes(monkeypatch, tmp_path):
    body = {"root": {"id": "toplevel", "children": [
        {"id": "group:root:0", "children": [{"id": "grouplist:other"}]}
    ]}}
    _capture_post(monkeypatch, body)
    engine = VespaSearchEngine("http://fake-vespa/movie/")
    template = _write_vespa_yql(tmp_path)

    with pytest.raises(ValueError) as exc:
        engine.fetch_field_values(template, "genres")
    msg = str(exc.value)
    assert "no grouplist found for field 'genres'" in msg
    assert "attribute" in msg  # precondition reminder
    assert "grouplist:other" in msg  # encountered nodes captured


def test_vespa_fetch_field_values__deeply_nested_grouplist_resolved_by_recursive_walk(monkeypatch, tmp_path):
    """The recursive walk must find a grouplist that sits one level deeper than the canonical
    layout — real Vespa responses sometimes nest the grouplist below the `group:root:0` node."""
    body = {
        "root": {
            "id": "toplevel",
            "children": [
                {
                    "id": "group:root:0",
                    "children": [
                        {
                            "id": "wrapper",
                            "children": [
                                {
                                    "id": "grouplist:genres",
                                    "label": "genres",
                                    "children": [
                                        {"id": "group:string:noir", "value": "noir"},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    }
    _capture_post(monkeypatch, body)
    engine = VespaSearchEngine("http://fake-vespa/movie/")
    template = _write_vespa_yql(tmp_path)
    assert engine.fetch_field_values(template, "genres") == ["noir"]


def test_vespa_fetch_field_values__empty_grouplist_returns_empty_list_silently(monkeypatch, tmp_path):
    body = _vespa_grouping_response("genres", [])
    _capture_post(monkeypatch, body)
    engine = VespaSearchEngine("http://fake-vespa/movie/")
    template = _write_vespa_yql(tmp_path)
    assert engine.fetch_field_values(template, "genres") == []


def test_vespa_fetch_field_values__http_error_propagates(monkeypatch, tmp_path):
    _capture_post(monkeypatch, {}, status_code=500)
    engine = VespaSearchEngine("http://fake-vespa/movie/")
    template = _write_vespa_yql(tmp_path)
    with pytest.raises(HTTPError):
        engine.fetch_field_values(template, "genres")
