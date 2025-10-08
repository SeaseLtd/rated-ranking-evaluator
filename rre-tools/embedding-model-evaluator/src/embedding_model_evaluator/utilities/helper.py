from pathlib import Path

from jsonlines import jsonlines

def read_corpus_reranking(path: Path) -> dict[str, dict[str, str]]:
    corpus_dict: dict[str, dict[str, str]] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            corpus_dict[row["id"]] = {"title": row["title"], "text": row["text"]}
    return corpus_dict

def read_corpus_retrieval(path: Path) -> dict[str, str]:
    corpus_dict: dict[str, str] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            corpus_dict[row["id"]] = row.get("title", "") + " " + row["text"]
    return corpus_dict


def read_queries(path: Path) -> dict[str, str]:
    queries_dict: dict[str, str] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            queries_dict[row["id"]] = row["text"]
    return queries_dict


def read_candidates(path: Path) -> dict[str, dict[str, dict[str, int]]]:
    candidates_dict: dict[str, dict[str, int]] = {}
    relevant_docs: dict[str, dict[str, int]] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            query_id = row["query_id"]
            doc_id = row["doc_id"]
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
