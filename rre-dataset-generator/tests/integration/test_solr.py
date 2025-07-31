import pytest
import requests
import os
import sys
from src.search_engine.solr_search_engine import SolrSearchEngine

if os.environ.get("PYTEST_CURRENT_TEST", "").endswith("test_solr.py::"):
    sys.argv.extend(["--search-engine=solr"])

def test_core_exists(search_url):
    r = requests.get(search_url + "../admin/cores?action=STATUS&wt=json")
    data = r.json()
    assert "testcore" in data["status"]

def test_core_has_docs(search_url):
    r = requests.get(search_url + "select?q=*:*&rows=0&wt=json")
    assert r.ok, r.text
    assert r.json()["response"]["numFound"] > 0

@pytest.mark.parametrize("field", ["id", "title"])
def test_docs_have_field(search_url, field):
    r = requests.get(search_url + "select?q=*:*&rows=1&fl=id,title&wt=json")
    assert r.ok
    assert field in r.json()["response"]["docs"][0]


def test_search_engine_fetch(search_url):
    engine = SolrSearchEngine(search_url)
    docs   = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    assert len(docs) == 3 and all(d.id and d.fields for d in docs)

