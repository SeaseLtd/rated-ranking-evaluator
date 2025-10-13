#!/usr/bin/env python3
"""
MTEB exporter (HF) → JSONL files suitable for embedding-model-evaluator.

Outputs to <out_root>/<dataset>/<split>/:
- corpus.jsonl     -> {id: str, title: str, text: str}
- queries.jsonl    -> {id: str, text: str}                      # only queries with ≥1 positive
- candidates.jsonl -> {query_id: str, doc_id: str, rating: int} # full qrels (+ optional negatives)
- manifest.json    -> metadata and counts (aligned with BEIR exporter style)

Features:
- Cross-platform (uses pathlib); no shell specifics.
- Deterministic caps by qrels encounter order (if provided).
- Optional synthetic negatives: random with safeguards.
- Light-weight validations and clear logging.
"""

from __future__ import annotations
import json
import logging
import random
import argparse
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Set, Tuple, List

# ========= DEFAULTS / PATHS =========
# Default out root aligned with embedding-model-evaluator/resources/mteb_datasets
DEFAULT_OUT_ROOT = (Path(__file__).resolve().parents[1] / "resources" / "mteb_datasets")
DEFAULT_DATASET = "nfcorpus"
DEFAULT_SPLIT = "test"    # "train" | "dev" | "test"
DEFAULT_OVERWRITE = False
DEFAULT_MAX_QUERIES = 0   # 0 = no cap
DEFAULT_MAX_DOCS = 0      # 0 = no cap

# ---- Negative sampling (minimal) ----
DEFAULT_NEGATIVE_PER_QUERY = 0   # 0 disables negatives
DEFAULT_RNG_SEED = 42

# ===============================================

# ---- dependencies (avoid circular imports) ----
try:
    import jsonlines  # type: ignore
except Exception:
    print("Missing dependency 'jsonlines'. Please install: pip install jsonlines")
    raise
try:
    import datasets  # type: ignore
    from datasets import get_dataset_config_names, get_dataset_split_names
except Exception:
    print("Missing dependency 'datasets'. Please install: pip install datasets")
    raise

log = logging.getLogger("mteb_export_min")

# ------------------------- CLI -------------------------
def parse_args() -> argparse.Namespace:
    """Build and parse CLI arguments (minimal)."""
    p = argparse.ArgumentParser(
        description="Download an MTEB dataset from HF and export to MTEB JSONL (retrieval-only).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dataset", default=DEFAULT_DATASET,
                   help="MTEB dataset name (e.g., arguana). Will resolve to 'mteb/<name>' on HF.")
    p.add_argument("--split", default=DEFAULT_SPLIT, choices=["train", "dev", "test"],
                   help="Split used for queries and qrels. Corpus split is resolved automatically.")
    p.add_argument("--out-root", default=None,
                   help=f"Root output dir (default: {DEFAULT_OUT_ROOT})")
    p.add_argument("--overwrite", action="store_true", default=DEFAULT_OVERWRITE,
                   help="Overwrite existing outputs")
    p.add_argument("--max-docs", type=int, default=DEFAULT_MAX_DOCS, help="0 = no cap")
    p.add_argument("--max-queries", type=int, default=DEFAULT_MAX_QUERIES, help="0 = no cap")
    p.add_argument("--negatives-per-query", type=int, default=DEFAULT_NEGATIVE_PER_QUERY,
                   help="Quota of random negatives to add per kept query (0 disables)")
    p.add_argument("--seed", type=int, default=DEFAULT_RNG_SEED, help="Random seed for determinism")
    return p.parse_args()

# ------------------------- validation -------------------------
def validate_args(args: argparse.Namespace) -> None:
    """Minimal but robust sanity checks for CLI arguments."""
    errs: List[str] = []
    if args.max_docs < 0:
        errs.append("--max-docs must be >= 0")
    if args.max_queries < 0:
        errs.append("--max-queries must be >= 0")
    if args.negatives_per_query < 0:
        errs.append("--negatives-per-query must be >= 0")
    if args.seed < 0:
        errs.append("--seed must be >= 0")
    if errs:
        for e in errs:
            log.error(e)
        raise SystemExit(1)

# ---------- utils ----------
def setup_logging() -> None:
    """Configure root logger at INFO level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def to_string(value: Any) -> str:
    """Convert any value to string safely, returning empty string for None."""
    return "" if value is None else (value if isinstance(value, str) else str(value))

def normalize_text(value: Any) -> str:
    """Normalize text fields handling various data types including lists."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(to_string(x) for x in value if x is not None)
    return to_string(value)

def to_int(value: Any) -> int:
    """Convert any value to integer safely, returning 0 for invalid values.
    Tries direct int conversion first, then float->int, finally defaults to 0.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

def normalize_doc(row: Dict[str, Any]) -> Tuple[str, str]:
    """Normalize common document fields into (title, text)."""
    title = normalize_text(row.get("title") or row.get("Title") or row.get("headline") or row.get("name"))
    text  = normalize_text(row.get("text")  or row.get("abstract") or row.get("contents") or row.get("body"))
    return title, text

def ensure_outputs(out_dir: Path, overwrite: bool) -> Tuple[Path, Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus = out_dir / "corpus.jsonl"
    queries = out_dir / "queries.jsonl"
    candidates = out_dir / "candidates.jsonl"
    manifest = out_dir / "manifest.json"
    if not overwrite and any(p.exists() for p in (corpus, queries, candidates, manifest)):
        log.error("Outputs already exist in %s (set OVERWRITE=True to replace).", out_dir)
        raise SystemExit(1)
    return corpus, queries, candidates, manifest

# ---------- loader adapted to MTEB/HF ----------
class MtebLoader:
    """Thin wrapper over HF datasets for MTEB layout.

    Loads 3 configs (default/corpus/queries) with appropriate splits:
      - default: train/dev/test (qrels)
      - corpus : typically the 'corpus' split (some datasets only expose this)
      - queries: train/dev/test (sometimes only 'test')
    """
    def __init__(self, ds_name: str, split: str):
        self.task_name = ds_name
        self.split = split
        self._load_dataset = datasets.load_dataset
        self.hub_id = self._resolve_hub_id()

    def _resolve_hub_id(self) -> str:
        """Resolve the dataset ID from the task name."""
        # Try exact then lowercase variant
        candidates = (f"mteb/{self.task_name}", f"mteb/{self.task_name.lower()}")
        last_err: Optional[Exception] = None
        for hid in candidates:
            try:
                get_dataset_config_names(hid)
                return hid
            except Exception as e:
                last_err = e
        log.error("Dataset not found on HF for %s. Last error: %s", candidates, last_err)
        if last_err is not None:
            raise last_err
        raise RuntimeError(f"Dataset not found for {candidates}")

    def _pick_split(self, config_name: str, preferred: List[str]) -> str:
        """Pick a split from the dataset."""
        splits = get_dataset_split_names(self.hub_id, config_name)
        for p in preferred:
            if p in splits:
                return p
        if len(splits) == 1:
            return str(splits[0])
        log.error("Split not available for %s/%s. Available splits: %s", self.hub_id, config_name, splits)
        raise SystemExit(1)

    def load_three(self) -> Tuple[Any, Any, Any]:
        """Load the three datasets."""
        # qrels (default)
        qrels_split = self._pick_split("default", [self.split, "test", "dev", "train"])
        qrels   = self._load_dataset(self.hub_id, split=qrels_split)

        # corpus (often only 'corpus' split)
        corpus_split = self._pick_split("corpus", ["corpus", self.split, "test", "dev", "train"])
        corpus  = self._load_dataset(self.hub_id, name="corpus", split=corpus_split)

        # queries
        queries_split = self._pick_split("queries", [self.split, "test", "dev", "train"])
        queries = self._load_dataset(self.hub_id, name="queries", split=queries_split)

        log.info("HF hub_id=%s | splits → default:%s | corpus:%s | queries:%s",
                 self.hub_id, qrels_split, corpus_split, queries_split)
        return corpus, queries, qrels

    # Iterators robust to field name variants
    def iter_corpus(self, corpus_ds: Any) -> Iterator[Dict[str, Any]]:
        """Iterate over the corpus."""
        for row in corpus_ds:
            did = to_string(row.get("_id") or row.get("id"))
            if not did:  # skip malformed
                continue
            title, text = normalize_doc(row)
            yield {"id": did, "title": title, "text": text}

    def iter_queries_ds(self, queries_ds: Any) -> Iterator[Tuple[str, str]]:
        """Iterate over the queries."""
        for row in queries_ds:
            qid = to_string(row.get("_id") or row.get("id") or row.get("query_id") or row.get("qid"))
            if not qid:
                continue
            yield qid, normalize_text(row.get("text", ""))

    def iter_qrels(self, qrels_ds: Any) -> Iterator[Dict[str, Any]]:
        """Iterate over the qrels."""
        for row in qrels_ds:
            qid = to_string(row.get("query-id") or row.get("query_id") or row.get("qid") or row.get("query"))
            did = to_string(row.get("corpus-id") or row.get("doc_id") or row.get("document_id") or row.get("doc") or row.get("corpus_id"))
            if not qid or not did:
                continue
            rating = to_int(row.get("score") or row.get("label") or row.get("relevance") or 0)
            yield {"query_id": qid, "doc_id": did, "rating": rating}

# ---------- negative sampling helper (random only) ----------
def _sample_random(universe: List[str], banned: Set[str], k: int) -> List[str]:
    """Sample k random documents excluding banned documents."""
    avail = [d for d in universe if d not in banned]
    if k <= 0 or not avail:
        return []
    if k >= len(avail):
        random.shuffle(avail)
        return avail
    return random.sample(avail, k)

# ---------- export ----------
def do_export(ds_name: str, split: str, out_root: Path, overwrite: bool, max_q: int, max_d: int, *,
              negatives_per_query: int, rng_seed: int) -> None:
    """Export an MTEB dataset to JSONL files under out_root/dataset/split.

    This preserves all positive pairs, deduplicates candidate pairs, caps via qrels order,
    and optionally appends synthetic negatives per query.
    """
    loader = MtebLoader(ds_name, split)
    corpus_ds, queries_ds, qrels_ds = loader.load_three()

    out_dir = out_root / ds_name / split
    corpus_path, queries_path, candidates_path, manifest_path = ensure_outputs(out_dir, overwrite)

    # -------- Step 1: write qrels into candidates, apply caps & gather stats --------
    keep_q: Optional[Set[str]] = set() if max_q > 0 else None
    keep_d: Optional[Set[str]] = set() if max_d > 0 else None
    pos_q: Set[str] = set()
    pos_docs_by_q: Dict[str, Set[str]] = {}
    neg_count_by_q: Dict[str, int] = {}
    pairs_seen: Set[Tuple[str, str]] = set()
    qrels_total: int = 0
    cand_total: int = 0
    cand_pos: int = 0
    cand_neg: int = 0

    with jsonlines.open(candidates_path, mode="w") as wr:
        for pair in loader.iter_qrels(qrels_ds):
            qid, did = to_string(pair["query_id"]), to_string(pair["doc_id"])
            rating   = int(pair.get("rating", 0))
            qrels_total += 1

            # caps (first time seeing each id until reaching limit)
            if keep_q is not None and qid not in keep_q:
                if len(keep_q) >= max_q:
                    continue
                keep_q.add(qid)
            if keep_d is not None and did not in keep_d:
                if len(keep_d) >= max_d:
                    continue
                keep_d.add(did)

            # dedupe (some datasets can repeat pairs)
            key = (qid, did)
            if key in pairs_seen:
                continue
            pairs_seen.add(key)

            wr.write({"query_id": qid, "doc_id": did, "rating": rating})
            cand_total += 1
            if rating > 0:
                pos_q.add(qid)
                pos_docs_by_q.setdefault(qid, set()).add(did)
                cand_pos += 1
            else:
                neg_count_by_q[qid] = neg_count_by_q.get(qid, 0) + 1
                cand_neg += 1

    if cand_total == 0:
        log.error("No candidate pairs after caps/filters. Check MAX_* or dataset/split.")
        raise SystemExit(1)

    # -------- Step 2: write corpus; also collect IDs (+ tokens if BM25 will be used) --------
    wrote_docs = 0
    seen_docs: Set[str] = set()
    doc_id_list: List[str] = []

    with jsonlines.open(corpus_path, mode="w") as wr:
        for row in loader.iter_corpus(corpus_ds):
            did = to_string(row.get("id"))
            if not did or did in seen_docs:
                continue
            if keep_d is not None and did not in keep_d:
                continue
            seen_docs.add(did)

            title, text = normalize_doc(row)
            wr.write({"id": did, "title": title, "text": text})
            wrote_docs += 1

            doc_id_list.append(did)

    # -------- Step 3: write queries (only those with ≥1 positive & within caps) --------
    wrote_q = 0
    seen_q: Set[str] = set()
    with jsonlines.open(queries_path, mode="w") as wr:
        for qid, qtext in loader.iter_queries_ds(queries_ds):
            if qid not in pos_q:  # only queries with positives
                continue
            if keep_q is not None and qid not in keep_q:
                continue
            if qid in seen_q:
                continue
            wr.write({"id": qid, "text": qtext or ""})
            seen_q.add(qid)
            wrote_q += 1

    # -------- Step 4: add synthetic negatives (policy-driven), appending to candidates --------
    negatives_added = 0
    if negatives_per_query > 0 and wrote_q > 0:
        # Negative candidate pool: restrict to kept docs if a doc cap was used, else all seen docs
        candidate_pool = list(keep_d) if keep_d is not None else list(seen_docs)
        with jsonlines.open(candidates_path, mode="a") as wr:
            for qid in seen_q:
                have_negs = neg_count_by_q.get(qid, 0)
                need = negatives_per_query - have_negs
                if need <= 0:
                    continue

                banned = set(pos_docs_by_q.get(qid, set()))
                # avoid duplicates across the whole file
                banned.update({did for (qq, did) in pairs_seen if qq == qid})

                picks: List[str] = _sample_random(candidate_pool, banned, need)

                # write them with rating=0
                for did in picks:
                    key = (qid, did)
                    if key in pairs_seen:
                        continue
                    wr.write({"query_id": qid, "doc_id": did, "rating": 0})
                    pairs_seen.add(key)
                    negatives_added += 1
                    cand_total += 1
                    cand_neg += 1

    # -------- Step 5: validations (minimal but useful) --------
    missing_docs = missing_queries = 0
    dup_pairs = 0
    # Quick referential integrity re-check by reading candidates once
    seen_pairs_check: Set[Tuple[str, str]] = set()
    with jsonlines.open(candidates_path, mode="r") as rd:
        for pair in rd:
            qid = to_string(pair.get("query_id"))
            did = to_string(pair.get("doc_id"))
            key = (qid, did)
            if key in seen_pairs_check:
                dup_pairs += 1
            else:
                seen_pairs_check.add(key)
            if keep_d is not None and did not in seen_docs:
                missing_docs += 1
            if qid not in seen_q:
                # allow this ONLY if it’s an explicit negative for a query that didn’t pass caps,
                # which we didn’t generate in our pipeline; treat as missing
                missing_queries += 1

    # minimal checks: warn on suspicious outcomes
    if wrote_q == 0:
        log.error("No queries with positive pairs were kept. Check split/dataset or caps.")
        raise SystemExit(1)

    # -------- Step 6: manifest --------
    manifest = {
        "schema": "mteb-export-v1",
        "dataset": ds_name,
        "split": split,
        "output_dir": str(out_dir),
        "files": ["corpus.jsonl", "queries.jsonl", "candidates.jsonl", "manifest.json"],
        "caps": {"max_docs": max_d, "max_queries": max_q},
        "negatives": {
            "used": bool(negatives_per_query > 0),
            "per_query_quota": negatives_per_query,
            "rng_seed": rng_seed,
            "added_total": negatives_added,
        },
        "counts": {
            "qrels_pairs_total": qrels_total,
            "candidate_pairs_total": cand_total,
            "candidate_pairs_positive": cand_pos,
            "candidate_pairs_negative": cand_neg,

            "corpus_docs": wrote_docs,
            "queries_with_positive_pairs": wrote_q,
            "missing_docs_in_candidates_due_to_caps": missing_docs,
            "missing_queries_in_candidates_due_to_caps": missing_queries,
            "duplicate_pairs_detected_posthoc": dup_pairs,
        },
        "hf": {
            "hub_id": loader.hub_id,
        },
        "notes": "Output structure aligned with beir_datasets (dataset/split).",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Final logs
    drop_ratio = (qrels_total - (cand_total - negatives_added)) / qrels_total if qrels_total else 0.0
    if drop_ratio > 0.20:
        log.warning("High drop ratio due to caps: %.1f%%", 100 * drop_ratio)
    log.info(
        "Done. corpus=%d, queries(≥1pos)=%d, candidates=%d (pos=%d, neg=%d), negatives_added=%d, qrels=%d",
        wrote_docs, wrote_q, cand_total, cand_pos, cand_neg, negatives_added, qrels_total
    )
    if missing_docs or missing_queries or dup_pairs:
        log.warning(
            "Post-checks: missing_docs=%d, missing_queries=%d, duplicate_pairs=%d",
            missing_docs, missing_queries, dup_pairs
        )

def main() -> None:
    args = parse_args()
    setup_logging()
    validate_args(args)
    random.seed(args.seed)
    out_root = Path(args.out_root) if args.out_root else DEFAULT_OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    do_export(
        ds_name=args.dataset,
        split=args.split,
        out_root=out_root,
        overwrite=args.overwrite,
        max_q=args.max_queries,
        max_d=args.max_docs,
        negatives_per_query=args.negatives_per_query,
        rng_seed=args.seed,
    )

if __name__ == "__main__":
    main()