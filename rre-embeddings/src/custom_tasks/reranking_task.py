import logging
from typing import Dict, Optional, Any

from datasets import Dataset, DatasetDict
from mteb.abstasks.AbsTask import TaskMetadata
from mteb.abstasks.AbsTaskReranking import AbsTaskReranking

from src.config import Config
from src.utilities.helper import read_corpus, read_queries, read_candidates

log = logging.getLogger(__name__)


def _compose_text(title: Optional[str], description: Optional[str]) -> str:
    if title and description:
        return f"{title}\n\n{description}"
    return title or description or ""


def _build_dataset(
    corpus: Dict[str, Dict],
    queries: Dict[str, str],
    candidates: Dict[str, Dict[str, int]],
    relevance_scale: str,
) -> list[dict]:
    dataset = []
    for query_id, query in queries.items():
        candidate_map = candidates.get(query_id)
        if candidate_map is None:
            continue
        positive_text = []
        negative_text = []

        for doc_id, rating in candidate_map.items():
            doc = corpus.get(doc_id, {})
            title = doc.get("title")
            text = doc.get("text")

            if not title and not text:
                log.warning(f"{doc_id} has no description and no title")
                continue
            composed_context = _compose_text(title, text)
            if relevance_scale == "binary":
                if rating > 0:
                    positive_text.append(composed_context)
                else:
                    negative_text.append(composed_context)
            elif relevance_scale == "graded":
                # In case of rating=1, we drop it as it might bring noise for reranking task
                if rating == 2:
                    positive_text.append(composed_context)
                elif rating == 0:
                    negative_text.append(composed_context)

        if positive_text and negative_text:
            dataset.append(
                {"query": query, "positive": positive_text, "negative": negative_text}
            )
        else:
            log.warning("Empty positive_text and negative_text lists")

    return dataset


class CustomRerankingTask(AbsTaskReranking):
    metadata = TaskMetadata(
        name="CustomRerankingTask",
        description="Custom Reranking Task.",
        reference="https://github.com/SeaseLtd/rated-ranking-evaluator/rre-embeddings",
        type="Reranking",
        category="s2p",
        eval_splits=["test"],
        eval_langs=["en"],
        main_score="map",
        dataset={
            "name": "data",
            "path": "rre-embeddings/resources/data",
            "revision": "v1",
            "url": "https://github.com/SeaseLtd/rated-ranking-evaluator/rre-embeddings/resources/data",
        },
    )

    def load_data(self, config: Config, **kwargs: Any) -> None:
        """
        Override AbsTask.load_data. By default, AbsTask.load_data fetches datasets from the Hugging Face Hub.
        In our case, we want to use local data files (paths defined in Config), so we override this method.
        """

        if config is None:
            raise ValueError(
                "Pass your internal Config via MTEB.run(..., config=Config)."
            )

        corpus = read_corpus(config.corpus_path)
        queries = read_queries(config.queries_path)
        candidates = read_candidates(config.candidates_path)["candidates"]

        dataset = _build_dataset(corpus, queries, candidates, config.relevance_scale)

        self.dataset = DatasetDict({"test": Dataset.from_list(dataset)})
        self.data_loaded = True
