import pytest
import requests
from src.search_engine.solr_search_engine import SolrSearchEngine

def test_core_exists(solr_url):
    r = requests.get(solr_url + "../admin/cores?action=STATUS&wt=json")
    data = r.json()
    assert "testcore" in data["status"]

def test_core_has_docs(solr_url):
    r = requests.get(solr_url + "select?q=*:*&rows=0&wt=json")
    assert r.ok, r.text                          # mensaje útil si falla
    assert r.json()["response"]["numFound"] > 0

@pytest.mark.parametrize("field", ["id", "title"])
def test_docs_have_field(solr_url, field):
    r = requests.get(solr_url + "select?q=*:*&rows=1&fl=id,title&wt=json")
    assert r.ok
    assert field in r.json()["response"]["docs"][0]


def test_search_engine_fetch(solr_url):
    engine = SolrSearchEngine(solr_url)
    docs   = engine.fetch_for_query_generation(None, 3, ["title","body"])
    assert len(docs) == 3 and all(d.id and d.fields for d in docs)
