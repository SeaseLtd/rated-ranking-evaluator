# Dataset Generator

This project provides a flexible command-line tool to generate relevance datasets for search evaluation. It can retrieve documents from a search engine, generate synthetic queries, and score the relevance of document-query pairs using LLMs.


## Project Structure

```bash
.
├── README.md                           # This file
├── config.yaml                         # Main configuration file for the dataset generation pipeline
├── main.py                             # CLI entry point for the application
├── Makefile                            # Contains useful commands for development (e.g., make clean, make test)
├── pyproject.toml                      # Project metadata and dependencies
├── queries.txt                         # Optional file with user-provided queries
├── dataset_generator/                  # Core application package
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
│       ├── open_search.py              # Client for OpenSearch
│       ├── solr.py                     # Client for Solr
│       └── vespa.py                    # Client for Vespa
└── tests/                              # Test suite
    ├── e2e/                            # End-to-end tests
    ├── integration/                    # Integration tests
    └── unit/                           # Unit tests
```

## Quickstart

### 1. Installation

- [uv](https://github.com/astral-sh/uv): A fast Python package installer and resolver.
- Python >=3.10

First, create and activate a virtual environment using `uv`:

```bash
# Create the virtual environment in .venv
uv init

# Venv generation
uv venv

# Install all dependencies from pyproject.toml
uv pip install -e '.[dev,test]'

# Activate the venv (Linux/macOS)
source .venv/bin/activate
```


### 2. Configuration

Create a `config.yaml` file in the root directory. This file controls the entire generation process. E.g:

```yaml
# config.yaml

# Template for search engine queries
queryTemplate: "{query_text}"

# Search engine configuration
searchEngineType: "Solr" # or Elastic, Opensearch, Vespa
searchEngineCollectionEndpoint: "http://localhost:8983/solr/my_core"
documentsFilter: "*:*" # Filter to apply when fetching documents
docNumber: 100 # Number of documents to retrieve
docFields: ["title", "content"] # Fields to concatenate for the LLM

# Query generation
queries: "queries.txt" # Optional: path to a file with one query per line
generateQueriesFromDocuments: true # Whether to generate queries from retrieved docs
totalNumQueriesToGenerate: 50 # Number of queries to generate via LLM

# LLM and Output
relevanceScale: "binary" # or "graded"
llmConfigurationFile: "llm_config.json" # Placeholder for LLM settings
outputFormat: "Quepid" # or RRE, MTEB Leaderboard
outputDestination: "./output/" # Directory to save results
outputExplanation: false # Whether the LLM should provide explanations
```

### 4. Running the Generator

Execute the main script via the `typer` CLI, pointing to your configuration file:

```bash
python main.py run --arg1 --arg2 # example --config ./config.yaml --reasoning --save_reasoning
```

The script will then:
1.  Fetch documents from the specified search engine.
2.  Generate or load queries.
3.  Score the relevance for each (document, query) pair.
4.  (Future) Save the output to the specified destination.
