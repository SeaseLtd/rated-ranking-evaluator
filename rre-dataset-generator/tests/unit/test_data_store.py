import json
from pathlib import Path
from typing import Any

import pytest

from src.model.document import Document
from src.search_engine.data_store import DataStore, TMP_FILE


@pytest.fixture
def empty_store() -> DataStore:
    """Fixture for an empty DataStore that ignores any saved data."""
    return DataStore(ignore_saved_data=True)



def mock_datastore_with_sample_data() -> DataStore:
    """Helper to create a DataStore instance with sample data."""
    ds = DataStore(ignore_saved_data=True)
    d1 = Document(id="d1", fields={"title": "AI", "text": "Deep learning"})
    d2 = Document(id="d2", fields={"title": "LLMs", "text": "Transformers"})
    ds.add_document(d1.id, d1)
    ds.add_document(d2.id, d2)
    qid1 = ds.add_query("artificial intelligence", d1.id)
    ds.add_rating_score(qid1, "d1", 1)
    ds.add_rating_score(qid1, "d2", 0)
    qid2 = ds.add_query("transformer models", d2.id)
    ds.add_rating_score(qid2, "d2", 1)
    return ds


# -------------------- Unit tests (in-memory) --------------------

def test_add_and_get_document__expects__documents_stored_in_data_store(empty_store: DataStore):
    docs = [
        Document(id="doc1", fields={"title": "Gadgets", "description": "Cutting edge technologies are on demand."}),
        Document(id="doc2", fields={"title": "Airpods", "description": "The quality of airpods from Apple is getting worse."}),
        Document(id="doc3", fields={"title": "MacBook Pro", "description": "The price of Apple laptops has been skyrocketed."}),
    ]
    for d in docs:
        empty_store.add_document(d.id, d)

    assert empty_store.get_document("doc1") == docs[0]
    assert empty_store.get_document("doc2") == docs[1]
    assert empty_store.get_document("doc3") == docs[2]


def test_add_and_get_query__expects__query_stored_and_reused(empty_store: DataStore):
    # Add new queries
    qid1 = empty_store.add_query("technology", "doc1")
    assert empty_store.get_query(qid1).get_query_text() == "technology"

    qid2 = empty_store.add_query("airpods", "doc2")
    assert empty_store.get_query(qid2).get_query_text() == "airpods"

    # Same query with a new doc_id -> should reuse the same query_id
    qid3 = empty_store.add_query("technology", "doc3")
    assert qid1 == qid3
    assert set(empty_store.get_query(qid3).get_doc_ids()) == {"doc1", "doc3"}


def test_datastore_add_query__expects__rating_can_be_added_and_checked(empty_store: DataStore):
    qid = empty_store.add_query("test", doc_id="d1")
    # sentinel: without rating yet
    assert empty_store.has_rating_score(qid, "d1") is False
    empty_store.add_rating_score(qid, "d1", 1)
    assert empty_store.get_rating_score(qid, "d1") == 1
    assert empty_store.has_rating_score(qid, "d1") is True


def test_save_and_load_tmp_file__expects__state_is_persisted_and_restored(tmp_path):
    """Tests that data store content is correctly saved and loaded from the default file."""
    # 1. Create a datastore, add data, and save it
    ds1 = mock_datastore_with_sample_data()
    ds1.save_tmp_file_content()

    # 2. Create a new datastore, which should auto-load the file
    ds2 = DataStore(ignore_saved_data=False)

    # 3. Verify that the loaded data is correct
    assert len(ds1.get_queries()) == len(ds2.get_queries())
    assert len(ds1.get_documents()) == len(ds2.get_documents())

    # Check a specific query and its ratings
    qid = ds1._query_text_to_query_id["artificial intelligence"]
    loaded_q = ds2.get_query(qid)
    assert loaded_q.get_query_text() == "artificial intelligence"
    assert loaded_q.get_rating_score("d1") == 1
    assert loaded_q.get_rating_score("d2") == 0

    # Check that documents were loaded correctly
    doc = ds2.get_document("d1")
    assert doc is not None
    assert doc.fields["title"] == "AI"


# Ensure the temporary file is cleaned up after tests
@pytest.fixture(autouse=True)
def cleanup_tmp_file():
    """Clean up the default tmp file before and after each test."""
    tmp_file = Path(TMP_FILE)
    if tmp_file.exists():
        tmp_file.unlink()
    yield
    if tmp_file.exists():
        tmp_file.unlink()
