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
    cat /app/schemas/doc.sd
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
    curl -s "http://localhost:8080/search/?yql=select%20*%20from%20doc%20where%20true"
    ```

-   **Run a Query with `vespa-cli`** (from the container)
    ```bash
    docker exec vespa vespa query 'select * from doc where true'
    ```

---

## 5. Running Integration Tests

Manual checks:

```bash
python -m pytest tests/integration/vespa-init/vespa_test_manual_integration.py
```

### TODO
Implement integration tests using a make command