#!/usr/bin/env bash
set -euo pipefail

# The target is the vespa container, accessible on port 8080.
CONFIG_URL="http://localhost:19071"
HTTP_URL="http://localhost:8080"

# Wait for Vespa to be healthy
echo "Waiting for Vespa to become healthy..."
for i in {1..300}; do
  if curl -s --head "$CONFIG_URL/ApplicationStatus" | grep "200 OK" >/dev/null; then
    echo "Vespa is healthy. Starting initialization..."
    break
  fi
  sleep 1
  if [ "$i" -eq 300 ]; then
    echo "Timeout waiting for Vespa to become healthy" >&2
    exit 1
  fi
done

# Deploy the application package
echo "Deploying Vespa application (config server $CONFIG_URL)…"
vespa deploy --wait 300 --target $CONFIG_URL /app
sleep 5

# Wait until the HTTP (query) endpoint is ready before feeding/querying
echo "Waiting for Vespa HTTP endpoint on $HTTP_URL to be ready…"
for i in {1..300}; do
  if curl -s --head "$HTTP_URL/status.html" | grep "200 OK" >/dev/null; then
    echo "HTTP port 8080 is up."
    break
  fi
  sleep 1
  if [ "$i" -eq 300 ]; then
    echo "Timeout waiting for HTTP endpoint" >&2
    exit 1
  fi
done

# Feed the sample data
EXPECTED_DOCS=$(ls /data/*.json | wc -l)

echo "Checking if corpus already indexed..."
indexed_docs=$(curl -s "$HTTP_URL/document/v1/news/news/docid?hits=0" \
               | jq '.root.fields.totalCount // 0')

if [ "$indexed_docs" -ge "$EXPECTED_DOCS" ]; then
  echo "Dataset already indexed ($indexed_docs docs). Skipping feed."
else
  echo "Feeding $EXPECTED_DOCS documents ..."
  vespa feed --target "$HTTP_URL" /data/*.json

  # Wait until all docs are visible
  echo "Waiting for Vespa to index documents ..."
  for i in {1..300}; do
    indexed_docs=$(curl -s "$HTTP_URL/document/v1/news/news/docid?hits=0" \
                   | jq '.root.fields.totalCount // 0')
    if [ "$indexed_docs" -ge "$EXPECTED_DOCS" ]; then
      echo "All $indexed_docs documents indexed."
      break
    fi
    sleep 1
    if [ "$i" -eq 300 ]; then
      echo "Timeout waiting for documents to be indexed" >&2
      exit 1
    fi
  done
fi