import pytest
import requests
from requests.exceptions import HTTPError
from pydantic_core import ValidationError

from src.logger import configure_logging
from src.config import Config
from src.search_engine.vespa_search_engine import VespaSearchEngine
from src.model.document import Document
from tests.mocks.vespa import MockResponseVespaSearch, MockResponseHealth

configure_logging()


def _monkeypatch_health(monkeypatch):
    # VespaSearchEngine itself does not call health, but the integration helper might – keep uniform
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseHealth())


def test_vespa_search_engine_EXPECTED_document_retrieval(monkeypatch):
    _monkeypatch_health(monkeypatch)
    config = Config.load("tests/unit/resources/good_config_vespa.yaml")

    # build a fake document returned by Vespa
    mock_doc = {
        "id": "doc::1",
        "fields": {
            "title": "A first mocked title",
            "description": "A first mocked description"
        }
    }

    # Mock POST /search
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseVespaSearch(mock_doc, status_code=200))

    search_engine = VespaSearchEngine("https://fakeurl", schema="doc")

    result = search_engine.fetch_for_query_generation(
        documents_filter=config.documents_filter,
        doc_number=config.doc_number,
        doc_fields=config.doc_fields,
    )

    expected = Document(id="doc::1", fields=mock_doc["fields"])
    assert result[0] == expected

    # Evaluation path
    result_eval = search_engine.fetch_for_evaluation(
        query_template=config.query_template,
        keyword="and",
        doc_fields=config.doc_fields,
    )
    assert result_eval[0] == expected


def test_vespa_search_engine_EXPECTED_http_error_on_negative_responses(monkeypatch):
    _monkeypatch_health(monkeypatch)
    config = Config.load("tests/unit/resources/good_config_vespa.yaml")

    for status_code in [400, 401, 402, 403, 500]:
        monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseVespaSearch({}, status_code=status_code))
        engine = VespaSearchEngine("https://fakeurl")

        with pytest.raises(HTTPError):
            engine.fetch_for_query_generation(
                documents_filter=config.documents_filter,
                doc_number=config.doc_number,
                doc_fields=config.doc_fields,
            )
        with pytest.raises(HTTPError):
            engine.fetch_for_evaluation(
                query_template=config.query_template,
                keyword="and",
                doc_fields=config.doc_fields,
            )


def test_vespa_search_engine_EXPECTED_validation_error_on_bad_url():
    with pytest.raises(ValidationError):
        _ = VespaSearchEngine("bad-non-url")
