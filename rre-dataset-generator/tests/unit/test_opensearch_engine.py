import logging

import requests

from src.config import Config
from src.logger import configure_logging
from src.model.document import Document
from src.search_engine.opensearch_engine import OpenSearchEngine
from tests.mocks.opensearch import MockResponseOpenSearchEngine

configure_logging(level=logging.DEBUG)


def test_opensearch_search_engine(monkeypatch):
    config = Config.load("tests/unit/resources/good_config_opensearch.yaml")
    search_engine = OpenSearchEngine("http://testurl/testcore")

    doc = {
        "id": "1",
        "title": "test title",
        "description": "test description"
    }

    hit = {
        "_index": "testcore",
        "_id": "1",
        "_score": 1.0,
        "_source": doc
    }

    expected_doc = Document(
        id=doc["id"],
        fields={k: search_engine._normalize(v) for k, v in doc.items() if k != "id"}
    )

    def post(*args, **kwargs):
        return MockResponseOpenSearchEngine([hit], status_code=200)

    monkeypatch.setattr(requests, "post", post)

    result = search_engine.fetch_for_query_generation(
        documents_filter=config.documents_filter,
        doc_number=config.doc_number,
        doc_fields=config.doc_fields
    )

    assert len(result) == 1
    assert result[0] == expected_doc

    result = search_engine.fetch_for_evaluation(
        keyword="car",
        query_template=config.query_template,
        doc_fields=config.doc_fields
    )

    assert len(result) == 1
    assert result[0] == expected_doc
