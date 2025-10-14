# tests/unit/test_vespa_search_engine.py
import re
import json
import pytest
import requests
from requests.exceptions import HTTPError

from rre_tools.shared.logger import configure_logging
from rre_tools.dataset_generator.config import Config
from rre_tools.shared.search_engines import VespaSearchEngine
from rre_tools.shared.models import Document
from rre_tools.shared.utils import clean_text
from rre_tools.shared.search_engines.search_engine_base import DOC_NUMBER_EACH_FETCH
from mocks.vespa import MockResponseVespaSearch

configure_logging(level="DEBUG")


"""
Magic Fixtures:
- monkeypatch: PyTest fixture for patching HTTP calls.
- caplog: PyTest log-capture fixture.
"""
@pytest.fixture
def vespa_config(resource_folder):
    """Fixture that loads a valid Vespa config for unit tests."""
    return Config.load(resource_folder / "good_config_vespa.yaml")

# -----------------------
# Helpers / monkeypatches
# -----------------------
def _capture_post(monkeypatch, response_json, status_code=200):
    """
    Monkeypatch POST capturing request + simulating response with status code and payload.
    Returns a dict with the last call params for assertions.
    """
    calls = {}

    class _Resp:
        def __init__(self, data, code):
            self._data = data
            self.status_code = code
        def json(self): return self._data
        def raise_for_status(self):
            if self.status_code >= 400:
                raise HTTPError(f"status {self.status_code}")
        @property
        def text(self): return json.dumps(self._data)

    def _post(url, headers=None, json=None, **kwargs):
        calls["url"] = url
        calls["headers"] = headers
        calls["json"] = json        # payload
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
        # strings are trimmed/cleaned by clean_text and wrapped into a list
        ("  Hello World  ", [clean_text("  Hello World  ")]),
        # list[str] -> each element cleaned
        (["  A  ", "B "], [clean_text("  A  "), clean_text("B ")]),
        # numbers -> coerced to List[str]
        (123, ["123"]),
        # None -> []
        (None, []),
        # mixed list -> strings cleaned, non-strings casted to str
        (["A", 1], ["A", "1"]),
        # dict -> JSON-dumped (string values cleaned inside the impl, numeric unchanged)
        ({"a": 1}, [json.dumps({"a": 1})]),
        # empty list -> []
        ([], []),
    ],
)
def test_normalize_field_value__expects__correct_conversion(input_val, expected_val):
    """Tests the static method for normalizing field values."""
    assert VespaSearchEngine._normalize_field_value(input_val) == expected_val



# --------------
# Happy-path generation
# --------------
def test_fetch_for_query_generation__expects__builds_valid_yql_handles_hits_and_parses_response(monkeypatch):
    """Verify YQL composition, hits propagation, and response parsing in the generation flow."""

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

    engine = VespaSearchEngine("https://fakehost/base/doc/")

    # Filter includes an invalid field (name with hyphen) that should be ignored in the WHERE clause
    documents_filter = [
        {"title": ["Helicopter"]},
        {"description": ["BOGOTA", "Colombia"]},
        {"bad-field": ["oops"]},  # invalid due to identifier regex -> should be ignored
    ]
    doc_number = 42
    doc_fields = ["title", "description"]

    docs = engine.fetch_for_query_generation(
        documents_filter=documents_filter,
        doc_number=doc_number,
        doc_fields=doc_fields,
    )

    # Endpoint and payload
    assert calls["url"].endswith("/base/doc/search/")
    payload = calls["json"]
    assert payload["hits"] == doc_number

    # YQL sanity
    yql = payload["yql"]
    assert re.search(r"select (title,\s*description|description,\s*title) from doc where ", yql)
    assert 'title contains "Helicopter"' in yql
    assert ('(description contains "BOGOTA" OR description contains "Colombia")' in yql or
            '(description contains "Colombia" OR description contains "BOGOTA")' in yql)
    assert "bad-field" not in yql

    # Parsed result
    expected_fields = {"title": ["Hello"], "description": ["A", "B"]}
    assert docs == [Document(id="id:news:news::1", fields=expected_fields)]


# -------------------
# Happy-path evaluation/keyword escaping
# -------------------
def test_fetch_for_evaluation__expects__properly_quotes_and_escapes_keyword(monkeypatch, resource_folder):
    """Ensure keyword literals are safely escaped/quoted in evaluation YQL."""
    vespa_raw = {"root": {"children": []}}
    calls = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakehost/base/doc/")
    template_path = resource_folder / "template_vespa_title.yql"

    # keyword with quotes, backslash and newline
    kw = 'He said "hi" \\ \n new'

    _ = engine.fetch_for_evaluation(
        query_template=template_path,
        doc_fields=["title"],  # kept for signature compatibility
        keyword=kw,
    )

    yql = calls["json"]["yql"]
    # With parameter substitution, the keyword is passed as a separate parameter
    assert "userInput(@kw)" in yql
    # Check that the keyword parameter is correctly set
    assert calls["json"]["kw"] == kw


# -------------------------
# Skips hits without ID
# -------------------------
def test_fetch_for_query_generation__expects__skip_hits_without_id(monkeypatch):
    """Hits missing an ``id`` must be discarded during query generation."""
    vespa_raw = {"root": {"children": [{"fields": {"title": "No ID here"}}]}}
    _ = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakehost/base/doc/")
    docs = engine.fetch_for_query_generation(documents_filter=None, doc_number=5, doc_fields=["title"])
    assert docs == []


# -----------------------
# HTTP/validation errors
# -----------------------
def test_http_requests__expects__raise_on_negative_responses(monkeypatch, resource_folder):
    """Search/evaluation requests must raise ``HTTPError`` on non-success HTTP status codes."""

    for code in (400, 401, 402, 403, 500):
        _ = _capture_post(monkeypatch, {"root": {}}, status_code=code)
        engine = VespaSearchEngine("https://fakehost/base/doc/")
        with pytest.raises(HTTPError):
            engine.fetch_for_query_generation(documents_filter=None, doc_number=1, doc_fields=None)
        with pytest.raises(HTTPError):
            template_path = resource_folder / "template_vespa_simple.yql"
            engine.fetch_for_evaluation(
                query_template=template_path,
                doc_fields=None,
                keyword="x"
            )


# --------------------
# Config compatibility (end-to-end with mocks)
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
def test_workflow_with_mocks_and_config__expects__work_with_existing(monkeypatch, mock_doc, vespa_config):
    """Validate generation & evaluation flows against legacy mocks and YAML config."""
    vespa_raw = {"root": {"children": [mock_doc]}}
    _ = _capture_post(monkeypatch, vespa_raw, status_code=200)

    engine = VespaSearchEngine("https://fakeurl/doc/")

    # Generation path
    res = engine.fetch_for_query_generation(
        documents_filter=vespa_config.documents_filter,
        doc_number=vespa_config.doc_number,
        doc_fields=vespa_config.doc_fields,
    )
    expected_fields = {k: VespaSearchEngine._normalize_field_value(v) for k, v in mock_doc["fields"].items()}
    assert res[0] == Document(id=mock_doc["id"], fields=expected_fields)

    # Evaluation path
    res_eval = engine.fetch_for_evaluation(
        query_template=vespa_config.query_template,
        keyword="and",
        doc_fields=vespa_config.doc_fields,
    )
    expected_fields_eval = {k: VespaSearchEngine._normalize_field_value(v) for k, v in mock_doc["fields"].items()}
    assert res_eval[0] == Document(id=mock_doc["id"], fields=expected_fields_eval)

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
            }
        }
    ]
)
def test_solr_search_engine_fetch_all__expects__results_returned(monkeypatch, vespa_config, mock_doc):
    search_engine = VespaSearchEngine("https://fakeurl")

    mock_dict = {
        "id": mock_doc["id"],
        "fields": {k: VespaSearchEngine._normalize_field_value(v) for k, v in mock_doc["fields"].items()}
    }

    call_counter = {"count": 0}

    def mock_post(*args, **kwargs):
        call_counter["count"] += 1
        if call_counter["count"] == 1: # first call is to just get the number of hits, in this case
            return MockResponseVespaSearch(json_data=[], total_hits=2*DOC_NUMBER_EACH_FETCH, status_code=200)
        elif call_counter["count"] == 2 or call_counter["count"] == 3:  # second and third are to catch actual docs call is to just get the number of hits, in this case
            return MockResponseVespaSearch(json_data=[mock_doc] * DOC_NUMBER_EACH_FETCH, status_code=200)
        else:
            return MockResponseVespaSearch(json_data=[], status_code=200)

    monkeypatch.setattr(requests, "post", mock_post)

    # search_engine.fetch_all, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_all(doc_fields=vespa_config.doc_fields)
    first = next(result)
    assert first == Document(**mock_dict)

    doc_list = [first]
    for doc in result:
        doc_list.append(doc)
    assert len(doc_list) == 2 * DOC_NUMBER_EACH_FETCH
