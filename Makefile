VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: help install up down ingest_recent build_index compute_ds eval test demo serve_llm

help:
	@echo "EDGAR AlphaOps v2 - Make Targets"
	@echo "--------------------------------"
	@echo "  up             Start Qdrant & Phoenix containers"
	@echo "  down           Stop containers"
	@echo "  install        Install Python dependencies"
	@echo "  ingest_recent  Run continuous SEC RSS ingestion (Ctrl+C to stop)"
	@echo "  build_index    Build Vector Index for RAG (requires TICKERS=...)"
	@echo "  compute_ds     Compute DS features (requires TICKERS=...)"
	@echo "  eval           Run RAGAS evaluation suite"
	@echo "  test           Run unit/integration tests"
	@echo "  lint           Run code quality checks (ruff)"
	@echo "  demo           Run Golden Path Demo (AAPL, MSFT, NVDA)"
	@echo "  serve_llm      Serve local MLX LLM (Mac)"
	@echo "  run_ui         Launch Streamlit UI"

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .
	$(PIP) install pytest ruff

lint:
	$(PYTHON) -m ruff check .

# Deliverable Commands
up:
	docker compose up -d --build

down:
	docker compose down

ingest_recent:
	@echo "Running Ingestion for $(TICKERS)"
	SEC_USER_AGENT="AlphaOps/Prod (admin@alphaops.ai)" $(PYTHON) -m apps.cli ingest-recent --tickers "$(TICKERS)"

reconcile_index:
	@echo "Reconciling Index for $(DATE)"
	$(PYTHON) -m apps.cli reconcile-index --date $(DATE)

build_index:
	$(PYTHON) -m apps.cli build-rag-index

compute_ds:
	$(PYTHON) -m apps.cli compute-event-study

eval:
	$(PYTHON) -m apps.cli run-eval

test:
	$(PYTHON) -m pytest tests -v

demo:
	@echo ">>> DEMO START <<<"
	make up
	make ingest_recent TICKERS="$(TICKERS)"
	make build_index
	make compute_ds
	@echo ">>> DEMO COMPLETE <<<"

