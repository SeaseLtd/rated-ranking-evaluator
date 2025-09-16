# Dataset Builder Scripts

Utilities to materialize retrieval datasets into the JSONL format consumed by `embedding-model-evaluator`.

Outputs follow a consistent structure:

```
<out_root>/<dataset>/<split>/
  ├─ corpus.jsonl      # {id: str, title: str, text: str}
  ├─ queries.jsonl     # {id: str, text: str}  (only queries with ≥1 positive)
  ├─ candidates.jsonl  # {query_id: str, doc_id: str, rating: int}
  └─ manifest.json     # metadata, caps, counts, notes
```

## Scripts

- build_beir_dataset.py — Download a BEIR dataset and convert it.
- build_mteb_dataset.py — Load an MTEB dataset from Hugging Face and export it.

Both are cross-platform (Python + pathlib). Run with either `python` or `uv`.

## Prerequisites

- Python 3.10+
- Install this package (and its extras) within the repo:
  - Using uv (recommended):
    - From the repo root: `uv sync`
  - Using pip (local dev):
    - `pip install -e rre-tools/embedding-model-evaluator`

This will install required deps: `jsonlines`, `datasets`, `rank-bm25` (optional), `beir` (for BEIR script).

## MTEB exporter

Default out root: `embedding-model-evaluator/resources/mteb_datasets`.

Examples:

- Minimal export (ArguAna test split):
  ```bash
  python scripts/build_mteb_dataset.py --dataset arguana --split test
  ```

- Add random negatives (100 per query), deterministic:
  ```bash
  python scripts/build_mteb_dataset.py \
    --dataset arguana --split test \
    --negative-policy random --negatives-per-query 100 --rng-seed 42
  ```

- BM25 negatives with safeguards (falls back to random if corpus too large or rank_bm25 missing):
  ```bash
  python scripts/build_mteb_dataset.py \
    --dataset arguana --split test \
    --negative-policy bm25 --bm25-k1 1.5 --bm25-b 0.75
  ```

- Custom output directory:
  ```bash
  python scripts/build_mteb_dataset.py --dataset arguana --split test --out-root /tmp/mteb
  ```

Common flags:
- `--max-docs`, `--max-queries` (0 = no cap). Caps are deterministic by qrels encounter order.
- `--overwrite` to replace existing outputs.

## BEIR exporter

Default out root: `resources/beir_datasets` relative to the current working directory. When run from this folder, it will be `embedding-model-evaluator/resources/beir_datasets`.

Examples:

- Download and convert SciFact (test split):
  ```bash
  python scripts/build_beir_dataset.py --dataset scifact --split test --overwrite
  ```

- Custom caches/paths:
  ```bash
  python scripts/build_beir_dataset.py \
    --dataset scifact --split test \
    --out-root ./resources/beir_datasets \
    --cache-dir ./resources/beir_downloads \
    --overwrite
  ```

## Notes & tips

- Determinism: pass `--rng-seed` (MTEB exporter) when using random negatives.
- BM25 negatives: requires `rank_bm25`. If not available or the corpus size is above `--negative-index-max-docs`, the script will fall back to random negatives.
- `manifest.json` mirrors the BEIR exporter style and includes counts, caps, and notes.
- The exporters perform light referential integrity checks and warn on suspicious situations (e.g., duplicates, missing docs/queries after caps). Use `--log-level DEBUG` for more details.

## Troubleshooting

- "Outputs exist": use `--overwrite` or change `--out-root`.
- "Dataset not found": verify dataset name (`--dataset`) and split (`--split`).
- Windows PowerShell: quote paths with spaces, e.g., `--out-root "C:\\temp\\mteb"`.
- Network: both scripts download data from the internet (Hugging Face or BEIR URLs). Ensure connectivity and credentials if needed.

## License

Apache 2.0
