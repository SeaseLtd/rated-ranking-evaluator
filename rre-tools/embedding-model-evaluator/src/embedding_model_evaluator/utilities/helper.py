import logging
from pathlib import Path
from typing import Dict

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


def _validate_shapes(corpus: Dict[str, dict], queries: Dict[str, str], candidates: Dict[str, Dict[str, int]]) -> None:
    """Validate data shapes and log missing IDs to detect mismatches early."""
    n_docs = len(corpus)
    n_q = len(queries)
    n_pairs = sum(len(v) for v in candidates.values())
    
    log.info("Loaded corpus=%d, queries=%d, candidate_pairs=%d", n_docs, n_q, n_pairs)
    
    # Sample check for missing document IDs in candidates
    missing = 0
    for qid, cmap in candidates.items():
        for did in cmap.keys():
            if did not in corpus:
                missing += 1
                if missing <= 5:  # Log only first 5 to avoid spam
                    log.warning("candidate doc_id %s not found in corpus", did)
    
    if missing:
        log.error("Missing %d candidate doc ids in corpus", missing)
    
    # Check for queries in candidates that don't exist in queries dict
    missing_queries = 0
    for qid in candidates.keys():
        if qid not in queries:
            missing_queries += 1
            if missing_queries <= 5:
                log.warning("candidate query_id %s not found in queries", qid)
    
    if missing_queries:
        log.error("Missing %d candidate query ids in queries", missing_queries)
