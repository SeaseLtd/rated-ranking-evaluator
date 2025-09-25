# Exact Search Evaluator

This tool provide a flexible tool to test a HuggingFace embedding model to ensure that works as expected with exact
vector search.

> **Exact Search vs. Approximate Search**

- **Approximate Search** uses a proxy to score a subset of documents considered *similar* via a pre-filtering stage. Techniques like ANN (Approximate Nearest Neighbors) rely on precomputed structures in the index (e.g., HNSW, IVF) to accelerate retrieval at the cost of some accuracy.

- **Exact Search**, by contrast here we compute the distance between every query and every document in the dataset (brute-force). This guarantees finding the "true" nearest neighbors (limited to the embedding model precision on the domain), but is computationally expensive and scales worse with dataset size.


> **Input parameters:**
- embedding model name (list)
- dataset metadata (list - name, path or url)
- task_to_evaluate (internal mapping (name-id)? EG: {"Retrieval:0, Rerank: 1..}, or flat. Eg: "Retrieval", "Rerank"..)
