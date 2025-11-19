FROM python:3.10-slim

RUN pip install --no-cache-dir requests

WORKDIR /opt/rre-dataset-generator

COPY opensearch_init.py /opt/rre-dataset-generator/opensearch_init.py
COPY data/ /opt/rre-dataset-generator/data/

# create embeddings dir inside the image
RUN mkdir -p /opt/rre-dataset-generator/embeddings \
 && chmod 755 /opt/rre-dataset-generator/embeddings


RUN chmod +x /opt/rre-dataset-generator/opensearch_init.py

CMD ["python", "/opt/rre-dataset-generator/opensearch_init.py"]

