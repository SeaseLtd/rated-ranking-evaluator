import json
import pytest
from pathlib import Path
from typing import Any
from src.model.document import Document
from src.search_engine.data_store import DataStore


def test_add_and_get_document_expect_documents_stored_in_data_store():
    data_store = DataStore()  # ← nuevo store para aislamiento

def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, obj: Any):
    # direct read from the path - no need for open()
    """
    with open(path, "w") as f:
        f.write(json.dumps(obj))
    - Defaults to ASCII escaping (ugly for UTF-8),
    - No indentation
    - Encoding custom for plataform
    - More verbose
    """
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def mock_datastore_empty(save_documents_: bool = False) -> DataStore:
    ds = DataStore(save_documents=save_documents_)
    return ds

# NOTE: we can inject the mock as fixture. Eg:

# @pytest.fixture
# def mock_datastore():
#     return mock_datastore_with_sample_data(save_documents=True)
# and then
# def test_something(mock_datastore_with_sample_data):
# but in this case we avoid it to parametrize the tests with save_documents

def mock_datastore_with_sample_data(save_documents: bool = False) -> DataStore:
    ds = DataStore(save_documents=save_documents)
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
    
    # Mock with default sample data
    ds = mock_datastore_with_sample_data(save_documents)
    
    # Save sample data
    path = tmp_path / "datastore.json"
    ds.save_tmp_file_content(path)

    # The created file exists?
    assert path.exists()
    
    # The created file has the expected content?
    data = _read_json(path)
    assert isinstance(data, list) and len(data) == 2

    for entry in data:
        assert "query_id" in entry
        assert "query_text" in entry
        assert "doc_ids" in entry
        assert "doc_ratings" in entry
        assert "documents" in entry


def test_load_tmp_file_content_expect_data_restored_correctly(tmp_path):
    # Create known content
    content = [
        {
            "query_id": "q1",
            "query_text": "ai",
            "doc_ids": ["d1", "d2"],
            "doc_ratings": {"d1": 1, "d2": 0},
            "documents": [
                {"id": "d1", "fields": {"title": "AI", "text": "Deep learning"}},
                {"id": "d2", "fields": {"title": "LLMs", "text": "Transformers"}},
            ]
        }
    ]

    # Write file manually
    path = tmp_path / "datastore.json"
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")

    ds = mock_datastore_empty()
    ds.load_tmp_file_content(path, clear=True)

    # Assertions
    assert ds.get_query("q1").get_query() == "ai"
    assert ds.get_rating_score("q1", "d1") == 1
    assert ds.get_rating_score("q1", "d2") == 0


def test_load_tmp_file_content_with_shared_document_EXPECTS_no_duplication(tmp_path):
    content = [
        {"query_id": "q1", "query_text": "q one", "doc_ratings": {"d1": 1},
         "documents": [{"id": "d1", "fields": {"title": "AI", "text": "X"}}]},
        {"query_id": "q2", "query_text": "q two", "doc_ratings": {"d1": 0},
         "documents": [{"id": "d1", "fields": {"title": "AI", "text": "X"}}]},
    ]
    path = tmp_path / "datastore.json"
    _write_json(path, content)

    ds = mock_datastore_empty()
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

    ds = mock_datastore_empty()
    with pytest.raises(KeyError):
        ds.load_tmp_file_content(path, clear=True)


def test_save_tmp_file_content_to_custom_path_EXPECTS_file_is_created(tmp_path):
    ds = DataStore()

    qid = ds.add_query("q", None)
    ds.add_rating_score(qid, "dX", 1)  # aunque no exista el doc, ratings se guardan

    path = tmp_path / "subdir" / "custom.json"
    assert not path.exists()
    ds.save_tmp_file_content(path)  # no debe redirigir a TMP_FILE

    assert path.exists()
    data = _read_json(path)
    assert isinstance(data, list) and len(data) == 1

