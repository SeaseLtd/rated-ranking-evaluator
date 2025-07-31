import json
import pytest
from src.model.document import Document
from src.search_engine.data_store import DataStore


# -------------------- Helpers --------------------

def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def _mk_ds_with_sample_data(save_documents: bool) -> DataStore:
    ds = DataStore(save_documents=save_documents)
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

def test_add_and_get_document_EXPECTS_documents_stored_in_data_store():
    ds = DataStore()
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
    ds = DataStore()
    # Alta de queries
    qid1 = ds.add_query("technology", "doc1")
    assert ds.get_query(qid1).get_query() == "technology"

    qid2 = ds.add_query("airpods", "doc2")
    assert ds.get_query(qid2).get_query() == "airpods"

    # Misma query con nuevo doc_id -> reaprovecha el mismo query_id
    qid3 = ds.add_query("technology", "doc3")
    assert qid1 == qid3
    assert set(ds.get_query(qid3).get_doc_ids()) == {"doc1", "doc3"}


# -------------------- Persistence tests (save/load) --------------------

@pytest.mark.parametrize("save_documents, expects_documents_key", [(True, True), (False, False)])
def test_save_tmp_file_content_EXPECTS_json_file_is_created_with_or_without_documents(tmp_path, save_documents, expects_documents_key):
    ds = _mk_ds_with_sample_data(save_documents)
    path = tmp_path / "datastore.json"
    ds.save_tmp_file_content(path)

    assert path.exists()
    data = _read_json(path)
    assert isinstance(data, list) and len(data) == 2

    for entry in data:
        assert "query_id" in entry
        assert "query_text" in entry
        assert isinstance(entry.get("doc_ratings"), dict)
        if expects_documents_key:
            assert isinstance(entry.get("documents"), list)
        else:
            assert "documents" not in entry


def test_load_tmp_file_content_EXPECTS_datastore_state_is_restored(tmp_path):
    content = [{
        "query_id": "q1",
        "query_text": "ai",
        "doc_ratings": {"d1": 1, "d2": 0},
        "documents": [
            {"id": "d1", "fields": {"title": "AI", "text": "Deep learning"}},
            {"id": "d2", "fields": {"title": "LLMs", "text": "Transformers"}},
        ],
    }]
    path = tmp_path / "datastore.json"
    _write_json(path, content)

    ds = DataStore()
    ds.load_tmp_file_content(path, clear=True)

    assert ds.get_query("q1").get_query() == "ai"
    assert ds.get_rating_score("q1", "d1") == 1
    assert ds.get_rating_score("q1", "d2") == 0
    assert ds.get_document("d1").fields["title"] == "AI"
    assert ds.get_document("d2").fields["text"] == "Transformers"


def test_load_tmp_file_content_with_shared_document_EXPECTS_no_duplication(tmp_path):
    content = [
        {"query_id": "q1", "query_text": "q one", "doc_ratings": {"d1": 1},
         "documents": [{"id": "d1", "fields": {"title": "AI", "text": "X"}}]},
        {"query_id": "q2", "query_text": "q two", "doc_ratings": {"d1": 0},
         "documents": [{"id": "d1", "fields": {"title": "AI", "text": "X"}}]},
    ]
    path = tmp_path / "datastore.json"
    _write_json(path, content)

    ds = DataStore()
    ds.load_tmp_file_content(path, clear=True)

    assert ds.get_document("d1") is not None
    assert ds.get_rating_score("q1", "d1") == 1
    assert ds.get_rating_score("q2", "d1") == 0


def test_load_tmp_file_content_with_duplicate_query_text_EXPECTS_key_error(tmp_path):
    content = [
        {"query_id": "q1", "query_text": "same", "doc_ratings": {}, "documents": []},
        {"query_id": "q2", "query_text": "same", "doc_ratings": {}, "documents": []},
    ]
    path = tmp_path / "datastore.json"
    _write_json(path, content)

    ds = DataStore()
    with pytest.raises(KeyError):
        ds.load_tmp_file_content(path, clear=True)


def test_save_tmp_file_content_to_custom_path_EXPECTS_file_is_created(tmp_path):
    ds = DataStore(save_documents=False)
    qid = ds.add_query("q", None)
    ds.add_rating_score(qid, "dX", 1)  # aunque no exista el doc, ratings se guardan

    path = tmp_path / "subdir" / "custom.json"
    assert not path.exists()
    ds.save_tmp_file_content(path)  # no debe redirigir a TMP_FILE

    assert path.exists()
    data = _read_json(path)
    assert isinstance(data, list) and len(data) == 1
