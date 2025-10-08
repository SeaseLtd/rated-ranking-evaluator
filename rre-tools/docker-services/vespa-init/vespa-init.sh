#!/usr/bin/env bash
set -euo pipefail

CONFIG_URL="${CONFIG_URL:-http://vespa:19071}"
HTTP_URL="${HTTP_URL:-http://vespa:8080}"

echo "Waiting for config-server UP… ($CONFIG_URL/state/v1/health)"
for i in {1..300}; do
  if curl -fsS "$CONFIG_URL/state/v1/health" | jq -e '.status.code=="up"' >/dev/null; then
    echo "Config-server UP."
    break
  fi
  sleep 1
  [[ $i -eq 300 ]] && { echo "Timeout waiting for config-server" >&2; exit 1; }
done

echo "Deploying app…"
vespa deploy --wait 600 --target "$CONFIG_URL" /app

# Wait for ALL app services to be UP
echo "Waiting for declared services (CLI)…"
vespa status --wait 600 --target "$CONFIG_URL"

# Real search readiness: /status.html = 200 when content clusters are UP
echo "Waiting for /status.html…"
for i in {1..300}; do
  code=$(curl -fsS -o /dev/null -w '%{http_code}' "$HTTP_URL/status.html" || true)
  if [[ "$code" == "200" ]]; then
    echo "Content clusters UP (status.html=200)."
    break
  fi
  sleep 1
  [[ $i -eq 300 ]] && { echo "Timeout waiting for status.html" >&2; exit 1; }
done

# Feed (opt)
EXPECTED_DOCS=$(ls /data/*.json 2>/dev/null | wc -l | tr -d ' ')
if [[ "${EXPECTED_DOCS:-0}" -gt 0 ]]; then
  echo "Checking existing documents (query hits=0)…"
  # Small backoff because cluster might be warming up
  backoff=1
  for attempt in {1..5}; do
    # +timeout=10s to avoid 504 if timing is tight
    if current_count=$(curl -fsS "$HTTP_URL/search/?yql=select+*+from+sources+*+where+true&hits=0&timeout=10s" \
                        | jq '.root.fields.totalCount // 0' 2>/dev/null); then
      break
    else
      echo "Count failed (maybe warming up). Retry #$attempt in ${backoff}s…"
      sleep "$backoff"; backoff=$(( backoff*2 ))
    fi
  done
  : "${current_count:=0}"

  if (( current_count >= EXPECTED_DOCS )); then
    echo "Index already populated ($current_count docs) — skipping feed."
  else
    echo "Feeding $EXPECTED_DOCS documents…"
    vespa feed --target "$HTTP_URL" /data/*.json

    echo "Waiting for search visibility…"
    for i in {1..300}; do
      current_count=$(curl -fsS "$HTTP_URL/search/?yql=select+*+from+sources+*+where+true&hits=0&timeout=10s" \
                       | jq '.root.fields.totalCount // 0')
      (( current_count >= EXPECTED_DOCS )) && { echo "Ready: $current_count docs."; break; }
      sleep 1
      [[ $i -eq 300 ]] && { echo "Timeout waiting for indexing" >&2; exit 1; }
    done
  fi
fi
