#!/bin/sh

set -euo pipefail

OPENSEARCH_HOST="http://opensearch:9200"
INDEX_NAME="testcore"
INDEX_URL="$OPENSEARCH_HOST/$INDEX_NAME"
DATASET_PATH="/opt/rre-dataset-generator/data/dataset.jsonl"

echo "[INFO] Waiting for OpenSearch to be ready…"
max=30
for i in $(seq 1 $max); do
  if curl -sf "$OPENSEARCH_HOST"; then
    echo "[INFO] OpenSearch is up"
    break
  fi
  echo "still waiting ($i/$max)"
  sleep 1
done

# exit if opensearch fails to start
if [ "$i" -eq "$max" ]; then
  echo "[ERROR] OpenSearch did not come up in time after $max attempts" >&2
  exit 1
fi


# create 'testcore' index if it doesn't exist
http_code=$(curl --max-time 5 -s -o /dev/null -w "%{http_code}" -XHEAD "$INDEX_URL" || echo "000")

if [ "$http_code" -eq 200 ]; then
  echo "[INFO] Index '$INDEX_NAME' already exists"
else
  echo "[INFO] Creating index '$INDEX_NAME'"
  curl -XPUT "$INDEX_URL" -H "Content-Type: application/json" -d '{}'
fi


# count documents
echo "[INFO] Checking document count in index '$INDEX_NAME'…"
doc_count=$(curl -s "$INDEX_URL/_count" | grep -o '"count":[0-9]*' | cut -d':' -f2)
echo "[INFO] Document count in '$INDEX_NAME': $doc_count"


# index dataset or skip if exists
if [ "$doc_count" -eq 0 ]; then
  echo "[INFO] Starting bulk indexing"

  bulk_response=$(jq -c '. as $doc | {"index":{"_id":$doc.id}}, $doc' "$DATASET_PATH" \
    | curl --max-time 120 --silent --show-error -XPOST "$INDEX_URL/_bulk?refresh=true" \
        -H "Content-Type: application/x-ndjson" --data-binary @- )

  if [ "$(echo "$bulk_response" | jq -r '.errors')" = "true" ]; then
    echo "[ERROR] Bulk indexing reported errors. Full response:" >&2
    echo "$bulk_response" | jq '.' >&2
    exit 1
  fi

  echo "[INFO] Done bulk indexing."
else
  echo "[INFO] Index already contains documents. Skipping bulk indexing."
fi


exit 0
