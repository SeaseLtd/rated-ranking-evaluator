# Dataset Generator

This tool provides a flexible command-line tool to generate relevance datasets for search evaluation. It can retrieve
documents from a search engine, generate synthetic queries, and score the relevance of document-query pairs using LLMs.


## Setup Configuration file

Create a `config.yaml` file in the dataset-generator directory. This file controls the entire generation process. E.g:
```yaml
query_template: "resources/template_solr.json"
search_engine_type: "solr"
collection_name: "testcore"
search_engine_endpoint: "http://localhost:8983/solr/"
documents_filter:
  - genre:
      - "horror"
      - "fantasy"
  - type:
      - "book"
doc_number: 100
doc_fields:
  - "title"
  - "description"
queries: "queries.txt"
generate_queries_from_documents: true
num_queries_needed: 10
relevance_scale: "graded"
llm_configuration_file: "dataset-generator/llm_config.yaml"
output_format: "quepid"
output_destination: "resources/generated_dataset.json"
```

We might include some more detailed explanation for each param.

Fill [LLM configutation file](llm_config.yaml) with your information and create the [.env](.env) file with your own API 
key.
