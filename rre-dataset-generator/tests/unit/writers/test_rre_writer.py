import json
from pathlib import Path

import pytest

from src.config import Config
from src.data_store import DataStore
from src.model import Query, Document
from src.writers.rre_writer import RreWriter


@pytest.fixture
def rre_config():
    """Loads a valid rre based config."""
    return Config.load("tests/unit/resources/rre_config.yaml")


@pytest.fixture
def populated_datastore() -> DataStore:
    """Returns a DataStore instance populated with test data."""
    ds = DataStore()

    # Add docs
    ds.add_doc(Document(id="doc1", fields={"title": "title 1"}))
    ds.add_doc(Document(id="doc2", fields={"title": "title 2"}))
    ds.add_doc(Document(id="doc4", fields={"title": "title 4"}))
    ds.add_doc(Document(id="doc5", fields={"title": "title 5"}))

    # Add queries and ratings
    q1 = Query(text="test query 1")
    ds.add_query(q1)
    ds.create_rating_score(q1.id, "doc1", 1)
    ds.create_rating_score(q1.id, "doc2", 1)

    q2 = Query(text="test query 2")
    ds.add_query(q2)
    ds.create_rating_score(q2.id, "doc4", 2)

    q3 = Query(text="test query 3")
    ds.add_query(q3)

    return ds


class TestRreWriter:
    def test_rre_file_successfully_written(self, rre_config, populated_datastore, tmp_path: Path):
        output_file = tmp_path/"ratings.json"
        writer = RreWriter(index=rre_config.index_name,
                         corpora_file=rre_config.corpora_file,
                         id_field=rre_config.id_field,
                         query_template=rre_config.rre_query_template,
                         query_placeholder=rre_config.rre_query_placeholder)

        writer.write(str(output_file), populated_datastore)

        assert output_file.exists()

        with open(output_file, 'r', newline='') as jsonfile:
            data = json.load(jsonfile)
            assert data["index"] == "testcore"
            assert data["id_field"] == "id"
            assert len(data["query_groups"]) == 2

            group = data["query_groups"][0]
            assert group["name"] == "test query 1"

            queries = group["queries"]
            assert len(queries) == 1
            assert "$query" in queries[0]["placeholders"]

            relevant = group["relevant_documents"]
            assert "doc1" in relevant["1"]
            assert "doc2" in relevant["1"]

            group = data["query_groups"][1]
            assert group["name"] == "test query 2"

            relevant = group["relevant_documents"]
            assert "doc4" in relevant["2"]
