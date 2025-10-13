import pytest
import requests
from requests.exceptions import HTTPError
from pydantic_core import ValidationError

from rre_tools.core.logger import configure_logging
from rre_tools.dataset_generator.config import Config
from rre_tools.core.search_engines.search_engine_base import DOC_NUMBER_EACH_FETCH
from mocks.elasticsearch import MockResponseElasticsearchEngine

from rre_tools.core.search_engines import ElasticsearchSearchEngine
from rre_tools.core.models import Document
import logging

configure_logging(level=logging.DEBUG)


@pytest.fixture
def elasticsearch_config(resource_folder):
    """Fixture that loads a valid OpenSearch config for unit tests."""
    return Config.load(resource_folder / "good_config_elasticsearch.yaml")

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

def test_elasticsearch_engine_fetch_all__expects__results_returned(monkeypatch, elasticsearch_config, mock_doc, mock_dict):
    search_engine = ElasticsearchSearchEngine("https://fakeurl")

    call_counter = {"count": 0}

    def mock_post(*args, **kwargs):
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            return MockResponseElasticsearchEngine(json_data=[], total_hits=2* DOC_NUMBER_EACH_FETCH, status_code=200)
        elif call_counter["count"] == 2 or call_counter["count"] == 3:
            return MockResponseElasticsearchEngine(json_data=[mock_doc] * DOC_NUMBER_EACH_FETCH, status_code=200)
        else:
            return MockResponseElasticsearchEngine(json_data=[], status_code=200)

    monkeypatch.setattr(requests, "post", mock_post)

    # search_engine.extract_documents_to_evaluate_system, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_all(doc_fields=elasticsearch_config.doc_fields)
    first = next(result)
    assert first == Document(**mock_dict)

    doc_list = [first]
    for doc in result:
        doc_list.append(doc)
    assert len(doc_list) == 2 * DOC_NUMBER_EACH_FETCH


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
