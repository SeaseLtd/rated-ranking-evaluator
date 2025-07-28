import os
import sys
import pytest
import requests

# Add project root to Python path 
# THIS IS A HARD-FIX to allow the test to run from the integration directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, project_root)

from src.search_engine.vespa_search_engine import VespaSearchEngine


# Allow overriding endpoint via env var for CI flexibility
VESPA_ENDPOINT = os.getenv("VESPA_ENDPOINT", "http://localhost:8080")
SCHEMA = os.getenv("VESPA_SCHEMA", "news")

# Skip all tests if Vespa is unreachable to give a clearer signal in CI
try:
    requests.get(f"{VESPA_ENDPOINT}/state/v1/health", timeout=2).raise_for_status()
except Exception as e:
    pytest.skip(f"Vespa endpoint {VESPA_ENDPOINT} is not reachable: {e}", allow_module_level=True)

engine = VespaSearchEngine(endpoint=VESPA_ENDPOINT, schema=SCHEMA)

def test_fetch_by_title():
    """Ensure the sample document can be retrieved by exact title filter."""
    filters = [{
        "title": [
            "Helicopter Crashes in Colombian Drug War, Kills 20"
        ]
    }]
    results = engine.fetch_for_query_generation(
        documents_filter=filters,
        doc_number=10,
        doc_fields=["id", "title", "description"],
    )

    assert len(results) == 1, "Expected exactly one document back"
    doc = results[0]
    assert doc.fields.get("title") == "Helicopter Crashes in Colombian Drug War, Kills 20"
    assert doc.fields.get("description"), "Description field should be present"

def test_fetch_all_documents():
    """Fetching without filters should at least return the demo doc."""
    results = engine.fetch_for_query_generation(
        documents_filter=None,
        doc_number=10,
        doc_fields=["id", "title"],
    )
    titles = {d.fields.get("title") for d in results}
    assert (
        "Helicopter Crashes in Colombian Drug War, Kills 20" in titles
    ), "Demo document not found in unfiltered fetch"
