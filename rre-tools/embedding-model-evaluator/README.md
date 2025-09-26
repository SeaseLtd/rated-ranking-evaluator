# Exact Search Evaluator (ESE)

This tool provide a flexible tool to test a HuggingFace embedding model to ensure that works as expected with exact
vector search.

### Exact Search vs. Approximate Search

- **Approximate Search** uses a proxy to score a subset of documents considered *similar* via a pre-filtering stage. Techniques like ANN (Approximate Nearest Neighbors) rely on precomputed structures in the index (e.g., HNSW, IVF) to accelerate retrieval at the cost of some accuracy.

- **Exact Search**, by contrast here we compute the distance between every query and every document in the dataset (brute-force). This guarantees finding the "true" nearest neighbors (limited to the embedding model precision on the domain), but is computationally expensive and scales worse with dataset size.


### **Input parameters** for configuration file

To be able to run the Exact Search Evaluator, a configuration file must be provided. The go-to way we suggest to take is 
to modify the [configuration file](embedding-model-evaluator/config.yaml) in the 
[embedding-model-evaluator](embedding-model-evaluator) folder.

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