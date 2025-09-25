# RRE tools features

## Quickstart: tools installation

- [uv](https://github.com/astral-sh/uv): A fast Python package installer and resolver. To installation follow instruction 
  [here](https://docs.astral.sh/uv/getting-started/installation/)
- Python >=3.10

First, create a virtual environment using `uv` following the file `pyproject.toml`. To do so, just execute:
```bash
# create env if don't exists
uv venv .venv

# activate env
source .venv/bin/activate

# install dependencies (editable mode - for devs)
uv pip install -e . 

# install dependencies (for users)
uv sync

# install optional dev dependencies such as mypy/ruff
uv sync --extra dev
```

## Running Dataset Generator (DAGE)

Before running the command below, you need to have running search engine instance (`solr`/`opensearch`/`elasticsearch`/`vespa`).

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

## Running Exact Search Evaluator (ESE)

For a detailed description to fill your configuration file (e.g., [Config](embedding-model-evaluator/config.yaml)) you can look 
at the Dataset Generator [README](embedding-model-evaluator/README.md).

Execute the main script via CLI, pointing to your ESE configuration file:
```bash
uv run embedding-model-evaluator --config <path-to-ESE-config-yaml>
```

## [INCOMING] Running Approximate Search Evaluator (ASE) 
Execute the main script via CLI, pointing to your ASE template file (used by RRE to compute desired evaluation metrics):
```bash
uv run approximate-search-evaluator --template <path-to-template-json>
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
4.  (Future) Save the output to the specified destination.


### 2. Integration Tests

> INCOMING


## Code Quality Tools

### Configuration Files
- `ruff.toml`: Configures Ruff's linting rules and settings
- `mypy.ini`: Configures Mypy's type checking settings

### Type checker with mypy

To run mypy type checks inside the dataset generator environment use
```bash
uv run mypy .
```

### Code linter with ruff

To run ruff linter inside the dataset generator environment use
```bash
uv run ruff check
```