import re
import json
import pytest
import requests
from requests.exceptions import HTTPError

from src.logger import configure_logging
from src.config import Config
from src.search_engine.vespa_search_engine import VespaSearchEngine, MAX_HITS
from src.model.document import Document

from tests.mocks.vespa import MockResponseVespaSearch

configure_logging()


# -----------------------
# Helpers / monkeypatches
# -----------------------

def _monkeypatch_schema_ok(monkeypatch, fields=("title", "description", "id")):
    """Simulate GET /schema/fields returning a payload with field names."""
    class _SchemaResp:
        status_code = 200
        def raise_for_status(self): return None
        def json(self):
            return {"fields": [{"name": f} for f in fields]}
    monkeypatch.setattr(requests, "get", lambda *a, **k: _SchemaResp())


def _monkeypatch_schema_fail(monkeypatch):
    """Simulate schema loading failure (VespaSearchEngine should continue gracefully)."""
    class _FailResp:
        def __getattr__(self, _): raise RuntimeError("boom")
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FailResp())


def _capture_post(monkeypatch, response_json, status_code=200):
    """
    Monkeypatch for requests.post that:
      - captures url/headers/json from the request
      - returns a Response-like object with .json() and .raise_for_status()
    """
    calls = {}
    class _Resp:
        def __init__(self, data, code):
            self._data = data
            self.status_code = code
        def json(self): return self._data
        def raise_for_status(self):
            if self.status_code >= 400: raise HTTPError(f"status {self.status_code}")
        @property
        def text(self): return json.dumps(self._data)

    def _post(url, headers=None, json=None, **kwargs):
        calls["url"] = url
        calls["headers"] = headers
        calls["json"] = json
        calls["kwargs"] = kwargs
        return _Resp(response_json, status_code)

    monkeypatch.setattr(requests, "post", _post)
    return calls


# ---------------------
# Field Value Normalization
# ---------------------

@pytest.mark.parametrize(
    "input_val, expected_val",
    [
        # Text cleaning and wrapping in list
        ("  Hello World  ", ["Hello World"]),
        # List of strings
        (["  A  ", "B "], ["A", "B"]),
        # Passthrough values that should not be changed
        (123, 123),
        (None, None),
        (["A", 1], ["A", 1]),
        ({"a": 1}, {"a": 1}),
        ([], []),
    ],
)
def test_normalize_field_value_EXPECTS_correct_conversion(input_val, expected_val):
    """Tests the static method for normalizing field values."""
    assert VespaSearchEngine._normalize_field_value(input_val) == expected_val


# --------------
# Happy-path generation
# --------------

def test_fetch_for_query_generation_EXPECTS_builds_valid_yql_caps_hits_and_parses_response(monkeypatch):
    _monkeypatch_schema_ok(monkeypatch)

    # Simulated Vespa response (one hit with title str, description list[str])
    vespa_raw = {
        "root": {
            "children": [{
                "id": "id:news:news::1",
                "fields": {"title": "Hello", "description": ["A", "B"]}
            }]
        }
    }
    calls = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakehost/base", schema="doc")
    # Filter includes an invalid field (name with hyphen) that should be ignored in the WHERE clause
    documents_filter = [
        {"title": ["Helicopter"]},
        {"description": ["BOGOTA", "Colombia"]},
        {"bad-field": ["oops"]},  # invalid due to identifier regex -> should be ignored
    ]
    doc_number = MAX_HITS + 50  # should be capped at MAX_HITS
    doc_fields = ["title", "description"]

    docs = engine.fetch_for_query_generation(
        documents_filter=documents_filter,
        doc_number=doc_number,
        doc_fields=doc_fields,
    )

    # Correct URL (robust construction with or without trailing slash)
    assert calls["url"].endswith("/base/search/")

    # Payload with expected YQL and hits limit
    payload = calls["json"]
    assert payload["hits"] == MAX_HITS
    yql = payload["yql"]

    # Should contain field selection
    assert re.search(r"select (title,\s*description|description,\s*title) from doc where ", yql)

    # Should contain valid filters
    assert 'title contains "Helicopter"' in yql
    assert ('(description contains "BOGOTA" OR description contains "Colombia")' in yql or
            '(description contains "Colombia" OR description contains "BOGOTA")' in yql)
    
    # Should not contain the invalid field
    assert "bad-field" not in yql

    # Field parsing and normalization - this is added in last place to avoid error propagation if previous test_ failures
    assert len(docs) == 1
    expected_fields = {
        k: VespaSearchEngine._normalize_field_value(v)
        for k, v in {"title": "Hello", "description": ["A", "B"]}.items()
    }
    assert docs[0] == Document(
        id="id:news:news::1",
        fields=expected_fields,
    )


# -------------------
# Happy-path evaluation/keyword
# -------------------

def test_fetch_for_evaluation_EXPECTS_properly_quotes_and_escapes_keyword(monkeypatch):
    _monkeypatch_schema_ok(monkeypatch)

    vespa_raw = {"root": {"children": []}}
    calls = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakehost/base", schema="doc")
    template = 'select * from doc where title contains #$query##'
    # keyword with quotes, backslash and newline: should be **quoted and escaped**
    kw = 'He said "hi" \\ \n new'

    _ = engine.fetch_for_evaluation(
        query_template=template,
        doc_fields=["title"],
        keyword=kw,
    )

    yql = calls["json"]["yql"]
    # Should contain a quoted literal
    assert '"' in yql and yql.endswith('"')
    # Internal quotes should be escaped
    assert '\"' in yql
    # Backslashes should be doubled when escaped
    assert '\\\\' in yql
    # Newline should not appear as is
    assert "\n" not in yql


# -------------------------
# Skips hits without ID
# -------------------------

def test_fetch_for_query_generation_EXPECTS_skip_hits_without_id(monkeypatch):
    _monkeypatch_schema_ok(monkeypatch)

    vespa_raw = {"root": {"children": [{"fields": {"title": "No ID here"}}]}}
    _ = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakehost/base", schema="doc")
    docs = engine.fetch_for_query_generation(documents_filter=None, doc_number=5, doc_fields=["title"])
    assert docs == []


# ----------------------
# Schema warnings
# ----------------------

def test_fetch_for_query_generation_EXPECTS_warn_on_unknown_schema_fields(monkeypatch, caplog):
    # Load a schema with only "title"
    _monkeypatch_schema_ok(monkeypatch, fields=("title",))

    vespa_raw = {"root": {"children": []}}
    _ = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakehost/base", schema="doc")
    with caplog.at_level("DEBUG"):
        _ = engine.fetch_for_query_generation(
            documents_filter=[{"unknown": ["x"]}, {"title": ["ok"]}],
            doc_number=1,
            doc_fields=["title"],
        )
    # Should warn about "unknown"
    assert any("not present in schema" in rec.message for rec in caplog.records)


# --------------------
# API loading failure
# --------------------

def test_schema_loading_EXPECTS_continue_on_failure(monkeypatch):
    _monkeypatch_schema_fail(monkeypatch)

    vespa_raw = {"root": {"children": []}}
    calls = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakehost/base", schema="doc")
    _ = engine.fetch_for_query_generation(documents_filter=None, doc_number=1, doc_fields=None)

    # Even if schema endpoint fails, search should still be called
    assert calls["url"].endswith("/base/search/")


# -----------------------
# HTTP/validation errors
# -----------------------

def test_http_requests_EXPECTS_raise_on_negative_responses(monkeypatch):
    _monkeypatch_schema_ok(monkeypatch)

    for code in (400, 401, 402, 403, 500):
        _ = _capture_post(monkeypatch, {"root": {}}, status_code=code)
        engine = VespaSearchEngine("https://fakehost/base")
        with pytest.raises(HTTPError):
            engine.fetch_for_query_generation(documents_filter=None, doc_number=1, doc_fields=None)
        with pytest.raises(HTTPError):
            engine.fetch_for_evaluation(query_template='select * from doc where true and #$query##', doc_fields=None, keyword="x")


# --------------------
# Config compatibility
# --------------------

@pytest.mark.parametrize(
    "mock_doc",
    [
        {
            "id": "id:news:news::1",
            "fields": {
                "sddocname": "news",
                "documentid": "id:news:news::1",
                "id": "1",
                "title": "Helicopter Crashes in Colombian Drug War, Kills 20",
                "description": "BOGOTA, Colombia  - A U.S.-made helicopter on an anti-drugs mission crashed in the Colombian jungle on Thursday, killing all 20 Colombian soldiers aboard, the army said.",
            },
        },
        {
            "id": "id:news:news::2",
            "fields": {
                "sddocname": "news",
                "documentid": "id:news:news::2",
                "id": "2",
                "title": "Mocked Title 2",
                "description": "Mocked Description 2",
            },
        },
    ],
)
def test_backwards_compatibility_EXPECTS_work_with_existing_mocks_and_config(monkeypatch, mock_doc):
    """
    Tests both generation and evaluation paths using MockResponseVespaSearch.
    """
    # POST /search with existing mock
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: MockResponseVespaSearch(mock_doc, status_code=200),
    )

    config = Config.load("tests/unit/resources/good_config_vespa.yaml")
    engine = VespaSearchEngine("https://fakeurl", schema="doc")

    # Test generation path
    res = engine.fetch_for_query_generation(
        documents_filter=config.documents_filter,
        doc_number=config.doc_number,
        doc_fields=config.doc_fields,
    )
    expected_fields = {
        k: VespaSearchEngine._normalize_field_value(v)
        for k, v in mock_doc["fields"].items()
    }
    expected = Document(id=mock_doc["id"], fields=expected_fields)
    assert res[0] == expected

    # Test evaluation path
    res_eval = engine.fetch_for_evaluation(
        query_template=config.query_template,
        keyword="and",
        doc_fields=config.doc_fields,
    )
    expected_fields = {
        k: VespaSearchEngine._normalize_field_value(v)
        for k, v in mock_doc["fields"].items()
    }
    expected = Document(id=mock_doc["id"], fields=expected_fields)
    assert res_eval[0] == expected
