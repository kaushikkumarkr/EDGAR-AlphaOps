import logging
import pandas as pd
import json
from typing import Optional, List
from pipelines.sec.client import SecClient
from lakehouse.db import Database
from pipelines.xbrl.quality_gates import QualityGates

class XbrlFactsFetcher:
    def __init__(self) -> None:
        self.client = SecClient()
        self.db = Database()

    def fetch_facts(self, cik: str, taxonomy: str = "us-gaap") -> None:
        """
        Fetch all company facts for a CIK (all taxonomies returned in one JSON usually).
        URL: https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
        """
        # CIK must be 10 digits
        cik = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        
        logging.info(f"Fetching XBRL facts for CIK {cik}...")
        try:
            resp = self.client._get(url)
            data = resp.json()
            
            # Structure:
            # { "cik": ..., "entityName": ..., "facts": { "us-gaap": { "AccountsPayableCurrent": { "units": { "USD": [ { "start":..., "end":..., "val":..., "accn":... } ] } } } } }
            
            facts_container = data.get("facts", {})
            if not facts_container:
                logging.warning(f"No facts found for CIK {cik}")
                return

            all_records = []
            
            # Iterate taxonomies (us-gaap, dei, etc)
            for tax_name, concepts in facts_container.items():
                if taxonomy and taxonomy != "all" and tax_name != taxonomy:
                    # If user specified specific taxonomy, skip. But usually we want all or us-gaap.
                    # Let's ingest 'us-gaap' and 'dei' mostly.
                    pass 
                
                # Concepts
                for tag, tag_data in concepts.items():
                    # Units
                    for unit, facts_list in tag_data.get("units", {}).items():
                        for fact in facts_list:
                            # Fact keys: start, end, val, accn, fy, fp, form, filed, frame
                            # Some are instant (no start/end, just 'end' usually?)
                            # Actually SEC JSON uses 'end' as the instant date for balance sheet items.
                            # And 'start' + 'end' for duration items.
                            
                            record = {
                                "cik": cik,
                                "taxonomy": tax_name,
                                "tag": tag,
                                "period_start": fact.get("start"),
                                "period_end": fact.get("end"),
                                "period_instant": None, # Logic below
                                "unit": unit,
                                "value": fact.get("val"),
                                "accession_number": fact.get("accn"),
                                "fy": fact.get("fy"),
                                "fp": fact.get("fp"),
                                "form": fact.get("form"),
                                "filed_date": fact.get("filed"),
                                "frame": fact.get("frame")
                            }
                            
                            # Handle Instant vs Duration
                            # If 'start' is missing, it's an Instant fact (Balance Sheet)
                            if "start" not in fact:
                                record["period_instant"] = fact.get("end") # The metadata uses 'end' key for instant date too
                                record["period_end"] = None
                            
                            all_records.append(record)

            if not all_records:
                logging.warning(f"No records parsed for CIK {cik}")
                return

            df = pd.DataFrame(all_records)
            
            # Quality Gates
            df = QualityGates.run_gates(df, context_str=f"CIK {cik}")
            
            # Save
            self._save_facts(df)
            
        except Exception as e:
            logging.error(f"Error fetching/saving facts for {cik}: {e}")
            # Don't raise, just log so loop continues?
            raise

    def _save_facts(self, df: pd.DataFrame) -> None:
        conn = self.db.get_connection()
        try:
            # Huge insert usually.
            logging.info(f"Inserting {len(df)} facts into Lakehouse...")
            conn.register("df_facts", df)
            
            # We assume clean insert for now. Dedupe handled in QualityGates broadly.
            # But really we should DELETE existing for this CIK/Taxonomy or use upsert.
            # For idempotent re-runs, let's DELETE WHERE CIK = ?
            # This is safer than complex upsert on millions of rows.
            
            ciks = df["cik"].unique()
            for c in ciks:
                conn.execute("DELETE FROM xbrl_facts WHERE cik = ?", [c])
            
            conn.execute("""
                INSERT INTO xbrl_facts 
                (cik, taxonomy, tag, period_start, period_end, period_instant, unit, value, accession_number, fy, fp, form, filed_date, frame)
                SELECT 
                    cik, taxonomy, tag, period_start, period_end, period_instant, unit, value, accession_number, fy, fp, form, filed_date, frame 
                FROM df_facts
            """)
            logging.info("Insert complete.")
            
        finally:
            conn.close()
