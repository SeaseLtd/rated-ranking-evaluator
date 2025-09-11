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

        # Orden recomendado: leer → castear → validar → construir relevant_docs
        corpus = read_corpus(config.corpus_path)
        queries = read_queries(config.queries_path)
        candidates_data = read_candidates(config.candidates_path)
        
        # Convertir candidates a formato iterable para validación
        candidates_list = [
            (qid, did, rating) 
            for qid, docs in candidates_data["candidates"].items() 
            for did, rating in docs.items()
        ]
        
        # Validate data shapes and log missing IDs
        _validate_shapes(corpus, queries, candidates_list)
        
        # Construir relevancias (binary @ rating>0)
        relevant_docs = {}
        for qid, did, rating in candidates_list:
            if rating and rating > 0:
                if qid not in relevant_docs:
                    relevant_docs[qid] = {}
                relevant_docs[qid][did] = rating
        
        # Loggear cuántas queries pierden todos los positivos tras filtrar
        dropped = sum(1 for qid in queries if qid not in relevant_docs or not relevant_docs[qid])
        if dropped:
            log.warning("Queries with no positives after filtering rating>0: %d", dropped)
        
        self.corpus = {"test": corpus}
        self.queries = {"test": queries}
        self.relevant_docs = {"test": relevant_docs}
        self.data_loaded = True

# the tasks need to be added to the official registry, otherwise are not seen from CachedEmbeddingWrapper class
TASKS_REGISTRY["CustomRetrievalTask"] = CustomRetrievalTask
