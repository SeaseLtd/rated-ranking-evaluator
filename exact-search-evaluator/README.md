# Exact Search Evaluator

> **Exact Search vs. Approximate Search**

- **Approximate Search** uses a proxy to score a subset of documents considered *similar* via a pre-filtering stage. Techniques like ANN (Approximate Nearest Neighbors) rely on precomputed structures in the index (e.g., HNSW, IVF) to accelerate retrieval at the cost of some accuracy.

- **Exact Search**, by contrast here we compute the distance between every query and every document in the dataset (brute-force). This guarantees finding the "true" nearest neighbors (limited to the embedding model precision on the domain), but is computationally expensive and scales worse with dataset size.


> **Input parameters:**
- embedding model name (list)
- dataset metadata (list - name, path or url)
- task_to_evaluate (internal mapping (name-id)? EG: {"Retrieval:0, Rerank: 1..}, or flat. Eg: "Retrieval", "Rerank"..)

## Usage

```bash
# create env if don't exists
uv venv .venv

# activate env
source .venv/bin/activate

# install dependencies
uv pip install -e . 

# now we can run the package entry point with our alias
## ( Check the pyproject.toml line: [project.scripts] exact-search-evaluator = "main:main")
exact-search-evaluator
```

## Proposed usage (Future Work)

### 1. Run exact search evaluator with CLI arguments
```bash
exact-search-evaluator --embedding-model "model_name" --dataset "path_to_dataset" --task-to-evaluate "Retrieval" --output_path "path_to_output"
```


### 2. Run exact search evaluator with  yaml config file
```bash
exact-search-evaluator --config "path_to_config_yaml"
```