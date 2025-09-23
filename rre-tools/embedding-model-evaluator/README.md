# Embedding Model Evaluator

## Installation and Usage

```bash
# Create virtual environment (if it doesn’t exist)
uv venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies in editable mode (for development)
uv pip install -e .

# Install dependencies (for end users)
uv sync

# Install optional development dependencies (mypy, ruff, etc.)
uv sync --extra dev
```

### Generate an MTEB Dataset in IR Task Format

```bash
cd embedding-model-evaluator

# Generate an MTEB dataset in IR task format
uv run scripts/mteb_retrieval_dataset_generator.py \
    --dataset "arguana" \
    --split "train"

# Expected default output: ./resources/mteb_datasets/arguana/train/
```

> **Note:** The *arguana* dataset is related to an Information Retrieval task.
> Therefore, set `task_to_evaluate: "retrieval"` in the configuration file.

### Run the Exact Search Evaluator with a YAML Config

```bash
uv run embedding-model-evaluator --config "config.yaml"
```

---

## `mteb_retrieval_dataset_generator` CLI Parameters - IR dataset

**Required**

* `--dataset`: MTEB dataset name (e.g. `"scifact"`)
* `--split`: Dataset split to export (default `"test"`, others: `"train"`, `"dev"`)

**Optional**

* `--out-root`: Output directory (default `resources/mteb_datasets`)
* `--overwrite`: Overwrite existing outputs (default `False`)
* `--max-docs`: Maximum number of documents to export (0 = no limit)
* `--max-queries`: Maximum number of queries to export (0 = no limit)
* `--negatives-per-query`: Number of random negatives per query (0 = disabled)
* `--seed`: Random seed (default 42)

**Note:** by default the qrels.json of IR dataset **does not** include negative samples -> if we want to include them (simple negative-mining), we need to use the `--negatives-per-query` parameter.
---

## `embedding-model-evaluator` Config Parameters - IR dataset

**Required**

* `model_id`: Hugging Face Model ID (e.g. `"sentence-transformers/all-MiniLM-L6-v2"`)
* `task_to_evaluate`: `"retrieval"` or `"reranking"`
* `corpus_path`: path to `corpus.jsonl`
* `queries_path`: path to `queries.jsonl`
* `candidates_path`: path to `candidates.jsonl`
* `relevance_scale`: `"binary"` or `"graded"`
* `dataset_name`: custom dataset name

**Optional**

* `split`: dataset split (default `"test"`, others: `"train"`, `"dev"`)
* `output_dest`: directory for evaluation results
* `embeddings_dest`: directory to save embeddings

---

## Code Quality Tools

This project uses:

* [Ruff](https://github.com/astral-sh/ruff) for linting.
* [Mypy](https://mypy.readthedocs.io/) for static type checking.

### Linting with Ruff

```bash
# Check for issues
ruff check .

# Auto-fix fixable issues
ruff check --fix .

# Format code (if enabled)
ruff format .
```

### Type Checking with Mypy

```bash
# Run type checking
mypy .
```

**Config Files**

* `ruff.toml`: Ruff linting rules and settings.
* `mypy.ini`: Mypy type checking rules and settings.

---

## Theory Note: Exact Search vs. Approximate Search

* **Approximate Search**
  Selects a subset of *potentially similar* documents using precomputed index structures (ANN, HNSW, IVF, etc.).

  * **Advantage:** Faster retrieval.
  * **Trade-off:** Some accuracy loss.

* **Exact Search**
  Computes the distance between each query and **all** documents in the dataset (brute-force).

  * **Advantage:** Guaranteed to return the true nearest neighbors (limited only by embedding precision).
  * **Drawback:** Computationally expensive and scales poorly for large datasets.
