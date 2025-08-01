import pytest
from pathlib import Path

import os
from pydantic import ValidationError

from src.data_store import DataStore
from src.model import Document, Query, Rating

import logging
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



def test_add_and_get_doc__expects__datastore_returns_the_same_document(ds, docA):
    ds.add_doc(docA)
    assert ds.has_doc(docA.id)
    assert ds.get_doc(docA.id) is docA
    assert len(ds.get_docs()) == 1

def test_add_doc_duplicate__expects__logs_error_and_keeps_original(ds, docA, caplog):
    ds.add_doc(docA)
    caplog.set_level(logging.ERROR)
    ds.add_doc(docA)
    assert "already exists" in caplog.text
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
    assert docA.id in ds.get_query(queryQ.id).doc_ids

def test_add_doc_to_query__expects__logs_error_for_unknown_ids(ds, caplog):
    caplog.set_level(logging.ERROR)
    ds.add_doc_to_query("missing-q", "missing-d")
    assert "Query missing-q not found" in caplog.text

def test_add_rating_score__expects__creates_rating_and_indexes(ds, docA, queryQ):
    ds.add_doc(docA)
    ds.add_query(queryQ)
    rid = ds.add_rating_score(queryQ.id, docA.id, 2)
    assert ds.has_rating(rid)
    assert ds.get_rating_score(queryQ.id, docA.id) == 2
    assert ds.rating_index[(queryQ.id, docA.id)] == rid
    assert rid in ds.get_query(queryQ.id).related_ratings_ids
    assert docA.id in ds.get_query(queryQ.id).doc_ids  # ensures doc<->query relationship

def test_add_rating_score__expects__updates_existing_rating(ds, docA, queryQ):
    ds.add_doc(docA); ds.add_query(queryQ)
    rid1 = ds.add_rating_score(queryQ.id, docA.id, 1)
    rid2 = ds.add_rating_score(queryQ.id, docA.id, 4)
    assert rid1 == rid2
    assert ds.get_rating_score(queryQ.id, docA.id) == 4

def test_add_rating_score__expects__negative_value_raises_validation_error(ds, docA, queryQ):
    ds.add_doc(docA); ds.add_query(queryQ)
    with pytest.raises(ValidationError):
        ds.add_rating_score(queryQ.id, docA.id, -1)

def test_get_rating_score__expects__logs_error_for_missing_query_or_doc(ds, caplog):
    caplog.set_level(logging.ERROR)
    assert ds.get_rating_score("q-missing", "d-missing") is None
    assert "Query q-missing not found" in caplog.text

def test_persistence__expects__save_and_load_roundtrip(tmp_db_path, docA, queryQ):
    ds1 = DataStore(path=tmp_db_path, ignore_saved_data=True)
    ds1.add_doc(docA)
    ds1.add_query(queryQ)
    rid = ds1.add_rating_score(queryQ.id, docA.id, 5)
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
