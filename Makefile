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

up:
	docker-compose up -d

down:
	docker-compose down

# Ingest new filings via RSS (Loop)
ingest_recent:
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli ingest-rss

# Build Vector Index (RAG)
build_index:
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli ingest-rag --tickers $(TICKERS)

# Compute Features (DS)
compute_ds:
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli compute-event-study --tickers $(TICKERS)

compute_risk:
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli compute-risk --tickers $(TICKERS)

# GraphRAG
build_graph:
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli build-graph --tickers $(TICKERS)

# Placeholder for Eval
eval:
	@echo "Running Eval..."
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m eval.ragas.pipeline
	# $(PYTHON) -m eval.run

test:
	$(PYTHON) -m pytest tests -v

serve_llm:
	$(PYTHON) -m mlx_lm.server --model mlx-community/Llama-3.2-3B-Instruct-4bit --port 8080

run_ui:
	$(VENV)/bin/streamlit run apps/streamlit_app.py

demo:
	@echo ">>> Running Golden Path Demo <<<"
	@echo "1. Ingesting Market Data (AAPL, MSFT, NVDA)..."
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli ingest-market --tickers AAPL,MSFT,NVDA
	@echo "2. Building Features..."
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli build-features --tickers AAPL,MSFT,NVDA
	@echo "3. Ingesting XBRL (Simulation)..."
	SEC_USER_AGENT="AlphaOps/0.2 (test@example.com)" $(PYTHON) -m apps.cli ingest-xbrl --tickers AAPL,MSFT,NVDA
	@echo "4. Checking Data..."
	$(PYTHON) check_data.py
	@echo ">>> Demo Ready. Run 'make run_ui' to interact. <<<"
