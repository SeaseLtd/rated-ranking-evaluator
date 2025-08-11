import os
import json
import pytest
import requests
from pathlib import Path
from requests.exceptions import ConnectionError


# ❶ Path to compose
@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(
        str(pytestconfig.rootdir), "tests", "integration", "docker-compose.yml"
    )

# ❷ solr health check - URL ENDPOINT return
@pytest.fixture(scope="session")
def solr_url(docker_ip, docker_services):
    port = docker_services.port_for("solr", 8983)
    url  = f"http://{docker_ip}:{port}/solr/testcore"

    def _is_ready() -> bool:
        try:
            r = requests.get(url + "/admin/ping?wt=json")
            return r.status_code == 200
        except ConnectionError:
            return False

    docker_services.wait_until_responsive(
        timeout=60, pause=0.5, check=_is_ready
    )
    return url + "/"   




@pytest.fixture(scope="session", autouse=True)
def seed_dataset(solr_url):
    """Load dataset.json if core empty."""
    if requests.get(solr_url + "select?q=*:*&rows=0&wt=json").json()["response"]["numFound"] > 0:
        return 

    dataset_path = Path("solr-init/data/dataset.json")
    
    with dataset_path.open() as f:
        payload = json.load(f) 

    resp = requests.post(
        solr_url + "update?commit=true",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    resp.raise_for_status()
