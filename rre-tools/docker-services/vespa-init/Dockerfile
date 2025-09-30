# vespa-init/Dockerfile
FROM python:3.10-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends bash curl jq ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir vespacli pyvespa requests

WORKDIR /app
COPY vespa-init.sh /app/vespa-init.sh
RUN chmod +x /app/vespa-init.sh

# (optional) sanity checks
RUN which vespa && vespa version && jq --version
