import json
from pathlib import Path

import pytest

from src.config import Config
from src.search_engine.data_store import DataStore
from src.writers.rre_writer import RreWriter


@pytest.fixture
def rre_config():
    """Loads a valid rre based config."""
    return Config.load("tests/unit/resources/rre_config.yaml")


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


class TestRreWriter:
    def test_rre_file_successfully_written(self, rre_config, populated_datastore, tmp_path: Path):
        output_dir = tmp_path
        writer = RreWriter(populated_datastore, index=rre_config.index_name,
                           corpora_file=rre_config.corpora_file,
                           id_field=rre_config.id_field,
                           query_template=rre_config.rre_query_template,
                           query_placeholder=rre_config.rre_query_placeholder)

        writer.write(str(output_dir))

        output_file = Path(output_dir) / "ratings.json"

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
