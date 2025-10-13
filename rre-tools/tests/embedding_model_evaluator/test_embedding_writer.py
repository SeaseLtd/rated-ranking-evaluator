from pathlib import Path
from typing import Sequence
from unittest.mock import create_autospec

import jsonlines
import numpy as np
from mteb.models.cache_wrapper import CachedEmbeddingWrapper

from rre_tools.embedding_model_evaluator.embedding_writer import EmbeddingWriter
from rre_tools.embedding_model_evaluator.constants import TASKS_NAME_MAPPING


def _create_fake_cache_wrapper(
    vectors: Sequence[Sequence[float] | np.ndarray]
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
        assert task_name == TASKS_NAME_MAPPING["retrieval"]
        return np.vstack([np.asarray(vector) for vector in vectors])

    cached.encode.side_effect = _encode
    return cached


def test_embeddings_writer_with_valid_inputs__expects__creates_jsonl_files_with_correct_embeddings(
        tmp_path: Path,
        resource_folder
) -> None:
    doc_vectors = [[0.1, 0.2, 0.3]]
    cached_doc = _create_fake_cache_wrapper(
        vectors=doc_vectors
    )
    query_vectors = [[1.0, 1.1, 1.2]]
    cached_query = _create_fake_cache_wrapper(
        vectors=query_vectors
    )

    embeddings_dir = tmp_path / "output" / "embeddings"

    writer = EmbeddingWriter(
        corpus_path= resource_folder / "data" / "corpus.jsonl",
        queries_path= resource_folder / "data" / "queries.jsonl",
        cached=cached_doc,
        cache_path=tmp_path / "cache",
        task_name=TASKS_NAME_MAPPING["retrieval"],
        batch_size=32,
    )

    writer.write(embeddings_dir)

    docs_file = embeddings_dir / "documents_embeddings.jsonl"

    assert docs_file.exists()
    with jsonlines.open(docs_file) as r:
        docs = list(r)
    assert docs == [{"id": "doc1", "vector": [0.1, 0.2, 0.3]}]

    # recreating again because of fake cached embedding wrapper for queries and corpus vectors
    writer = EmbeddingWriter(
        corpus_path= resource_folder / "data" / "corpus.jsonl",
        queries_path= resource_folder / "data" / "queries.jsonl",
        cached=cached_query,
        cache_path=tmp_path / "cache",
        task_name=TASKS_NAME_MAPPING["retrieval"],
        batch_size=32,
    )

    writer.write(embeddings_dir)
    queries_file = embeddings_dir / "queries_embeddings.jsonl"
    assert queries_file.exists()

    with jsonlines.open(queries_file) as r:
        queries = list(r)
    assert queries == [{"id": "query1", "vector": [1.0, 1.1, 1.2]}]

