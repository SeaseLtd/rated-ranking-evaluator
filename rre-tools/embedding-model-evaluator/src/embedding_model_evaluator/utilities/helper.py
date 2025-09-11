import logging
from pathlib import Path
from typing import Dict, Iterable, Tuple
from collections import Counter

from jsonlines import jsonlines

log = logging.getLogger(__name__)


def read_corpus(path: Path) -> dict[str, dict[str, str]]:
    corpus_dict: dict[str, dict[str, str]] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            corpus_dict[str(row["id"])] = {"title": row["title"], "text": row["text"]}
    return corpus_dict


def read_queries(path: Path) -> dict[str, str]:
    queries_dict: dict[str, str] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            queries_dict[str(row["id"])] = row["text"]
    return queries_dict


def read_candidates(path: Path) -> dict[str, dict[str, dict[str, int]]]:
    candidates_dict: dict[str, dict[str, int]] = {}
    relevant_docs: dict[str, dict[str, int]] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            query_id = str(row["query_id"])  # Ensure string type
            doc_id = str(row["doc_id"])      # Ensure string type
            rating = int(row["rating"])
            if query_id not in candidates_dict:
                candidates_dict[query_id] = {}
            candidates_dict[query_id][doc_id] = rating
            # Include rating=1 and rating=2 to relevant docs for retrieval task
            if rating > 0:
                if query_id not in relevant_docs:
                    relevant_docs[query_id] = {}
                relevant_docs[query_id][doc_id] = rating
    return {
        "candidates": candidates_dict,
        "relevant_docs": relevant_docs,
    }


def _validate_shapes(
    corpus: Dict[str, dict], 
    queries: Dict[str, str], 
    candidates: Iterable[Tuple[str, str, int]]
) -> None:
    """Validate data shapes and log missing IDs, duplicates, empty texts, and rating distribution."""
    # Conteos
    n_docs, n_queries = len(corpus), len(queries)

    # Conjuntos de IDs
    doc_ids = set(corpus.keys())
    query_ids = set(queries.keys())

    # Pase sobre candidatos
    miss_docs = 0
    miss_queries = 0
    label_hist = Counter()
    seen_pairs = set()
    dup_pairs = 0
    
    for qid, did, rating in candidates:
        label_hist[rating] += 1
        if qid not in query_ids:
            miss_queries += 1
        if did not in doc_ids:
            miss_docs += 1
        key = (qid, did)
        if key in seen_pairs:
            dup_pairs += 1
        else:
            seen_pairs.add(key)

    # Textos vacíos (muestra, no O(N) caro si ya lo tienes indexado)
    empty_docs = sum(1 for d in corpus.values() if not (d.get("text") or "").strip())
    empty_queries = sum(1 for q in queries.values() if not (q or "").strip())

    log.info(
        "Validate: docs=%d, queries=%d, candidates=%d, labels=%s, "
        "missing_docs=%d, missing_queries=%d, empty_docs=%d, empty_queries=%d, dup_pairs=%d",
        n_docs, n_queries, len(seen_pairs), dict(label_hist),
        miss_docs, miss_queries, empty_docs, empty_queries, dup_pairs
    )

    # Fail-fast estrictos
    if miss_docs or miss_queries:
        raise ValueError(f"Missing references: docs={miss_docs}, queries={miss_queries}")
