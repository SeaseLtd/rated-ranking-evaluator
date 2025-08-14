import pytest
import requests
from pydantic import HttpUrl

from src.config import Config
from src.search_engine.elasticsearch_search_engine import ElasticsearchSearchEngine
from tests.integration.end_to_end_pipeline import end_to_end_pipeline_with_llm_mock


@pytest.fixture(scope="session")
def elastic_config():
    """Fixture that loads a valid Elasticsearch config for e2e tests."""
    return Config.load("tests/integration/resources/good_elasticsearch_config.yaml")


@pytest.fixture(scope="session")
def search_url(pytestconfig, docker_ip, docker_services):
    port = docker_services.port_for("elasticsearch", 9200)
    url = f"http://{docker_ip}:{port}/"

    def _is_ready() -> bool:
        try:
            health = requests.get(url + "_cluster/health", timeout=2)
            if health.status_code != 200:
                return False
            indices = requests.get(url + "_cat/indices/testcore?format=json", timeout=2)
            return indices.status_code == 200 and len(indices.json()) > 0
        except requests.exceptions.RequestException:
            return False

    docker_services.wait_until_responsive(timeout=90, pause=0.5, check=_is_ready)


    def _has_200_docs() -> bool:
        response = requests.get(url + "testcore/_count")
        return response.json()["count"] == 200

    docker_services.wait_until_responsive(timeout=90, pause=0.5, check=_has_200_docs)

    return HttpUrl(url)


def test_index_exists(search_url):
    r = requests.get(search_url.encoded_string() + "_cat/indices/testcore?format=json")
    assert r.ok
    assert any(idx.get("index") == "testcore" for idx in r.json())


def test_index_has_docs(search_url):
    r = requests.get(search_url.encoded_string() + "testcore/_count")
    assert r.ok
    assert r.json()["count"] > 0


@pytest.mark.parametrize("field", ["title"])
def test_docs_have_field(search_url, field):
    r = requests.get(search_url.encoded_string() + "testcore/_search?size=1", timeout=5)
    assert r.ok
    hits = r.json()["hits"]["hits"]
    assert hits and field in hits[0]["_source"]


def test_search_engine_fetch(search_url):
    engine = ElasticsearchSearchEngine(search_url)
    docs = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    assert len(docs) == 3 and all(d.id and d.fields for d in docs)


def test_big_bang(elastic_config, tmp_path):
    end_to_end_pipeline_with_llm_mock(elastic_config, tmp_path)
