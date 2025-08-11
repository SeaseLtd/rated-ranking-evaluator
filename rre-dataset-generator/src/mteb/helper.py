import csv
from typing import Dict

from jsonlines import jsonlines


def read_corpus(path) -> Dict[str, Dict]:
    out = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            out[row["id"]] = {"title": row["title"], "text": row["text"]}
    return out


def read_queries(path) -> Dict[str, str]:
    out = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            out[row["id"]] = row["text"]
    return out


def read_query_relations_tsv(path) -> Dict[str, Dict[str, int]]:
    query_relations = {}
    with open(path) as file:
        for query_id, doc_id, score in csv.reader(file, delimiter="\t"):
            query_relations.setdefault(query_id, {})[doc_id] = int(score)
    return query_relations


def read_candidates_jsonl(path) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    with jsonlines.open(path) as rows:
        for row in rows:
            query_id = row["query_id"]
            doc_id = row["doc_id"]
            label = int(row.get("label", 1))
            out.setdefault(query_id, {})[doc_id] = label
    return out

