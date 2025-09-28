SHELL := /bin/bash
.DEFAULT_GOAL := help

# Tools
UV ?= uv
PY := $(UV) run
PYTEST ?= pytest
PYTEST_FLAGS ?= -q
MYPY_TARGET ?= src

# Coverage config
COV_FAIL_UNDER ?= 95
COV_FLAGS ?= --cov=src/confinit --cov-report=term-missing --cov-report=xml

# Test temp directory (helps in constrained environments)
TMPDIR ?= .pytest_tmp

.PHONY: help setup run lint lint-fix format format-check fix typecheck test cov cov-html build clean clean-all ci bench examples-full-run examples-quickstart-run print-version

help: ## Show this help message
	@echo "Available targets:" && \
	awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create venv and sync dev dependencies
	$(UV) sync --group dev

run: ## Run the CLI locally (prints greeting)
	$(PY) confinit

lint: ## Lint with Ruff
	$(PY) ruff check .

lint-fix: ## Lint and auto-fix with Ruff
	$(PY) ruff check --fix .

format: ## Format code with Ruff
	$(PY) ruff format .

format-check: ## Check formatting with Ruff (no changes)
	$(PY) ruff format --check .

fix: ## Apply formatting and lint auto-fixes
	$(MAKE) format lint-fix

typecheck: ## Type-check with MyPy
	$(PY) mypy $(MYPY_TARGET)

test: ## Run tests
	@mkdir -p $(TMPDIR)
	TMPDIR=$(TMPDIR) $(PY) $(PYTEST) $(PYTEST_FLAGS)

cov: ## Run tests with coverage report (fails under $(COV_FAIL_UNDER)%)
	@mkdir -p $(TMPDIR)
	TMPDIR=$(TMPDIR) $(PY) $(PYTEST) -q $(COV_FLAGS) --cov-fail-under=$(COV_FAIL_UNDER)

cov-html: ## Run tests with HTML coverage report
	@mkdir -p $(TMPDIR)
	TMPDIR=$(TMPDIR) $(PY) $(PYTEST) -q $(COV_FLAGS) --cov-report=html

build: ## Build sdist and wheel with hatchling
	uvx hatchling build

bench: ## Run simple benchmark script if present
	@if [ -f scripts/bench.py ]; then $(PY) python scripts/bench.py; else echo "No benchmark found"; fi

clean: ## Remove build artifacts and caches
	rm -rf dist build .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml

clean-all: ## Clean and remove pytest tmpdir and coverage HTML
	rm -rf dist build .pytest_cache $(TMPDIR) .mypy_cache .ruff_cache .coverage coverage.xml htmlcov

ci: ## Run lint, format-check, typecheck, and tests
	$(MAKE) lint format-check typecheck test

examples-full-run: ## Run the full app example
	$(PY) python examples/full_app/app.py

examples-quickstart-run: ## Run the quickstart example
	$(PY) python examples/quickstart.py

print-version: ## Print current confinit version
	$(PY) python -c 'import confinit as c; print(c.__version__)'
