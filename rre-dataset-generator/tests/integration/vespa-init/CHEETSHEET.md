# Vespa Integration Test Cheatsheet

This guide summarizes the commands used to manage and test integration with Vespa, using the workflow defined in the `Makefile`.

---

## Main Workflow (Makefile)

All commands must be executed from the `tests/integration/vespa-init/` directory.

```bash
# Run the full CI cycle: install, start, initialize, test, and clean up.
make ci

# Start Vespa services in the background.
make up

# Initialize Vespa: deploy the app and load test data.
make init

# Run Pytest tests for Vespa.
make test

# Stop and remove Vespa containers and volumes.
make down
```

---

## General Container Management (Docker Compose)

For manual operations or debugging.

```bash
# List running containers.
docker compose ps

# Tail Vespa container logs in real time.
docker compose logs -f vespa

# Open an interactive shell inside the Vespa container.
docker compose exec vespa bash

# Stop the services.
docker compose stop

# Restart previously stopped services.
docker compose start
```

---

## Vespa Commands

These commands must be executed **inside the container** (`docker compose exec vespa ...`).

```bash
# Deploy the application (defined under /app inside the container).
vespa deploy --wait 300 /app

# Feed Vespa with test data (located in /dataset).
vespa feed /dataset/dataset.json

# Perform a basic query to verify data ingestion.
vespa query "select * from news where true"

# Retrieve a document by its ID.
vespa document get id:news:news::1
```

---

## Health Checks
We're having some troubles using the healthchecks, but should be available at:

```bash
# Check Vespa container health.
curl http://localhost:8080/state/v1/health

# Check Vespa config server health.
curl http://localhost:19071/state/v1/health
```

---

## Important Notes
* **Test Configuration**: The tests in `test_vespa.py` connect to `http://localhost:8080` by default. This can be overridden using the `VESPA_ENDPOINT` environment variable. The pytest relies on the Vespa app / container being initialized before. So automatically it won't run all the tests by default. We need to configure in the GitLab CI to run properly.

* **Working Directory**: The `make` and `docker compose` commands must be run from `tests/integration/vespa-init/`.
