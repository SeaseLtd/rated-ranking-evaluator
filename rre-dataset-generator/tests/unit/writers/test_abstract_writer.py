import pytest
from src.search_engine.data_store import DataStore
from src.writers.abstract_writer import AbstractWriter
from src.model.query_rating_context import Document, Query
from pathlib import Path


# ---------------------------------------------------------------------------
# shared util (same as in test_quepid_writer)
# ---------------------------------------------------------------------------

def _add_query_with_doc(ds: DataStore, query_text: str, doc_id: str) -> str:
    doc = Document(id=doc_id, fields={"field": "value"})
    ds.add_doc(doc)
    q = Query(text=query_text)
    ds.add_query(q)
    ds.add_doc_to_query(q.id, doc_id)
    return q.id


@pytest.fixture
def populated_datastore() -> DataStore:
    ds = DataStore(ignore_saved_data=True)

    # Query 1: 2 rated docs, 1 unrated
    q1_id = _add_query_with_doc(ds, "test query 1", "doc1")
    _add_query_with_doc(ds, "test query 1", "doc2")
    _add_query_with_doc(ds, "test query 1", "doc3")
    ds.add_rating_score(q1_id, "doc1", 1)
    ds.add_rating_score(q1_id, "doc2", 2)

    # Query 2: 1 rated doc
    q2_id = _add_query_with_doc(ds, "test query 2", "doc4")
    ds.add_rating_score(q2_id, "doc4", 3)

    # Query 3: No rated docs
    _add_query_with_doc(ds, "test query 3", "doc5")

    return ds


# Concrete implementation of AbstractWriter for testing
class ConcreteWriter(AbstractWriter):
    def write(self, output_path: str | Path) -> None:
        pass


class TestAbstractWriter:
    def test_get_queries_with_ratings_expect_correct_tuples(self, populated_datastore):
        writer = ConcreteWriter(populated_datastore)
        result = writer._get_queries_with_ratings()

        expected = [
            ("test query 1", "doc1", 1),
            ("test query 1", "doc2", 2),
            ("test query 2", "doc4", 3),
        ]

        assert sorted(result) == sorted(expected)
