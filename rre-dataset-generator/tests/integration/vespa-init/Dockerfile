FROM python:3.10-slim

RUN apt-get update && apt-get install -y bash curl jq
RUN pip install requests vespacli

COPY vespa-init.sh /app/vespa-init.sh
RUN chmod +x /app/vespa-init.sh

WORKDIR /app
