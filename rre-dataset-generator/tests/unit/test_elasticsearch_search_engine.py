import pytest
import requests
from requests.exceptions import HTTPError
from pydantic_core import ValidationError

from src.logger import configure_logging
from src.config import Config
from tests.mocks.elasticsearch import MockResponseElasticsearchEngine


from src.search_engine.elasticsearch_search_engine import ElasticsearchSearchEngine
from src.model.document import Document
import logging

configure_logging(level=logging.DEBUG)


@pytest.fixture
def elasticsearch_config():
    """Fixture that loads a valid OpenSearch config for unit tests."""
    return Config.load("tests/unit/resources/elasticsearch_good_config.yaml")

@pytest.fixture
def mock_doc():
    return {
        "_id": "1",
        '_source': {
            "mock_title": ["A first mocked title"],
            "mock_description": ["A first mocked description"]
        }
    }

@pytest.fixture
def mock_dict(mock_doc):
    return {
        'id': mock_doc['_id'],
        'fields': mock_doc["_source"]
    }

def test_elasticsearch_search_engine_fetch_for_query_generation__expects__result_returned(monkeypatch, elasticsearch_config, mock_doc, mock_dict):
    url = "https://fakeurl"
    search_engine = ElasticsearchSearchEngine(url)

    # apply the monkeypatch for requests.post to mock_post
    monkeypatch.setattr(requests, "post",
                        lambda *args, **kwargs: MockResponseElasticsearchEngine([mock_doc], status_code=200)
                        )
    # search_engine.extract_documents_to_generate_queries, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_for_query_generation(documents_filter=elasticsearch_config.documents_filter,
                                                      doc_number=elasticsearch_config.doc_number,
                                                      doc_fields=elasticsearch_config.doc_fields)
    assert result[0] == Document(**mock_dict)

def test_elasticsearch_search_engine_fetch_for_evaluation__expects__result_returned(monkeypatch, elasticsearch_config, mock_doc, mock_dict):
    url = "https://fakeurl"
    search_engine = ElasticsearchSearchEngine(url)

    # apply the monkeypatch for requests.post to mock_post
    monkeypatch.setattr(requests, "post",
                        lambda *args, **kwargs: MockResponseElasticsearchEngine([mock_doc], status_code=200)
                        )
    # search_engine.extract_documents_to_evaluate_system, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_for_evaluation(keyword="and",
                                                query_template=elasticsearch_config.query_template,
                                                doc_fields=elasticsearch_config.doc_fields)
    assert result[0] == Document(**mock_dict)

def test_elasticsearch_search_engine_negative_post_fetch_for_query_generation__expects__raises_http_error(monkeypatch, elasticsearch_config):
    for status_code in [400, 401, 402, 403, 500]:
        monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseElasticsearchEngine([],
                                                                                                    status_code=status_code))

        search_engine = ElasticsearchSearchEngine("https://fakeurl")

        with pytest.raises(HTTPError):
            search_engine.fetch_for_query_generation(
                documents_filter=elasticsearch_config.documents_filter,
                doc_number=elasticsearch_config.doc_number,
                doc_fields=elasticsearch_config.doc_fields
            )


def test_elasticsearch_search_engine_negative_post_fetch_for_evaluation__expects__raises_http_error(monkeypatch, elasticsearch_config):
    for status_code in [400, 401, 402, 403, 500]:
        monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponseElasticsearchEngine([],
                                                                                                    status_code=status_code))

        search_engine = ElasticsearchSearchEngine("https://fakeurl")

        with pytest.raises(HTTPError):
            search_engine.fetch_for_evaluation(
                keyword="and",
                query_template=elasticsearch_config.query_template,
                doc_fields=elasticsearch_config.doc_fields
            )

def test_elasticsearch_search_engine_bad_url__expects__raises_validation_error():
    with pytest.raises(ValidationError):
        _ = ElasticsearchSearchEngine("fake-NONurl")
