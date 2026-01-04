import logging
import pandas as pd
from typing import Dict, Any, List
from pipelines.sec.client import SecClient
from lakehouse.db import Database

class CompanyMetadataFetcher:
    def __init__(self) -> None:
        self.client = SecClient()
        self.db = Database()

    def fetch_and_save(self) -> None:
        """
        Fetches company_tickers.json from SEC and updates the companies table.
        """
        url = "https://www.sec.gov/files/company_tickers.json"
        logging.info("Fetching company metadata from SEC...")
        
        try:
            # SEC returns a dict of dicts: {"0": {"cik":..., "ticker":...}, "1": ...}
            resp = self.client._get(url)
            data = resp.json()
            
            # Convert to DataFrame
            # The JSON structure is essentially a list of records indexed by number string
            records = list(data.values())
            df = pd.DataFrame(records)
            
            # Rename columns to match schema
            # SEC keys: cik_str, ticker, title
            df = df.rename(columns={
                "cik_str": "cik",
                "ticker": "ticker",
                "title": "company_name"
            })
            
            # Format CIK as 10-digit string
            df["cik"] = df["cik"].astype(str).str.zfill(10)
            
            logging.info(f"Parsed {len(df)} companies. Saving to Lakehouse...")
            
            self._save_to_db(df)
            
        except Exception as e:
            logging.error(f"Failed to fetch company metadata: {e}")
            raise

    def _save_to_db(self, df: pd.DataFrame) -> None:
        conn = self.db.get_connection()
        try:
            # Upsert logic? DuckDB's INSERT OR REPLACE or Insert Ignore
            # For simplicity, we can do INSERT OR REPLACE if primary key exists.
            # But standard SQL usually merge.
            # Given the scale (10k rows), deleting and re-inserting or just INSERT OR IGNORE is easiest for Sprint 2.
            # Companies don't change often.
            
            # DuckDB generic append
            # But we want to preserve 'created_at' if we re-insert.
            # Let's use INSERT OR REPLACE INTO (DuckDB extension) or just ON CONFLICT DO UPDATE
            
            # Prepare data for insertion (match schema columns)
            # Schema: cik, ticker, company_name, sic, sic_description, exchanges ...
            # The JSON only gives CIK, Ticker, Name.
            # We will fill others as NULL or updated later.
            
            # We iterate and insert.
            conn.execute("BEGIN TRANSACTION")
            
            # Bulk insert is faster. Register DF and Insert.
            conn.register("df_staging", df)
            
            # Upsert
            query = """
                INSERT INTO companies (cik, ticker, company_name)
                SELECT cik, ticker, company_name FROM df_staging
                ON CONFLICT (cik) DO UPDATE SET
                    ticker = EXCLUDED.ticker,
                    company_name = EXCLUDED.company_name,
                    updated_at = now()
            """
            conn.execute(query)
            conn.execute("COMMIT")
            
            logging.info("Company metadata sync complete.")
            
        except Exception as e:
            conn.execute("ROLLBACK")
            logging.error(f"DB Error saving companies: {e}")
            raise
        finally:
            conn.close()
