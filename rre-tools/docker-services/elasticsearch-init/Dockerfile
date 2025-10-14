FROM alpine:3.22.1

RUN apk add --no-cache curl jq

COPY data/dataset.jsonl /opt/rre-dataset-generator/data/dataset.jsonl
COPY --chmod=777 elasticsearch-init.sh /opt/rre-dataset-generator/elasticsearch-init.sh
