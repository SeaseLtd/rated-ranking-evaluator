"""Regression test: shipped value-discovery sample templates must be parseable by the engines
that load them. Catches the comment-in-JSON foot-gun (and would catch a `#` header sneaking
into the YQL sample).
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from rre_tools.shared.search_engines import SolrSearchEngine


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"


def test_genre_facet_solr_json__parses_via_engine_loader():
    """Solr engine `_parse_query_template` is `json.load` under the hood — comments would break it."""
    template = TEMPLATES_DIR / "genre_facet_solr.json"

    class _Resp:
        def json(self):
            return {"uniqueKey": "id"}
        def raise_for_status(self):
            pass

    # Solr engine `__init__` issues a GET to fetch the unique key. Skip it.
    orig_get = requests.get
    try:
        requests.get = lambda *a, **kw: _Resp()  # type: ignore[assignment]
        engine = SolrSearchEngine("http://fake-solr/collection/")
    finally:
        requests.get = orig_get

    payload = engine._parse_query_template(template)
    assert isinstance(payload, dict)
    assert payload["facet.field"] == "genres"
    assert "facet.limit" in payload
    # Solr params must be scalars (str/int/bool) — `requests.get(..., params=)` requires it.
    for k, v in payload.items():
        assert isinstance(v, (str, int, float, bool)), f"Solr param {k!r} must be a scalar, got {type(v).__name__}"


def test_genre_facet_es_json__parses_via_json_load_with_aggs_shape():
    template = TEMPLATES_DIR / "genre_facet_es.json"
    payload = json.loads(template.read_text(encoding="utf-8"))
    # Request body shape: `aggs` (not `aggregations` — that's the response key).
    assert "aggs" in payload
    # Convention: agg result key equals the field we'll be querying on.
    assert "genres" in payload["aggs"]
    assert "terms" in payload["aggs"]["genres"]
    assert "field" in payload["aggs"]["genres"]["terms"]


def test_genre_facet_opensearch_json__same_shape_as_es():
    template = TEMPLATES_DIR / "genre_facet_opensearch.json"
    payload = json.loads(template.read_text(encoding="utf-8"))
    assert "aggs" in payload
    assert "genres" in payload["aggs"]
    assert "terms" in payload["aggs"]["genres"]
    assert "field" in payload["aggs"]["genres"]["terms"]


def test_genre_facet_vespa_yql__plain_text_no_hash_comments():
    """The YQL sample is sent to Vespa verbatim. A `#` line would be parsed as part of the
    query (or rejected). Disallow them in the shipped file."""
    text = (TEMPLATES_DIR / "genre_facet_vespa.yql").read_text(encoding="utf-8")
    assert "group(genres)" in text
    for ln in text.splitlines():
        assert not ln.lstrip().startswith("#"), f"YQL sample must not contain # lines: {ln!r}"
        assert not ln.lstrip().startswith("//"), f"YQL sample must not contain // lines: {ln!r}"
