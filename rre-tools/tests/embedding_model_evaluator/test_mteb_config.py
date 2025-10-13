from pathlib import Path

import pytest
from pydantic import FilePath
from pydantic_core import ValidationError

from rre_tools.embedding_model_evaluator.config import Config


@pytest.fixture
def config(resource_folder) -> Config:
    return Config.load(resource_folder / "valid_mteb_config.yaml")


def test_config_with_valid_yaml_file__expects__loads_all_parameters_correctly(config: Config) -> None:
    assert config.model_id == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.corpus_path == FilePath("tests/resources/data/corpus.jsonl")
    assert config.queries_path == FilePath("tests/resources/data/queries.jsonl")
    assert config.candidates_path == FilePath("tests/resources/data/candidates.jsonl")
    assert config.output_dest == Path("output")
    assert config.task_to_evaluate == "retrieval"
    assert config.relevance_scale == "binary"


def test_config_with_invalid_file_extension__expects__raises_validation_error(resource_folder) -> None:
    path = resource_folder / "invalid_mteb_config.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(path)
