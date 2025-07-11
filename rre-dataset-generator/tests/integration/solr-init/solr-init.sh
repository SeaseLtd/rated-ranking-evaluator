#!/bin/sh
set -euo pipefail

COLLECTION_ENDPOINT="http://solr:8983/solr/testcore";

echo "[INFO] Waiting for Solr core '\''testcore'\'' to be ready…";
max=30;
for i in $(seq 1 $max); do
  if curl -sf $COLLECTION_ENDPOINT/admin/ping?wt=json > /dev/null; then
    echo "[INFO] Core is ready";
    break;
  fi;
  echo "  …still waiting ($i/$max)";
  sleep 1;
done

# if still not up, exit
if ! curl -sf $COLLECTION_ENDPOINT/admin/ping?wt=json > /dev/null; then
  echo "[ERROR] core did not come up in time after $max attempts" >&2;
  exit 1;
fi

SOLR_RESPONSE=$(curl -sf $COLLECTION_ENDPOINT/select\?q\=\*:\*)
COUNT_FOUND=$(echo "$SOLR_RESPONSE" | { grep -cE '"numFound":[1-9]+' || test $? = 1; })
echo "num found: $COUNT_FOUND"

if [ "$COUNT_FOUND" -eq 0 ]; then
  echo "[INFO] Indexing dataset…";
  curl -f -X POST \
       -H "Content-Type: application/json" \
       --data-binary @/opt/rre-dataset-generator/data/dataset.json \
       $COLLECTION_ENDPOINT/update?commit=true;
  echo "[INFO] Done indexing.";
else
  echo "[INFO] Collection already contains data, skipping indexing.";
fi

exit 0;


