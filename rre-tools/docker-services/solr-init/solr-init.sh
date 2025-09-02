#!/bin/sh
set -euo pipefail

COLLECTION_ENDPOINT="http://solr:8983/solr/testcore";
DATASET_FILE="/opt/rre-dataset-generator/data/dataset.json";
EMBEDDINGS_FOLDER="/opt/rre-dataset-generator/embeddings";
EMBEDDINGS_FILE="$EMBEDDINGS_FOLDER/doc_embeddings.jsonl";
TMP_FILE="/tmp/merged_dataset.json";

echo "[INFO] Waiting for Solr core \"testcore\" to be ready…";
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

mkdir -p $EMBEDDINGS_FOLDER

if [ -f "$EMBEDDINGS_FILE" ] && command -v jq >/dev/null 2>&1; then
  VECTOR_DIM=$(head -n 1 "$EMBEDDINGS_FILE" | jq '.vector | length')
  echo "[INFO] Embeddings file found -> detected embedding dimension: $VECTOR_DIM"
  echo "[INFO] jq available → merging…"
  jq --slurpfile emb "$EMBEDDINGS_FILE" '       # parse the $EMBEDDINGS_FILE into the var `emb` and execute the following script
  map(
    . as $doc                                   # save each line of the document in the var `doc`
    | ($emb[] | select(.id == $doc.id)) as $e   # assign to the var `e` the line of the emb file if it has the same id
    | if $e != null
      then $doc + {vector: $e.vector}           # appends the embedding to the document
      else $doc                                 # otherwise it keeps just the fields
      end
  )
' "$DATASET_FILE" > "$TMP_FILE"
  echo "[INFO] Updating solr collection with vector field (dim=$VECTOR_DIM)…"
  curl -f -X POST -H 'Content-type:application/json' --data-binary "{
  \"add-field-type\" : {
      \"name\":\"knn_vector\",
      \"class\":\"solr.DenseVectorField\",
      \"vectorDimension\":$VECTOR_DIM,
      \"similarityFunction\":\"cosine\",
      \"knnAlgorithm\":\"hnsw\"
    },
  \"add-field\" : {
      \"name\":\"vector\",
      \"type\":\"knn_vector\",
      \"indexed\":true,
      \"stored\":true
    }
  }" $COLLECTION_ENDPOINT/schema
else
  echo "[INFO] Using plain dataset (no embeddings or jq missing)…"
  cp "$DATASET_FILE" "$TMP_FILE"
fi

if [ "$COUNT_FOUND" -eq 0 ]; then
  echo "[INFO] Indexing dataset…";
  curl -f -X POST \
       -H "Content-Type: application/json" \
       --data-binary @"$TMP_FILE" \
       $COLLECTION_ENDPOINT/update?commit=true;
  echo "[INFO] Done indexing.";
else
  echo "[INFO] Collection already contains data, skipping indexing.";
fi

exit 0;


