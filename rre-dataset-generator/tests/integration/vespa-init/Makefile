.PHONY: ci up init down install test

VESPA_COMPOSE = docker compose
PYTEST       = python -m pytest -k vespa

# ---------------- CI / ONE-SHOT ----------------
ci: install up init test down

# ---------------- STEPS ----------------
up:
	$(VESPA_COMPOSE) up -d --remove-orphans

init:
	./vespa-init.sh

install:
	# CAUTION: hard-coded path
	pip install -e ../../../

test:
	$(PYTEST)

down:
	$(VESPA_COMPOSE) down -v