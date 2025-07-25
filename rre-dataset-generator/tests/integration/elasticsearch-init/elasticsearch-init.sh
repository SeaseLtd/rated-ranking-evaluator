#!/bin/sh
set -euo pipefail

CLUSTER="http://elasticsearch:9200"
INDEX="testindex"
ENDPOINT="$CLUSTER/$INDEX"

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

# Create index with mappings if it doesn't exist
if ! curl -sf -XGET "$ENDPOINT"; then
  echo "[INFO] Creating index '$INDEX' with mappings"
  curl -sf -XPUT "$ENDPOINT" -H 'Content-Type: application/json' -d '{
    "mappings": {
      "properties": {
        "title": {"type": "text"},
        "description": {"type": "text"}
      }
    }
  }'
fi

# Check document count in the index
COUNT=$(curl -s "$ENDPOINT/_count" | grep -o '"count":[0-9]\+' | sed 's/"count"://')
echo "[INFO] Document count in '$INDEX': $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "[INFO] Indexing dataset into '$INDEX'..."
  curl -sf -XPOST "$ENDPOINT/_bulk?refresh=true" \
       -H "Content-Type: application/x-ndjson" \
       --data-binary @/opt/rre-dataset-generator/data/dataset.jsonl
  echo "[INFO] Done indexing."
else
  echo "[INFO] Data already present in '$INDEX'; skipping indexing."
fi

exit 0
