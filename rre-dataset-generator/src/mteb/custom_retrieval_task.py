import os
from pathlib import Path

from mteb import AbsTaskRetrieval, TaskMetadata

from src.mteb.helper import read_corpus, read_queries, read_query_relations_tsv

ROOT = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "data"


class MyRetrievalTask(AbsTaskRetrieval):
    metadata = TaskMetadata(
        name="MyRetrievalTask",
        description="Custom retrieval task.",
        reference="https://github.com/SeaseLtd/rated-ranking-evaluator",
        type="Retrieval",
        category="p2p",
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
            "name": "my_local_dataset",
            "path": "local",
            "revision": "v1",
            "url": "https://github.com/SeaseLtd/rated-ranking-evaluator"
        },
    )

    def __init__(self, hf_subsets=None, **kwargs):
        super().__init__(hf_subsets=hf_subsets, **kwargs)
        self.queries = {}
        self.corpus = {}
        self.relevant_docs = {}

    def load_data(self, **kwargs):
        base = DATA_ROOT
        self.corpus = {"test": read_corpus(os.path.join(base, "corpus.jsonl"))}
        self.queries = {"test": read_queries(os.path.join(base, "queries.jsonl"))}
        self.relevant_docs = {"test": read_query_relations_tsv(os.path.join(base, "relevant_docs.tsv"))}
