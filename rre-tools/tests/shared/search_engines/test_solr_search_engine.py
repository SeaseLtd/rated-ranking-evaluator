import pytest
import requests
from requests.exceptions import HTTPError
from pydantic_core import ValidationError

from rre_tools.shared.logger import configure_logging
from rre_tools.dataset_generator.config import Config
from mocks.solr import MockResponseSolrEngine, MockResponseUniqueKey


from rre_tools.shared.search_engines import SolrSearchEngine
from rre_tools.shared.search_engines.search_engine_base import DOC_NUMBER_EACH_FETCH
from rre_tools.shared.models import Document
import logging

configure_logging(level=logging.DEBUG)

@pytest.fixture
def solr_config(resource_folder):
    """Fixture that loads a valid OpenSearch config for unit tests."""
    return Config.load(resource_folder / "good_config_solr.yaml")

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
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseSolrEngine([mock_doc], status_code=200))

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
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseSolrEngine([mock_doc], status_code=200))

    # search_engine.extract_documents_to_evaluate_system, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_for_evaluation(keyword="and",
                                                query_template=solr_config.query_template,
                                                doc_fields=solr_config.doc_fields)
    assert result[0] == Document(**mock_dict)

def test_solr_search_engine_fetch_all__expects__results_returned(monkeypatch, solr_config, mock_doc, mock_dict):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="mock_id"))
    search_engine = SolrSearchEngine("https://fakeurl")

    call_counter = {"count": 0}

    def mock_get(*args, **kwargs):
        call_counter["count"] += 1
        if call_counter["count"] == 1: # first call is to just get the number of hits, in this case
            return MockResponseSolrEngine(json_data=[], total_hits=2*DOC_NUMBER_EACH_FETCH, status_code=200)
        elif call_counter["count"] == 2 or call_counter["count"] == 3:  # second and third are to catch actual docs call is to just get the number of hits, in this case
            return MockResponseSolrEngine(json_data=[mock_doc] * DOC_NUMBER_EACH_FETCH, status_code=200)
        else:
            return MockResponseSolrEngine(json_data=[], status_code=200)

    monkeypatch.setattr(requests, "get", mock_get)

    # search_engine.fetch_all, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_all(doc_fields=solr_config.doc_fields)
    first = next(result)
    assert first == Document(**mock_dict)

    doc_list = [first]
    for doc in result:
        doc_list.append(doc)
    assert len(doc_list) == 2 * DOC_NUMBER_EACH_FETCH

def test_solr_search_engine_negative_post_fetch_for_query_generation__expects__raises_http_error(monkeypatch, solr_config):
    for status_code in [400, 401, 402, 403, 500]:
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="identifier"))

        search_engine = SolrSearchEngine("https://fakeurl")

        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseSolrEngine([], status_code=status_code))


        with pytest.raises(HTTPError):
            search_engine.fetch_for_query_generation(
                documents_filter=solr_config.documents_filter,
                doc_number=solr_config.doc_number,
                doc_fields=solr_config.doc_fields
            )


def test_solr_search_engine_negative_post_fetch_for_evaluation__expects__raises_http_error(monkeypatch, solr_config):
    for status_code in [400, 401, 402, 403, 500]:
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseUniqueKey(ident="identifier"))

        search_engine = SolrSearchEngine("https://fakeurl")

        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponseSolrEngine([], status_code=status_code))

        with pytest.raises(HTTPError):
            search_engine.fetch_for_evaluation(
                keyword="and",
                query_template=solr_config.query_template,
                doc_fields=solr_config.doc_fields
            )

def test_solr_search_engine_bad_url__expects__raises_validation_error():
    with pytest.raises(ValidationError):
        _ = SolrSearchEngine("fake-NONurl")
