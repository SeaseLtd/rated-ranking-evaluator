from pathlib import Path

import pytest
from pydantic import FilePath
from pydantic_core import ValidationError

from embedding_model_evaluator.config import Config


@pytest.fixture
def config() -> Config:
    return Config.load("embedding-model-evaluator/tests/unit/resources/valid_config.yaml")


def test_config_with_valid_yaml_file__expects__loads_all_parameters_correctly(config: Config) -> None:
    assert config.model_id == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.corpus_path == FilePath("embedding-model-evaluator/tests/unit/resources/data/corpus.jsonl")
    assert config.queries_path == FilePath("embedding-model-evaluator/tests/unit/resources/data/queries.jsonl")
    assert config.candidates_path == FilePath(
        "embedding-model-evaluator/tests/unit/resources/data/candidates.jsonl"
    )
    assert config.output_dest == Path("output")
    assert config.task_to_evaluate == "retrieval"
    assert config.relevance_scale == "binary"


def test_config_with_invalid_file_extension__expects__raises_validation_error() -> None:
    path = "embedding-model-evaluator/tests/unit/resources/invalid_config.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(path)
