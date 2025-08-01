# tests/test_datastore.py

import pytest
import json
from src.model.document import Document
from src.search_engine.data_store import DataStore
from src.search_engine import data_store

@pytest.fixture
def empty_store():
    return DataStore(ignore_saved_data=True)


@pytest.fixture
def sample_store():
    ds = DataStore(ignore_saved_data=True)
    d1 = Document(id="d1", fields={"title": "AI"})
    d2 = Document(id="d2", fields={"title": "LLMs"})
    ds.add_document("d1", d1)
    ds.add_document("d2", d2)
    q1 = ds.add_query("AI", doc_id="d1")
    q2 = ds.add_query("LLMs", doc_id="d2")
    ds.add_rating_score(q1, "d1", 1)
    ds.add_rating_score(q2, "d2", 1)
    return ds


def test_add_and_get_document(empty_store):
    doc = Document(id="dX", fields={"title": "New"})
    empty_store.add_document("dX", doc)
    assert empty_store.get_document("dX") == doc


def test_add_duplicate_document_raises(empty_store):
    doc = Document(id="d1", fields={"text": "some text"})
    empty_store.add_document("d1", doc)
    with pytest.raises(KeyError):
        empty_store.add_document("d1", doc)


def test_add_query_and_rating(empty_store):
    qid = empty_store.add_query("test", doc_id="d1")
    empty_store.add_rating_score(qid, "d1", 1)
    assert empty_store.get_rating_score(qid, "d1") == 1


def test_get_nonexistent_rating_raises(empty_store):
    with pytest.raises(KeyError):
        empty_store.get_rating_score("invalid_qid", "d1")


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "datastore.json"
    # Override class global variable
    data_store.TMP_FILE = str(path)

    ds1 = DataStore(ignore_saved_data=True)
    doc = Document(id="d1", fields={"text": "some text"})
    ds1.add_document("d1", doc)
    qid = ds1.add_query("test", doc_id="d1")
    ds1.add_rating_score(qid, "d1", 1)
    ds1.save_tmp_file_content()

    ds2 = DataStore(ignore_saved_data=False)
    assert ds2.get_query(qid).get_query_text() == "test"
    assert ds2.get_rating_score(qid, "d1") == 1
    assert ds2.get_document("d1") == doc


def test_load_with_duplicate_query_text(tmp_path):
    content = {
        "queries": {
            "q1": {"query_id": "q1", "query_text": "dup", "doc_ratings": {}},
            "q2": {"query_id": "q2", "query_text": "dup", "doc_ratings": {}}
        },
        "documents": {}
    }
    path = tmp_path / "ds.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    # Override class global variable
    data_store.TMP_FILE = str(path)

    ds = DataStore(ignore_saved_data=True)
    with pytest.raises(KeyError):
        ds.load_tmp_file_content()
