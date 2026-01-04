VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

up:
	docker compose up -d

down:
	docker compose down

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -e .[dev]

test:
	$(VENV)/bin/pytest

lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/mypy .

format:
	$(VENV)/bin/black .
	$(VENV)/bin/ruff check . --fix

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

ingest_recent:
	$(VENV)/bin/python -m apps.cli ingest-rss

ingest_xbrl:
	SEC_USER_AGENT="AlphaOps/0.1 (kaushik.kumar@testmail.com)" $(VENV)/bin/python -m apps.cli ingest-xbrl --tickers AAPL,MSFT

ingest_market:
	$(VENV)/bin/python -m apps.cli ingest-market --tickers AAPL,MSFT

build_features:
	$(VENV)/bin/python -m apps.cli build-features --tickers AAPL,MSFT

ingest_rag:
	SEC_USER_AGENT="AlphaOps/0.1 (kaushik.kumar@testmail.com)" $(VENV)/bin/python -m apps.cli ingest-rag --tickers AVAH

run_ui:
	$(VENV)/bin/streamlit run apps/streamlit_app.py

serve_llm:
	$(VENV)/bin/python -m mlx_lm.server --model mlx-community/Llama-3.2-3B-Instruct-4bit --port 8080
