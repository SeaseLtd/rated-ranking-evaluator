# Creating the environment

## Prerequisites (Docker Compose)
Follow the instructions to install Docker Compose on your system: https://docs.docker.com/compose/install/

## Running the search engine

### Running Solr (Standalone)


To run a local Solr test environment using docker-compose:
```bash
cd rre-tools/docker-services/
```

> This environment comes with the default Solr configuration. All text field are preprocessed as seen in the [Schemaless 
mode](https://solr.apache.org/guide/solr/latest/indexing-guide/schemaless-mode.html) from Solr. For further info, run 
the [Solr Admin UI](https://solr.apache.org/guide/solr/latest/getting-started/solr-admin-ui.html) and check the schema 
of your collection.

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

**Note:** for hygiene reasons we recommend building the `Solr` container without cache first:
```bash
docker-compose -f docker-compose.solr.yml build --no-cache
```

### Running OpenSearch (Single Node)

To run a local OpenSearch test environment using docker-compose:
```bash
cd rre-tools/docker-services/
```

Depending on your Docker version, you may need to use `docker compose` instead of `docker-compose`, i.e., 
```bash
docker-compose -f docker-compose.opensearch.yml up --build
```
or
```bash
docker compose -f docker-compose.opensearch.yml up --build
```

This will start 2 services:
 - `opensearch`, available at http://localhost:9200/
 - `opensearch-init`, loads documents (`bulk indexing`) from opensearch-init/data/dataset.jsonl.


### Running Elasticsearch (Single Node)

Similarly to Solr, to run a local Elasticsearch test environment using docker-compose:
```bash
cd rre-tools/docker-services/
```

Depending on your Docker version, you may need to use `docker compose` instead of `docker-compose`, i.e.,
```bash
docker-compose -f docker-compose.elasticsearch.yml up --build 
```
or
```bash
docker compose -f docker-compose.elasticsearch.yml up --build
```

This will start 2 services:
 - `elasticsearch`, available at http://localhost:9200
 - `elasticsearch-init`, loads documents from elasticsearch-init/data/dataset.jsonl only if Elasticsearch doesn't have 
any documents in the index.

## Running the Quepid container

```bash
cd docker-services/
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
