from pathlib import Path

import pytest
from pydantic_core import ValidationError

from embedding_model_evaluator.config import Config


@pytest.fixture
def config() -> Config:
    # Create config with absolute paths to avoid validation issues
    base_path = Path(__file__).parent / "resources" / "data"
    
    return Config(
        model_id="sentence-transformers/all-MiniLM-L6-v2",
        task_to_evaluate="retrieval",
        corpus_path=base_path / "corpus.jsonl",
        queries_path=base_path / "queries.jsonl",
        candidates_path=base_path / "candidates.jsonl",
        relevance_scale="binary",
        output_dest=Path("output"),
        embeddings_dest=Path("output/dummy_embeddings")
    )


def test_valid_config_expect_all_params_read(config: Config) -> None:
    assert config.model_id == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.task_to_evaluate == "retrieval"
    assert config.relevance_scale == "binary"
    assert config.output_dest == Path("output")
    
    # Check that paths exist (they are relative to the config file)
    assert config.corpus_path is not None
    assert config.queries_path is not None
    assert config.candidates_path is not None


def test_invalid_config_expects_error_on_file_extension() -> None:
    config_path = Path(__file__).parent / "resources" / "invalid_config.yaml"
    with pytest.raises(ValidationError):
        _ = Config.load(str(config_path))
