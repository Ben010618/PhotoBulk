# ==============================================================================
# KameraPh AI Studio Suite: Developer Makefile
# ==============================================================================

PYTHON ?= python
NPM ?= npm
PORT ?= 8000
HOST ?= 127.0.0.1

.PHONY: all install init-db build dev run test demo models clean help

all: help

help:
	@echo "KameraPh Studio Suite - Available Commands:"
	@echo "  make install      - Install Python requirements and frontend npm dependencies"
	@echo "  make models       - Download and verify AI neural model weights with checksums"
	@echo "  make init-db      - Instantiate database schema (SQLite/Postgres)"
	@echo "  make build        - Compile and build React/Vite frontend into dist/"
	@echo "  make run          - Launch backend server (serves frontend at http://$(HOST):$(PORT))"
	@echo "  make dev          - Run backend with hot reload"
	@echo "  make test         - Run test suite"
	@echo "  make demo         - Run end-to-end portrait pipeline demo with before/after comparisons"
	@echo "  make clean        - Clean temporary artifacts and pycache"

models:
	$(PYTHON) scripts/download_models.py

install:
	$(PYTHON) -m pip install -r requirements.txt
	cd frontend && $(NPM) install

init-db:
	$(PYTHON) init_db.py

build:
	cd frontend && $(NPM) run build

run: init-db
	$(PYTHON) -m uvicorn api_server:app --host $(HOST) --port $(PORT)

dev: init-db
	$(PYTHON) -m uvicorn api_server:app --host $(HOST) --port $(PORT) --reload

test:
	$(PYTHON) -m pytest -v tests/ || $(PYTHON) test_pipeline.py

demo:
	$(PYTHON) scripts/demo_run.py

clean:
	rm -rf __pycache__ */__pycache__ temp_pdf_render/*.jpg temp_pdf_render/*.pdf .pytest_cache demo_output output
