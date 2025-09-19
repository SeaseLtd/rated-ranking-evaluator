# Exact Search Evaluator

## Installing and Use

```bash
# create env if don't exists
uv venv .venv

# activate env
source .venv/bin/activate

# install dependencies (editable mode - for devs)
uv pip install -e . 

# install dependencies (for users)
uv sync

# install optional dev dependencies such as mypy/ruff
uv sync --extra dev

cd embedding-model-evaluator

# Generate a mteb dataset in the ingestion format for BEIR
# default output:  ./resources/mteb_datasets/arguana/train/
uv run scripts/mteb_retrieval_dataset_generator.py --dataset "arguana" --split "train"

## arguana dataset is related to an IR task, so for running the main pipeline
## in this case we need to set the task_to_evaluate to "retrieval" in the configuration file

# Run exact search evaluator with  yaml config file
uv run embedding-model-evaluator --config "config.yaml"
```
> "mteb_retrieval_dataset_generator" CLI params:
scripts/mteb_retrieval_dataset_generator.py

> "embedding-model-evaluator" config parameters:
- embedding model name (list)
- dataset metadata (list - name, path or url)
- task_to_evaluate (internal mapping (name-id)? EG: {"Retrieval:0, Rerank: 1..}, or flat. Eg: "Retrieval", "Rerank"..)


## Code Quality Tools

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and [Mypy](https://mypy.readthedocs.io/) for static type checking to maintain code quality and consistency.

### Running Code Quality Checks

#### Linting with Ruff
```bash
# Check for issues
ruff check .

# Auto-fix fixable issues
ruff check --fix .

# Format code (if formatter is enabled)
ruff format .
```

#### Type Checking with Mypy
```bash
# Run type checking
mypy .
```

### Configuration Files
- `ruff.toml`: Configures Ruff's linting rules and settings
- `mypy.ini`: Configures Mypy's type checking settings

> **Theory Note: Exact Search vs. Approximate Search**

- **Approximate Search** uses a proxy to score a subset of documents considered *similar* via a pre-filtering stage. Techniques like ANN (Approximate Nearest Neighbors) rely on precomputed structures in the index (e.g., HNSW, IVF) to accelerate retrieval at the cost of some accuracy.

- **Exact Search**, by contrast here we compute the distance between every query and every document in the dataset (brute-force). This guarantees finding the "true" nearest neighbors (limited to the embedding model precision on the domain), but is computationally expensive and scales worse with dataset size.
