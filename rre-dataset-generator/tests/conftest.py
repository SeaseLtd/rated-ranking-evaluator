import os
import subprocess
import pytest

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(
        str(pytestconfig.rootdir), "tests", "integration", "docker-compose.full.yml"
    )

@pytest.fixture(scope="session", autouse=True)
def docker_compose_cleanup(docker_compose_file):

    yield

    print("\nStopping and removing Docker Compose services...")
    try:
        subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "down", "--volumes", "--remove-orphans"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error during Docker cleanup: {e}")
