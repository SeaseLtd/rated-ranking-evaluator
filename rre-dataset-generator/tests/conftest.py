# from pathlib import Path
#
# import pytest
# import os
# import json
# import requests
# from requests.exceptions import ConnectionError
# import docker
#
# def pytest_configure(config):
#     """
#     Remove any existing container for the selected search engine
#     to avoid 'container name already in use' errors.
#     """
#     engine = config.getoption("--search-engine")
#     client = docker.from_env()
#
#     try:
#         container = client.containers.get(engine)
#         print(f"[pytest-docker] Removing existing container '{engine}' to avoid name conflicts.")
#         container.remove(force=True)
#     except docker.errors.NotFound:
#         pass
#
# @pytest.fixture(scope="session")
# def docker_compose_file(pytestconfig):
#     engine = pytestconfig.getoption("search_engine")
#     return os.path.join(
#         str(pytestconfig.rootdir), "tests", "integration", f"docker-compose.{engine}.yml"
#     )
#
# @pytest.fixture(scope="session")
# def search_url(pytestconfig, docker_ip, docker_services):
#     engine = pytestconfig.getoption("search_engine")
#     if engine == "solr":
#         port = docker_services.port_for("solr", 8983)
#         url = f"http://{docker_ip}:{port}/solr/testcore/"
#
#         def _is_ready() -> bool:
#             try:
#                 r = requests.get(url + "admin/ping?wt=json")
#                 return r.status_code == 200
#             except ConnectionError:
#                 return False
#
#     elif engine == "elasticsearch":
#         port = docker_services.port_for("elasticsearch", 9200)
#         url = f"http://{docker_ip}:{port}/"
#
#         def _is_ready() -> bool:
#             try:
#                 r = requests.get(url)
#                 return r.status_code == 200 and "cluster_name" in r.json()
#             except ConnectionError:
#                 return False
#
#     elif engine == "opensearch":
#         port = docker_services.port_for("opensearch", 9200)
#         url = f"http://{docker_ip}:{port}/"
#
#         def _is_ready() -> bool:
#             try:
#                 r = requests.get(url)
#                 return r.status_code == 200 and "cluster_name" in r.json()
#             except ConnectionError:
#                 return False
#
#     elif engine == "vespa":
#         port = docker_services.port_for("vespa", 8080)
#         url = f"http://{docker_ip}:{port}/document/v1/test/test/docid/"
#
#         def _is_ready() -> bool:
#             try:
#                 r = requests.get(url)
#                 return r.status_code in (200, 400)  # Vespa may return 400 if doc not found
#             except ConnectionError:
#                 return False
#
#     else:
#         raise ValueError(f"Unsupported engine: {engine}")
#
#     docker_services.wait_until_responsive(timeout=60, pause=0.5, check=_is_ready)
#     return url
#
# @pytest.fixture(scope="session", autouse=True)
# def seed_dataset(pytestconfig, search_url):
#     engine = pytestconfig.getoption("search_engine")
#     dataset_path = Path(os.path.join(str(pytestconfig.rootdir),
#                                      "tests", "integration",
#                                      "solr-init/data/dataset.json")
#                         )  # Or make this path dynamic per engine
#
#     with dataset_path.open() as f:
#         payload = json.load(f)
#
#     if engine == "solr":
#         url = search_url
#         if requests.get(url + "select?q=*:*&rows=0&wt=json").json()["response"]["numFound"] > 0:
#             return
#         resp = requests.post(
#             url + "update?commit=true",
#             headers={"Content-Type": "application/json"},
#             data=json.dumps(payload),
#             timeout=60,
#         )
#         resp.raise_for_status()
#
#     elif engine in {"elasticsearch", "opensearch"}:
#         # Optional: clear existing docs
#         requests.delete(search_url + "test-index", timeout=10)
#         resp = requests.put(search_url + "test-index", timeout=10)
#         resp.raise_for_status()
#         for doc in payload:
#             r = requests.post(search_url + "test-index/_doc", json=doc)
#             r.raise_for_status()
#
#     elif engine == "vespa":
#         for doc in payload:
#             doc_id = doc.get("id", "doc")  # Adjust if needed
#             r = requests.post(
#                 f"{search_url}{doc_id}",
#                 json={"fields": doc},
#                 headers={"Content-Type": "application/json"},
#                 timeout=10
#             )
#             r.raise_for_status()
