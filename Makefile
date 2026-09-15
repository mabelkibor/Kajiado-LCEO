# Kajiado-LCEO — common tasks.
.DEFAULT_GOAL := help
PYTHON ?= python3
SCENARIO ?= baseline

.PHONY: help install install-dev sample run scenarios sensitivity figures test lint format typecheck clean clean-outputs

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	$(PYTHON) -m pip install -e .

install-dev:  ## Install with development and GIS extras
	$(PYTHON) -m pip install -e ".[dev,notebooks]"

sample:  ## Generate the synthetic county in data/raw
	$(PYTHON) -m kajiado_lceo.cli sample-data

run:  ## Run the model (SCENARIO=baseline)
	$(PYTHON) -m kajiado_lceo.cli run --scenario $(SCENARIO)

scenarios:  ## Run every scenario and tabulate the results
	$(PYTHON) -m kajiado_lceo.cli compare-scenarios

sensitivity:  ## Sweep the configured sensitivity parameters
	$(PYTHON) -m kajiado_lceo.cli sensitivity

figures:  ## Render the standard result figures
	$(PYTHON) -m kajiado_lceo.cli figures --scenario $(SCENARIO)

test:  ## Run the test suite
	$(PYTHON) -m pytest

lint:  ## Lint with ruff
	$(PYTHON) -m ruff check src tests

format:  ## Auto-format with ruff
	$(PYTHON) -m ruff format src tests
	$(PYTHON) -m ruff check --fix src tests

typecheck:  ## Type-check with mypy
	$(PYTHON) -m mypy

clean-outputs:  ## Remove generated outputs (keeps inputs)
	rm -rf outputs/tables/* outputs/figures/* outputs/maps/* outputs/reports/* outputs/logs/*
	rm -rf data/interim/* data/processed/*

clean: clean-outputs  ## Remove outputs and Python caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info
