import pytest
import csv
from pathlib import Path

from src.search_engine.data_store import DataStore
from src.writers import QuepidWriter


@pytest.fixture
def populated_datastore() -> DataStore:
    """Returns a DataStore instance populated with test data."""
    datastore = DataStore()

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



@pytest.fixture
def empty_datastore() -> DataStore:
    """Returns an empty DataStore instance."""
    return DataStore()


@pytest.fixture
def unrated_datastore() -> DataStore:
    """Returns a DataStore with unrated documents."""
    datastore = DataStore()
    datastore.add_query("query 1", "doc1")
    datastore.add_query("query 2", "doc2")
    return datastore


class TestQuepidWriter:
    def test_write(self, populated_datastore, tmp_path: Path):
        """Tests that the QuepidWriter correctly writes a CSV file."""
        output_file = tmp_path / "output.csv"
        writer = QuepidWriter(populated_datastore)

        writer.write(str(output_file))

        assert output_file.exists()

        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            assert header == ['query', 'docid', 'rating']

            rows = set(tuple(row) for row in reader)
            expected_rows = {
                ('test query 1', 'doc1', '1'),
                ('test query 1', 'doc2', '2'),
                ('test query 2', 'doc4', '3'),
            }
            assert rows == expected_rows

    def test_write_with_empty_datastore(self, empty_datastore, tmp_path: Path):
        """Tests writing from an empty datastore."""
        output_file = tmp_path / "output.csv"
        writer = QuepidWriter(empty_datastore)
        writer.write(str(output_file))

        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            assert header == ['query', 'docid', 'rating']
            # Check that there are no more rows
            with pytest.raises(StopIteration):
                next(reader)

    def test_write_with_no_rated_documents(self, unrated_datastore, tmp_path: Path):
        """Tests writing when no documents have been rated."""
        output_file = tmp_path / "output.csv"
        writer = QuepidWriter(unrated_datastore)
        writer.write(str(output_file))

        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            assert header == ['query', 'docid', 'rating']
            # Check that there are no more rows
            with pytest.raises(StopIteration):
                next(reader)

    def test_write_with_special_characters(self, tmp_path: Path):
        """Tests writing with special characters in query and doc_id."""
        datastore = DataStore()
        query_text = 'query with "quotes" and a comma,'
        doc_id = 'doc_id_with_a_newline\n'
        query_id = datastore.add_query(query_text, doc_id)
        datastore.add_rating_score(query_id, doc_id, 1)

        output_file = tmp_path / "output.csv"
        writer = QuepidWriter(datastore)
        writer.write(str(output_file))

        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            assert header == ['query', 'docid', 'rating']
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0] == [query_text, doc_id, '1']

    def test_write_with_zero_rating(self, tmp_path: Path):
        """Tests that a rating of 0 is correctly written."""
        datastore = DataStore()
        query_id = datastore.add_query("query", "doc1")
        datastore.add_rating_score(query_id, "doc1", 0)

        output_file = tmp_path / "output.csv"
        writer = QuepidWriter(datastore)
        writer.write(str(output_file))

        with open(output_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            assert header == ['query', 'docid', 'rating']
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0] == ["query", "doc1", "0"]
