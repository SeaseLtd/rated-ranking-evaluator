"""
solr_init.py
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Any

import requests

COLLECTION_ENDPOINT = os.getenv("COLLECTION_ENDPOINT", "http://solr:8983/solr/testcore")
DATASET = os.getenv("DATASET", "/opt/rre-dataset-generator/data/dataset.json")

EMBEDDINGS_FOLDER = "/opt/rre-dataset-generator/embeddings"
os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)

EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_FOLDER, "documents_embeddings.jsonl")
TMP_FILE = os.getenv("TMP_FILE", "/tmp/merged_dataset.json")

DEFAULT_TIMEOUT = float(os.getenv("DEFAULT_TIMEOUT", "10.0"))
FORCE_REINDEX = os.getenv("FORCE_REINDEX", "false").lower() == "true"

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("solr_init")


def wait_for_solr_core(endpoint: str, timeout: int = 30, interval: float = 1.0) -> None:
    """Waits until Solr core /admin/ping endpoint returns 200 or timeouts."""
    ping_url = f"{endpoint.rstrip('/')}/admin/ping?wt=json"
    log.info("Waiting for Solr core at %s ...", ping_url)
    for attempt in range(timeout):
        try:
            response = requests.get(ping_url, timeout=DEFAULT_TIMEOUT)
            if response.ok:
                log.info("Core is ready (attempt %d)", attempt + 1)
                return
        except requests.RequestException:
            pass
        log.debug("  ...still waiting (%d/%d)", attempt + 1, timeout)
        time.sleep(interval)
    raise RuntimeError(f"Solr core did not become ready after {timeout} seconds: {ping_url}")


def get_num_found(endpoint: str) -> int:
    """Returns numFound from /select endpoint or 0 in case of exception."""
    select_url = f"{endpoint.rstrip('/')}/select"
    params: dict[str, Any] = {"q": "*:*", "wt": "json", "rows": 0}
    try:
        response = requests.get(select_url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        body = response.json()
        num_found = body.get("response", {}).get("numFound", 0)
        return int(num_found or 0)
    except Exception as e:
        log.warning("Unable to get numFound from Solr: %s", e)
        return 0


def load_dataset_to_dict(path: str) -> list[dict[str, Any]]:
    """Loads dataset (no embeddings) """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    with p.open("r", encoding="utf-8") as file:
        data = json.load(file)
        if isinstance(data, list):
            return data
        else:
            raise ValueError("Expected dataset JSON file to be an array of documents")


def load_embeddings_to_dict(path: str) -> dict[str, list[float]]:
    """
    Loads embeddings from a jsonl file. Each line: {"id":"...","vector":[...] }
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
    """Rounds each value in the vector to digits=12 decimals"""
    return [round(float(x), digits) for x in vector]


def merge_docs_with_embeddings(docs: list[dict[str, Any]], embeddings: dict[str, list[float]],
                               output_path: Optional[str] = None) -> list[dict[str, Any]]:
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


def get_embedding_dimension_size(embeddings: dict[str, list[float]]) -> Optional[int]:
    """Returns embedding dimension size or None"""
    if not embeddings:
        return None
    # pick first vector
    first = next(iter(embeddings.values()))
    return len(first)


def create_vector_field(endpoint: str, dimension: int) -> None:
    """
    Sends POST to /schema endpoint to add a DenseVectorField and a field "vector".
    """
    schema_url = f"{endpoint.rstrip('/')}/schema"
    payload = {
        "add-field-type": {
            "name": "knn_vector",
            "class": "solr.DenseVectorField",
            "vectorDimension": dimension,
            "similarityFunction": "cosine",
            "knnAlgorithm": "hnsw"
        },
        "add-field": {
            "name": "vector",
            "type": "knn_vector",
            "indexed": True,
            "stored": True
        }
    }
    log.info("Creating vector field (dimension=%d) at %s", dimension, schema_url)
    try:
        response = requests.post(schema_url, json=payload, timeout=DEFAULT_TIMEOUT)
        if response.status_code >= 400:
            log.debug("Response (status=%s)", response.status_code)
            return
        log.info("Schema updated successfully (status=%s)", response.status_code)
    except requests.RequestException as e:
        log.error("Failed to update schema: %s", e)
        raise
    return


def index_documents(endpoint: str, docs: list[dict[str, Any]]) -> None:
    """
    Sends documents to /update endpoint and commit.
    """
    update_url = f"{endpoint.rstrip('/')}/update?commit=true"
    log.info("Indexing %d documents into Solr", len(docs))
    try:
        response = requests.post(update_url, json=docs, timeout=60.0)
        response.raise_for_status()
        log.info("Indexing successful (status=%s)", response.status_code)
    except requests.RequestException as e:
        log.error("Failed to index documents: %s", e)
        raise


def main() -> int:
    log.info("Starting solr_init.py")
    try:
        wait_for_solr_core(COLLECTION_ENDPOINT, timeout=60, interval=1.0)
    except Exception as e:
        log.error("Solr core not available: %s", e)
        sys.exit(1)

    num_found = get_num_found(COLLECTION_ENDPOINT)
    log.info("Solr reports numFound = %d", num_found)

    if num_found == 0 or FORCE_REINDEX:
        docs = load_dataset_to_dict(DATASET)
        embeddings = load_embeddings_to_dict(EMBEDDINGS_FILE)

        if embeddings:
            embedding_dimension_size = get_embedding_dimension_size(embeddings)
            if embedding_dimension_size is None:
                log.error("No valid embeddings detected; aborting embedding merge")
                sys.exit(1)
            log.info("Detected embedding dimension = %d", embedding_dimension_size)

            merged_docs = merge_docs_with_embeddings(docs, embeddings, output_path=TMP_FILE)
            create_vector_field(COLLECTION_ENDPOINT, embedding_dimension_size)

            index_documents(COLLECTION_ENDPOINT, merged_docs)
        else:
            log.info("Using plain dataset without embeddings")
            index_documents(COLLECTION_ENDPOINT, docs)
            Path(TMP_FILE).unlink(missing_ok=True)
    else:
        log.info("Skipping indexing as there are already docs indexed. Use FORCE_REINDEX=true to force re-indexing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
