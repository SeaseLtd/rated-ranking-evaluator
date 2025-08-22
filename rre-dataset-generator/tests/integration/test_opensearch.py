import pytest
import requests
from pydantic import HttpUrl

from src.config import Config
from src.search_engine.opensearch_engine import OpenSearchEngine
from tests.integration.end_to_end_pipeline import end_to_end_pipeline_with_llm_mock


@pytest.fixture(scope="session")
def opensearch_config():
    """Fixture that loads a valid OpenSearch config for e2e tests."""
    return Config.load("tests/integration/resources/good_opensearch_config.yaml")


@pytest.fixture(scope="session")
def search_url(pytestconfig, docker_ip, docker_services):
    port = docker_services.port_for("opensearch", 9200)
    url = f"http://{docker_ip}:{port}/"

    return HttpUrl(url)


@pytest.mark.dependency()
def test_index_exists(search_url, docker_services):
    def _is_ready() -> bool:
        try:
            health = requests.get(search_url.encoded_string() + "_cluster/health", timeout=2)
            return health.status_code == 200
        except requests.exceptions.RequestException:
            return False

    docker_services.wait_until_responsive(timeout=90, pause=0.5, check=_is_ready)
    assert _is_ready()


@pytest.mark.dependency(depends=["test_index_exists"])
def test_index_has_200_docs(search_url, docker_services):
    def _has_200_docs() -> bool:
        response = requests.get(search_url.encoded_string() + "testcore/_count")
        if response.ok:
            return response.json()["count"] == 200
        else:
            return False

    docker_services.wait_until_responsive(timeout=90, pause=0.5, check=_has_200_docs)
    assert _has_200_docs()


@pytest.mark.dependency(depends=["test_index_has_200_docs"])
@pytest.mark.parametrize("field", ["title"])
def test_docs_have_field(search_url, field):
    r = requests.get(search_url.encoded_string() + "testcore/_search?size=1", timeout=5)
    assert r.ok
    hits = r.json()["hits"]["hits"]
    assert hits and field in hits[0]["_source"]


@pytest.mark.dependency(depends=["test_index_has_200_docs"])
def test_search_engine_fetch(search_url):
    engine = OpenSearchEngine(search_url)
    docs = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    assert len(docs) == 3 and all(d.id and d.fields for d in docs)


@pytest.mark.dependency(depends=["test_index_has_200_docs"])
def test_big_bang(opensearch_config, tmp_path):
    end_to_end_pipeline_with_llm_mock(opensearch_config, tmp_path)
