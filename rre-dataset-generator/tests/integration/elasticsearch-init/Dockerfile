FROM docker.elastic.co/elasticsearch/elasticsearch:9.0.4

COPY data/dataset.jsonl /opt/rre-dataset-generator/data/dataset.jsonl
COPY --chmod=777 elasticsearch-init.sh /opt/rre-dataset-generator/elasticsearch-init.sh
