import json
from src.model.document import Document
from src.search_engine.data_store import DataStore


def test_add_and_get_document_expect_documents_stored_in_data_store():
    # CHANGED - now the DataStore get's refreshed for each fn and it's not shared
    ## NOTE: this can be generalized with pytest fixtures, but since there only 3 test fns, we can keep it simple for now
    data_store = DataStore()  
    

    doc1 = Document(
        id="doc1",
        fields={
            "title": "Gadgets",
            "description": "Cutting edge technologies are on demand."
        }
    )

    doc2 = Document(
        id="doc2",
        fields={
            "title": "Airpods",
            "description": "The quality of airpods from Apple is getting worse."
        }
    )

    doc3 = Document(
        id="doc3",
        fields={
            "title": "MacBook Pro",
            "description": "The price of Apple laptops has been skyrocketed."
        }
    )

    data_store.add_document(doc1.id, doc1)
    data_store.add_document(doc2.id, doc2)
    data_store.add_document(doc3.id, doc3)

    assert data_store.get_document("doc1") == doc1
    assert data_store.get_document("doc2") == doc2
    assert data_store.get_document("doc3") == doc3


def test_add_and_get_query_expect_query_stored_in_data_store_and_check_same_queries():
    data_store = DataStore()

    # Add first query
    query_id_1 = data_store.add_query("technology", "doc1")
    assert data_store.get_query(query_id_1)._query == "technology"

    # Add second query
    query_id_2 = data_store.add_query("airpods", "doc2")
    assert data_store.get_query(query_id_2)._query == "airpods"

    # Add same query with new doc_id
    query_id_3 = data_store.add_query("technology", "doc3")

    assert query_id_1 == query_id_3
    assert set(data_store.get_query(query_id_3).get_doc_ids()) == {"doc1", "doc3"}


# tmp_path: pytest fixture with a temporal dir
def test_save_tmp_file_content_expect_json_created(tmp_path):
    ds = DataStore()

    # Add Documents
    doc1 = Document(id="d1", fields={"title": "AI", "text": "Deep learning"})
    doc2 = Document(id="d2", fields={"title": "LLMs", "text": "Transformers"})
    ds.add_document(doc1.id, doc1)
    ds.add_document(doc2.id, doc2)

    # Add Queries and Ratings
    qid1 = ds.add_query("artificial intelligence", doc1.id)
    ds.add_rating_score(qid1, "d1", 1)
    ds.add_rating_score(qid1, "d2", 0)

    qid2 = ds.add_query("transformer models", doc2.id)
    ds.add_rating_score(qid2, "d2", 1)

    # Save to disk
    path = tmp_path / "datastore.json"
    ds.save_tmp_file_content(path)

    # Assertions
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 2
    for entry in data:
        assert "query_id" in entry
        assert "query_text" in entry
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

    # Load from disk
    ds = DataStore()
    ds.load_tmp_file_content(path)

    # Assertions
    assert ds.get_query("q1").get_query() == "ai"
    assert ds.get_rating_score("q1", "d1") == 1
    assert ds.get_rating_score("q1", "d2") == 0

    doc1 = ds.get_document("d1")
    doc2 = ds.get_document("d2")
    assert doc1.fields["title"] == "AI"
    assert doc2.fields["text"] == "Transformers"