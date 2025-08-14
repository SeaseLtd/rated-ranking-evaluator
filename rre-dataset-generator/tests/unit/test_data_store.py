import pytest
from pathlib import Path
import os
import logging
from pydantic import ValidationError

from src.data_store import DataStore
from src.model import Document, Query


# --- pytests integrated fixtures ---
## caplog for logging messages when calling functions
## tmp_path: pytest fixture for temporary directory


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


# --- helper: normalize return value of create_rating_score / add_rating_score ---
def rating_id_of(ret):
    return ret if isinstance(ret, str) else ret.id


# --- tests ---
def test_add_and_get_doc__expects__datastore_returns_the_same_document(ds, docA):
    ds.add_doc(docA)
    assert ds.has_doc(docA.id)
    assert ds.get_doc(docA.id) is docA
    assert len(ds.get_docs()) == 1

def test_add_doc_duplicate__expects__logs_debug_and_keeps_original(ds, docA, caplog):
    ds.add_doc(docA)
    caplog.set_level(logging.DEBUG)
    ds.add_doc(docA)
    assert "[add_doc] exists" in caplog.text
    assert len(ds.get_docs()) == 1  # does not overwrite

def test_add_and_get_query__expects__datastore_returns_the_same_query(ds, queryQ):
    ds.add_query(queryQ)
    assert ds.has_query(queryQ.id)
    assert ds.get_query(queryQ.id) is queryQ
    assert len(ds.get_queries()) == 1

def test_add_doc_to_query__expects__association_successful(ds, docA, queryQ):
    ds.add_doc(docA)
    ds.add_query(queryQ)
    ds.add_doc_to_query(queryQ.id, docA.id)
    assert docA.id in ds.get_doc_ids_for_query(queryQ.id)

def test_add_doc_to_query__expects__logs_debug_for_unknown_ids(ds, caplog):
    caplog.set_level(logging.DEBUG)
    ds.add_doc_to_query("missing-q", "missing-d")
    assert "query_not_found" in caplog.text

def test_create_rating_score__expects__creates_rating_and_indexes(ds, docA, queryQ):
    ds.add_doc(docA)
    ds.add_query(queryQ)
    ret = ds.create_rating_score(queryQ.id, docA.id, 2)
    rid = rating_id_of(ret)
    assert ds.has_rating(rid)
    assert ds.get_rating_score(queryQ.id, docA.id) == 2
    # principal index (q,d) -> rid
    assert ds.rating_index[(queryQ.id, docA.id)] == rid
    
    # query -> ratings (deterministic order by id)
    rating_ids = [r.id for r in ds.get_ratings_for_query(queryQ.id)]
    assert rid in rating_ids
    # query -> docs
    assert docA.id in ds.get_doc_ids_for_query(queryQ.id)

def test_create_rating_score__expects__second_call_does_not_update_existing(ds, docA, queryQ, caplog):
    ds.add_doc(docA); ds.add_query(queryQ)
    rid1 = rating_id_of(ds.create_rating_score(queryQ.id, docA.id, 1))
    caplog.set_level(logging.DEBUG)
    rid2 = rating_id_of(ds.create_rating_score(queryQ.id, docA.id, 4))  # insert-only: does not update
    assert rid1 == rid2
    assert ds.get_rating_score(queryQ.id, docA.id) == 1  # keeps the first
    assert "rating_for_pair_exists" in caplog.text

def test_create_rating_score__expects__negative_value_is_none_and_logs_error(ds, docA, queryQ, caplog):
    ds.add_doc(docA); ds.add_query(queryQ)
    caplog.set_level(logging.DEBUG)
    ret = ds.create_rating_score(queryQ.id, docA.id, -1)
    assert ret is None
    assert "validation_failed" in caplog.text

def test_get_rating_score__expects__logs_debug_for_missing_query_or_doc(ds, caplog):
    caplog.set_level(logging.DEBUG)
    assert ds.get_rating_score("q-missing", "d-missing") is None
    assert "query_not_found" in caplog.text

def test_persistence__expects__save_and_load_roundtrip(tmp_db_path, docA, queryQ):
    ds1 = DataStore(path=tmp_db_path, ignore_saved_data=True)
    ds1.add_doc(docA)
    ds1.add_query(queryQ)
    rid = rating_id_of(ds1.create_rating_score(queryQ.id, docA.id, 5))
    ds1.save()
    assert os.path.exists(tmp_db_path)

    ds2 = DataStore(path=tmp_db_path)  # load() is called in __init__
    assert ds2.has_doc(docA.id)
    assert ds2.has_query(queryQ.id)
    assert ds2.has_rating(rid)
    assert ds2.get_rating_score(queryQ.id, docA.id) == 5
    # ratings index reconstructed
    assert ds2.rating_index[(queryQ.id, docA.id)] == rid

def test_load_when_file_missing__expects__returns_empty_store(tmp_path):
    path = tmp_path / "no-such.json"
    ds = DataStore(path=path)  # should not raise
    assert ds.get_docs() == []
    assert ds.get_queries() == []
    assert ds.get_ratings() == []
