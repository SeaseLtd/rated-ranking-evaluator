import pytest
from typing import Any
from src.search_engine.data_store import DataStore
from src.schemas import Document, Query, Score


@pytest.fixture
def ds() -> DataStore:
    """Returns a fresh DataStore instance for each test."""
    return DataStore()


@pytest.fixture
def doc1() -> Document:
    """Returns a sample document."""
    return Document(id="doc-1", fields={"title": "Test Document 1"})


@pytest.fixture
def doc2() -> Document:
    """Returns another sample document."""
    return Document(id="doc-2", fields={"title": "Test Document 2"})


def test_add_and_get_document(ds: DataStore, doc1: Document):
    ds.add_document(doc1.id, doc1)
    retrieved_doc = ds.get_document(doc1.id)
    assert retrieved_doc == doc1


def test_get_nonexistent_document_raises_keyerror(ds: DataStore):
    with pytest.raises(KeyError):
        ds.get_document("nonexistent-doc")


def test_add_and_get_query(ds: DataStore, doc1: Document):
    ds.add_document(doc1.id, doc1)
    query_id = ds.add_query(query_text="test query", doc_id=doc1.id)
    retrieved_query = ds.get_query(query_id)
    assert retrieved_query.id == query_id
    assert retrieved_query.text == "test query"
    assert len(retrieved_query.scores) == 1
    assert doc1.id in retrieved_query.scores


def test_get_all_queries(ds, doc1):
    # First add the document
    ds.add_document(doc1.id, doc1)
    # Then create queries that reference it
    q1_id = ds.add_query(query_text="query 1", doc_id=doc1.id)
    q2_id = ds.add_query(query_text="query 2", doc_id=doc1.id)
    # Verify we get both queries back
    queries = ds.get_queries()
    assert len(queries) == 2
    assert {q.id for q in queries} == {q1_id, q2_id}


def test_get_queries_empty(ds):
    assert ds.get_queries() == []


def test_add_and_get_score(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query_id = ds.add_query(query_text="test query", doc_id=doc1.id)
    assert ds.get_score(query_id, doc1.id) == -1

    # Add a new score
    ds.add_score(query_id, doc1.id, 5)
    assert ds.get_score(query_id, doc1.id) == 5


def test_update_score(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query_id = ds.add_query(query_text="test query", doc_id=doc1.id)
    ds.add_score(query_id, doc1.id, 5)
    ds.add_score(query_id, doc1.id, 10)
    assert ds.get_score(query_id, doc1.id) == 10


def test_add_score_for__doc_to_existing_query(ds, doc1, doc2):
    ds.add_document(doc1.id, doc1)
    ds.add_document(doc2.id, doc2)
    query_id = ds.add_query(query_text="test query", doc_id=doc1.id)
    ds.add_score(query_id, doc2.id, 7)
    assert ds.get_score(query_id, doc1.id) == -1  # Initial score
    assert ds.get_score(query_id, doc2.id) == 7


def test_has_score(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query_id = ds.add_query(query_text="test query", doc_id=doc1.id)
    assert ds.has_score(query_id, doc1.id) is False

    # After scoring, should be True
    ds.add_score(query_id, doc1.id, 5)
    assert ds.has_score(query_id, doc1.id) is True


def test_get_score_for_nonexistent_doc_raises_keyerror(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query_id = ds.add_query(query_text="test query", doc_id=doc1.id)
    with pytest.raises(KeyError, match="Document 'nonexistent-doc' not found in DataStore"):
        ds.get_score(query_id, "nonexistent-doc")


def test_add_score_for_nonexistent_query_raises_keyerror(ds, doc1):
    ds.add_document(doc1.id, doc1)
    with pytest.raises(KeyError, match="Query 'nonexistent-query' not found in DataStore"):
        ds.add_score("nonexistent-query", doc1.id, 5)


def test_add_score_for_nonexistent_document_raises_keyerror(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query_id = ds.add_query(query_text="test query", doc_id=doc1.id)
    with pytest.raises(KeyError, match="Document 'nonexistent-doc' not found in DataStore"):
        ds.add_score(query_id, "nonexistent-doc", 5)
