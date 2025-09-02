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
query_template: "q=#$query##&fq=genre:horror&wt=json"
search_engine_type: "solr"
index_name: "testcore"
search_engine_collection_endpoint: "http://localhost:8983/solr/mycore"
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
llm_configuration_file: "llm_config.yaml"
output_format: "quepid"
output_destination: "output/generated_dataset.json"
```

### 3. Running the Generator

Before running the command below, you need to have running search engine instance (`solr`/`opensearch`/`elasticsearch`/`vespa`).


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
docker-compose -f docker-compose.solr.yml up --build
```
If you have Docker Compose v2 installed, use:
```bash
docker compose -f docker-compose.solr.yml up --build
```

This will start 2 services:
 - `solr`, available at http://localhost:8983/solr
 - `solr-init`, loads documents from solr-init/data/dataset.json.


##### Running OpenSearch (Single Node)

To run a local OpenSearch test environment using docker-compose:
```bash
cd tests/integration/
```

Depending on your Docker version, you may need to use `docker compose` instead of `docker-compose`.
If you have Docker Compose v1 installed, use:

```bash
docker-compose -f docker-compose.opensearch.yml up --build
```
If you have Docker Compose v2 installed, use:
```bash
docker compose -f docker-compose.opensearch.yml up --build
```

This will start 2 services:
 - `opensearch`, available at http://localhost:9200/
 - `opensearch-init`, loads documents (`bulk indexing`) from opensearch-init/data/dataset.jsonl.


##### Running Elasticsearch (Single Node)

Similarly to Solr, to run a local Elasticsearch test environment using docker-compose:
```bash
cd tests/integration/
```

Depending on your Docker version, you may need to use `docker compose` instead of `docker-compose`.
If you have Docker Compose v1 installed, use:

```bash
docker-compose -f docker-compose.elasticsearch.yml up --build 
```
If you have Docker Compose v2 installed, use:
```bash
docker compose -f docker-compose.elasticsearch.yml up --build
```

This will start 2 services:
 - `elasticsearch`, available at http://localhost:9200
 - `elasticsearch-init`, loads documents from elasticsearch-init/data/dataset.jsonl only if Elasticsearch doesn't have 
any documents in the index.

## Running the Quepid container

```bash
cd tests/integration/
docker compose -f docker-compose.quepid.yml up -d

# then go to http://localhost/sessions/new and sign up / sign in.
```

This will download the Quepid nightly image and start two containers:
- `quepid_app` (HTTP available at http://localhost on port 80; internal port 5000)
- `quepid_db` (MySQL exposed on port 3306)

Data persists in the Docker volume `integration_quepid_mysql`.

Notes about the nightly Docker Compose setup
- Uses image `o19s/quepid:nightly` (no build step required).
- Both services load environment from `tests/integration/quepid-init/corenv`. See `tests/integration/quepid-init/README.md` for variable details.
- App requires `DATABASE_URL` and `SECRET_KEY_BASE`; optional: `QUEPID_DOMAIN`, `SIGNUP_ENABLED`, `QUEPID_DEFAULT_SCORER`.
- MySQL healthcheck uses `CMD-SHELL` with `-p$$MYSQL_ROOT_PASSWORD` so the password expands inside the container.




## Running code checks

### type checker with mypy

To run mypy type checks inside the dataset generator environment use
```bash
uv run mypy
```

### code linter with ruff

To run ruff linter inside the dataset generator environment use
```bash
uv run ruff check
```