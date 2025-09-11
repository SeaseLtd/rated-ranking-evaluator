#!/usr/bin/env python3
"""
BEIR → MTEB (retrieval-only) converter — streaming & RAM-friendly.

Downloads a BEIR dataset and converts it to MTEB-compatible JSONL with the files:

Output files (saved to <out_root>/<dataset>/<split>/):
- corpus.jsonl     -> {id: str, title: str, text: str}
- queries.jsonl    -> {id: str, text: str}  # Only queries that have ≥1 positive (rating > 0) pair
- candidates.jsonl -> {query_id: str, doc_id: str, rating: int}  # QRELS format
- manifest.json    -> Metadata: dataset, split, caps, counts, params

Directory structure:
<out_root>/  # Default: 'resources/beir_datasets/'
  <dataset>/  # e.g., 'scifact', 'nq', 'hotpotqa'
    <split>/  # 'train' | 'dev' | 'test'
      corpus.jsonl
      queries.jsonl
      candidates.jsonl
      manifest.json

Key properties:
- Streams BEIR JSONL to minimize memory usage.
- Deterministic capping via --max-queries and --max-docs (by qrels encounter order).
- Document subset is determined by first appearance in BEIR qrels (preserved deterministically).
  * If you also want the *output order of corpus.jsonl* to follow qrels order, use
    --preserve-doc-order together with a finite --max-docs (required to avoid unbounded RAM).
- Maintains backward compatibility with MTEB's retrieval task format.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Iterable, Tuple, Set, Optional

# Third-party deps are intentionally imported lazily with clear error messages.
try:
    import jsonlines  # type: ignore
except Exception as e:
    raise SystemExit(
        "Missing dependency 'jsonlines'. Install with: pip install jsonlines\n"
        f"Import error: {e}"
    )

# --------------------------------------------------------------------------------------
# Config / logging
# --------------------------------------------------------------------------------------

BEIR_DATASET_URL = (
    "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
)

DEFAULT_OUTPUT_ROOT = "resources/beir_datasets"
DEFAULT_CACHE_DIR = "resources/beir_downloads"

log = logging.getLogger("beir2mteb")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download a BEIR dataset and convert it to local MTEB JSONL (retrieval-only).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--dataset",
        default="scifact",
        help="BEIR dataset id (see https://github.com/beir-cellar/beir/wiki/Datasets-available)",
    )
    p.add_argument(
        "--split",
        default="test",
        help="Dataset split: 'train', 'dev', or 'test'. Must match an existing qrels/<split>.tsv",
        choices=["train", "dev", "test"],
    )
    p.add_argument(
        "--out-root",
        default=None,
        help=f"Root directory for outputs. Final path is <out_root>/<dataset>/<split>/. Default: <repo>/{DEFAULT_OUTPUT_ROOT}",
    )
    p.add_argument(
        "--cache-dir",
        default=None,
        help=f"Directory to download/unzip BEIR datasets. Default: <repo>/{DEFAULT_CACHE_DIR}",
    )
    p.add_argument("--overwrite", action="store_true", help="Overwrite output files if they already exist")
    p.add_argument("--max-docs", type=int, default=0, help="Cap number of documents (0 = no cap)")
    p.add_argument("--max-queries", type=int, default=0, help="Cap number of queries (0 = no cap)")
    p.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g., DEBUG, INFO, WARNING, ERROR)",
    )
    p.add_argument(
        "--preserve-doc-order",
        action="store_true",
        help=(
            "Write corpus.jsonl in the same order documents first appear in qrels. "
            "Requires --max-docs > 0 to bound memory; otherwise it is rejected."
        ),
    )
    p.add_argument(
        "--include-nonpositive",
        action="store_true",
        help=(
            "Include non-positive labels (rating <= 0) in candidates.jsonl. "
            "queries.jsonl will still only include queries that have at least one positive (rating > 0) pair."
        ),
    )
    return p.parse_args()


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
        datefmt="-%Y-%m-%d %H:%M:%S",
    )


# --------------------------------------------------------------------------------------
# BEIR download helpers
# --------------------------------------------------------------------------------------

def _import_beir_util():
    try:
        from beir import util  # type: ignore
    except Exception as e:
        log.error(
            "BEIR is required to download datasets. Install with 'pip install beir'. Error: %s",
            e,
        )
        raise SystemExit(1)
    return util


def _download_dataset(dataset: str, cache_dir: Path) -> Path:
    util = _import_beir_util()
    url = BEIR_DATASET_URL.format(dataset=dataset)
    log.info("Downloading dataset '%s' from %s → %s", dataset, url, cache_dir)
    try:
        data_path = util.download_and_unzip(url, str(cache_dir))
        return Path(data_path)
    except Exception as e:
        log.error("Failed to download/unzip '%s': %s", dataset, e)
        raise SystemExit(1)


# --------------------------------------------------------------------------------------
# IO utilities
# --------------------------------------------------------------------------------------

def _resolve_paths(dataset: str, split: str, out_root_arg: Optional[str], cache_dir_arg: Optional[str]) -> Tuple[Path, Path, Path, Path, Path, Path]:
    """
    Resolve repo root, output root, output dir (dataset/split), and file paths.
    Returns: (repo_root, out_root, out_dir, corpus_path, queries_path, candidates_path, cache_dir)
    """
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parent

    out_root = Path(out_root_arg) if out_root_arg else (repo_root / DEFAULT_OUTPUT_ROOT)
    out_dir = out_root / dataset / split
    out_dir.mkdir(parents=True, exist_ok=True)

    corpus_path = out_dir / "corpus.jsonl"
    queries_path = out_dir / "queries.jsonl"
    candidates_path = out_dir / "candidates.jsonl"

    cache_dir = Path(cache_dir_arg) if cache_dir_arg else (repo_root / DEFAULT_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)

    return repo_root, out_root, out_dir, corpus_path, queries_path, candidates_path, cache_dir


def _beir_input_paths(data_path: Path, split: str) -> Tuple[Path, Path, Path]:
    """
    Validates and returns input file paths for a BEIR dataset.
    """
    base = Path(data_path)
    corpus_in = base / "corpus.jsonl"
    queries_in = base / "queries.jsonl"
    qrels_in = base / "qrels" / f"{split}.tsv"

    for p, label in ((corpus_in, "corpus"), (queries_in, "queries"), (qrels_in, f"qrels/{split}")):
        if not p.exists():
            log.error("BEIR %s file not found: %s", label, p)
            raise SystemExit(1)

    return corpus_in, queries_in, qrels_in


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------

def _pick(row: dict, keys: Iterable[str]) -> Optional[str]:
    for k in keys:
        v = row.get(k)
        if v is not None and v != "":
            return str(v)
    return None


def _norm_str(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "\n".join(str(x) for x in v if x is not None)
    return str(v)


def _normalize_doc(row: dict) -> Tuple[str, str]:
    title = _norm_str(row.get("title", ""))
    text = _norm_str(row.get("text") or row.get("abstract") or row.get("contents") or row.get("body") or "")
    return title, text


def _parse_int(v: Optional[str]) -> int:
    if v is None:
        return 0
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            return 0


# --------------------------------------------------------------------------------------
# Pass 1: collect keep sets from qrels (deterministic by encounter order)
# --------------------------------------------------------------------------------------

def _collect_keep_sets(
    qrels_path: Path,
    max_queries: int,
    max_docs: int,
) -> Tuple[Optional[Set[str]], Optional[Set[str]], int, Optional[list[str]]]:
    """
    Reads qrels and determines which query/doc ids to keep based on caps.
    Returns:
      keep_qids (or None if uncapped),
      keep_doc_ids (or None if uncapped),
      initial_pairs count,
      doc_ids_order (list preserving first-encounter doc order if max_docs > 0 else None).
    """
    initial_pairs = 0
    keep_qids: Optional[Set[str]] = set() if max_queries > 0 else None

    track_docs = max_docs > 0
    doc_ids_order: Optional[list[str]] = [] if track_docs else None
    doc_seen: Optional[Set[str]] = set() if track_docs else None

    with qrels_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            initial_pairs += 1

            qid = _pick(row, ("query-id", "qid", "query_id", "query"))
            doc_id = _pick(row, ("corpus-id", "doc-id", "doc_id", "document_id", "doc"))

            if not qid or not doc_id:
                continue

            if keep_qids is not None:
                if qid not in keep_qids:
                    if len(keep_qids) < max_queries:
                        keep_qids.add(qid)
                    else:
                        # query cap reached → ignore this pair entirely (no doc tracking)
                        continue

            if track_docs and doc_ids_order is not None and doc_seen is not None:
                if doc_id not in doc_seen:
                    doc_seen.add(doc_id)
                    doc_ids_order.append(doc_id)

    keep_doc_ids: Optional[Set[str]] = None
    if track_docs and doc_ids_order:
        keep_doc_ids = set(doc_ids_order[:max_docs])

    return keep_qids, keep_doc_ids, initial_pairs, doc_ids_order


# --------------------------------------------------------------------------------------
# Pass 2a: write corpus (streaming, optional reordering)
# --------------------------------------------------------------------------------------

def _write_corpus_stream(
    beir_corpus_in: Path,
    out_corpus: Path,
    max_docs: int,
    keep_doc_ids: Optional[Set[str]],
    preserve_doc_order: bool,
    doc_ids_order: Optional[list[str]],
) -> Tuple[Optional[Set[str]], int]:
    """
    Writes corpus.jsonl. If preserve_doc_order is True, requires max_docs > 0 and uses the order
    provided by doc_ids_order; otherwise it streams BEIR corpus order.
    Returns (written_doc_ids or None, count).
    """
    count = 0

    if preserve_doc_order:
        if max_docs <= 0:
            log.error("--preserve-doc-order requires --max-docs > 0 to bound memory.")
            raise SystemExit(1)
        if not keep_doc_ids or not doc_ids_order:
            log.error("preserve-doc-order requested but no doc ids were selected from qrels.")
            raise SystemExit(1)

        # Collect selected docs into a dict (bounded by --max-docs), then emit in qrels order.
        selected: dict[str, dict] = {}
        with jsonlines.open(beir_corpus_in) as reader:
            for row in reader:
                doc_id = str(row.get("_id") or row.get("id"))
                if doc_id in keep_doc_ids and doc_id not in selected:
                    title, text = _normalize_doc(row)
                    selected[doc_id] = {"id": doc_id, "title": title, "text": text}
                    if len(selected) >= len(keep_doc_ids):
                        break

        with jsonlines.open(out_corpus, mode="w") as writer:
            for did in doc_ids_order:
                if did in selected:
                    writer.write(selected[did])
                    count += 1

        written_ids = set(selected.keys())
        return written_ids, count

    # Streaming path (BEIR corpus order). Track written ids only if needed downstream.
    track_written = keep_doc_ids is not None or max_docs > 0
    written_ids: Optional[Set[str]] = set() if track_written else None

    with jsonlines.open(beir_corpus_in) as reader, jsonlines.open(out_corpus, mode="w") as writer:
        for row in reader:
            doc_id = str(row.get("_id") or row.get("id"))
            if keep_doc_ids is not None and doc_id not in keep_doc_ids:
                continue
            if keep_doc_ids is None and max_docs > 0 and count >= max_docs:
                break
            title, text = _normalize_doc(row)
            writer.write({"id": doc_id, "title": title, "text": text})
            count += 1
            if written_ids is not None:
                written_ids.add(doc_id)

    return written_ids, count


# --------------------------------------------------------------------------------------
# Pass 2b: write qrels → candidates.jsonl (streaming)
# --------------------------------------------------------------------------------------

def _write_candidates_stream(
    qrels_path: Path,
    out_candidates: Path,
    keep_qids: Optional[Set[str]],
    keep_doc_ids: Optional[Set[str]],
    include_nonpositive: bool,
) -> Tuple[int, int, Set[str]]:
    """
    Writes candidates.jsonl and returns:
      (total_pairs_written, positive_pairs_written, qids_with_positive_pairs)
    """
    total_written = 0
    positive_written = 0
    qids_with_positive_pairs: Set[str] = set()

    with qrels_path.open("r", encoding="utf-8") as f, jsonlines.open(out_candidates, mode="w") as writer:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            qid = _pick(row, ("query-id", "qid", "query_id", "query"))
            doc_id = _pick(row, ("corpus-id", "doc-id", "doc_id", "document_id", "doc"))
            if not qid or not doc_id:
                continue

            if keep_qids is not None and qid not in keep_qids:
                continue
            if keep_doc_ids is not None and doc_id not in keep_doc_ids:
                continue

            rating = _parse_int(_pick(row, ("score", "label", "relevance")))
            if include_nonpositive or rating > 0:
                writer.write({"query_id": qid, "doc_id": doc_id, "rating": rating})
                total_written += 1
                if rating > 0:
                    positive_written += 1
                    qids_with_positive_pairs.add(qid)
            else:
                # Non-positive pair skipped from output when include_nonpositive=False
                # but still considered for capping order earlier (by design).
                continue

    return total_written, positive_written, qids_with_positive_pairs


# --------------------------------------------------------------------------------------
# Pass 2c: write queries (streaming)
# --------------------------------------------------------------------------------------

def _write_queries_stream(
    beir_queries_in: Path,
    out_queries: Path,
    keep_qids: Set[str],
) -> int:
    """
    Writes queries.jsonl for the given set of keep_qids (queries having ≥1 positive pair).
    Returns the number of queries written.
    """
    count = 0
    with jsonlines.open(beir_queries_in) as reader, jsonlines.open(out_queries, mode="w") as writer:
        for row in reader:
            qid = str(row.get("_id") or row.get("id"))
            if qid in keep_qids:
                writer.write({"id": qid, "text": str(row.get("text", ""))})
                count += 1
    return count


# --------------------------------------------------------------------------------------
# Manifest (reproducibility)
# --------------------------------------------------------------------------------------

def _write_manifest(
    out_dir: Path,
    *,
    dataset: str,
    split: str,
    max_docs: int,
    max_queries: int,
    counts: dict,
    include_nonpositive: bool,
    preserve_doc_order: bool,
    out_root: Path,
    cache_dir: Path,
) -> None:
    manifest = {
        "dataset": dataset,
        "split": split,
        "output": {
            "root": str(out_root),
            "dir": str(out_dir),
            "files": ["corpus.jsonl", "queries.jsonl", "candidates.jsonl", "manifest.json"],
        },
        "caps": {"max_docs": max_docs, "max_queries": max_queries},
        "flags": {
            "include_nonpositive": include_nonpositive,
            "preserve_doc_order": preserve_doc_order,
        },
        "counts": counts,
        "cache_dir": str(cache_dir),
        "beir_source_url": BEIR_DATASET_URL.format(dataset=dataset),
        "notes": (
            "Document subset is determined by first encounter order in qrels. "
            "When preserve_doc_order=True and max_docs>0, corpus.jsonl is emitted in that qrels order."
        ),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()
    _setup_logging(args.log_level)

    if args.max_docs < 0 or args.max_queries < 0:
        log.error("max-docs and max-queries must be >= 0 (got %s, %s)", args.max_docs, args.max_queries)
        raise SystemExit(1)

    (
        repo_dir,
        out_root,
        out_dir,
        corpus_path,
        queries_path,
        candidates_path,
        cache_dir,
    ) = _resolve_paths(args.dataset, args.split, args.out_root, args.cache_dir)

    # Safety: avoid accidental overwrite unless explicitly requested
    if not args.overwrite and any(p.exists() for p in (corpus_path, queries_path, candidates_path, out_dir / "manifest.json")):
        log.error("Output files already exist in %s. Use --overwrite to replace them.", out_dir)
        raise SystemExit(1)

    # Download (or reuse) dataset
    data_path = _download_dataset(args.dataset, cache_dir)
    beir_corpus_in, beir_queries_in, beir_qrels_in = _beir_input_paths(data_path, args.split)

    # Pass 1: collect keep sets (deterministic)
    keep_qids_pre, keep_doc_ids_pre, initial_pairs, doc_ids_order = _collect_keep_sets(
        beir_qrels_in, args.max_queries, args.max_docs
    )
    if keep_qids_pre is not None:
        log.info("Capping queries to first %d by qrels order", len(keep_qids_pre))
    if keep_doc_ids_pre is not None:
        log.info("Capping documents to first %d by qrels encounter order", len(keep_doc_ids_pre))

    # Pass 2a: corpus
    keep_doc_ids_actual, corpus_count = _write_corpus_stream(
        beir_corpus_in,
        corpus_path,
        args.max_docs,
        keep_doc_ids=keep_doc_ids_pre,
        preserve_doc_order=args.preserve_doc_order,
        doc_ids_order=doc_ids_order,
    )

    # Pass 2b: candidates (qrels)
    candidates_total, candidates_positive, qids_with_positive = _write_candidates_stream(
        beir_qrels_in,
        candidates_path,
        keep_qids_pre,
        keep_doc_ids_actual,
        include_nonpositive=args.include_nonpositive,
    )
    if candidates_total == 0:
        log.error("No candidate pairs after filtering/capping.")
        raise SystemExit(1)

    # Pass 2c: queries (only those with ≥1 positive pair)
    queries_count = _write_queries_stream(beir_queries_in, queries_path, qids_with_positive)

    counts = {
        "qrels_pairs_total": initial_pairs,
        "candidate_pairs_written_total": candidates_total,
        "candidate_pairs_written_positive": candidates_positive,
        "corpus_docs_written": corpus_count,
        "queries_with_positive_pairs": queries_count,
    }

    _write_manifest(
        out_dir,
        dataset=args.dataset,
        split=args.split,
        max_docs=args.max_docs,
        max_queries=args.max_queries,
        counts=counts,
        include_nonpositive=args.include_nonpositive,
        preserve_doc_order=args.preserve_doc_order,
        out_root=out_root,
        cache_dir=cache_dir,
    )

    log.info(
        "Done. corpus=%d, queries(with ≥1 positive)=%d, candidates(total)=%d, positives=%d (from qrels total=%d)",
        corpus_count,
        queries_count,
        candidates_total,
        candidates_positive,
        initial_pairs,
    )


if __name__ == "__main__":
    main()
