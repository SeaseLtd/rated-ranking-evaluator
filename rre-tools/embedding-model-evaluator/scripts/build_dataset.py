#!/usr/bin/env python3
"""
BEIR → MTEB (retrieval-only) converter — streaming & RAM-friendly.

Outputs to <out_root>/<dataset>/<split>/:
- corpus.jsonl     -> {id: str, title: str, text: str}
- queries.jsonl    -> {id: str, text: str}  # only queries having ≥1 positive pair
- candidates.jsonl -> {query_id: str, doc_id: str, rating: int}  # full qrels
- manifest.json    -> minimal metadata

Notes:
- Caps via --max-queries and --max-docs are deterministic by qrels encounter order.
- If --max-docs > 0, corpus is emitted in qrels order (bounded memory). Otherwise it streams in BEIR order.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Any, Iterable, Optional, Set, Tuple

import jsonlines

BEIR_DATASET_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
DEFAULT_OUT_ROOT = Path("resources/beir_datasets")
DEFAULT_CACHE_DIR = Path("resources/beir_downloads")

log = logging.getLogger("beir2mteb")

# ------------------------- CLI & logging -------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download a BEIR dataset and convert it to MTEB JSONL (retrieval-only).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dataset", default="scifact",
                   help="See https://github.com/beir-cellar/beir/wiki/Datasets-available")
    p.add_argument("--split", default="test", choices=["train", "dev", "test"])
    p.add_argument("--out-root", default=None, help=f"Root output dir (default: {DEFAULT_OUT_ROOT})")
    p.add_argument("--cache-dir", default=None, help=f"Download/cache dir (default: {DEFAULT_CACHE_DIR})")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    p.add_argument("--max-docs", type=int, default=0, help="0 = no cap")
    p.add_argument("--max-queries", type=int, default=0, help="0 = no cap")
    p.add_argument("--log-level", default="INFO")
    return p.parse_args()

def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

# ------------------------- BEIR download -------------------------
def import_beir_util() -> Any:
    try:
        from beir import util  # type: ignore
    except Exception as e:
        log.error("Missing 'beir'. Install: pip install beir  (error: %s)", e)
        raise SystemExit(1)
    return util

def download_dataset(dataset: str, cache_dir: Path) -> Path:
    util = import_beir_util()
    url = BEIR_DATASET_URL.format(dataset=dataset)
    log.info("Downloading '%s' from %s → %s", dataset, url, cache_dir)
    try:
        path = util.download_and_unzip(url, str(cache_dir))
        return Path(path)
    except Exception as e:
        log.error("Download/unzip failed for '%s': %s", dataset, e)
        raise SystemExit(1)

# ------------------------- IO paths -------------------------
def resolve_paths(dataset: str, split: str, out_root_arg: Optional[str], cache_dir_arg: Optional[str]) -> tuple[Path, Path, Path, Path, Path, Path]:
    out_root = Path(out_root_arg) if out_root_arg else DEFAULT_OUT_ROOT
    out_dir = out_root / dataset / split
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus_out = out_dir / "corpus.jsonl"
    queries_out = out_dir / "queries.jsonl"
    candidates_out = out_dir / "candidates.jsonl"

    cache_dir = Path(cache_dir_arg) if cache_dir_arg else DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return out_root, out_dir, corpus_out, queries_out, candidates_out, cache_dir

def beir_inputs(data_path: Path, split: str) -> tuple[Path, Path, Path]:
    corpus_in = data_path / "corpus.jsonl"
    queries_in = data_path / "queries.jsonl"
    qrels_in = data_path / "qrels" / f"{split}.tsv"
    for p, name in ((corpus_in, "corpus"), (queries_in, "queries"), (qrels_in, f"qrels/{split}")):
        if not p.exists():
            log.error("Missing BEIR %s file: %s", name, p)
            raise SystemExit(1)
    return corpus_in, queries_in, qrels_in

# ------------------------- Helpers -------------------------
def pick(row: dict, keys: Iterable[str]) -> Optional[str]:
    for k in keys:
        v = row.get(k)
        if v not in (None, ""):
            return str(v)
    return None


def norm_str(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "\n".join(str(x) for x in v if x is not None)
    return str(v)


def normalize_doc(row: dict) -> Tuple[str, str]:
    title = norm_str(row.get("title", ""))
    text_fields = [
        row.get("text"),
        row.get("abstract"),
        row.get("contents"),
        row.get("body"),
        ""
    ]
    text = next((str(field) for field in text_fields if field), "")
    return title, text

def to_int(v: Optional[str]) -> int:
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return 0

# ------------------------- Pass 1: decide caps -------------------------
def collect_keep_sets(qrels_path: Path, max_q: int, max_d: int) -> tuple[Optional[set[str]], Optional[set[str]], int, Optional[list[str]]]:
    keep_q: Optional[Set[str]] = set() if max_q > 0 else None
    doc_seen: Optional[Set[str]] = set() if max_d > 0 else None
    doc_order: Optional[list[str]] = [] if max_d > 0 else None
    total = 0

    with qrels_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            total += 1
            qid = pick(row, ("query-id", "qid", "query_id", "query"))
            did = pick(row, ("corpus-id", "doc-id", "doc_id", "document_id", "doc"))
            if not qid or not did:
                continue
            if keep_q is not None and qid not in keep_q:
                if len(keep_q) < max_q:
                    keep_q.add(qid)
                else:
                    continue
            if doc_seen is not None and did not in doc_seen:
                doc_seen.add(did)
                doc_order.append(did)  # type: ignore

    keep_docs = set(doc_order[:max_d]) if doc_order else None
    return keep_q, keep_docs, total, doc_order

# ------------------------- Pass 2a: corpus -------------------------
def write_corpus(corpus_in: Path, corpus_out: Path, max_docs: int,
                 keep_docs: Optional[Set[str]], doc_order: Optional[list[str]]) -> Tuple[Optional[Set[str]], int]:
    """
    If max_docs>0, emit in qrels order (bounded by max_docs memory).
    Else stream BEIR order (no reordering).
    """
    if max_docs > 0:
        selected = {}
        with jsonlines.open(corpus_in) as reader:
            for row in reader:
                did = str(row.get("_id") or row.get("id"))
                if did in (keep_docs or ()):
                    title, text = normalize_doc(row)
                    selected[did] = {"id": did, "title": title, "text": text}
                    if len(selected) >= len(keep_docs or ()):
                        break
        count = 0
        with jsonlines.open(corpus_out, mode="w") as writer:
            for did in (doc_order or []):
                if did in selected:
                    writer.write(selected[did])
                    count += 1
        return set(selected.keys()), count

    # Streaming path
    count = 0
    written_ids: Optional[Set[str]] = set() if (keep_docs is not None or max_docs > 0) else None
    with jsonlines.open(corpus_in) as reader, jsonlines.open(corpus_out, mode="w") as writer:
        for row in reader:
            did = str(row.get("_id") or row.get("id"))
            if keep_docs is not None and did not in keep_docs:
                continue
            title, text = normalize_doc(row)
            writer.write({"id": did, "title": title, "text": text})
            count += 1
            if written_ids is not None:
                written_ids.add(did)
    return written_ids, count

# ------------------------- Pass 2b: candidates -------------------------
def write_candidates(qrels_path: Path, out_path: Path,
                     keep_q: Optional[Set[str]], keep_docs: Optional[Set[str]]) -> tuple[int, int, set[str]]:
    """
    Write all qrels. Track queries with ≥1 positive pair for the next pass.
    """
    total, positives = 0, 0
    q_with_pos: Set[str] = set()

    with qrels_path.open("r", encoding="utf-8") as f, jsonlines.open(out_path, mode="w") as writer:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            qid = pick(row, ("query-id", "qid", "query_id", "query"))
            did = pick(row, ("corpus-id", "doc-id", "doc_id", "document_id", "doc"))
            if not qid or not did:
                continue
            if keep_q is not None and qid not in keep_q:
                continue
            if keep_docs is not None and did not in keep_docs:
                continue
            rating = to_int(pick(row, ("score", "label", "relevance")))
            writer.write({"query_id": qid, "doc_id": did, "rating": rating})
            total += 1
            if rating > 0:
                positives += 1
                q_with_pos.add(qid)
    return total, positives, q_with_pos

# ------------------------- Pass 2c: queries -------------------------
def write_queries(queries_in: Path, queries_out: Path, keep_qids: Set[str]) -> int:
    cnt = 0
    with jsonlines.open(queries_in) as reader, jsonlines.open(queries_out, mode="w") as writer:
        for row in reader:
            qid = str(row.get("_id") or row.get("id"))
            if qid in keep_qids:
                writer.write({"id": qid, "text": str(row.get("text", ""))})
                cnt += 1
    return cnt

# ------------------------- Manifest -------------------------
def write_manifest(out_dir: Path, *, dataset: str, split: str, out_root: Path,
                   caps: dict, counts: dict, cache_dir: Path) -> None:
    manifest = {
        "dataset": dataset, "split": split,
        "output_dir": str(out_dir),
        "files": ["corpus.jsonl", "queries.jsonl", "candidates.jsonl", "manifest.json"],
        "caps": caps, "counts": counts,
        "cache_dir": str(cache_dir),
        "source_url": BEIR_DATASET_URL.format(dataset=dataset),
        "notes": "corpus is qrels-ordered if --max-docs>0; otherwise BEIR order (streamed).",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

# ------------------------- Main -------------------------
def main() -> None:
    args = parse_args()
    setup_logging(args.log_level)

    if args.max_docs < 0 or args.max_queries < 0:
        log.error("max-docs and max-queries must be >= 0")
        raise SystemExit(1)

    paths = resolve_paths(
        args.dataset,
        args.split,
        args.out_root,
        args.cache_dir
    )
    out_root, out_dir, corpus_out, queries_out, candidates_out, cache_dir = paths
    if not args.overwrite and any(p.exists() for p in (corpus_out, queries_out, candidates_out, out_dir / "manifest.json")):
        log.error("Outputs exist in %s. Use --overwrite to replace.", out_dir)
        raise SystemExit(1)

    data_path = download_dataset(args.dataset, cache_dir)
    corpus_in, queries_in, qrels_in = beir_inputs(data_path, args.split)

    keep_q, keep_docs, qrels_total, doc_order = collect_keep_sets(qrels_in, args.max_queries, args.max_docs)
    if keep_q is not None:
        log.info("Capped queries to %d by qrels order", len(keep_q))
    if keep_docs is not None:
        log.info("Capped docs to %d by first-encounter order", len(keep_docs))

    written_doc_ids, corpus_count = write_corpus(corpus_in, corpus_out, args.max_docs, keep_docs, doc_order)
    cand_total, cand_pos, qids_with_pos = write_candidates(qrels_in, candidates_out, keep_q, written_doc_ids)
    if cand_total == 0:
        log.error("No candidate pairs after filtering/capping.")
        raise SystemExit(1)
    queries_count = write_queries(queries_in, queries_out, qids_with_pos)

    write_manifest(
        out_dir,
        dataset=args.dataset,
        split=args.split,
        out_root=out_root,
        caps={"max_docs": args.max_docs, "max_queries": args.max_queries},
        counts={
            "qrels_pairs_total": qrels_total,
            "candidate_pairs_total": cand_total,
            "candidate_pairs_positive": cand_pos,
            "corpus_docs": corpus_count,
            "queries_with_positive_pairs": queries_count,
        },
        cache_dir=cache_dir,
    )
    log.info("Done. corpus=%d, queries(≥1 pos)=%d, candidates(total)=%d, positives=%d (from qrels=%d)",
             corpus_count, queries_count, cand_total, cand_pos, qrels_total)

if __name__ == "__main__":
    main()
