import os
import sys
import requests
import pytest
# from src.search_engine.elasticsearch_search_engine import ElasticsearchSearchEngine

if os.environ.get("PYTEST_CURRENT_TEST", "").endswith("test_elasticsearch.py::"):
    sys.argv.extend(["--search-engine=elasticsearch"])


def test_index_exists(search_url):
    """Check that the 'testcore' exists."""
    # r = requests.get(search_url + "testcore")
    # assert r.ok, f"Index 'testcore' not found: {r.text}"
    assert False

def test_index_has_docs(search_url):
    """Check that there are documents in the index."""
    # r = requests.get(search_url + "testcore/_search", params={"size": 0})
    # assert r.ok, r.text
    # assert r.json()["hits"]["total"]["value"] > 0
    assert False

@pytest.mark.parametrize("field", ["_id", "title"])
def test_docs_have_field(search_url, field):
    """Verify that a given field exists in a sample doc."""
    # r = requests.get(search_url + "test-index/_search", params={"size": 1, "_source": field})
    # assert r.ok, r.text
    # doc = r.json()["hits"]["hits"][0]["_source"]
    # assert field in doc, f"Field '{field}' not in document: {doc}"
    assert False


def test_search_engine_fetch(search_url):
    # engine = ElasticsearchSearchEngine(search_url)
    # docs   = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    # assert len(docs) == 3 and all(d.id and d.fields for d in docs)
    assert False
