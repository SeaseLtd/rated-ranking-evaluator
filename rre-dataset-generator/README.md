# Dataset Generator

This project provides a flexible command-line tool to generate relevance datasets for search evaluation. It can retrieve
documents from a search engine, generate synthetic queries, and score the relevance of document-query pairs using LLMs.

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


### 2. Integration Test

#### Creating the environment

##### Prerequisites (Docker Compose)
Follow the instructions to install Docker Compose on your system: https://docs.docker.com/compose/install/

##### Running Solr (Standalone)


To run a local Solr test environment using docker-compose:
```bash
cd tests/integration/
```

Depending on your Docker version, you may need to use `docker compose` instead of `docker-compose`.
If you have Docker Compose v1 installed, use:

```bash
docker-compose up --build
```
If you have Docker Compose v2 installed, use:
```bash
docker compose up --build
```

This will start 2 services:
 - `solr`, available at http://localhost:8983/solr
 - `solr-init`, loads documents from solr/data/dataset.json only if Solr doesn't index any documents.
