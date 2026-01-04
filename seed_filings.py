from lakehouse.db import Database
from datetime import date

def seed_aapl_10k():
    db = Database()
    conn = db.get_connection()
    try:
        # AAPL 10-K (Filed 2023-11-03)
        accession = "0000320193-23-000106"
        cik = "0000320193"
        ticker = "AAPL"
        company_name = "Apple Inc."
        form_type = "10-K"
        filing_date = date(2023, 11, 3)
        report_period = date(2023, 9, 30)
        # We don't need primary_doc_url strictly if ingest-rag resolves it from index?
        # apps/cli.py constructs base_dir and index_path.
        # It needs the record in DB to trigger processing.
        # But wait, logic says: if not os.path.exists(index_path): continue
        # Apps/cli.py tries to resolve locally? 
        # Line 147: if not os.path.exists(index_path): logging.warning("Index file missing")
        # WAIT. apps/cli.py assumes the filing (RSS) has already downloaded the index page!
        
        # S1 RSS downloader saves index.html locally.
        # S4 RAG ingest assumes local file exists?
        # Let's check apps/cli.py line 147 again.
        
        # If apps/cli.py REQUIRES local file, I must download it too.
        # I can modify seed script to also download the index page.
        pass
        
    finally:
        conn.close()

if __name__ == "__main__":
    # Correction: The current CLI logic expects the 'index.html' to be present locally.
    # It says "Run ingest-rss first".
    # So I must simulate what ingest-rss does: Download index.html to data/filings/{cik}/{accession}/index.html
    # AND insert DB record.
    
    import os
    import requests
    from pipelines.sec.client import SecClient
    
    client = SecClient()
    
    # AAPL 10-K 2023
    cik = "0000320193"
    accession = "0000320193-23-000106"
    accession_no_dash = accession.replace("-", "")
    # RSS link usually points to index page
    index_url = f"https://www.sec.gov/Archives/edgar/data/320193/{accession_no_dash}/{accession}-index.htm"
    # Actually for 2023 it might be -index.htm or .txt
    
    print(f"Downloading index from {index_url}...")
    html = client.get_filing_html(index_url)
    
    # Save locally
    base_dir = f"data/filings/{cik}/{accession}"
    os.makedirs(base_dir, exist_ok=True)
    with open(f"{base_dir}/index.html", "w") as f:
        f.write(html)
        
    # Insert DB
    db = Database()
    conn = db.get_connection()
    try:
        conn.execute(f"""
            INSERT OR REPLACE INTO filings (accession_number, cik, ticker, company_name, form_type, filing_date, report_period)
            VALUES ('{accession}', '{cik}', 'AAPL', 'Apple Inc.', '10-K', '2023-11-03', '2023-09-30')
        """)
        print("Seeded AAPL 10-K into DB.")
    finally:
        conn.close()
