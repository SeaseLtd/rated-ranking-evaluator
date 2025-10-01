# Vespa Integration Cheatsheet

If handling Vespa alone is consider difficult, with Compose it hardens a bit. Hence, here we add a summary of commands to ease things while inspecting, and testing the local Vespa integration environment.

---

## 1. Environment Management


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
