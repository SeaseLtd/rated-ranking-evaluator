# Approximate Search Evaluator

This tool provide a flexible tool to deply RRE and extract metrics to test your search engine collection given a 
[template](https://github.com/SeaseLtd/rated-ranking-evaluator/wiki/What%20We%20Need%20To%20Provide#query-templates).
The main purpose of this module is to evaluate, given the queries' embeddings computed in 
[Embedding Model Evaluator](../../docs/embedding_model_evaluator/README.md) module. The goal is to test the ANN
(approximate nearest neighbour) algorithm used by the collection enriched with embeddings from the search engine.


## Setup configuration file

Create a [config.yaml](../../configs/dataset_generator/dataset_generator_config.yaml) file (or modify the existing one) 
in the `approximate_search_evaluator` directory. This file contains all the information needed to set up RRE for 
The parameters needed are:

> - **query_template**: Path pointing to a template file for queries with a placeholder for keywords 
> (e.g., "templates/only_vector.json")
> - **search_engine_type**: Type of search engine to use
>   - accepted values:
>     - "solr"
>     - "elasticsearch"
> - **collection_name**: Name of the search engine index/collection (e.g., "testcore", the one used in Docker containers)
> - **search_engine_url**: URL of the search engine (e.g., "http://localhost:8983/solr/")
> - **search_engine_version** (Optional): to see supported releases, take a look at 
> [constants.py](../../src/rre_tools/vector_search_doctor/approximate_search_evaluator/constants.py). By defaults, uses the latest version supported:
> (9.9.0 for Solr and 7.4.2 for Elasticsearch)
> - id_field (Optional): id field for the unique key. Defaults to "id" for Solr and "_id" for Elasticsearch search
> search engines
> - query_placeholder: "$query",
> - **ratings_path** (Optional): Path to the rre ratings file (e.g., "resources/ratings.json"). If not given, the 
> content of the datastore is used.
> - **embeddings_folder** (Optional): (e.g., "resources/embeddings")
> - **output_destination** (Optional): Path where the output dataset will be saved.  Defaults to "resources"