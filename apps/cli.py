import sys
from observability.logging import setup_logging
from observability.setup import setup_observability
from pipelines.sec.rss import RssWatcher
from lakehouse.db import Database
import logging
import time

def ingest_rss_loop():
    """
    Continuous loop to monitor SEC RSS.
    """
    watcher = RssWatcher()
    logging.info("Starting SEC RSS Ingestion Loop... (Ctrl+C to stop)")
    
    while True:
        try:
            watcher.run_cycle()
            logging.info("Cycle complete. Sleeping for 10 minutes...")
            time.sleep(600) # 10 minutes
        except KeyboardInterrupt:
            logging.info("Stopping...")
            break
        except Exception as e:
            logging.error(f"Error in ingest cycle: {e}")
            time.sleep(60)

def main():
    setup_logging()
    setup_observability()
    
    # Init DB Schema
    db = Database()
    db.init_schema()

    if len(sys.argv) < 2:
        print("Usage: python -m apps.cli [command]")
        print("Commands:")
        print("  ingest-rss   Start monitoring SEC RSS feed")
        return

    command = sys.argv[1]
    
    if command == "ingest-rss":
        ingest_rss_loop()
    
    elif command == "ingest-xbrl":
        # python -m apps.cli ingest-xbrl --tickers AAPL,MSFT
        from pipelines.xbrl.metadata import CompanyMetadataFetcher
        from pipelines.xbrl.facts import XbrlFactsFetcher
        
        # 1. Update Company Metadata
        meta_fetcher = CompanyMetadataFetcher()
        meta_fetcher.fetch_and_save()
        
        # 2. Fetch Facts
        facts_fetcher = XbrlFactsFetcher()
        
        # Parse args manually for simplicity or use argparse properly
        # Ideally we refactor to argparse, but let's do simple argv check
        tickers = []
        if "--tickers" in sys.argv:
            idx = sys.argv.index("--tickers")
            if idx + 1 < len(sys.argv):
                tickers = sys.argv[idx+1].split(",")
        
        if not tickers:
            logging.info("No tickers provided. Ingesting default list for demo...")
            tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
            
        # We need CIKs. Let's query DB.
        conn = db.get_connection()
        for t in tickers:
            t = t.strip().upper()
            res = conn.execute("SELECT cik FROM companies WHERE ticker = ?", [t]).fetchone()
            if res:
                cik = res[0] # String
                try:
                    facts_fetcher.fetch_facts(cik)
                except Exception as e:
                    logging.error(f"Failed to ingest XBRL for {t}: {e}")
            else:
                logging.warning(f"Ticker {t} not found in companies table.")
        conn.close()

    elif command == "ingest-market":
        from pipelines.market.client import MarketDataFetcher
        tickers = _parse_tickers_arg()
        fetcher = MarketDataFetcher()
        fetcher.fetch_prices(tickers)

    elif command == "build-features":
        from lakehouse.features.builder import FeatureBuilder
        tickers = _parse_tickers_arg()
        builder = FeatureBuilder()
        for t in tickers:
            builder.build_features(t)

    elif command == "ingest-rag":
        # python -m apps.cli ingest-rag --tickers AAPL
        from pipelines.sec.client import SecClient
        from pipelines.sec.resolver import FilingResolver
        from pipelines.rag.processor import DocumentProcessor
        from pipelines.rag.embedder import Embedder
        from pipelines.rag.store import VectorBooster
        import os

        
        tickers = _parse_tickers_arg()
        client = SecClient()
        db = Database()
        processor = DocumentProcessor()
        embedder = Embedder()
        store = VectorBooster()
        
        # 1. Get recent filings for tickers from DB or RSS history
        # For Demo, let's just pick the LATEST accession from filings table for each ticker's CIK
        conn = db.get_connection()
        
        for t in tickers:
            logging.info(f"Starting RAG ingestion for {t}...")
            # Get CIK
            res = conn.execute("SELECT cik FROM companies WHERE ticker = ?", [t]).fetchone()
            if not res:
                logging.warning(f"Ticker {t} not found.")
                continue
            cik = res[0]
            
            # Get latest 10-K or 10-Q ingestion record
            # We look at filings table.
            # Ideally we check what we downloaded in Sprint 1.
            filing_row = conn.execute(f"SELECT accession_number FROM filings WHERE cik='{cik}' ORDER BY filing_date DESC LIMIT 1").fetchone()
            if not filing_row:
                logging.warning(f"No filings found in DB for {t}. Run ingest-rss first or wait for history backfill.")
                # Fallback: Try to ingest RSS specifically for this ticker? 
                # S1 was RSS watcher. If AAPL not in recent RSS, we have no entry.
                # For this demo, user might need to have run RSS.
                continue
                
            accession = filing_row[0]
            
            # Directory: data/filings/{cik}/{accession}/
            base_dir = f"data/filings/{cik}/{accession}"
            index_path = f"{base_dir}/index.html"
            primary_path = f"{base_dir}/primary_doc.html"
            
            if not os.path.exists(index_path):
                logging.warning(f"Index file missing: {index_path}")
                continue
                
            # Resolve Primary Doc
            with open(index_path, "r", encoding="utf-8") as f:
                index_html = f.read()
                
            resolution = FilingResolver.resolve_primary_doc_url(index_html, "")
            if not resolution:
                logging.warning(f"Could not resolve primary doc for {accession}")
                continue
                
            doc_url, filename = resolution
            logging.info(f"Resolved primary doc: {doc_url}")
            
            # Download Primary Doc if not exists
            if not os.path.exists(primary_path):
                logging.info(f"Downloading primary doc...")
                html_content = client.get_filing_html(doc_url)
                if html_content:
                    with open(primary_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                else:
                    logging.error("Failed to download primary doc.")
                    continue
            else:
                with open(primary_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            
            # Process (Chunk)
            logging.info("Chunking document...")
            chunks = processor.process_html(html_content)
            logging.info(f"Generated {len(chunks)} chunks.")
            
            # Embed
            logging.info("Embedding chunks...")
            vectors = embedder.embed_texts(chunks)
            
            # Index
            payloads = [{"text": c, "cik": cik, "ticker": t, "accession": accession, "chunk_index": i} for i, c in enumerate(chunks)]
            store.upsert_batch(vectors, payloads)
            
        conn.close()

    else:
        print(f"Unknown command: {command}")

def _parse_tickers_arg() -> list[str]:
    tickers = []
    if "--tickers" in sys.argv:
        idx = sys.argv.index("--tickers")
        if idx + 1 < len(sys.argv):
            tickers = sys.argv[idx+1].split(",")
    if not tickers:
        logging.info("Using default tickers: AAPL, MSFT")
        return ["AAPL", "MSFT"]
    return [t.strip().upper() for t in tickers]

if __name__ == "__main__":
    main()
