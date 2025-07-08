# Dataset Generator

This project provides a flexible command-line tool to generate relevance datasets for search evaluation. It can retrieve
documents from a search engine, generate synthetic queries, and score the relevance of document-query pairs using LLMs.


## Project Structure

```bash
.
├── README.md                           # This file
├── config.yaml                         # Main configuration file for the dataset generation pipeline
├── dataset_generator.py                # CLI entry point for the application
├── Makefile                            # Contains useful commands for development (e.g., make clean, make test)
├── pyproject.toml                      # Project metadata and dependencies
├── queries.txt                         # Optional file with user-provided queries
├── src/                                # Core application package
│   ├── __init__.py                     # Exposes the main DatasetGenerator service
│   ├── cache.py                        # Caching utilities 
│   ├── config.py                       # Pydantic model for parsing and validating config.yaml
│   ├── logger.py                       # Structured logging configuration
│   ├── models.py                       # Pydantic models for internal data structures
│   ├── prompts.py                      # Prompts for the LLM 
│   ├── llm/                            # Sub-package for Large Language Model services
│   │   ├── __init__.py                 # Defines the LLMServiceInterface
│   │   ├── api_llm.py                  # Implementation for API-based LLMs 
│   │   └── local_llm.py                # Implementation for local LLMs 
│   └── search_engine/                  # Sub-package for search engine clients
│       ├── __init__.py                 # Defines the SearchEngineInterface
│       ├── opensearch.py               # Client for OpenSearch
│       ├── solr.py                     # Client for Solr
│       ├── vespa.py                    # Client for Vespa
│       └── elasticsearch.py            # Client for Elasticsearch
└── tests/                              # Test suite
    ├── e2e/                            # End-to-end tests
    ├── integration/                    # Integration tests
    └── unit/                           # Unit tests
```

## Quickstart

### 1. Installation

- [uv](https://github.com/astral-sh/uv): A fast Python package installer and resolver. To installation follow instruction 
  [here](https://docs.astral.sh/uv/getting-started/installation/)
- Python >=3.10

First, create a virtual environment using `uv` following the file `pyproject.toml`. To do so, just execute:
```bash
uv sync
```


### 2. Configuration

Create a `config.yaml` file in the root directory. This file controls the entire generation process. E.g:
```yaml
QueryTemplate: "q=#$query##&fq=genre:horror&wt=json"
SearchEngineType: "Solr"
SearchEngineCollectionEndpoint: "http://localhost:8983/solr/mycore"
documentsFilter:
  - genre:
      - "horror"
      - "fantasy"
  - type:
      - "book"
docNumber: 100
docFields:
  - "title"
  - "body"
queries: "queries.txt"
generateQueriesFromDocuments: true
totalNumQueriesToGenerate: 10
RelevanceScale: "Graded"
LLMConfigurationFile: "llm_config.yaml"
OutputFormat: "Quepid"
OutputDestination: "output/generated_dataset.json"
OutputExplanation: true
```

### 3. Running the Generator

Execute the main script via the `argparse` CLI, pointing to your configuration file:
```bash
uv run dataset_generator.py --config_file config.yaml
```
To know more about all the possible CLI parameters, execute:
```bash
uv run dataset_generator.py --help
```

### 4. Running tests

First thing to do is to check if the environment is active. If not, execute (in Unix based machines) the following 
command to activate it:
```bash
source .venv/bin/activate
```

Now that the environment is active, execute `pytest` command as follows:
```bash
pytest tests/
```

The script will then:
1.  Fetch documents from the specified search engine.
2.  Generate or load queries.
3.  Score the relevance for each (document, query) pair.
4.  (Future) Save the output to the specified destination.
