from pathlib import Path
from typing import Sequence
from unittest.mock import create_autospec

import jsonlines
import numpy as np
import pytest
from mteb.models.cache_wrapper import CachedEmbeddingWrapper

from embedding_model_evaluator.config import Config
from embedding_model_evaluator.writers.embedding_writer import EmbeddingWriter


@pytest.fixture
def config() -> Config:
    return Config.load("embedding-model-evaluator/tests/unit/resources/valid_config.yaml")


def _create_fake_cache_wrapper(
    doc_vectors: Sequence[Sequence[float] | np.ndarray],
    query_vectors: Sequence[Sequence[float] | np.ndarray],
) -> CachedEmbeddingWrapper:
    cached: CachedEmbeddingWrapper = create_autospec(
        CachedEmbeddingWrapper, instance=True
    )

    def _encode(
        texts: list[str],
        *,
        task_name: str,
        batch_size: int,
    ) -> np.ndarray:
        assert batch_size == 32
        if task_name.endswith("-corpus"):
            return np.vstack([np.asarray(vector) for vector in doc_vectors])
        if task_name.endswith("-queries"):
            return np.vstack([np.asarray(vector) for vector in query_vectors])
        raise AssertionError(f"Unexpected encode name: {task_name}")

    cached.encode.side_effect = _encode
    return cached


def test_embeddings_writer_with_valid_inputs__expects__creates_jsonl_files_with_correct_embeddings(
    config: Config, tmp_path: Path
) -> None:
    doc_vectors = [[0.1, 0.2, 0.3]]
    query_vectors = [[1.0, 1.1, 1.2]]
    cached = _create_fake_cache_wrapper(
        doc_vectors=doc_vectors, query_vectors=query_vectors
    )
    config.embeddings_dest = tmp_path / "output" / "embeddings"

    writer = EmbeddingWriter(
        config=config,
        cached=cached,
        cache_path=tmp_path / "cache",
        task_name="test_custom_task-corpus",
        batch_size=32,
    )

    writer.write(config.embeddings_dest)

    embedding_dir = config.embeddings_dest
    docs_file = embedding_dir / "documents_embeddings.jsonl"

    assert docs_file.exists()
    with jsonlines.open(docs_file) as r:
        docs = list(r)
    assert docs == [{"id": "doc1", "vector": [0.1, 0.2, 0.3]}]

    # recreating again because of fake cached embedding wrapper for queries and corpus vectors
    writer = EmbeddingWriter(
        config=config,
        cached=cached,
        cache_path=tmp_path / "cache",
        task_name="test_custom_task-queries",
        batch_size=32,
    )

    writer.write(config.embeddings_dest)
    queries_file = embedding_dir / "queries_embeddings.jsonl"
    assert queries_file.exists()

    with jsonlines.open(queries_file) as r:
        queries = list(r)
    assert queries == [{"id": "query1", "vector": [1.0, 1.1, 1.2]}]

