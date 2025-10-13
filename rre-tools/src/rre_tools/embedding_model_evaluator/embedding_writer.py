import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import jsonlines
from mteb.models.cache_wrapper import CachedEmbeddingWrapper

from rre_tools.embedding_model_evaluator.custom_mteb_tasks.reranking_task import compose_text
from rre_tools.embedding_model_evaluator.utils import read_corpus_retrieval, read_corpus_reranking, read_queries
from rre_tools.embedding_model_evaluator.constants import TASKS_NAME_MAPPING

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
        corpus_path: str | Path,
        queries_path: str | Path,
        cached: CachedEmbeddingWrapper,
        cache_path: str | Path,
        task_name: str,
        batch_size: int,
    ):
        self.corpus_path = corpus_path
        self.queries_path = queries_path
        self.cached = cached
        self.cache_path = Path(cache_path)
        self.task_name = task_name
        self.batch_size = batch_size

    def write(self, embedding_path: str | Path | None) -> None:
        """
        Write embeddings to <embedding_path>.
        """
        # by default embeddings will be written into <resources/embeddings>
        if embedding_path is None:
            embedding_path = "resources/embeddings"

        path = Path(embedding_path)
        path.mkdir(parents=True, exist_ok=True)

        # documents
        documents_path = path / "documents_embeddings.jsonl"
        if self.task_name == TASKS_NAME_MAPPING["retrieval"]:
            doc_dict_retrieval= read_corpus_retrieval(Path(self.corpus_path))
            doc_ids = list(doc_dict_retrieval.keys())
            doc_texts = list(doc_dict_retrieval.values())
        elif self.task_name == TASKS_NAME_MAPPING["reranking"]:
            doc_dict_reranking = read_corpus_reranking(Path(self.corpus_path))
            doc_ids = list(doc_dict_reranking.keys())
            doc_texts = [
                compose_text(doc_dict_reranking[_id].get("title"), doc_dict_reranking[_id].get("text"))
                for _id in doc_ids
            ]
        else:
            raise ValueError(f"Unknown task: {self.task_name}")


        doc_vectors = self.cached.encode(
            texts=doc_texts,
            task_name=self.task_name,
            batch_size=self.batch_size,
        )
        _write_embeddings_jsonl(documents_path, zip(doc_ids, doc_vectors))

        # queries
        queries_path = path / "queries_embeddings.jsonl"
        query_dict = read_queries(Path(self.queries_path))
        query_ids = list(query_dict.keys())
        query_texts = [query_dict[qid] for qid in query_ids]

        query_vectors = self.cached.encode(
            texts=query_texts,
            task_name=self.task_name,
            batch_size=self.batch_size,
        )
        _write_embeddings_jsonl(queries_path, zip(query_ids, query_vectors))

        self.cached.close()
