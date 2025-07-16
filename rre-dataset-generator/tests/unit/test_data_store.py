import pytest
from typing import Any
from src.search_engine.data_store import DataStore
from src.model import Document, Query

@pytest.fixture
def ds():
    """Returns a fresh DataStore instance for each test."""
    return DataStore()

@pytest.fixture
def doc1():
    """Returns a sample Document."""
    return Document(id="doc-1", fields={"title": "Test Document 1"})

@pytest.fixture
def doc2():
    """Returns another sample Document."""
    return Document(id="doc-2", fields={"title": "Test Document 2"})

def test_add_and_get_document(ds, doc1):
    ds.add_document(doc1.id, doc1)
    retrieved_doc = ds.get_document(doc1.id)
    assert retrieved_doc == doc1

def test_get_nonexistent_document_raises_keyerror(ds):
    with pytest.raises(KeyError, match="'nonexistent-doc' not found in DataStore"):
        ds.get_document("nonexistent-doc")

def test_add_and_get_query(ds, doc1):
    query = ds.add_query(query_text="test query", doc_id=doc1.id)
    assert isinstance(query, Query)
    assert query.text == "test query"
    assert len(query.scores) == 1
    assert query.scores[0].doc_id == doc1.id

    retrieved_query = ds.get_query(query.id)
    assert retrieved_query == query

def test_get_all_queries(ds, doc1):
    q1 = ds.add_query(query_text="query 1", doc_id=doc1.id)
    q2 = ds.add_query(query_text="query 2", doc_id=doc1.id)
    queries = ds.get_queries()
    assert len(queries) == 2
    assert q1 in queries
    assert q2 in queries

def test_get_queries_empty(ds):
    assert ds.get_queries() == []

def test_add_and_get_score(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query = ds.add_query(query_text="test query", doc_id=doc1.id)
    
    # Score is -1 by default
    assert ds.get_score(query.id, doc1.id) == -1

    # Add a new score
    ds.add_score(query.id, doc1.id, 2)
    assert ds.get_score(query.id, doc1.id) == 2

def test_update_score(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query = ds.add_query(query_text="test query", doc_id=doc1.id)
    ds.add_score(query.id, doc1.id, 1)
    assert ds.get_score(query.id, doc1.id) == 1

    # Update the score
    ds.add_score(query.id, doc1.id, 0)
    assert ds.get_score(query.id, doc1.id) == 0

def test_add_score_for_new_doc_to_existing_query(ds, doc1, doc2):
    ds.add_document(doc1.id, doc1)
    ds.add_document(doc2.id, doc2)
    query = ds.add_query(query_text="test query", doc_id=doc1.id)
    
    # Add score for a new document
    ds.add_score(query.id, doc2.id, 2)
    
    retrieved_query = ds.get_query(query.id)
    assert len(retrieved_query.scores) == 2
    assert ds.get_score(query.id, doc2.id) == 2

def test_has_score(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query = ds.add_query(query_text="test query", doc_id=doc1.id)
    
    # Default score is -1, so has_score should be False
    assert not ds.has_score(query.id, doc1.id)

    # After scoring, should be True
    ds.add_score(query.id, doc1.id, 1)
    assert ds.has_score(query.id, doc1.id)

def test_get_score_for_nonexistent_doc_raises_keyerror(ds, doc1):
    ds.add_document(doc1.id, doc1)
    query = ds.add_query(query_text="test query", doc_id=doc1.id)
    with pytest.raises(KeyError, match="Document 'nonexistent-doc' not found in DataStore"):
        ds.get_score(query.id, "nonexistent-doc")

def test_add_score_for_nonexistent_query_raises_keyerror(ds, doc1):
    ds.add_document(doc1.id, doc1)
    with pytest.raises(KeyError, match="'nonexistent-query' not found in DataStore"):
        ds.add_score("nonexistent-query", doc1.id, 1)

def test_add_score_for_nonexistent_document_raises_keyerror(ds, doc1):
    query = ds.add_query(query_text="test query", doc_id="doc-1")
    with pytest.raises(KeyError, match="'doc-1' not found in DataStore"):
        ds.add_score(query.id, "doc-1", 1)
