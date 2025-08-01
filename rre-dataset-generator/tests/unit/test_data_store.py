from pathlib import Path
from typing import Any, Dict

import importlib
import json

import pytest

from src.model.document import Document
from src.search_engine import data_store as ds_module
from src.search_engine.data_store import DataStore


def test_add_and_get_document_expect_documents_stored_in_data_store():
    data_store = DataStore()  # ← nuevo store para aislamiento

def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, obj: Any):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def mock_datastore_empty(ignore_saved_data: bool = True) -> DataStore:
    """Return a clean DataStore instance."""
    return DataStore(ignore_saved_data=ignore_saved_data)

def mock_datastore_with_sample_data(ignore_saved_data: bool = True) -> DataStore:
    """Return a DataStore pre-populated with two documents, two queries and ratings."""
    ds = DataStore(ignore_saved_data=ignore_saved_data)
    d1 = Document(id="d1", fields={"title": "AI", "text": "Deep learning"})
    d2 = Document(id="d2", fields={"title": "LLMs", "text": "Transformers"})
    ds.add_document(d1.id, d1)
    ds.add_document(d2.id, d2)
    qid1 = ds.add_query("artificial intelligence", d1.id)
    ds.add_rating_score(qid1, "d1", 1)
    ds.add_rating_score(qid1, "d2", 0)

    qid2 = ds.add_query("transformer models", doc2.id)
    ds.add_rating_score(qid2, "d2", 1)


# -------------------- Unit tests (in-memory) --------------------

def test_add_and_get_document_EXPECTS_documents_stored_in_data_store():
    ds = mock_datastore_empty()
    docs = [
        Document(id="doc1", fields={"title": "Gadgets", "description": "Cutting edge technologies are on demand."}),
        Document(id="doc2", fields={"title": "Airpods", "description": "The quality of airpods from Apple is getting worse."}),
        Document(id="doc3", fields={"title": "MacBook Pro", "description": "The price of Apple laptops has been skyrocketed."}),
    ]
    for d in docs:
        ds.add_document(d.id, d)

    assert ds.get_document("doc1") == docs[0]
    assert ds.get_document("doc2") == docs[1]
    assert ds.get_document("doc3") == docs[2]


def test_add_and_get_query_EXPECTS_query_stored_in_data_store_and_check_same_queries():
    ds = mock_datastore_empty()
    # Add queries
    qid1 = ds.add_query("technology", "doc1")
    assert ds.get_query(qid1).get_query_text() == "technology"

    qid2 = ds.add_query("airpods", "doc2")
    assert ds.get_query(qid2).get_query_text() == "airpods"

    # Misma query con nuevo doc_id -> reaprovecha el mismo query_id
    qid3 = ds.add_query("technology", "doc3")
    assert qid1 == qid3
    assert set(ds.get_query(qid3).get_doc_ids()) == {"doc1", "doc3"}


# -------------------- Persistence tests (save/load) --------------------

def _patch_tmp(monkeypatch, tmp_path: Path) -> Path:
    """Override `TMP_FILE` constant in the datastore module so we can control I/O path."""
    path = tmp_path / "datastore.json"
    monkeypatch.setattr(ds_module, "TMP_FILE", str(path), raising=False)
    # ensure fresh import pick-up (for defensive re-imports elsewhere)
    importlib.reload(ds_module)
    return path

def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    """Persist datastore to disk and load it back verifying full round-trip."""

    # ---- Save phase ------------------------------------------------------
    save_path = _patch_tmp(monkeypatch, tmp_path)
    ds1 = mock_datastore_with_sample_data()
    ds1.save_tmp_file_content()

    assert save_path.exists()

    # ---- Load phase ------------------------------------------------------
    ds2 = DataStore(ignore_saved_data=False)

    # The new instance should have identical observable state
    assert ds2.has_document("d1") and ds2.get_document("d1") == ds1.get_document("d1")
    assert ds2.get_query_text(ds2._query_text_to_query_id["artificial intelligence"]) == "artificial intelligence"
    assert ds2.get_rating_score(ds2._query_text_to_query_id["artificial intelligence"], "d1") == 1

    # Verify on-disk JSON structure
    stored: Dict[str, Any] = _read_json(save_path)
    assert set(stored.keys()) == {"queries", "documents"}

def test_load_tmp_file_content_EXPECTS_datastore_state_is_restored(tmp_path):
    content = {
        "queries": [
            {"query_id": "q1", "query_text": "ai", "doc_ratings": {"d1": 1, "d2": 0}},
            {"query_id": "q2", "query_text": "transformer models", "doc_ratings": {"d2": 1}},
        ],
        "documents": [
            {"id": "d1", "fields": {"title": "AI", "text": "Deep learning"}},
            {"id": "d2", "fields": {"title": "LLMs", "text": "Transformers"}},
        ],
    }
    path = tmp_path / "datastore.json"
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")

    ds_module.TMP_FILE = str(path)
    ds = mock_datastore_empty()
    ds.load_tmp_file_content()

    assert ds.get_query_text(ds._query_text_to_query_id["ai"]) == "ai"
    assert ds.get_rating_score(ds._query_text_to_query_id["ai"], "d1") == 1
    assert ds.get_rating_score(ds._query_text_to_query_id["ai"], "d2") == 0
    assert ds.get_document("d1").fields["title"] == "AI"
    assert ds.get_document("d2").fields["text"] == "Transformers"

def test_load_tmp_file_content_with_shared_document_EXPECTS_no_duplication(tmp_path):
    content = {
        "queries": [
            {"query_id": "q1", "query_text": "q one", "doc_ratings": {"d1": 1}},
            {"query_id": "q2", "query_text": "q two", "doc_ratings": {"d1": 0}},
        ],
        "documents": [
            {"id": "d1", "fields": {"title": "AI", "text": "X"}},
        ],
    }
    path = tmp_path / "datastore.json"
    _write_json(path, content)

    ds_module.TMP_FILE = str(path)
    ds = mock_datastore_empty()
    ds.load_tmp_file_content()

    assert ds.get_document("d1") is not None
    assert ds.get_rating_score(ds._query_text_to_query_id["q one"], "d1") == 1
    assert ds.get_rating_score(ds._query_text_to_query_id["q two"], "d1") == 0

def test_load_tmp_file_content_with_duplicate_query_text_EXPECTS_key_error(tmp_path):
    content = {
        "queries": [
            {"query_id": "q1", "query_text": "same", "doc_ratings": {}},
            {"query_id": "q2", "query_text": "same", "doc_ratings": {}},
        ],
        "documents": [],
    }
    path = tmp_path / "datastore.json"
    _write_json(path, content)

    ds_module.TMP_FILE = str(path)
    ds = mock_datastore_empty()
    with pytest.raises(KeyError):
        ds.load_tmp_file_content()

def test_save_tmp_file_content_to_custom_path_EXPECTS_file_is_created(tmp_path):
    ds = DataStore()

    qid = ds.add_query("q", None)
    ds.add_rating_score(qid, "dX", 1)  # aunque no exista el doc, ratings se guardan

    path = tmp_path / "subdir" / "custom.json"
    assert not path.exists()
    ds_module.TMP_FILE = str(path)
    ds.save_tmp_file_content()  # should respect patched TMP_FILE

    assert path.exists()
    data = _read_json(path)
    assert isinstance(data, dict)
    assert set(data.keys()) == {"queries", "documents"}
