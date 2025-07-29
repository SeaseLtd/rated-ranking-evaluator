"""Integration checks against the Vespa instance used in tests.

The file can be:
1. *Imported* by **pytest**, which will discover the `test_*` functions.
2. *Executed directly* with ``python vespa_test_feed.py`` for an ad-hoc check
   without the full pytest runner.

Environment variables:
    VESPA_ENDPOINT – Base URL to the Vespa HTTP port (default: http://localhost:8080)
    VESPA_SCHEMA   – Name of the document schema to query (default: news)
"""

import os
import sys
import traceback
import requests
import pytest

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, project_root)

from src.search_engine.vespa_search_engine import VespaSearchEngine


# Allow overriding endpoint via env var for CI flexibility
VESPA_ENDPOINT = os.getenv("VESPA_ENDPOINT", "http://localhost:8080")
SCHEMA = os.getenv("VESPA_SCHEMA", "news")

def check_vespa_up() -> None:
    """Raise pytest skip or RuntimeError if Vespa endpoint is unreachable."""
    try:
        requests.get(f"{VESPA_ENDPOINT}/state/v1/health", timeout=2).raise_for_status()
    except Exception as e:
        if "PYTEST_CURRENT_TEST" in os.environ:
            # When running under pytest we mark the module as skipped.
            pytest.skip(
                f"Vespa endpoint {VESPA_ENDPOINT} is not reachable: {e}",
                allow_module_level=True,
            )
        else:
            raise RuntimeError(f"Vespa endpoint {VESPA_ENDPOINT} is not reachable: {e}") from e


# ------------------------- pytest test cases -----------------------------

def test_fetch_by_title(engine: VespaSearchEngine):
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
    title_val = doc.fields.get("title")
    if isinstance(title_val, list):
        assert "Helicopter Crashes in Colombian Drug War, Kills 20" in title_val
    else:
        assert title_val == "Helicopter Crashes in Colombian Drug War, Kills 20"
    assert doc.fields.get("description"), "Description field should be present"

def test_fetch_all_documents(engine: VespaSearchEngine):
    """Fetching without filters should at least return the demo doc."""
    results = engine.fetch_for_query_generation(
        documents_filter=None,
        doc_number=10,
        doc_fields=["id", "title"],
    )

    titles: set[str] = set()
    for doc in results:
        val = doc.fields.get("title")
        if isinstance(val, list):
            titles.update(val)
        elif val is not None:
            titles.add(str(val))

    assert (
        "Helicopter Crashes in Colombian Drug War, Kills 20" in titles
    ), "Demo document not found in unfiltered fetch"

# ----------------------------- CLI entry ---------------------------------

def main() -> None:
    """Run the same checks without pytest, printing a concise summary."""
    print(f"Checking Vespa at {VESPA_ENDPOINT} (schema '{SCHEMA}')…")
    check_vespa_up()

    engine = VespaSearchEngine(endpoint=VESPA_ENDPOINT, schema=SCHEMA)

    try:
        test_fetch_by_title(engine)
        print("✔ fetch_by_title passed")

        test_fetch_all_documents(engine)
        print("✔ fetch_all_documents passed")

    except AssertionError as err:
        msg = str(err) or repr(err)
        print(f"❌ Test assertion failed: {msg}")
        sys.exit(1)
    except Exception as exc:
        print("❌ Unexpected exception during checks: \n" + ''.join(traceback.format_exception(exc)))
        sys.exit(1)

    print("All Vespa integration checks passed.")

if __name__ == "__main__":
    main()
