# Rated Ranking Evaluator Tools (RRE)

## Overview
- Dataset Generator
- Vector Search Doctor
  - Embedding Model Evaluator
  - Approximate Search Evaluator

### [Dataset Generator](docs/dataset_generator/README.md) 

This tool provides a flexible command-line tool to generate relevance datasets for search evaluation. It can retrieve
documents from a search engine, generate synthetic queries, and score the relevance of document-query pairs using LLMs.

### Vector Search Doctor

This tool helps diagnose and optimize vector search performance by evaluating both embedding models and search 
configurations. It consists of two sub-tools that work together to identify bottlenecks and improve retrieval quality in
your vector search pipeline.

#### [Embedding Model Evaluator](docs/embedding_model_evaluator/README.md)

This sub-tool extends MTEB benchmarking tool to test a HuggingFace embedding model performance on both Retrieval and Reranking
tasks based on custom datasets.

#### [Approximate Search Evaluator](docs/approximate_search_evaluator/README.md)

This sub-tool provides a flexible tool to deply RRE and extract metrics to test your search engine collection given a 
[template](https://github.com/SeaseLtd/rated-ranking-evaluator/wiki/What%20We%20Need%20To%20Provide#query-templates).

## Quickstart: tools installation

- [uv](https://github.com/astral-sh/uv): A fast Python package installer and resolver. To install uv follow the 
instructions [here](https://docs.astral.sh/uv/getting-started/installation/)
- Python=3.10 version is fixed and widely used in the project, see [.python-version file](.python-version)

First, create a virtual environment using `uv` following the file `pyproject.toml`. To do so, just execute:
```bash
# place yourself in the rre-tools folder
cd rre-tools

# install dependencies (for users)
uv sync

# install development dependencies as well (e.g., mypy and ruff)
uv sync --group dev
```

## Running Dataset Generator

Before running the command below, you need to have running search engine instance 
(`solr`/`opensearch`/`elasticsearch`/`vespa`). This can be done even with the test collections in folder 
[docker-services](docker-services/README.md). 

For a detailed description to fill your configuration file (e.g., 
[Config](configs/dataset_generator/dataset_generator_config.yaml)) you can look at the Dataset Generator 
[README](docs/dataset_generator/README.md).

Execute the main script via CLI, pointing to your DAGE configuration file:
```bash
uv run dataset_generator --config <path-to-config-yaml>
```
By default, the CLI is pointing to the 
[file](configs/dataset_generator/dataset_generator_config.yaml) inside the `configs/` directory.

To know more about all the possible CLI parameters, execute:
```bash
uv run dataset_generator --help
```

## Running Embedding Model Evaluator

For a detailed description to fill in configuration file (e.g., 
[Config](configs/embedding_model_evaluator/embedding_model_evaluator_config.yaml)) you can look at the 
[README](docs/embedding_model_evaluator/README.md).

Execute the main script via CLI, pointing to configuration file:
```bash
uv run embedding_model_evaluator --config <path-to-config-yaml>
```
By default, the CLI is pointing to the  
[configs/](configs/embedding_model_evaluator/embedding_model_evaluator_config.yaml) inside the `configs/` directory.

## Running Approximate Search Evaluator
For a detailed description to fill in configuration file (e.g., 
[Config](configs/approximate_search_evaluator/approximate_search_evaluator_config.yaml)) you can look at the 
[README](docs/approximate_search_evaluator/README.md).

```bash
uv run approximate_search_evaluator --config <path-to-config-yaml>
```
By default, the CLI is pointing to the 
[file](configs/approximate_search_evaluator/approximate_search_evaluator_config.yaml) inside the `configs/` directory.

## Running tests

### 1. Unit Tests

Execute `pytest` command as follows:
```bash
uv run pytest
```

The script will then:
1.  Fetch documents from the specified search engine.
2.  Generate or load queries.
3.  Score the relevance for each (document, query) pair.
4.  Save the output to the destination (specified in the config file).

## Code Quality Tools

This project uses:

* [Ruff](https://github.com/astral-sh/ruff) for linting.
* [Mypy](https://mypy.readthedocs.io/) for static type checking.

### Linting with Ruff

```bash
# Check for issues
uv run ruff check .

# Auto-fix fixable issues
uv run ruff check --fix .

# Format code (if enabled)
uv run ruff format .
```

### Type Checking with Mypy

```bash
# Run type checking
uv run mypy .
```

**Config Files**

* `ruff.toml`: Ruff linting rules and settings.
* `mypy.ini`: Mypy type checking rules and settings.

---