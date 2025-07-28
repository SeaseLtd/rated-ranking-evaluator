# Docker + Vespa Cheetsheet

## Docker Container Management


```txt
https://docs.vespa.ai/en/vespa-quick-start.html
```

```bash
docker ps                             # List running containers
docker stats vespa                    # Show real-time resource usage for Vespa
docker logs -f vespa                  # Stream logs from Vespa container

docker start vespa                    # Start Vespa container
docker stop vespa                     # Stop Vespa container
docker rm vespa                       # Remove Vespa container


docker exec -it vespa bash -c "sleep 5" # Code (bash) execution on the Docker container instance

docker compose up --wait  # que bloquea hasta que el healthcheck sea “healthy”.

# Run Vespa detached
docker run -d --name vespa --hostname vespa-container -p 8080:8080 -p 19071:19071 vespaengine/vespa                   
```

**Persistent storage / volumes**

```bash
mkdir -p /tmp/vespa/var /tmp/vespa/logs
sudo chown -R 1000:1000 /tmp/vespa/var /tmp/vespa/logs

docker run -d --name vespa --hostname vespa-container \
  --user vespa:vespa \
  -v /tmp/vespa/var:/opt/vespa/var \
  -v /tmp/vespa/logs:/opt/vespa/logs \
  -p 8080:8080 vespaengine/vespa
```

---

## Application Deployment

```bash
vespa deploy --wait 300 ./app
```

---

## Health Checks

```bash
curl http://localhost:8080/state/v1/health         # Container health
curl http://localhost:19071/state/v1/health        # Configserver health
```

---

## Querying Vespa

```bash
# Basic text match query
vespa query "select * from music where album contains 'head'" language=en-US

# Query with custom ranking and user profile
vespa query "select * from music where true" \
  "ranking=rank_albums" \
  "input.query(user_profile)={pop:0.8,rock:0.2,jazz:0.1}"

# Query with tensor presentation options
vespa query "select * from music where true" \
  "ranking=rank_albums" \
  "input.query(user_profile)={pop:0.8,rock:0.2,jazz:0.1}" \
  "presentation.format.tensors=short-value"
```

*Note: Query language and ranking features depend on the application schema.*

---

## Document Operations

```bash
# Fetch a document by its ID
vespa document get id:mynamespace:music::a-head-full-of-dreams

# List all documents in the cluster
vespa visit
```

---

## Useful Utilities

```bash
docker exec -it vespa bash                                                               # Open a shell inside Vespa container
docker exec vespa bash -c '/opt/vespa/bin/vespa-logfmt /opt/vespa/logs/vespa/vespa.log'  # Pretty-print Vespa logs
docker stop vespa && docker rm vespa                                                     # Stop and remove Vespa container
```

---

### NOTES

* Ensure Docker has at least 4–6 GB RAM allocated for stable Vespa operation.
* Validate the app files (`services.xml`, schema, etc.) when/before deploying + use testing queries

```bash
# NOTE: the 'where' clausule, it's mandatory
$ vespa query "select * from news where true" language=en-US
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1
        },
        "coverage": {
            "coverage": 100,
            "documents": 1,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "id:news:news::1",
                "relevance": 0.0,
                "source": "news",
                "fields": {
                    "sddocname": "news",
                    "documentid": "id:news:news::1",
                    "id": "1",
                    "title": "Helicopter Crashes in Colombian Drug War, Kills 20",
                    "description": "BOGOTA, Colombia  - A U.S.-made helicopter on an anti-drugs mission crashed in the Colombian jungle on Thursday, killing all 20 Colombian soldiers aboard, the army said."
                }
            }
        ]
    }
}
```
* [Vespa Query API docs](https://docs.vespa.ai/en/query-api.html) for advanced querying.
