import json
from pathlib import Path

import pytest

from src.config import Config
from src.search_engine.data_store import DataStore
from src.writers.mteb_writer import MtebWriter


@pytest.fixture
def config():
    """Loads a valid config."""
    return Config.load("tests/unit/resources/mteb_config.yaml")


@pytest.fixture
def populated_datastore() -> DataStore:
    """Returns a DataStore instance populated with test data."""
    datastore = DataStore()

    # Query 1: 2 rated docs
    query_1_id = datastore.add_query("test query 1", "doc1")
    datastore.add_query("test query 1", "doc2")
    datastore.add_rating_score(query_1_id, "doc1", 1)
    datastore.add_rating_score(query_1_id, "doc2", 1)

    # Query 2: 1 rated doc
    query_2_id = datastore.add_query("test query 2", "doc4")
    datastore.add_rating_score(query_2_id, "doc4", 2)

    # Query 3: No rated docs
    datastore.add_query("test query 3", "doc5")

    return datastore


class TestMtebWriter:

    def test_write_expect_written_to_jsonl(self, config, populated_datastore, tmp_path: Path):
        output_dir = tmp_path
        writer = MtebWriter(populated_datastore)

        writer.write(output_dir)

        corpus_file = output_dir / "corpus.jsonl"
        queries_file = output_dir / "queries.jsonl"
        candidates_file = output_dir / "candidates.jsonl"

        assert corpus_file.exists()
        assert queries_file.exists()
        assert candidates_file.exists()

        lines = corpus_file.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]

        docs = populated_datastore.get_documents()
        assert len(rows) == len(docs)

        for row in rows:
            assert set(row.keys()) == {"id", "title", "text"}
            assert isinstance(row["id"], str)
            assert isinstance(row["title"], str)
            assert isinstance(row["text"], str)

        lines = queries_file.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]

        queries = populated_datastore.get_queries()
        assert len(rows) == len(queries)

        for row in rows:
            assert set(row.keys()) == {"id", "text"}
            assert isinstance(row["id"], str)
            assert isinstance(row["text"], str)

        lines = candidates_file.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]

        expected = set()
        for query_context in populated_datastore.get_queries():
            query_id = query_context.get_query_id()
            for doc_id in query_context.get_doc_ids():
                if query_context.has_rating_score(doc_id):
                    expected.add((query_id, doc_id, query_context.get_rating_score(doc_id)))

        assert len(rows) == len(expected)

        for row in rows:
            assert set(row.keys()) == {"query_id", "doc_id", "rating"}
            assert isinstance(row["query_id"], str)
            assert isinstance(row["doc_id"], str)
            assert isinstance(row["rating"], int)

        written = {(row["query_id"], row["doc_id"], row["rating"]) for row in rows}
        assert written == expected
