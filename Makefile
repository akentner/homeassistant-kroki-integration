.PHONY: help install lint format check test test-verbose clean validate

VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
PYTEST   := $(VENV)/bin/pytest
RUFF     := $(VENV)/bin/ruff

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: $(VENV) ## Install all dependencies
	$(PIP) install --upgrade pip
	$(PIP) install pytest-homeassistant-custom-component ruff pre-commit

$(VENV):
	python3 -m venv $(VENV)

lint: ## Run ruff linter
	$(RUFF) check custom_components/ tests/

format: ## Format code with ruff
	$(RUFF) format custom_components/ tests/
	$(RUFF) check --fix custom_components/ tests/

check: ## Check formatting and linting (no changes)
	$(RUFF) format --check custom_components/ tests/
	$(RUFF) check custom_components/ tests/

test: ## Run tests
	$(PYTEST)

test-verbose: ## Run tests with verbose output
	$(PYTEST) -v

clean: ## Remove build artifacts and caches
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

validate: ## Run HA hassfest and HACS validation (requires Docker)
	pre-commit run hassfest --all-files
	pre-commit run hacs-validate --all-files
