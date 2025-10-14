#!/bin/sh
set -euo pipefail

CLUSTER="http://elasticsearch:9200"
INDEX="testcore"
ENDPOINT="$CLUSTER/$INDEX"
DATASET_PATH="/opt/rre-dataset-generator/data/dataset.jsonl"

echo "[INFO] Waiting for Elasticsearch..."
# Wait until Elasticsearch responds (up to 30s)
max=30;
for i in $(seq 1 $max); do
  if curl -sf "$CLUSTER"; then break; fi
  echo "  ...still waiting ($i/$max)"
  sleep 1
done
if ! curl -sf "$CLUSTER"; then
  echo "[ERROR] Elasticsearch not reachable"; exit 1
fi

# Create index if it doesn't exist
if ! curl -sf -XGET "$ENDPOINT"; then
  echo "[INFO] Creating index '$INDEX'"
  curl -XPUT "$ENDPOINT" -H "Content-Type: application/json" -d '{}'
fi

# Check document count in the index
COUNT=$(curl -s "$ENDPOINT/_count" | grep -o '"count":[0-9]\+' | sed 's/"count"://')
echo "[INFO] Document count in '$INDEX': $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "[INFO] Indexing dataset into '$INDEX'..."

  bulk_response=$(jq -c '. as $doc | {"index":{"_id":$doc.id}}, $doc' "$DATASET_PATH" \
    | curl --max-time 120 --silent --show-error -XPOST "$ENDPOINT/_bulk?refresh=true" \
        -H "Content-Type: application/x-ndjson" --data-binary @- )

  if [ "$(echo "$bulk_response" | jq -r '.errors')" = "true" ]; then
    echo "[ERROR] Bulk indexing reported errors. Full response:" >&2
    echo "$bulk_response" | jq '.' >&2
    exit 1
  fi

  echo "[INFO] Done indexing."
else
  echo "[INFO] Data already present in '$INDEX'; skipping indexing."
fi

exit 0
