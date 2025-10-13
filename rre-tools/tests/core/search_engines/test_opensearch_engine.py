import json
import logging

import pytest
import requests

from rre_tools.dataset_generator.config import Config
from rre_tools.core.logger import configure_logging
from rre_tools.core.models import Document
from rre_tools.core.search_engines import OpenSearchEngine
from rre_tools.core.search_engines.search_engine_base import DOC_NUMBER_EACH_FETCH
from mocks.opensearch import MockResponseOpenSearchEngine

configure_logging(level=logging.DEBUG)


@pytest.fixture
def opensearch_config(resource_folder):
    """Fixture that loads a valid OpenSearch config for unit tests."""
    return Config.load(resource_folder / "good_config_opensearch.yaml")

@pytest.fixture
def expected_doc():
    opensearch = OpenSearchEngine("http://testurl/testcore")
    return Document(
        id="1",
        fields={
            "title": opensearch._normalize("test title"),
            "description": opensearch._normalize("test description")
        }
    )

@pytest.fixture
def opensearch_hit():
    return {
        "_index": "testcore",
        "_id": "1",
        "_score": 1.0,
        "_source": {
            "id": "1",
            "title": "test title",
            "description": "test description"
        }
    }


def test_opensearch_engine_fetch_for_query_generation__expects__result_returned(monkeypatch, opensearch_config, opensearch_hit, expected_doc):
    opensearch = OpenSearchEngine("http://testurl/testcore")

    def mock_post(*args, **kwargs):
        return MockResponseOpenSearchEngine([opensearch_hit], status_code=200)

    monkeypatch.setattr(requests, "post", mock_post)

    result = opensearch.fetch_for_query_generation(
        documents_filter=opensearch_config.documents_filter,
        doc_number=opensearch_config.doc_number,
        doc_fields=opensearch_config.doc_fields
    )

    assert len(result) == 1, "Expected one document"
    assert result[0] == expected_doc, "Mismatch in query generated doc"


def test_opensearch_engine_fetch_for_evaluation__expects__result_returned(monkeypatch, opensearch_config, opensearch_hit, expected_doc):
    opensearch = OpenSearchEngine("http://testurl/testcore")

    def mock_post(*args, **kwargs):
        return MockResponseOpenSearchEngine([opensearch_hit], status_code=200)

    monkeypatch.setattr(requests, "post", mock_post)

    result = opensearch.fetch_for_evaluation(
        query_template=opensearch_config.query_template,
        keyword="car",
        doc_fields=opensearch_config.doc_fields
    )

    assert len(result) == 1, "Expected one document"
    assert result[0] == expected_doc, "Mismatch in doc evaluation"

def test_opensearch_engine_fetch_all__expects__results_returned(monkeypatch, opensearch_config, opensearch_hit, expected_doc):
    search_engine = OpenSearchEngine("https://fakeurl")

    call_counter = {"count": 0}

    def mock_post(*args, **kwargs):
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            return MockResponseOpenSearchEngine(hits_data=[], total_hits =2 * DOC_NUMBER_EACH_FETCH, status_code=200)
        elif call_counter["count"] == 2 or call_counter["count"] == 3:
            return MockResponseOpenSearchEngine(hits_data=[opensearch_hit] * DOC_NUMBER_EACH_FETCH, status_code=200)
        else:
            return MockResponseOpenSearchEngine(hits_data=[], status_code=200)

    monkeypatch.setattr(requests, "post", mock_post)

    # search_engine.extract_documents_to_evaluate_system, which contains requests.post, uses the monkeypatch
    result = search_engine.fetch_all(doc_fields=opensearch_config.doc_fields)
    first = next(result)
    assert first == expected_doc

    doc_list = [first]
    for doc in result:
        doc_list.append(doc)
    assert len(doc_list) == 2 * DOC_NUMBER_EACH_FETCH


def test_normalize():
    engine = OpenSearchEngine("http://dummy")

    assert engine._normalize("  hello  ") == ["hello"], "Failed to normalize string"
    assert engine._normalize(["a", " b "]) == ["a", "b"], "Failed to normalize list of strings"
    assert engine._normalize(123) == ["123"], "Failed to normalize integer"
    assert engine._normalize(None) == [], "Failed to normalize None"
    assert engine._normalize({"key": "   value  "}) == [json.dumps({"key": "value"})], "Failed to normalize dict"

