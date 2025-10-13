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
uv run scripts/mteb_retrieval_dataset_generator.py --dataset "nfcorpus" --split "test"

# Expected default output: ./resources/mteb_datasets/nfcorpus/test/
```

> **Note:** The *nfcorpus* dataset is related to an Information Retrieval task.
> Therefore, we must set `task_to_evaluate: "retrieval"` in the configuration file.

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


## Theory Note: Exact Search vs. Approximate Search

* **Approximate Search**
  Selects a subset of *potentially similar* documents using precomputed index structures (ANN, HNSW, IVF, etc.).

  * **Advantage:** Faster retrieval.
  * **Trade-off:** Some accuracy loss.

* **Exact Search**
  Computes the distance between each query and **all** documents in the dataset (brute-force).

  * **Advantage:** Guaranteed to return the true nearest neighbors (limited only by embedding precision).
  * **Drawback:** Computationally expensive and scales poorly for large datasets.
=======
This tool provide a flexible tool to test a HuggingFace embedding model to ensure that works as expected with exact
vector search.

### Exact Vector Search vs. Approximate Vector Search

- **Exact Vector Search**, by contrast here we compute the distance between every query and every document in the dataset (brute-force). This guarantees finding the "true" nearest neighbors (limited to the embedding model precision on the domain), but is computationally expensive and scales worse with dataset size.
- **Approximate Vector Search** uses a proxy to score a subset of documents considered *similar* via a pre-filtering stage. Techniques like ANN (Approximate Nearest Neighbors) rely on precomputed structures in the index (e.g., HNSW, IVF) to accelerate retrieval at the cost of some accuracy.


### **Input parameters** for configuration file

To be able to run the Embedding Model Evaluator, a configuration file must be provided. The go-to way we suggest to take is 
to modify the [configuration file](../../configs/embedding_model_evaluator/default.yaml).

A detailed description of the parameter that you must provide in the configuration file is the following:

> - **model_id**: Model ID for [HuggingFace embedding model](https://huggingface.co/models?other=embeddings)
> - **task_to_evaluate**: Task name that you need to evaluate
>   - accepted values: 
>     - "reranking" (main metric: `MAP`) 
>     - "retrieval" (main metric: `nDCG@10`)
> - **corpus_path**: Path of the `corpus.jsonl` file (e.g., "resources/data/corpus.jsonl"). Format: <id,title,text>.
> - **queries_path**: Path of the `queries.jsonl` file (e.g., "resources/data/queries.jsonl"). Format: <id,text>.
> - **candidates_path**: Path of the `conadidates.jsonl` file (e.g., "resources/data/candidates.jsonl") Format: <query_id,doc_id,rating>.
> - **relevance_scale**: Relevance scale used in candidates dataset for rating field
>   - accepted values: "binary" or "graded", where
>     - binary: 0 (not relevant), 1 (relevant)
>     - graded: 0 (not relevant), 1 (maybe ok), 2 (that’s my result)
> - **output_dest** (Optional): Path to write mteb output, if not given it will be written to resource directory in 
the root folder (e.g., "resources")
> - **embeddings_dest** (Optional): Path to write mteb document and query embeddings, if not given it will be written 
to resources/embeddings directory (e.g., "resources/embeddings")