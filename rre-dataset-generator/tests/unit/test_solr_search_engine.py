import pytest
import requests
from requests.exceptions import HTTPError
from pydantic_core import ValidationError

from src.logger import configure_logging
from src.config import Config
from src.utils import parse_args

from src.search_engine.solr_search_engine import SolrSearchEngine
from src.model.document import Document
import logging

configure_logging(level=logging.DEBUG)


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return {
            "response": {
                "docs": [
                    self._json_data
                ]
            }
        }

def test_solr_search_engine(monkeypatch):
    config = Config.load("tests/unit/resources/good_config.yaml")
    search_engine = SolrSearchEngine("https://fakeurl")

    mock_doc = {
        "id": "1",
        "mock_title": "A first mocked title",
        "mock_description": "A first mocked description"
    }
    mock_dict = {
        'id': mock_doc['id'],
        'fields': {k:v for k, v in mock_doc.items() if k !='id'}
    }

    def mock_post(*args, **kwargs):
        return MockResponse(mock_doc, 200)

    # apply the monkeypatch for requests.post to mock_post
    monkeypatch.setattr(requests, "post", mock_post)

    # search_engine.extract_documents_to_generate_queries, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_for_query_generation(documents_filter=config.documents_filter,
                                                      doc_number=config.doc_number,
                                                      doc_fields=config.doc_fields)
    assert result[0] == Document(**mock_dict)
    # search_engine.extract_documents_to_evaluate_system, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_for_evaluation(keyword="and",
                                                query_template=config.query_template,
                                                doc_fields=config.doc_fields)
    assert result[0] == Document(**mock_dict)

def test_solr_search_engine_negative_post(monkeypatch):
    config = Config.load("tests/unit/resources/good_config.yaml")
    for status_code in [400, 401, 402, 403, 500]:
        def mock_post(*args, **kwargs):
            return MockResponse({}, status_code=status_code)

        monkeypatch.setattr(requests, "post", mock_post)

        search_engine = SolrSearchEngine("https://fakeurl")

        with pytest.raises(HTTPError):
            search_engine.fetch_for_query_generation(
                documents_filter=config.documents_filter,
                doc_number=config.doc_number,
                doc_fields=config.doc_fields
            )

        with pytest.raises(HTTPError):
            search_engine.fetch_for_evaluation(
                keyword="and",
                query_template=config.query_template,
                doc_fields=config.doc_fields
            )

def test_template_to_json_body():
    template = 'q=ghosts&fq=genre:horror&wt=json'
    expected_payload = {
        'query': 'ghosts',
        'params': {
            'fq' : 'genre:horror',
            'wt': 'json'
        }
    }
    assert SolrSearchEngine.template_to_json_body(template) == expected_payload

    template = 'q=do we have ghosts&fq=genre:horror&wt=json'
    expected_payload = {
        'query': 'do we have ghosts',
        'params': {
            'fq': 'genre:horror',
            'wt': 'json'
        }
    }
    assert SolrSearchEngine.template_to_json_body(template) == expected_payload

    template = 'q="ghosts"&fq=genre:horror&wt=json'
    expected_payload = {
        'query': '"ghosts"',
        'params': {
            'fq': 'genre:horror',
            'wt': 'json'
        }
    }
    assert SolrSearchEngine.template_to_json_body(template) == expected_payload

    template = 'q=ghosts?&fq=genre:horror&wt=json'
    expected_payload = {
        'query': 'ghosts?',
        'params': {
            'fq': 'genre:horror',
            'wt': 'json'
        }
    }
    assert SolrSearchEngine.template_to_json_body(template) == expected_payload

def test_solr_search_engine_bad_url():
    with pytest.raises(ValidationError):
        _ = SolrSearchEngine("fake-NONurl")
