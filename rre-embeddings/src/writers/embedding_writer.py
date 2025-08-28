import logging
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import jsonlines
from mteb.models.cache_wrapper import CachedEmbeddingWrapper

from src.config import Config
from src.custom_tasks.reranking_task import compose_text
from src.utilities.helper import read_corpus, read_queries

log = logging.getLogger(__name__)


def _write_embeddings_jsonl(
    path: Path, items: Iterable[tuple[str, np.ndarray | list[float]]]
) -> None:
    with jsonlines.open(path, mode="w") as jsonl:
        for _id, vector in items:
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            jsonl.write({"id": _id, "vector": vector})
    log.info(f"Embeddings are saved into {path}")


class EmbeddingWriter:
    """
    Encodes documents and queries embeddings using mteb.CachedEmbeddingWrapper and writes them into the following
    jsonl files:
    <embeddings_path>/documents_embeddings.jsonl
    <embeddings_path>/queries_embeddings.jsonl
    """

    def __init__(
        self,
        config: Config,
        cached: CachedEmbeddingWrapper,
        cache_path: str | Path,
        task_name: str,
        normalize_embeddings: bool,
        batch_size: int,
    ):
        self.config = config
        self.cached = cached
        self.cache_path = Path(cache_path)
        self.task_name = task_name
        self.normalize_embeddings = normalize_embeddings
        self.batch_size = batch_size

    def write(self, embedding_path: str | Path | None) -> None:
        """
        Write embeddings to <embedding_path>.
        """
        # by default embeddings will be written into <output/embeddings>
        if embedding_path is None:
            embedding_path = "output/embeddings"

        path = Path(embedding_path)
        os.makedirs(path, exist_ok=True)

        # documents
        documents_path = path / "documents_embeddings.jsonl"
        doc_dict = read_corpus(Path(self.config.corpus_path))
        doc_ids = list(doc_dict.keys())
        doc_texts = [
            compose_text(doc_dict[_id].get("title"), doc_dict[_id].get("text"))
            for _id in doc_ids
        ]

        doc_vectors = self.cached.encode(
            doc_texts,
            task_name=self.task_name,
            name=f"{self.task_name}-corpus",
            normalize_embeddings=self.normalize_embeddings,
            batch_size=self.batch_size,
        )
        _write_embeddings_jsonl(documents_path, zip(doc_ids, doc_vectors))

        # queries
        queries_path = path / "queries_embeddings.jsonl"
        query_dict = read_queries(Path(self.config.queries_path))
        query_ids = list(query_dict.keys())
        query_texts = [query_dict[qid] for qid in query_ids]

        query_vectors = self.cached.encode(
            query_texts,
            task_name=self.task_name,
            name=f"{self.task_name}-queries",
            normalize_embeddings=self.normalize_embeddings,
            batch_size=self.batch_size,
        )
        _write_embeddings_jsonl(queries_path, zip(query_ids, query_vectors))

        self.cached.close()
