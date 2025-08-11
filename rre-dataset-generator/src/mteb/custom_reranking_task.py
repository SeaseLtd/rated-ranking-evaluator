import os
from pathlib import Path

from datasets import Dataset, DatasetDict
from mteb import TaskMetadata, AbsTaskReranking

from src.mteb.helper import read_corpus, read_query_relations_tsv, read_queries, read_candidates_jsonl

ROOT = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "data"


def _make_samples_from_beir(corpus, queries, relevance_docs, candidates):
    samples = []
    for query_id, query in queries.items():
        cand_map = candidates.get(query_id, {})  # dict[doc_id] -> label
        pos_txt = []
        neg_txt = []

        for doc_id, label in cand_map.items():
            doc = corpus.get(doc_id)
            if not doc:
                continue
            text = " ".join(t for t in (doc.get("title"), doc.get("text")) if t)
            if not text:
                continue

            relevance = relevance_docs.get(query_id, {}).get(doc_id, label)
            if relevance > 0:
                pos_txt.append(text)
            else:
                neg_txt.append(text)

        if pos_txt and neg_txt:
            samples.append({"query": query, "positive": pos_txt, "negative": neg_txt})

    return samples


class MyRerankingTask(AbsTaskReranking):
    metadata = TaskMetadata(
        name="MyRerankingTask",
        description="Custom reranking task.",
        reference="https://github.com/SeaseLtd/rated-ranking-evaluator",
        type="Reranking",
        category="s2p",
        eval_splits=["test"],
        eval_langs=["en"],
        main_score="map",
        dataset={
            "name": "my_local_dataset",
            "path": "local",
            "revision": "v1",
            "url": "https://github.com/SeaseLtd/rated-ranking-evaluator"
        },
    )

    def load_data(self, **kwargs):
        base = DATA_ROOT
        corpus = {"test": read_corpus(os.path.join(base, "corpus.jsonl"))}
        queries = {"test": read_queries(os.path.join(base, "queries.jsonl"))}
        relevant_docs = {"test": read_query_relations_tsv(os.path.join(base, "relevant_docs.tsv"))}
        candidates = {"test": read_candidates_jsonl(os.path.join(base, "candidates.jsonl"))}

        samples_test = _make_samples_from_beir(corpus["test"], queries["test"], relevant_docs["test"],
                                               candidates["test"])
        ds_test = Dataset.from_list(samples_test)
        self.dataset = DatasetDict({"test": ds_test})
        self.data_loaded = True
