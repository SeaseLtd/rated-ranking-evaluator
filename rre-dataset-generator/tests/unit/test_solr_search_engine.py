import pytest
import requests
from requests.exceptions import HTTPError
from pydantic_core import ValidationError

from src.logger import configure_logging
from src.config import Config
from tests.mocks.solr import MockResponseSolrEngine, MockResponseUniqueKey


from src.search_engine.solr_search_engine import SolrSearchEngine
from src.model.document import Document
import logging

configure_logging(level=logging.DEBUG)

@pytest.fixture
def solr_config():
    """Fixture that loads a valid OpenSearch config for unit tests."""
    return Config.load("tests/unit/resources/solr_good_config.yaml")

@pytest.fixture
def mock_doc():
    return {
        "mock_id": "1",
        "mock_title": ["A first mocked title"],
        "mock_description": ["A first mocked description"]
    }

@pytest.fixture
def mock_dict(mock_doc):
    return {
        'id': mock_doc['mock_id'],
        'fields': {k: v for k, v in mock_doc.items() if k != 'mock_id'}
    }

def test_solr_search_engine_fetch_for_query_generation__expects__result_returned(monkeypatch, solr_config, mock_doc, mock_dict):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="mock_id"))
    search_engine = SolrSearchEngine("https://fakeurl")

    assert search_engine.UNIQUE_KEY == "mock_id"

    # apply the monkeypatch for requests.post to mock_post
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseSolrEngine([mock_doc], status_code=200))

    # search_engine.extract_documents_to_generate_queries, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_for_query_generation(documents_filter=solr_config.documents_filter,
                                                      doc_number=solr_config.doc_number,
                                                      doc_fields=solr_config.doc_fields)
    assert result[0] == Document(**mock_dict)

def test_solr_search_engine_fetch_for_evaluation__expects__result_returned(monkeypatch, solr_config, mock_doc, mock_dict):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="mock_id"))
    search_engine = SolrSearchEngine("https://fakeurl")

    assert search_engine.UNIQUE_KEY == "mock_id"

    # apply the monkeypatch for requests.post to mock_post
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseSolrEngine([mock_doc], status_code=200))

    # search_engine.extract_documents_to_evaluate_system, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_for_evaluation(keyword="and",
                                                query_template=solr_config.query_template,
                                                doc_fields=solr_config.doc_fields)
    assert result[0] == Document(**mock_dict)

def test_solr_search_engine_negative_post_fetch_for_query_generation__expects__raises_http_error(monkeypatch, solr_config):
    for status_code in [400, 401, 402, 403, 500]:
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="identifier"))
        monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseSolrEngine([], status_code=status_code))

        search_engine = SolrSearchEngine("https://fakeurl")

        with pytest.raises(HTTPError):
            search_engine.fetch_for_query_generation(
                documents_filter=solr_config.documents_filter,
                doc_number=solr_config.doc_number,
                doc_fields=solr_config.doc_fields
            )


def test_solr_search_engine_negative_post_fetch_for_evaluation__expects__raises_http_error(monkeypatch, solr_config):
    for status_code in [400, 401, 402, 403, 500]:
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="identifier"))
        monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseSolrEngine([], status_code=status_code))

        search_engine = SolrSearchEngine("https://fakeurl")


        with pytest.raises(HTTPError):
            search_engine.fetch_for_evaluation(
                keyword="and",
                query_template=solr_config.query_template,
                doc_fields=solr_config.doc_fields
            )

def test_template_to_json_payload(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="id"))
    solr_engine = SolrSearchEngine("https://fakeurl")
    template = 'q=ghosts&fq=genre:horror&wt=json'
    expected_payload = {
        'query': 'ghosts',
        'params': {
            'fq' : 'genre:horror',
            'wt': 'json'
        }
    }
    assert solr_engine._template_to_json_payload(template) == expected_payload

    template = 'q=do we have ghosts&fq=genre:horror&wt=json'
    expected_payload = {
        'query': 'do we have ghosts',
        'params': {
            'fq': 'genre:horror',
            'wt': 'json'
        }
    }
    assert solr_engine._template_to_json_payload(template) == expected_payload

    template = 'q="ghosts"&fq=genre:horror&wt=json'
    expected_payload = {
        'query': '"ghosts"',
        'params': {
            'fq': 'genre:horror',
            'wt': 'json'
        }
    }
    assert solr_engine._template_to_json_payload(template) == expected_payload

    template = 'q=ghosts?&fq=genre:horror&wt=json'
    expected_payload = {
        'query': 'ghosts?',
        'params': {
            'fq': 'genre:horror',
            'wt': 'json'
        }
    }
    assert solr_engine._template_to_json_payload(template) == expected_payload

def test_solr_search_engine_bad_url__expects__raises_validation_error():
    with pytest.raises(ValidationError):
        _ = SolrSearchEngine("fake-NONurl")
