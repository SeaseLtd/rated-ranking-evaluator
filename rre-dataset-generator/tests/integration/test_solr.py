import pytest
import requests
from pydantic import HttpUrl

from src.config import Config
from src.search_engine.solr_search_engine import SolrSearchEngine
from tests.integration.end_to_end_pipeline import end_to_end_pipeline_with_llm_mock


@pytest.fixture(scope="session")
def solr_config():
    """Fixture that loads a valid Solr config for e2e tests."""
    return Config.load("tests/integration/resources/good_solr_config.yaml")


@pytest.fixture(scope="session")
def search_url(pytestconfig, docker_ip, docker_services):
    port = docker_services.port_for("solr", 8983)
    url = f"http://{docker_ip}:{port}/solr/"

    return HttpUrl(url + "testcore/")


@pytest.mark.dependency()
def test_index_exists(search_url, docker_services):
    def _is_ready() -> bool:
        try:
            ping = requests.get(search_url.encoded_string() + "admin/ping?wt=json", timeout=2)
            return ping.status_code == 200
        except requests.exceptions.RequestException:
            return False

    docker_services.wait_until_responsive(timeout=90, pause=0.5, check=_is_ready)
    assert _is_ready()


@pytest.mark.dependency(depends=["test_index_exists"])
def test_index_has_200_docs(search_url, docker_services):
    def _has_200_docs() -> bool:
        response = requests.get(search_url.encoded_string() + "select?q=*:*&rows=0&wt=json")
        if response.ok:
            return response.json()["response"]["numFound"] == 200
        else:
            return False

    docker_services.wait_until_responsive(timeout=90, pause=0.5, check=_has_200_docs)
    assert _has_200_docs()


@pytest.mark.dependency(depends=["test_index_has_200_docs"])
@pytest.mark.parametrize("field", ["id", "title"])
def test_docs_have_field(search_url, field):
    r = requests.get(search_url.encoded_string() + "select?q=*:*&rows=1&fl=id,title&wt=json", timeout=5)
    assert r.ok
    hits = r.json()["response"]["docs"]
    assert hits and field in hits[0]


@pytest.mark.dependency(depends=["test_index_has_200_docs"])
def test_search_engine_fetch(search_url):
    engine = SolrSearchEngine(search_url)
    docs = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    assert len(docs) == 3 and all(d.id and d.fields for d in docs)

# this might go in the e2e folder
@pytest.mark.dependency(depends=["test_index_has_200_docs"])
def test_big_bang(solr_config, tmp_path):
    end_to_end_pipeline_with_llm_mock(solr_config, tmp_path)
