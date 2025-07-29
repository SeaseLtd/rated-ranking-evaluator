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
	@echo "Waiting for Vespa admin endpoint to respond..."
	@timeout 300 bash -c 'until curl -s --head http://localhost:19071/ApplicationStatus | grep "200 OK" >/dev/null; do sleep 1; done'
	@echo "Vespa is healthy. Running initialization script..."
	docker exec vespa bash /app/vespa-init.sh

# Run a test query against the Vespa container
vespa-test-query:
	docker exec vespa vespa query "select * from news where true"

# Clean up orphan containers
vespa-clean:
	docker compose -f docker-compose.vespa.yaml down --remove-orphans


## This could be upgraded, and expanded to include the same functionality for other services
## Also: this could be used orchestrate the automation of the integration test
