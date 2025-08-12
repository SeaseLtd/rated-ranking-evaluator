import pytest
import requests
import os
import sys

from src.config import Config
from src.search_engine.solr_search_engine import SolrSearchEngine
from .end_to_end_pipeline import end_to_end_pipeline_with_llm_mock

if os.environ.get("PYTEST_CURRENT_TEST", "").endswith("test_solr.py::"):
    sys.argv.extend(["--search-engine=solr"])


@pytest.fixture(scope="session")
def solr_config():
    """Fixture that loads a valid Solr config for e2e tests."""
    return Config.load("tests/integration/resources/good_solr_config.yaml")

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

# this might go in the e2e folder
def test_big_bang(solr_config):
    end_to_end_pipeline_with_llm_mock(solr_config)