import json
from pathlib import Path

import pytest
from pathlib import Path
from typing import Any, Dict

import importlib
import json

import json
import pytest

from src.model.document import Document
from src.search_engine.data_store import DataStore
from src.search_engine import data_store


@pytest.fixture
def empty_store():
    return DataStore(ignore_saved_data=True)


# -------------------- Helpers --------------------

def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, obj: Any):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def _mk_ds_with_sample_data(save_documents: bool) -> DataStore:
    ds = DataStore(save_documents=save_documents, ignore_saved_data=True)
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

def test_add_and_get_document__expects__documents_stored_in_data_store():
    ds = DataStore(ignore_saved_data=True)
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


def test_add_and_get_query__expects__query_stored_in_data_store_and_check_same_queries():
    ds = DataStore(ignore_saved_data=True)
    # Alta de queries
    qid1 = ds.add_query("technology", "doc1")
    assert ds.get_query(qid1).get_query_text() == "technology"

    qid2 = ds.add_query("airpods", "doc2")
    assert ds.get_query(qid2).get_query_text() == "airpods"

    # Misma query con nuevo doc_id -> reaprovecha el mismo query_id
    qid3 = ds.add_query("technology", "doc3")
    assert qid1 == qid3
    assert set(ds.get_query(qid3).get_doc_ids()) == {"doc1", "doc3"}


def test_add_query_rating_and_has_rating_flag(empty_store):
    qid = empty_store.add_query("test", doc_id="d1")
    # centinela: sin rating aún
    assert empty_store.has_rating_score(qid, "d1") is False
    empty_store.add_rating_score(qid, "d1", 1)
    assert empty_store.get_rating_score(qid, "d1") == 1
    assert empty_store.has_rating_score(qid, "d1") is True

@pytest.mark.parametrize("save_documents, expects_documents_key", [(True, True), (False, False)])
def test_save_tmp_file_content__expect__json_file_is_created_with_or_without_documents(tmp_path: Path, save_documents: bool, expects_documents_key: bool):
    ds = _mk_ds_with_sample_data(save_documents)
    # path = tmp_path / "datastore.json"
    ds.save_tmp_file_content()

    newDataStore = DataStore(ignore_saved_data=False)
    for context_1, context_2 in zip(ds.get_queries(), newDataStore.get_queries()):
        assert context_1.get_query() == context_2.get_query()
        assert context_1.get_query_id() == context_2.get_query_id()
        assert set(context_1.get_doc_ids()) == set(context_2.get_doc_ids())

    # Carga automática en __init__ porque ignore_saved_data=False
    ds2 = DataStore(ignore_saved_data=False)
    assert ds2.get_query(qid).get_query_text() == "test"
    assert ds2.get_rating_score(qid, "d1") == 1
    assert ds2.get_document("d1") == doc

# def test_load_tmp_file_content__expect__datastore_state_is_restored(tmp_path):
#     content = [{
#         "query_id": "q1",
#         "query_text": "ai",
#         "doc_ratings": {"d1": 1, "d2": 0},
#         "documents": [
#             {"id": "d1", "fields": {"title": "AI", "text": "Deep learning"}},
#             {"id": "d2", "fields": {"title": "LLMs", "text": "Transformers"}},
#         ],
#     }]
#     path = tmp_path / "datastore.json"
#     _write_json(path, content)
#
#     ds = DataStore()
#     ds.load_tmp_file_content(path, clear=True)
#
#     assert ds.get_query("q1").get_query() == "ai"
#     assert ds.get_rating_score("q1", "d1") == 1
#     assert ds.get_rating_score("q1", "d2") == 0
#     assert ds.get_document("d1").fields["title"] == "AI"
#     assert ds.get_document("d2").fields["text"] == "Transformers"


# def test_load_tmp_file_content_with_shared_document__expects__no_duplication(tmp_path):
#     content = [
#         {"query_id": "q1", "query_text": "q one", "doc_ratings": {"d1": 1},
#          "documents": [{"id": "d1", "fields": {"title": "AI", "text": "X"}}]},
#         {"query_id": "q2", "query_text": "q two", "doc_ratings": {"d1": 0},
#          "documents": [{"id": "d1", "fields": {"title": "AI", "text": "X"}}]},
#     ]
#     path = tmp_path / "datastore.json"
#     _write_json(path, content)
#
#     ds = DataStore()
#     ds.load_tmp_file_content(path, clear=True)
#
#     assert ds.get_document("d1") is not None
#     assert ds.get_rating_score("q1", "d1") == 1
#     assert ds.get_rating_score("q2", "d1") == 0

#
# def test_save_tmp_file_content_to_custom_path__expects__file_is_created(tmp_path):
#     ds = DataStore()
#     qid = ds.add_query("q", None)
#     ds.add_rating_score(qid, "dX", 1)
#
#     path = tmp_path / "subdir" / "custom.json"
#     assert not path.exists()
#     ds.save_tmp_file_content(path)
#
#     assert path.exists()
#     data = _read_json(path)
#     assert isinstance(data, list) and len(data) == 1
#

