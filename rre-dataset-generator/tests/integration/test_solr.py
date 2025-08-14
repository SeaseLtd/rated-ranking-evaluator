import json
from pathlib import Path

import pytest
import requests
import os
import docker
from pydantic import HttpUrl

from src.config import Config
from src.search_engine.solr_search_engine import SolrSearchEngine
from .end_to_end_pipeline import end_to_end_pipeline_with_llm_mock

def pytest_configure():
    client = docker.from_env()

    try:
        container = client.containers.get("solr")
        print(f"[pytest-docker] Removing existing container 'solr' to avoid name conflicts.")
        container.remove(force=True)
    except docker.errors.NotFound:
        pass

@pytest.fixture(scope="session")
def solr_config():
    """Fixture that loads a valid Solr config for e2e tests."""
    return Config.load("tests/integration/resources/good_solr_config.yaml")

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(
        str(pytestconfig.rootdir), "tests", "integration", f"docker-compose.solr.yml"
    )

@pytest.fixture(scope="session")
def search_url(pytestconfig, docker_ip, docker_services):
    port = docker_services.port_for("solr", 8983)
    url = f"http://{docker_ip}:{port}/solr/testcore/"
    print(url)

    def _is_ready() -> bool:
        try:
            ping = requests.get(url + "admin/ping?wt=json", timeout=2)
            if ping.status_code != 200:
                return False
            cores = requests.get(url + "../admin/cores?action=STATUS&wt=json", timeout=2)
            return "testcore" in cores.json().get("status", {})
        except requests.exceptions.RequestException:
            return False

    docker_services.wait_until_responsive(timeout=60, pause=0.5, check=_is_ready)
    return HttpUrl(url)

@pytest.fixture(scope="session", autouse=True)
def seed_dataset(pytestconfig, search_url):
    dataset_path = Path(os.path.join(str(pytestconfig.rootdir),
                                     "tests", "integration",
                                     "solr-init/data/dataset.json")
                        )

    with dataset_path.open() as f:
        payload = json.load(f)

    if requests.get(search_url.encoded_string() + "select?q=*:*&rows=0&wt=json").json()["response"]["numFound"] > 0:
        return
    resp = requests.post(
        search_url.encoded_string() + "update?commit=true",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    resp.raise_for_status()

def test_core_exists(search_url):
    r = requests.get(search_url.encoded_string() + "../admin/cores?action=STATUS&wt=json")
    data = r.json()
    assert "testcore" in data["status"]

def test_core_has_docs(search_url):
    r = requests.get(search_url.encoded_string() + "select?q=*:*&rows=0&wt=json")
    assert r.ok, r.text
    assert r.json()["response"]["numFound"] > 0

@pytest.mark.parametrize("field", ["id", "title"])
def test_docs_have_field(search_url, field):
    r = requests.get(search_url.encoded_string() + "select?q=*:*&rows=1&fl=id,title&wt=json")
    assert r.ok
    assert field in r.json()["response"]["docs"][0]


def test_search_engine_fetch(search_url):
    engine = SolrSearchEngine(search_url)
    docs   = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    assert len(docs) == 3 and all(d.id and d.fields for d in docs)

# this might go in the e2e folder
def test_big_bang(solr_config):
    end_to_end_pipeline_with_llm_mock(solr_config)