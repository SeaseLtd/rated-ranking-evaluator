import pytest
import requests
import logging

from src.logger import configure_logging
from src.config import Config
from src.utils import parse_args

from src.search_engine.solr_search_engine import SolrSearchEngine

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
    config = Config.load("tests/integration/resources/good_config.yaml")
    search_engine = SolrSearchEngine("https://fakeurl")

    mock_dict = {
        "mock_id": "1",
        "mock_title": "A first mocked title",
        "mock_description": "A first mocked description"
    }

    def mock_post(*args, **kwargs):
        return MockResponse(mock_dict, 200)

    # apply the monkeypatch for requests.post to mock_post
    monkeypatch.setattr(requests, "post", mock_post)

    # search_engine.extract_documents_to_generate_queries, which contains requests.post, uses the monkeypatch
    result = search_engine.extract_documents_to_generate_queries(documents_filter=config.documents_filter,
                                                        doc_number=config.doc_number)
    assert result[0] == mock_dict
    # search_engine.extract_documents_to_evaluate_system, which contains requests.post, uses the monkeypatch
    result = search_engine.extract_documents_to_evaluate_system(keyword="and",
                                                                query_template=config.query_template)
    assert result[0] == mock_dict

def test_solr_search_engine_negative_post(monkeypatch):
    config = Config.load("tests/integration/resources/good_config.yaml")

    def mock_post(*args, **kwargs):
        return MockResponse({}, status_code=500)

    monkeypatch.setattr(requests, "post", mock_post)

    search_engine = SolrSearchEngine("https://fakeurl")

    with pytest.raises(ValueError):
        search_engine.extract_documents_to_generate_queries(
            documents_filter=config.documents_filter,
            doc_number=config.doc_number
        )

    with pytest.raises(ValueError):
        search_engine.extract_documents_to_evaluate_system(
            keyword="and",
            query_template=config.query_template
        )
