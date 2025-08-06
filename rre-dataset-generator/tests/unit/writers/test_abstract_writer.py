import pytest
from src.search_engine.data_store import DataStore
from src.writers.abstract_writer import AbstractWriter


@pytest.fixture
def populated_datastore() -> DataStore:
    """Returns a DataStore instance populated with test data."""
    datastore = DataStore(ignore_saved_data=True)

    # Query 1: 2 rated docs, 1 unrated
    query_1_id = datastore.add_query("test query 1", "doc1")
    datastore.add_query("test query 1", "doc2")
    datastore.add_query("test query 1", "doc3")
    datastore.add_rating_score(query_1_id, "doc1", 1)
    datastore.add_rating_score(query_1_id, "doc2", 2)

    # Query 2: 1 rated doc
    query_2_id = datastore.add_query("test query 2", "doc4")
    datastore.add_rating_score(query_2_id, "doc4", 3)

    # Query 3: No rated docs
    datastore.add_query("test query 3", "doc5")

    return datastore


# A concrete implementation of AbstractWriter for testing purposes
class ConcreteWriter(AbstractWriter):
    def write(self, output_path: str) -> None:
        pass


class TestAbstractWriter:
    def test_get_queries_with_ratings_expect_correct_tuples(self, populated_datastore):
        """Tests that the helper method extracts the correct rated documents."""
        writer = ConcreteWriter(populated_datastore)
        result = writer._get_queries_with_ratings()

        expected = [
            ('test query 1', 'doc1', 1),
            ('test query 1', 'doc2', 2),
            ('test query 2', 'doc4', 3),
        ]

        # Sort both lists to ensure comparison is order-independent
        assert sorted(result) == sorted(expected)
