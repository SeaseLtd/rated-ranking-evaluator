import pytest
from pathlib import Path
import os
import json
import logging
from pydantic import ValidationError

from src.data_store import DataStore
from src.model import Document, Query


# --- fixtures ---
@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "datastore.json"

@pytest.fixture
def ds(tmp_db_path: Path) -> DataStore:
    return DataStore(path=tmp_db_path, ignore_saved_data=True)

@pytest.fixture
def docA() -> Document:
    return Document(id="doc-A", fields={"title": "A", "body": "..."})

@pytest.fixture
def docB() -> Document:
    return Document(id="doc-B", fields={"title": "B"})

@pytest.fixture
def queryQ() -> Query:
    return Query(text="hello world")


# --- helpers (tests only) ---
def _ratings_for_query(ds: DataStore, query_id: str):
    """Compat helper now that DataStore has no get_ratings_for_query()."""
    return [r for r in ds.get_ratings() if r.query_id == query_id]


# --- tests ---
def test_add_and_get_doc__expects__datastore_returns_the_same_document(ds, docA):
    ds.add_document(docA)
    assert ds.has_document(docA.id)
    assert ds.get_document(docA.id) is docA
    assert len(ds.get_documents()) == 1
    assert ds.get_document("missing-doc") is None

def test_add_document_duplicate__expects__logs_debug_and_keeps_original(ds, docA, caplog):
    caplog.set_level(logging.DEBUG)  # Ensure logs are captured (warnings/debug)
    ds.add_document(docA)
    assert len(ds.get_documents()) == 1
    ds.add_document(docA)
    assert "exists" in caplog.text
    assert len(ds.get_documents()) == 1  # does not overwrite

def test_add_and_get_query__expects__datastore_returns_the_same_query(ds, queryQ):
    ds.add_query(queryQ)
    assert ds.has_query(queryQ.id)
    assert ds.get_query(queryQ.id) is queryQ
    assert len(ds.get_queries()) == 1
    assert ds.get_query("missing-query") is None

def test_create_rating_score__expects__creates_rating_and_indexes(ds, docA, queryQ):
    ds.add_document(docA)
    ds.add_query(queryQ)
    rating = ds.create_rating_score(queryQ.id, docA.id, 2)

    assert rating is not None
    # Check if the rating object is in the main dictionary
    assert ds.rating_by_pair.get((queryQ.id, docA.id)) is rating

    # Check ratings "by query" via helper (since no get_ratings_for_query)
    ratings_for_query = _ratings_for_query(ds, queryQ.id)
    assert rating in ratings_for_query
    # Missing query returns empty
    assert _ratings_for_query(ds, "missing-query") == []

def test_create_rating_score__expects__second_call_does_not_update_existing(ds, docA, queryQ, caplog):
    ds.add_document(docA); ds.add_query(queryQ)
    rating1 = ds.create_rating_score(queryQ.id, docA.id, 1)
    caplog.set_level(logging.DEBUG)
    rating2 = ds.create_rating_score(queryQ.id, docA.id, 4)  # insert-only: does not update
    assert rating1 is rating2  # Should return the exact same object
    assert (queryQ.id, docA.id) in ds.rating_by_pair
    assert ds.rating_by_pair[(queryQ.id, docA.id)] == rating1
    assert "existing" in caplog.text

def test_create_rating_score__expects__negative_value_is_none_and_logs_error(ds, docA, queryQ, caplog):
    ds.add_document(docA); ds.add_query(queryQ)
    caplog.set_level(logging.DEBUG)
    ret = ds.create_rating_score(queryQ.id, docA.id, -1)
    assert ret is None
    assert "validation_failed" in caplog.text

def test_create_rating_score__expects__logs_warning_for_missing_ids(ds, caplog):
    caplog.set_level(logging.WARNING)
    assert ds.create_rating_score("q-missing", "d-existing", 1) is None
    assert "query_not_found" in caplog.text

def test_persistence__expects__save_and_load_roundtrip(tmp_db_path, docA, queryQ):
    ds1 = DataStore(path=tmp_db_path, ignore_saved_data=True)
    ds1.add_document(docA)
    ds1.add_query(queryQ)
    ds1.create_rating_score(queryQ.id, docA.id, 5)
    ds1.save()
    assert os.path.exists(tmp_db_path)

    ds2 = DataStore(path=tmp_db_path)  # load() is called in __init__
    assert ds2.has_document(docA.id)
    assert ds2.has_query(queryQ.id)

    assert (queryQ.id, docA.id) in ds2.rating_by_pair
    assert ds2.rating_by_pair[(queryQ.id, docA.id)].score == 5

def test_load_when_file_missing__expects__returns_empty_store(tmp_path):
    path = tmp_path / "no-such.json"
    ds = DataStore(path=path)  # should not raise
    assert ds.get_documents() == []
    assert ds.get_queries() == []
    assert ds.get_ratings() == []

def test_add_query__expects__returns_id_for_new_and_duplicate_queries(ds):
    query1 = Query(text="unique text")
    returned_id1 = ds.add_query(query1)
    assert returned_id1 == query1.id

    query2_duplicate = Query(text="unique text")  # Same text, different object/id
    returned_id2 = ds.add_query(query2_duplicate)
    assert returned_id2 == query1.id  # Should return the ID of the original query

def test_load_with_broken_references__expects__skips_dangling_ratings(tmp_db_path, docA, queryQ, caplog):
    # Simulate a corrupt file with a rating pointing to a non-existent doc
    corrupt_data = {
        "docs": [],  # docA is missing
        "queries": [queryQ.model_dump()],
        "ratings": [
            {"id": "r1", "query_id": queryQ.id, "doc_id": docA.id, "score": 5}
        ]
    }
    tmp_db_path.write_text(json.dumps(corrupt_data))

    caplog.set_level(logging.WARNING)
    ds = DataStore(path=tmp_db_path)

    # Reconstruction avoids adding "corrupt" ratings - must be associated to an existing query and document
    assert len(ds.get_ratings()) == 0      # The dangling rating should be skipped
    assert "doc_not_found" in caplog.text  # Logged from _add_rating
