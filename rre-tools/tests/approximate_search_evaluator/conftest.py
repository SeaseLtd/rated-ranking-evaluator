from pathlib import Path
import pytest


@pytest.fixture
def resource_folder():
    return Path(__file__).parent.parent / "resources" / "approximate_search_evaluator"
