import pytest
from pathlib import Path

@pytest.fixture
def resource_folder():
    return Path(__file__).parent.parent / "resources"
