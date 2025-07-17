from src.model.document import Document
from src.search_engine.data_store import DataStore

data_store = DataStore()


def test_add_and_get_document_expect_documents_stored_in_data_store():
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

    assert data_store.get_document("doc1") is doc1
    assert data_store.get_document("doc2") is doc2
    assert data_store.get_document("doc3") is doc3


def test_add_and_get_query_expect_query_stored_in_data_store_and_check_same_queries():
    query_id_1 = data_store.add_query("technology", "doc1")

    assert data_store.get_query(query_id_1).get_query() is "technology"

    query_id_2 = data_store.add_query("airpods", "doc2")
    assert data_store.get_query(query_id_2).get_query() is "airpods"

    query_id_3 = data_store.add_query("technology", "doc3")
    assert query_id_1 == query_id_3
    assert data_store.get_query(query_id_3).get_doc_ids() == ["doc1", "doc3"]


