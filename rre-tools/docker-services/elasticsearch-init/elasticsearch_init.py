"""
elasticsearch_init.py
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Any

import requests

HOST_ENDPOINT = os.getenv("ELASTICSEARCH_ENDPOINT", "http://elasticsearch:9200")
INDEX_NAME = os.getenv("INDEX_NAME", "testcore")
INDEX_ENDPOINT = HOST_ENDPOINT + "/" + INDEX_NAME
DATASET = os.getenv("DATASET", "/opt/rre-dataset-generator/data/dataset.jsonl")

EMBEDDINGS_FOLDER = "/opt/rre-dataset-generator/embeddings"
os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)

EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_FOLDER, "documents_embeddings.jsonl")
TMP_FILE = os.getenv("TMP_FILE", "/tmp/merged_dataset.json")

DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "600"))
FORCE_REINDEX = os.getenv("FORCE_REINDEX", "false").lower() == "true"
INDEX_BATCH_SIZE = 1000

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("elasticsearch_init")


def wait_for_elasticsearch(host_endpoint: str, timeout: int, interval: float = 1.0) -> None:
    """Waits until Elasticsearch /_cluster/health returns 200."""
    health_url = f"{host_endpoint.rstrip('/')}/_cluster/health"

    log.info("Waiting for Elasticsearch at %s ...", health_url)

    for attempt in range(timeout):
        try:
            response = requests.get(health_url, timeout=timeout)
            if response.ok:
                log.info("Elasticsearch is ready (attempt %d)", attempt + 1)
                return
        except requests.RequestException:
            pass
        log.debug("  ...still waiting (%d/%d)", attempt + 1, timeout)
        time.sleep(interval)
    raise RuntimeError(f"Elasticsearch did not become ready after {timeout} seconds: {health_url}")


def create_index(index_endpoint: str, timeout: int) -> None:
    """Creates index if doesn't exist else skips"""
    try:
        if requests.head(index_endpoint, timeout=timeout).ok:
            log.info("Index already exists at %s. Skipping creation.", index_endpoint)
            return
    except requests.RequestException:
        pass

    payload = {"settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}}}

    log.info("Creating index at %s ...", index_endpoint)
    try:
        response = requests.put(index_endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        log.info("Index created successfully, %s", index_endpoint)
    except requests.RequestException as e:
        log.error("Failed to create index: %s", e)
        raise


def get_count(index_endpoint: str, timeout: int) -> int:
    """Returns count from Elasticsearch /_count endpoint or 0 in case of exception."""
    count_url = f"{index_endpoint.rstrip('/')}/_count"

    params: dict[str, Any] = {"q": "*:*"}
    try:
        response = requests.get(count_url, params=params, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        return int(body.get("count", 0))
    except Exception as e:
        log.warning("Unable to get _count endpoint from Elasticsearch: %s", e)
        return 0


def load_dataset_to_dict(path: str) -> list[dict[str, Any]]:
    """Loads dataset from jsonl file to dict (no embeddings)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset file is not found: {path}")
    data = []
    with p.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def load_embeddings_to_dict(path: str) -> dict[str, list[float]]:
    """
    Loads embeddings from jsonl file to dict. Each line: {"id":"...","vector":[...] }
    Returns dict of (id, [vector])
    """
    vectors: dict[str, list[float]] = {}
    p = Path(path)
    if not p.exists():
        log.info("Embeddings file not found: %s", path)
        return vectors
    with p.open("r", encoding="utf-8") as file:
        for i, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                _id = row.get("id")
                vector = row.get("vector")
                if _id and isinstance(vector, list):
                    vectors[str(_id)] = vector
                else:
                    log.debug("Skipping embeddings line %d: missing id or vector", i)
            except json.JSONDecodeError:
                log.warning("Skipping invalid JSON line %d in embeddings file", i)
    log.info("Loaded %d embeddings from %s", len(vectors), path)
    return vectors


def round_vector(vector: list[float], digits: int = 12) -> list[float]:
    """Rounds each value in the vector to digits=12 decimals."""
    return [round(float(x), digits) for x in vector]


def merge_docs_with_embeddings(docs: list[dict[str, Any]], embeddings: dict[str, list[float]],
                               output_path: Optional[str] = None) -> list[dict[str, Any]]:
    """ Merges two dicts one containing the doc fields e.g. title, context, etc.
    while the other one contains <id, vector> fields"""
    merged = []
    for d in docs:
        doc = dict(d)
        doc_id = str(doc.get("id"))
        if not doc_id:
            log.debug("Document missing id")

        vector = embeddings.get(doc_id)
        if vector is not None:
            doc["vector"] = round_vector(vector, digits=12)
        merged.append(doc)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(merged, file, ensure_ascii=False)
        log.info("Wrote merged dataset to %s", output_path)
    return merged


def get_embedding_dimension(embeddings: dict[str, list[float]]) -> Optional[int]:
    """Returns embedding dimension size or None."""
    if not embeddings:
        return None
    # pick first vector
    first = next(iter(embeddings.values()))
    return len(first)


def create_vector_field(index_endpoint: str, dimension: int, timeout: int) -> None:
    """Sends PUT to /_mapping to add a 'vector' field with type dense_vector"""
    mapping_url = f"{index_endpoint.rstrip('/')}/_mapping"

    payload = {
        "properties": {
            "vector": {
                "type": "dense_vector",
                "dims": dimension,
                "index": True,
                "similarity": "cosine",
            }
        }
    }

    log.info("Creating dense_vector field (dimension=%d) at %s", dimension, mapping_url)
    try:
        response = requests.put(mapping_url, json=payload, timeout=timeout)
        if response.status_code >= 400:
            log.error("Failed to update mapping. Status: %s, Body: %s",
                      response.status_code, response.text)
            return

        log.info("Mapping updated successfully (status=%s)", response.status_code)
    except requests.RequestException as e:
        log.error("Failed to update mapping: %s", e)
        raise
    return


def index_documents(host_endpoint: str, index_name: str, docs: list[dict[str, Any]], timeout: int) -> None:
    """Sends documents to Elasticsearch using /_bulk endpoint in batches."""
    total_docs = len(docs)
    if total_docs == 0:
        log.info("No documents provided for indexing.")
        return

    log.info("Indexing %d documents into Elasticsearch index '%s'", total_docs, index_name)

    num_batches = (total_docs + INDEX_BATCH_SIZE - 1) // INDEX_BATCH_SIZE

    bulk_url = f"{host_endpoint.rstrip('/')}/_bulk"

    for i in range(num_batches):
        start_index = i * INDEX_BATCH_SIZE
        end_index = min((i + 1) * INDEX_BATCH_SIZE, total_docs)
        batch = [doc.copy() for doc in docs[start_index:end_index]]

        if not batch:
            continue

        body_lines = []
        for doc in batch:
            metadata = {"index": {"_index": index_name}}

            if "id" in doc:
                metadata["index"]["_id"] = str(doc.pop("id"))

            body_lines.append(json.dumps(metadata))
            body_lines.append(json.dumps(doc))

        payload = "\n".join(body_lines) + "\n"

        log.info(f"Sending Batch {i + 1}/{num_batches} ({len(batch)} docs)")

        try:
            headers = {"Content-Type": "application/x-ndjson"}
            response = requests.post(bulk_url, data=payload, headers=headers, timeout=timeout)
            response.raise_for_status()

            log.debug(f"Batch {i + 1} indexing successful (status={response.status_code})")

        except requests.RequestException as e:
            log.error(f"Failed to index batch {i + 1}: {e}")
            raise Exception(f"Failed during batch {i + 1} indexing.") from e

    log.info(
        "Successfully indexed %d documents in %d batches.", total_docs, num_batches
    )


def main() -> int:
    log.info("Starting elasticsearch_init.py")
    try:
        wait_for_elasticsearch(host_endpoint=HOST_ENDPOINT, timeout=DEFAULT_TIMEOUT, interval=1.0)
    except Exception as e:
        log.error("Elasticsearch is not available: %s", e)
        sys.exit(1)
    create_index(index_endpoint=INDEX_ENDPOINT, timeout=DEFAULT_TIMEOUT)
    count_docs = get_count(index_endpoint=INDEX_ENDPOINT, timeout=DEFAULT_TIMEOUT)
    log.info("Elasticsearch has count = %d docs", count_docs)

    if count_docs == 0 or FORCE_REINDEX:
        docs = load_dataset_to_dict(DATASET)
        embeddings = load_embeddings_to_dict(EMBEDDINGS_FILE)

        if embeddings:
            embedding_dimension = get_embedding_dimension(embeddings)
            if embedding_dimension is None:
                log.error("No valid embeddings detected; aborting embedding merge")
                sys.exit(1)
            log.info("Detected embedding dimension = %d", embedding_dimension)

            merged_docs = merge_docs_with_embeddings(docs, embeddings, output_path=TMP_FILE)
            create_vector_field(index_endpoint=INDEX_ENDPOINT, dimension=embedding_dimension,timeout=DEFAULT_TIMEOUT)

            index_documents(host_endpoint=HOST_ENDPOINT,index_name=INDEX_NAME,
                            docs=merged_docs,timeout=DEFAULT_TIMEOUT)
        else:
            log.info("Using plain dataset without embeddings")
            index_documents(host_endpoint=HOST_ENDPOINT, index_name=INDEX_NAME, docs=docs, timeout=DEFAULT_TIMEOUT)
            Path(TMP_FILE).unlink(missing_ok=True)
    else:
        log.info("Skipping indexing as there are already docs indexed. Use FORCE_REINDEX=true to force re-indexing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
