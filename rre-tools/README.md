# Rated Ranking Evaluator Tools (RRE)

## Overview
- Dataset Generator
- Embedding Model Evaluator
- Approximate Search Evaluator

### [Dataset Generator](dataset-generator/README.md) (DAGE)

This tool provides a flexible command-line tool to generate relevance datasets for search evaluation. It can retrieve
documents from a search engine, generate synthetic queries, and score the relevance of document-query pairs using LLMs.

### [Embedding Model Evaluator](embedding-model-evaluator/README.md)

This tool provide a flexible tool to test a HuggingFace embedding model to ensure that works as expected with exact
vector search.

### Approximate Search Evaluator

This tool provide a flexible tool to deply RRE and extract metrics to test your search engine collection given a 
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

# install optional dev dependencies such as mypy/ruff
uv sync --extra dev
```

## Running Dataset Generator (DAGE)

Before running the command below, you need to have running search engine instance 
(`solr`/`opensearch`/`elasticsearch`/`vespa`). This can be done even with the test collections in folder 
[docker-services](docker-services/README.md). 

For a detailed description to fill your configuration file (e.g., [Config](dataset-generator/config.yaml)) you can look 
at the Dataset Generator [README](dataset-generator/README.md).

Execute the main script via CLI, pointing to your DAGE configuration file:
```bash
uv run dataset-generator --config_file <path-to-DAGE-config-yaml>
```
To know more about all the possible CLI parameters, execute:
```bash
uv run dataset-generator --help
```

## Running Embedding Model Evaluator

For a detailed description to fill in configuration file (e.g., [Config](embedding-model-evaluator/config.yaml)) you can look 
at the [README](embedding-model-evaluator/README.md).

Execute the main script via CLI, pointing to configuration file:
```bash
uv run embedding-model-evaluator --config <path-to-config-yaml>
```

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

### Configuration Files
- `ruff.toml`: Configures Ruff's linting rules and settings
- `mypy.ini`: Configures Mypy's type checking settings

### Type checker with mypy

To run mypy type checks inside the environment use
```bash
uv run mypy .
```

### Code linter with ruff

To run ruff linter inside the environment use
```bash
uv run ruff check
```