import json
from pathlib import Path

import pytest

from src.config import Config
from src.data_store import DataStore
from src.model import Document, WriterConfig
from src.writers.mteb_writer import MtebWriter


@pytest.fixture
def writer_config():
    """Loads a valid rre based config."""
    params = {
        'output_format': 'mteb',
        'index': 'testcore'
    }

    return WriterConfig(**params)


@pytest.fixture
def populated_datastore() -> DataStore:
    """Returns a DataStore instance populated with test data."""
    datastore = DataStore(ignore_saved_data=True)

    # Add docs
    datastore.add_document(Document(id="doc1", fields={"title": "title 1", "description": "desc 1"}))
    datastore.add_document(Document(id="doc2", fields={"title": "title 2", "description": "desc 2"}))
    datastore.add_document(Document(id="doc4", fields={"title": "title 4", "description": "desc 4"}))
    datastore.add_document(Document(id="doc5", fields={"title": "title 5", "description": "desc 5"}))

    # Add queries and ratings
    q1 = datastore.add_query("test query 1")
    datastore.create_rating_score(q1.id, "doc1", 1)
    datastore.create_rating_score(q1.id, "doc2", 1)

    q2 = datastore.add_query("test query 2")
    datastore.create_rating_score(q2.id, "doc4", 2)

    datastore.add_query("test query 3")

    return datastore


class TestMtebWriter:

    def test_write_expect_written_to_jsonl(self, writer_config, populated_datastore, tmp_path: Path):
        output_dir = tmp_path
        writer = MtebWriter(writer_config)
        writer.write(output_dir, populated_datastore)

        corpus_file = output_dir / "corpus.jsonl"
        queries_file = output_dir / "queries.jsonl"
        candidates_file = output_dir / "candidates.jsonl"

        assert corpus_file.exists()
        assert queries_file.exists()
        assert candidates_file.exists()

        # Corpus verification
        lines = corpus_file.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        docs = populated_datastore.get_documents()
        assert len(rows) == len(docs)
        for row in rows:
            assert set(row.keys()) == {"id", "title", "text"}

        # Queries verification
        lines = queries_file.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        queries = populated_datastore.get_queries()
        assert len(rows) == len(queries)
        for row in rows:
            assert set(row.keys()) == {"id", "text"}

        # Candidates verification
        lines = candidates_file.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        ratings = populated_datastore.get_ratings()
        assert len(rows) == len(ratings)

        expected_ratings = {(r.query_id, r.doc_id, r.score) for r in ratings}
        written_ratings = {(row["query_id"], row["doc_id"], row["rating"]) for row in rows}
        assert written_ratings == expected_ratings
