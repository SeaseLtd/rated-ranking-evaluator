import argparse
import logging
import sys
from pathlib import Path

import jsonlines

log = logging.getLogger(__name__)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download a BEIR dataset and convert it to the local MTEB JSONL schema (retrieval-only)."
        )
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="scifact",
        help="BEIR dataset name (default: scifact)",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to load (e.g., train/dev/test). Default: test",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help=(
            "Output directory for JSONL files. If not provided, defaults to "
            "<repo>/rre-embeddings/resources/data/beir/<dataset>"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files if they already exist.",
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=0,
        help="Optional cap on number of documents (0 = no cap).",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=0,
        help="Optional cap on number of queries (0 = no cap).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (e.g., DEBUG, INFO, WARNING). Default: INFO",
    )
    return parser.parse_args()


def _setup_logging(level: str) -> None:
    level_num = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=level_num,
        format="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def _import_beir():
    """Import BEIR modules with a friendly error message if missing."""
    try:
        from beir import util  # type: ignore
        from beir.datasets.data_loader import GenericDataLoader  # type: ignore
    except Exception as e:  # noqa: BLE001
        log.error(
            f"Failed to import BEIR. Install 'pip install beir' or the optional extra "
            f"'pip install -e .[beir]'. Error: {e}"
        )
        sys.exit(1)
    return util, GenericDataLoader


def _normalize_str(value) -> str:
    """Return a normalized string given arbitrary value types (str, list, None, etc.)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(str(v) for v in value if v is not None)
    return str(value)


def _normalize_document_fields(document: dict) -> tuple[str, str]:
    """Extract normalized (title, text) from a BEIR document, with safe fallbacks."""
    # Prefer common BEIR fields in order
    title = _normalize_str(document.get("title", ""))
    text = _normalize_str(
        document.get("text")
        or document.get("abstract")
        or document.get("contents")
        or document.get("body")
        or ""
    )
    return title, text


def _write_corpus(path: Path, corpus: dict[str, dict], max_docs: int) -> int:
    """Write corpus JSONL in MTEB schema: {id, title, text}. Returns rows written."""
    count = 0
    with jsonlines.open(path, mode="w") as writer:
        # sort for deterministic order (reproducibility)
        for idx, doc_id in enumerate(sorted(corpus.keys())):
            doc = corpus[doc_id]
            if max_docs and idx >= max_docs:
                break
            title, text = _normalize_document_fields(doc)
            writer.write({"id": str(doc_id), "title": title, "text": text})
            count += 1
    return count


def _write_queries(path: Path, queries: dict[str, str], keep_qids: set[str]) -> int:
    """Write queries JSONL in MTEB schema: {id, text}, restricted to keep_qids. Returns rows written."""
    count = 0
    with jsonlines.open(path, mode="w") as writer:
        # sort for deterministic order (reproducibility)
        qids = [qid for qid in sorted(queries.keys()) if qid in keep_qids]
        for qid in qids:
            writer.write({"id": str(qid), "text": str(queries[qid])})
            count += 1
    return count


def _write_candidates(
    path: Path, qrels: dict[str, dict[str, int]], keep_qids: set[str], keep_doc_ids: set[str]
) -> int:
    """Write candidates JSONL: {query_id, doc_id, rating} for retrieval (ratings from qrels)."""
    count = 0
    with jsonlines.open(path, mode="w") as writer:
        # sort for deterministic order (reproducibility)
        for qid in sorted(qrels.keys()):
            if qid not in keep_qids:
                continue
            for doc_id in sorted(qrels[qid].keys()):
                score = qrels[qid][doc_id]
                if doc_id not in keep_doc_ids:
                    continue
                writer.write({
                    "query_id": str(qid),
                    "doc_id": str(doc_id),
                    "rating": int(score),
                })
                count += 1
    return count


def _resolve_paths(dataset: str, out_dir_arg: str | None) -> tuple[Path, Path, Path, Path, Path, Path]:
    """Resolve repository paths and ensure output/cache directories exist."""
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parent  # rre-embeddings/
    default_out_dir = repo_root / "resources" / "data" / "beir" / dataset
    out_dir = Path(out_dir_arg) if out_dir_arg else default_out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    corpus_path = out_dir / "corpus.jsonl"
    queries_path = out_dir / "queries.jsonl"
    candidates_path = out_dir / "candidates.jsonl"

    cache_dir = repo_root / "resources" / "beir_datasets"
    cache_dir.mkdir(parents=True, exist_ok=True)

    return repo_root, out_dir, corpus_path, queries_path, candidates_path, cache_dir


def _validate_splits(corpus, queries, qrels) -> None:
    if not corpus:
        log.error("Loaded corpus is empty.")
        sys.exit(1)
    if not queries:
        log.error("Loaded queries are empty.")
        sys.exit(1)
    if not qrels:
        log.error("Loaded qrels are empty (retrieval requires positives).")
        sys.exit(1)


def _download_dataset(util, dataset: str, cache_dir: Path) -> str:
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
    log.info(f"Downloading dataset '{dataset}' to {cache_dir}")
    try:
        return util.download_and_unzip(url, str(cache_dir))
    except Exception as e:  # noqa: BLE001
        log.error(f"Failed to download/unzip dataset '{dataset}': {e}")
        sys.exit(1)


def _load_split(GenericDataLoader, data_path: str, split: str):
    log.info(f"Loading dataset from {data_path} (split={split})")
    try:
        return GenericDataLoader(data_folder=data_path).load(split=split)
    except Exception as e:  # noqa: BLE001
        log.error(f"Failed to load dataset split '{split}' from {data_path}: {e}")
        sys.exit(1)


def _filter_qrels(
    corpus: dict[str, dict],
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
) -> tuple[dict[str, dict[str, int]], set[str], int]:
    """Filter qrels to known query/doc ids. Return (filtered, kept_query_ids, initial_pair_count)."""
    initial_pairs = sum(len(v) for v in qrels.values())
    missing_query_qids = 0
    missing_doc_ids = 0
    filtered_qrels: dict[str, dict[str, int]] = {}
    # Deterministic order for reproducibility
    for qid in sorted(qrels.keys()):
        docs = qrels[qid]
        if qid not in queries:
            missing_query_qids += 1
            continue
        for doc_id in sorted(docs.keys()):
            score = docs[doc_id]
            if doc_id not in corpus:
                missing_doc_ids += 1
                continue
            filtered_qrels.setdefault(qid, {})[doc_id] = int(score)

    if missing_query_qids or missing_doc_ids:
        log.warning(
            f"Dropped qrels with unknown items: {missing_query_qids} queries, {missing_doc_ids} doc refs."
        )

    keep_qids = [qid for qid, docs in filtered_qrels.items() if len(docs) > 0]
    keep_qids_set = set(keep_qids)
    if not keep_qids_set:
        log.error("No queries left after filtering qrels.")
        sys.exit(1)

    return filtered_qrels, keep_qids_set, initial_pairs


def _sampling(
    filtered_qrels: dict[str, dict[str, int]],
    keep_qids_set: set[str],
    max_queries: int,
    max_docs: int,
    corpus: dict[str, dict],
) -> tuple[dict[str, dict[str, int]], set[str], set[str], int]:
    """Apply deterministic sampling to queries/docs. Return updated (qrels, qids, doc_ids, pair_count)."""
    # Deterministic order for reproducibility
    keep_qids = sorted(list(keep_qids_set))
    if max_queries and max_queries > 0:
        keep_qids = keep_qids[:max_queries]
        keep_qids_set = set(keep_qids)
        filtered_qrels = {qid: filtered_qrels[qid] for qid in keep_qids}
        log.warning(f"Sampling queries to first {max_queries} items. Kept={len(keep_qids_set)}")

    keep_doc_ids = set(corpus.keys())
    if max_docs and max_docs > 0:
        # Deterministic by sorting ids
        keep_doc_ids = set(sorted(list(corpus.keys()))[:max_docs])
        for qid in list(filtered_qrels.keys()):
            filtered_qrels[qid] = {
                doc_id: score
                for doc_id, score in filtered_qrels[qid].items()
                if doc_id in keep_doc_ids
            }
        keep_qids = [qid for qid, docs in filtered_qrels.items() if len(docs) > 0]
        keep_qids_set = set(keep_qids)
        filtered_qrels = {qid: filtered_qrels[qid] for qid in keep_qids}
        log.warning(
            f"Sampling documents to first {max_docs} items. Kept_docs={len(keep_doc_ids)}, "
            f"Kept_queries={len(keep_qids_set)}"
        )

    final_pairs = sum(len(v) for v in filtered_qrels.values())
    if final_pairs == 0:
        log.error("No candidate pairs to write after filtering/sampling.")
        sys.exit(1)

    return filtered_qrels, keep_qids_set, keep_doc_ids, final_pairs


def main() -> None:
    args = _parse_args()
    _setup_logging(args.log_level)

    # Arg validation
    if args.max_docs < 0 or args.max_queries < 0:
        log.error(f"max-docs and max-queries must be >= 0 (got {args.max_docs}, {args.max_queries})")
        sys.exit(1)

    # Resolve paths
    repo_dir, out_dir, corpus_path, queries_path, candidates_path, cache_dir = _resolve_paths(
        args.dataset, args.out_dir
    )

    if not args.overwrite and any(p.exists() for p in [corpus_path, queries_path, candidates_path]):
        log.error(f"Output files already exist in {out_dir}. Use --overwrite to replace them.")
        sys.exit(1)

    # lazy BEIR import (noisy error when missing)
    util, GenericDataLoader = _import_beir()

    data_path = _download_dataset(util, args.dataset, cache_dir)
    # load splits
    corpus, queries, qrels = GenericDataLoader(data_folder=data_path).load(split=args.split)
    # split validation
    _validate_splits(corpus, queries, qrels)
    log.info(
        f"Loaded sizes: corpus={len(corpus)}, queries={len(queries)}, "
        f"qrels_pairs={sum(len(v) for v in qrels.values())}"
    )

    # Filter qrels to existing queries & docs
    filtered_qrels, keep_qids_set, initial_pairs = _filter_qrels(corpus, queries, qrels)

    # Apply sampling (queries first)
    filtered_qrels, keep_qids_set, keep_doc_ids, pairs_final = _sampling(
        filtered_qrels, keep_qids_set, args.max_queries, args.max_docs, corpus
    )

    # Write outputs
    log.info(f"Writing outputs to {out_dir}")
    corpus_count = _write_corpus(corpus_path, corpus, args.max_docs)
    queries_count = _write_queries(queries_path, queries, keep_qids_set)
    candidates_count = _write_candidates(
        candidates_path, filtered_qrels, keep_qids_set, keep_doc_ids
    )

    log.info(
        f"Done. corpus={corpus_count}, queries(with qrels)={queries_count}, "
        f"candidate_pairs={candidates_count} (from {initial_pairs})"
    )


if __name__ == "__main__":
    main()
