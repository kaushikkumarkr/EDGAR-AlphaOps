import feedparser
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pipelines.sec.client import SecClient
from lakehouse.db import Database
from pathlib import Path
import os

class RssWatcher:
    def __init__(self) -> None:
        self.client = SecClient()
        self.db = Database()
        self.settings = self.db.settings
        self.filings_dir = Path(self.settings.DATA_DIR) / "filings"
        self.filings_dir.mkdir(parents=True, exist_ok=True)

    def _parse_accession(self, id_str: str) -> str:
        # id is like "urn:tag:sec.gov,2008:accession-number=0001062993-24-000001"
        # or simplified in some feeds. Usually we extract from link or string.
        # In Atom feed: <id>urn:tag:sec.gov,2008:accession-number=0001140361-24-000123</id>
        if "accession-number=" in id_str:
            return id_str.split("accession-number=")[1]
        return id_str

    def _extract_cik(self, title: str) -> str:
        # Title format: "10-Q - Company Name (0001234567) (Filer)"
        # Regex is better but simple split might work for now.
        import re
        match = re.search(r'\((\d{10})\)', title)
        if match:
            return match.group(1)
        return "UNKNOWN"

    def _is_processed(self, accession: str) -> bool:
        conn = self.db.get_connection()
        try:
            res = conn.execute("SELECT 1 FROM filings WHERE accession_number = ?", [accession]).fetchone()
            return res is not None
        finally:
            conn.close()

    def _save_meta(self, meta: Dict[str, Any]) -> None:
        conn = self.db.get_connection()
        try:
            conn.execute("""
                INSERT INTO filings (accession_number, cik, company_name, form_type, filing_date, primary_doc_url, filing_html_path, report_period)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                meta["accession"],
                meta["cik"],
                meta["company_name"],
                meta["form"],
                meta["filing_date"],
                meta["url"],
                str(meta["path"]),
                meta.get("report_period") # Optional
            ])
            logging.info(f"Saved metadata for {meta['accession']}")
        except Exception as e:
            logging.error(f"DB Error saving {meta['accession']}: {e}")
        finally:
            conn.close()

    def run_cycle(self) -> None:
        content = self.client.get_rss_feed(count=100)
        feed = feedparser.parse(content)
        
        logging.info(f"Found {len(feed.entries)} entries in RSS feed.")
        
        for entry in feed.entries:
            # Example entry keys: title, link, updated, id, summary
            # title: "8-K - APPLE INC (0000320193) (Filer)"
            accession = self._parse_accession(entry.id)
            
            if self._is_processed(accession):
                continue
                
            form_type = entry.get("category", "")
            # Basic filters: only 10-K, 10-Q, 8-K for now
            # Relaxing for Sprint 1 verification if no major filings are found
            if form_type not in ["10-K", "10-Q", "8-K", "4", "SC 13G", "SC 13D"]:
                logging.debug(f"Skipping form: {form_type}")
                continue
                
            logging.info(f"Processing {form_type} for {entry.title}")
                
            cik = self._extract_cik(entry.title)
            company_name = entry.title.split("(")[0].replace(f"{form_type} - ", "").strip()
            
            # Link in feed is to the summary page usually, e.g. http://www.sec.gov/Archives/edgar/data/320193/000032019324000001/0000320193-24-000001-index.htm
            # We want the text/html document.
            # Usually strict mapping: data/{cik}/{accession_no_dashes}/{primary_doc}
            # BUT determining primary doc name from RSS is hard without scraping index page.
            # SHORTCUT: The RSS "link" usually goes to the index page. We might need to grab the HTML from there.
            # HOWEVER, for simplicity in MVP, we can try to construct a "txt" url which is the full submission, or parse the index.
            
            # Let's simple scrape the index page to find the primary document link?
            # Or use the .txt full submission (contains UGLY uuencoded files).
            # BETTER: The "link" href in Atom often points to the summary.
            
            # Let's assume we fetch the link provided (Index page) and find the first row "Document".
            # For Sprint 1, let's just save the link provided in the RSS as "primary" and download THAT check if it is HTML.
            # Actually, the RSS link is usually the index page.
            index_url = entry.link
            
            # Download Logic
            # 1. Create directory
            filing_path = self.filings_dir / cik / accession
            filing_path.mkdir(parents=True, exist_ok=True)
            
            # 2. Fetch Index Page to find real HTML document? 
            # This adds 1 extra request per filing. total 2 req/filing.
            # Let's skip deep parsing for now and just save the index page or try to find the .htm link if obvious.
            # If we want the text content for RAG, the full .txt submission is easiest to parse programmatically but huge.
            # Let's stick to downloading the content at `link` for now, recognizing it might be an index page.
            # TODO: Improve to fetch actual report HTML in refinement.
            
            local_file = filing_path / "index.html"
            html_content = self.client.get_filing_html(index_url)
            
            with open(local_file, "w") as f:
                f.write(html_content)
                
            # Save Metadata
            filing_meta = {
                "accession": accession,
                "cik": cik,
                "company_name": company_name,
                "form": form_type,
                "filing_date": datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%S%z").date(),
                "url": index_url,
                "path": local_file,
                "report_period": None # Need to parse from body
            }
            
            self._save_meta(filing_meta)
