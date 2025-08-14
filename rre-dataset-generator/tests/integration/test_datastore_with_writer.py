import json

import pytest
import csv
from pathlib import Path

from src.model.document import Document
from src.search_engine.data_store import DataStore
from src.writers.quepid_writer import QuepidWriter
from src.writers.rre_writer import RreWriter


@pytest.fixture
def empty_store() -> DataStore:
    """Fixture for an empty DataStore that ignores any saved data."""
    return DataStore(ignore_saved_data=True)

@pytest.fixture
def docs():
    return [
        Document(id="doc1", fields={"title": "Gadgets", "description": "Cutting edge technologies are on demand."}),
        Document(id="doc2",
                 fields={"title": "Airpods", "description": "The quality of airpods from Apple is getting worse."}),
        Document(id="doc3",
                 fields={"title": "MacBook Pro", "description": "The price of Apple laptops has been skyrocketed."}),
    ]

@pytest.fixture
def query_doc_pairs():
    return [
        ("Apple products", "doc2"),
        ("Apple products", "doc3"),
        ("Apple's headphones", "doc2"),
        ("Apple's pc", "doc3"),
    ]

def test_documents_with_ratings__expects__file_in_tmp_folder_quepid(empty_store: DataStore,
                                                                    tmp_path: Path,
                                                                    docs,
                                                                    query_doc_pairs):
    for d in docs:
        empty_store.add_document(d.id, d)

    for query, doc_id in query_doc_pairs:
        query_id = empty_store.add_query(query, doc_id)
        empty_store.add_rating_score(query_id, doc_id, 1)

    output_file = tmp_path / "quepid.csv"
    writer = QuepidWriter(empty_store)
    writer.write(output_path=output_file)

    assert output_file.exists(), "Output file was not created."

    with output_file.open(newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    header = reader[0]
    assert header == ["query", "docid", "rating"], f"Unexpected header: {header}"

    data_rows = reader[1:]
    assert len(data_rows) == 4, f"Expected 4 rows, got {len(data_rows)}"

    ratings = [row[2] for row in data_rows]
    assert all(r == "1" for r in ratings), f"Expected all ratings to be '1', got {ratings}"

def test_documents_with_ratings__expects__file_in_tmp_folder_rre(empty_store: DataStore,
                                                                 tmp_path: Path,
                                                                 docs,
                                                                 query_doc_pairs):
    for d in docs:
        empty_store.add_document(d.id, d)

    for query, doc_id in query_doc_pairs:
        query_id = empty_store.add_query(query, doc_id)
        empty_store.add_rating_score(query_id, doc_id, 1)

    writer = RreWriter(
        datastore=empty_store,
        index="test_index",
        corpora_file="corpora.json",
        id_field="id",
        query_template="template.json",
        query_placeholder="query"
    )

    output_file = tmp_path / "ratings.json"
    writer.write(output_file)

    assert output_file.exists(), "RRE ratings.json file was not created."

    with output_file.open(encoding="utf-8") as f:
        data = json.load(f)

    assert data["index"] == "test_index"
    assert data["corpora_file"] == "corpora.json"
    assert data["id_field"] == "id"
    assert data["query_placeholder"] == "query"
    assert "query_groups" in data

    total_pairs = 0
    for group in data["query_groups"]:
        assert "name" in group
        assert "queries" in group
        assert isinstance(group["queries"], list) and len(group["queries"]) == 1
        assert "relevant_documents" in group
        for gain, docs in group["relevant_documents"].items():
            assert gain == "1"  # we only gave rating 1
            total_pairs += len(docs)

    assert total_pairs == 4, f"Expected 4 total pairs, got {total_pairs}"
