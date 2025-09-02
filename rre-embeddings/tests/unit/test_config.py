import pytest
from pydantic import FilePath
from pydantic_core import ValidationError

from src.config import Config


@pytest.fixture
def config() -> Config:
    return Config.load("tests/unit/resources/valid_config.yaml")


def test_valid_config_expect_all_params_read(config: Config) -> None:
    assert config.model_id == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.corpus_path == FilePath("tests/unit/resources/data/corpus.jsonl")
    assert config.queries_path == FilePath("tests/unit/resources/data/queries.jsonl")
    assert config.candidates_path == FilePath(
        "tests/unit/resources/data/candidates.jsonl"
    )
    assert config.output_dest == FilePath("output")


def test_invalid_config_expects_error_on_file_extension() -> None:
    path = "tests/unit/resources/invalid_config.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(path)
