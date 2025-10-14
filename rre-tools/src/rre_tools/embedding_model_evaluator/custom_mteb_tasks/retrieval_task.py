import logging
from pathlib import Path
from typing import Any

from mteb.abstasks.AbsTask import TaskMetadata
from mteb.abstasks.AbsTaskRetrieval import AbsTaskRetrieval
from mteb.overview import TASKS_REGISTRY

from rre_tools.embedding_model_evaluator.utils import read_corpus_retrieval, read_queries, read_candidates

log = logging.getLogger(__name__)


class CustomRetrievalTask(AbsTaskRetrieval):
    metadata = TaskMetadata(
        name="CustomRetrievalTask",
        description="Custom Retrieval Task.",
        reference="https://github.com/SeaseLtd/rated-ranking-evaluator/rre-embeddings",
        type="Retrieval",
        category="s2p",
        eval_splits=["test"],
        eval_langs=["en"],
        main_score="ndcg_at_10",
        date=("2020-01-01", "2030-01-01"),
        domains=["Engineering"],
        task_subtypes=["Article retrieval"],
        license="not specified",
        annotations_creators="derived",
        sample_creation="created",
        dataset={
            "name": "data",
            "path": "rre-embeddings/resources/data",
            "revision": "v1",
            "url": "https://github.com/SeaseLtd/rated-ranking-evaluator/rre-embeddings/resources/data",
        },
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.corpus: dict[str, dict[str, str]] = {}
        self.queries: dict[str, dict[str, str]] = {}
        self.relevant_docs: dict[str, dict[str, dict[str, int]]] = {}

    def load_data(
            self,
            corpus_path: Path,
            queries_path: Path,
            candidates_path: Path,
            **kwargs: Any
    ) -> None:
        """
        Override AbsTask.load_data. By default, AbsTask.load_data fetches datasets from the Hugging Face Hub.
        In our case, we want to use local data files (paths defined in Config), so we override this method.
        """
        self.corpus = {"test": read_corpus_retrieval(corpus_path)}
        self.queries = {"test": read_queries(queries_path)}
        self.relevant_docs = {
            "test": read_candidates(candidates_path)["relevant_docs"]
        }
        self.data_loaded = True

# the tasks need to be added to the official registry, otherwise are not seen from CachedEmbeddingWrapper class
TASKS_REGISTRY["CustomRetrievalTask"] = CustomRetrievalTask
