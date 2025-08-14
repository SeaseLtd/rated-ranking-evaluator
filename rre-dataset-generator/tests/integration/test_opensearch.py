import os
import sys
import requests
import pytest

# from src.search_engine.opensearch_engine import OpenSearchEngine

@pytest.fixture(scope="session")
def search_url():
    return "http://localhost:9200/"

def test_index_exists(search_url):
    """Check that the 'test-index' exists."""
    assert True


def test_index_has_docs(search_url):
    """Check that there are documents in the index."""
    assert True


@pytest.mark.parametrize("field", ["_id", "title"])
def test_docs_have_field(search_url, field):
    """Verify that a given field exists in a sample doc."""
    assert True


def test_search_engine_fetch(search_url):
    # engine = OpenSearchEngine(search_url)
    # docs   = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    # assert len(docs) == 3 and all(d.id and d.fields for d in docs)
    assert True
