import logging
from typing import Any

from mteb.abstasks.AbsTask import TaskMetadata
from mteb.abstasks.AbsTaskRetrieval import AbsTaskRetrieval
from mteb.overview import TASKS_REGISTRY

from embedding_model_evaluator.config import Config
from embedding_model_evaluator.utilities.helper import read_corpus, read_queries, read_candidates, _validate_shapes

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
        self.corpus: dict[str, dict[str, dict[str, str]]] = {}
        self.queries: dict[str, dict[str, str]] = {}
        self.relevant_docs: dict[str, dict[str, dict[str, int]]] = {}

    def load_data(self, config: Config | None, **kwargs: Any) -> None:
        """
        Override AbsTask.load_data. By default, AbsTask.load_data fetches datasets from the Hugging Face Hub.
        In our case, we want to use local data files (paths defined in Config), so we override this method.
        """
        if config is None:
            message = "No config is provided. Pass your internal Config via MTEB.run(..., config=Config)."
            log.error(message)
            raise ValueError(message)

        corpus = read_corpus(config.corpus_path)
        queries = read_queries(config.queries_path)
        candidates_data = read_candidates(config.candidates_path)
        
        # Validate data shapes and log missing IDs
        _validate_shapes(corpus, queries, candidates_data["candidates"])
        
        # Filter relevant_docs to only include ratings > 0
        rels = candidates_data["relevant_docs"]
        filtered_relevant_docs = {
            qid: {did: r for did, r in dids.items() if r > 0}
            for qid, dids in rels.items()
        }
        
        self.corpus = {"test": corpus}
        self.queries = {"test": queries}
        self.relevant_docs = {"test": filtered_relevant_docs}
        self.data_loaded = True

# the tasks need to be added to the official registry, otherwise are not seen from CachedEmbeddingWrapper class
TASKS_REGISTRY["CustomRetrievalTask"] = CustomRetrievalTask
