SHELL := /bin/bash
.DEFAULT_GOAL := help

# Tools
UV := uv
PY := $(UV) run

# Coverage config
COV_FAIL_UNDER ?= 95

.PHONY: help setup run lint format format-check typecheck test cov build clean ci bench

help: ## Show this help message
	@echo "Available targets:" && \
	awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create venv and sync dev dependencies
	$(UV) sync --group dev

run: ## Run the CLI locally (prints greeting)
	$(PY) confinit

lint: ## Lint with Ruff
	$(PY) ruff check .

format: ## Format code with Ruff
	$(PY) ruff format .

format-check: ## Check formatting with Ruff (no changes)
	$(PY) ruff format --check .

typecheck: ## Type-check with MyPy
	$(PY) mypy src

test: ## Run tests
	$(PY) pytest -q

cov: ## Run tests with coverage report (fails under $(COV_FAIL_UNDER)%)
	$(PY) pytest -q \
	  --cov=src/confinit \
	  --cov-report=term-missing \
	  --cov-report=xml \
	  --cov-fail-under=$(COV_FAIL_UNDER)

build: ## Build sdist and wheel with hatchling
	uvx hatchling build

bench: ## Run simple benchmark script if present
	@if [ -f scripts/bench.py ]; then $(PY) python scripts/bench.py; else echo "No benchmark found"; fi

clean: ## Remove build artifacts and caches
	rm -rf dist build .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml

ci: ## Run lint, format-check, typecheck, and tests
	$(MAKE) lint format-check typecheck test

