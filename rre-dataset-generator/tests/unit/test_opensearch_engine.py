import json
import logging

import pytest
import requests

from src.config import Config
from src.logger import configure_logging
from src.model.document import Document
from src.search_engine.opensearch_engine import OpenSearchEngine
from tests.mocks.opensearch import MockResponseOpenSearchEngine

configure_logging(level=logging.DEBUG)


@pytest.fixture
def opensearch_config():
    """Fixture that loads a valid OpenSearch config for unit tests."""
    return Config.load("tests/unit/resources/good_config_opensearch.yaml")


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


def test_fetch_for_query_generation(monkeypatch, opensearch_config, opensearch_hit):
    opensearch = OpenSearchEngine("http://testurl/testcore")

    expected_doc = Document(
        id="1",
        fields={
            "title": opensearch._normalize("test title"),
            "description": opensearch._normalize("test description")
        }
    )

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


def test_fetch_for_evaluation(monkeypatch, opensearch_config, opensearch_hit):
    opensearch = OpenSearchEngine("http://testurl/testcore")

    expected_doc = Document(
        id="1",
        fields={
            "title": opensearch._normalize("test title"),
            "description": opensearch._normalize("test description")
        }
    )

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


def test_normalize():
    engine = OpenSearchEngine("http://dummy")

    assert engine._normalize("  hello  ") == ["hello"], "Failed to normalize string"
    assert engine._normalize(["a", " b "]) == ["a", "b"], "Failed to normalize list of strings"
    assert engine._normalize(123) == ["123"], "Failed to normalize integer"
    assert engine._normalize(None) == [], "Failed to normalize None"
    assert engine._normalize({"key": "   value  "}) == [json.dumps({"key": "value"})], "Failed to normalize dict"

