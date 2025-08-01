import os
import sys
import requests
import pytest

# from src.search_engine.vespa_search_engine import VespaSearchEngine

if os.environ.get("PYTEST_CURRENT_TEST", "").endswith("test_vespa.py::"):
    sys.argv.extend(["--search-engine=vespa"])


def test_index_exists(search_url):
    """Check that the 'test-index' exists."""
    assert False


def test_index_has_docs(search_url):
    """Check that there are documents in the index."""
    assert False


@pytest.mark.parametrize("field", ["_id", "title"])
def test_docs_have_field(search_url, field):
    """Verify that a given field exists in a sample doc."""
    assert False


def test_search_engine_fetch(search_url):
    # engine = VespaSearchEngine(search_url)
    # docs   = engine.fetch_for_query_generation(None, 3, ["title", "description"])
    # assert len(docs) == 3 and all(d.id and d.fields for d in docs)
    assert False
