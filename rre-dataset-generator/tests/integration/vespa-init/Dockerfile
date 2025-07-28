FROM python:3.10-slim

RUN apt-get update && apt-get install -y bash curl jq
RUN pip install requests vespacli

COPY vespa-init.sh /opt/rre-dataset-generator/
RUN chmod +x /opt/rre-dataset-generator/vespa-init.sh

WORKDIR /opt/rre-dataset-generator
