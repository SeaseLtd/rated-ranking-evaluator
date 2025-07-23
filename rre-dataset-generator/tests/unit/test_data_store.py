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
def test_save_and_load_queries_and_ratings_roundtrip(tmp_path):

    # Step 1: build the intial instance
    ds1 = DataStore()

    # Step 2: add Documents
    doc1 = Document(id="d1", fields={"title": "AI", "text": "Deep learning"})
    doc2 = Document(id="d2", fields={"title": "LLMs", "text": "Transformers"})
    ds1.add_document(doc1.id, doc1)
    ds1.add_document(doc2.id, doc2)

    # Step 3: add queries and ratings
    qid1 = ds1.add_query("artificial intelligence", doc1.id)
    ds1.add_rating_score(qid1, doc1.id, 1)
    ds1.add_rating_score(qid1, doc2.id, 0)

    qid2 = ds1.add_query("transformer models", doc2.id)
    ds1.add_rating_score(qid2, doc2.id, 1)

    # Step 4: save into disk
    queries_path = tmp_path / "queries.json"
    triples_path = tmp_path / "triples.json"

    ds1.save_queries_and_docs(queries_path)
    ds1.save_rating_triples(triples_path)

    # Step 5: Verify saving
    assert queries_path.exists()
    assert triples_path.exists()
    assert json.loads(queries_path.read_text(encoding="utf-8"))  # assert not empty 
    assert json.loads(triples_path.read_text(encoding="utf-8"))  # assert not empty 

    # Step 6: load a new datastore - avoid caching artifacts
    ds2 = DataStore()
    ds2.load_queries_and_docs(queries_path)
    ds2.load_rating_triples(triples_path)

    # Step 7: verify integrity after loading
    assert ds2.get_query(qid1).get_query() == "artificial intelligence"
    assert set(ds2.get_query(qid1).get_doc_ids()) == {"d1", "d2"}
    assert ds2.get_rating_score(qid1, "d1") == 1
    assert ds2.get_rating_score(qid1, "d2") == 0

    assert ds2.get_query(qid2).get_query() == "transformer models"
    assert ds2.get_rating_score(qid2, "d2") == 1
