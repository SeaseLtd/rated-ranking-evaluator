# Vespa Integration Cheatsheet

Summary of commands to manage, inspect, and test the local Vespa integration environment.



---

## 1. Environment Management (Makefile)

These commands should be run from the `tests/integration/` directory. The `Makefile` is the simplest way to manage the container lifecycle.

-   **Start and Initialize Vespa** (Recommended)
    ```bash
    make vespa-all
    ```

-   **Start Container Only**
    ```bash
    make vespa-up
    ```


-   **Stop and Remove Container**
    ```bash
    make vespa-down
    ```

-   **Open a Shell Inside the Container**
    ```bash
	# Start the container
    docker compose -f docker-compose.vespa.yaml up -d
	# Open a shell inside the container
	docker exec -it vespa bash
    ```

-   **Follow Container Logs**
    ```bash
    docker compose -f docker-compose.vespa.yaml logs -f
	# or the makefile shortcut
	make vespa-logs
    ```

---

## 2. Health and Status Checks

Use these `curl` commands from your host machine to verify that Vespa is running correctly.

-   **Check Query Service Health**
    ```bash
    curl -s http://localhost:8080/state/v1/health
    ```

-   **Check Admin/Config Service Status**
    ```bash
    curl -s http://localhost:19071/ApplicationStatus
    ```

---

## 3. Application and Schema Inspection

-   **View Deployed Schema File** (in the directory containing this file)
    The most reliable way to check the schema is to view the source file directly.
    ```bash
    cat /app/schemas/news.sd
    ```

-   **View Service Configuration** (in the directory containing this file)
    This file defines the content cluster and services.
    ```bash
    cat /app/services.xml
    ```

---

## 4. Querying

-   **Run a YQL Query with `curl`** (from host machine)
    ```bash
    curl -s "http://localhost:8080/search/?yql=select%20*%20from%20news%20where%20true"
    ```

-   **Run a Query with `vespa-cli`** (from the container)
    ```bash
    docker exec vespa vespa query 'select * from news where true'
    ```

---

## 5. Running Integration Tests

Manual checks:

```bash
python -m pytest tests/integration/vespa-init/vespa_test_manual_integration.py
```

### TODO
Implement integration tests using a make command


---

### Makefile
```bash
# Makefile for managing the Vespa integration testing environment

.PHONY: all up down logs init test-query clean

vespa-all: vespa-up vespa-init

# Start the Vespa container in detached mode
vespa-up:
	docker compose -f docker-compose.vespa.yaml up -d

# Stop and remove the Vespa container
vespa-down:
	docker compose -f docker-compose.vespa.yaml down

# Follow the logs of the Vespa container
vespa-logs:
	docker compose -f docker-compose.vespa.yaml logs -f

# Run the initialization script inside the Vespa container
vespa-init:
	@echo "Running initialization script. Checking health state..\n"
	docker exec vespa bash /app/vespa-init.sh

# Run a test query against the Vespa container
vespa-test-query:
	docker exec vespa vespa query "select * from news where true"

# Clean up orphan containers
vespa-clean:
	docker compose -f docker-compose.vespa.yaml down --remove-orphans


## This could be upgraded, and expanded to include the same functionality for other services
## Also: this could be used orchestrate the automation of the integration test
```