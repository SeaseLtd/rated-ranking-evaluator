import pytest
from pathlib import Path
import os
import json
import logging

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
def doc_a() -> Document:
    return Document(id="doc-A", fields={"title": "A", "body": "..."})

@pytest.fixture
def doc_b() -> Document:
    return Document(id="doc-B", fields={"title": "B"})

@pytest.fixture
def query_q() -> Query:
    return Query(text="hello world")


# --- helpers (tests only) ---
def _ratings_for_query(ds: DataStore, query_id: str):
    """Compat helper now that DataStore has no get_ratings_for_query()."""
    return [r for r in ds.get_ratings() if r.query_id == query_id]


# --- tests ---
def test_add_and_get_doc__expects__datastore_returns_the_same_document(ds, doc_a):
    ds.add_document(doc_a)
    assert ds.has_document(doc_a.id)
    assert ds.get_document(doc_a.id) is doc_a
    assert len(ds.get_documents()) == 1
    assert ds.get_document("missing-doc") is None

def test_add_document_duplicate__expects__logs_debug_and_keeps_original(ds, doc_a, caplog):
    caplog.set_level(logging.DEBUG)  # Ensure logs are captured (warnings/debug)
    ds.add_document(doc_a)
    assert len(ds.get_documents()) == 1
    ds.add_document(doc_a)
    assert "exists" in caplog.text
    assert len(ds.get_documents()) == 1  # does not overwrite

def test_add_and_get_query__expects__datastore_returns_the_same_query(ds, query_q):
    query = ds.add_query(query_q.text)
    assert isinstance(query, Query)
    assert ds.has_query(query.id)
    assert ds.get_query(query.id).text == query_q.text
    assert len(ds.get_queries()) == 1
    assert ds.get_query("missing-query") is None

def test_create_rating_score__expects__creates_rating_and_indexes(ds, doc_a, query_q):
    query = ds.add_query(query_q.text)
    ds.add_document(doc_a)
    rating = ds.create_rating_score(query.id, doc_a.id, 2)

    assert rating is not None
    # Check if the rating object is in the main dictionary
    assert ds.rating_by_pair.get((query.id, doc_a.id)) is rating

    # Check ratings "by query" via helper (since no get_ratings_for_query)
    ratings_for_query = _ratings_for_query(ds, query.id)
    assert rating in ratings_for_query
    # Missing query returns empty
    assert _ratings_for_query(ds, "missing-query") == []

def test_create_rating_score__expects__second_call_does_not_update_existing(ds, doc_a, query_q, caplog):
    query = ds.add_query(query_q.text)
    ds.add_document(doc_a)
    rating1 = ds.create_rating_score(query.id, doc_a.id, 1)
    caplog.set_level(logging.DEBUG)
    rating2 = ds.create_rating_score(query.id, doc_a.id, 4)  # insert-only: does not update
    assert rating1 is rating2  # Should return the exact same object
    assert (query.id, doc_a.id) in ds.rating_by_pair
    assert ds.rating_by_pair[(query.id, doc_a.id)] == rating1
    assert "existing" in caplog.text

def test_create_rating_score__expects__negative_value_is_none_and_logs_error(ds, doc_a, query_q, caplog):
    ds.add_document(doc_a)
    ds.add_query(query_q.text)
    caplog.set_level(logging.DEBUG)
    ret = ds.create_rating_score(query_q.id, doc_a.id, -1)
    assert ret is None
    assert "validation_failed" in caplog.text

def test_create_rating_score__expects__logs_warning_for_missing_ids(ds, caplog):
    caplog.set_level(logging.WARNING)
    rating = ds.create_rating_score("q-missing", "d-existing", 1)
    assert rating is not None
    assert rating.query_id == "q-missing"
    assert rating.doc_id == "d-existing"
    assert "query_not_found" in caplog.text

def test_persistence__expects__save_and_load_roundtrip(tmp_db_path, doc_a, query_q):
    ds1 = DataStore(path=tmp_db_path, ignore_saved_data=True)
    ds1.add_document(doc_a)
    query = ds1.add_query(query_q.text)
    ds1.create_rating_score(query.id, doc_a.id, 5)
    ds1.save()
    assert os.path.exists(tmp_db_path)

    ds2 = DataStore(path=tmp_db_path)  # load() is called in __init__
    assert len(ds2.get_documents()) == 1
    assert len(ds2.get_queries()) == 1
    assert len(ds2.get_ratings()) == 1
    assert ds2.get_document(doc_a.id).fields == doc_a.fields
    assert ds2.get_queries()[0].text == query_q.text
    assert ds2.get_ratings()[0].score == 5

def test_load_when_file_missing__expects__returns_empty_store(tmp_path):
    path = tmp_path / "no-such.json"
    ds = DataStore(path=path)  # should not raise
    assert ds.get_documents() == []
    assert ds.get_queries() == []
    assert ds.get_ratings() == []

def test_add_query__expects__returns_id_for_new_and_duplicate_queries(ds):
    query1 = Query(text="unique text")
    returned_query1 = ds.add_query(query1.text)
    assert isinstance(returned_query1, Query)
    assert returned_query1.text == query1.text
    assert len(ds.get_queries()) == 1

    query2_duplicate = Query(text="unique text")  # Same text, different object/id
    returned_query2 = ds.add_query(query2_duplicate.text)
    assert isinstance(returned_query2, Query)
    assert returned_query2.id == returned_query1.id  # Should return the same query as before

def test_load_with_broken_references__expects__skips_dangling_ratings_and_warns(tmp_db_path, doc_a, query_q, caplog):
    # Simulate a corrupt file with a rating pointing to a non-existent doc
    corrupt_data = {
        "docs": [],  # doc_a is missing
        "queries": [query_q.model_dump()],
        "ratings": [
            {"id": "r1", "query_id": query_q.id, "doc_id": doc_a.id, "score": 5}
        ]
    }
    tmp_db_path.write_text(json.dumps(corrupt_data))

    caplog.set_level(logging.WARNING)
    ds = DataStore(path=tmp_db_path)

    # The rating is skipped because the document is missing, and a warning is logged.
    assert len(ds.get_ratings()) == 0
    assert 'doc_not_found' in caplog.text
