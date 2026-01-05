
import requests
import logging
from datetime import datetime
from pipelines.sec.client import SecClient
from pipelines.models import Filing, FilingState
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class Reconciler:
    def __init__(self, session: Session):
        self.session = session
        self.client = SecClient()
        self.base_url = "https://www.sec.gov/Archives/edgar/daily-index"

    def reconcile_date(self, date_str: str): # YYYYMMDD
        """
        Downloads master.idx for the given date (qtr logic needed) and ensuring all filings exist.
        URL Format: https://www.sec.gov/Archives/edgar/daily-index/2024/QTR1/master.20240103.idx
        """
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        year = date_obj.year
        qtr = (date_obj.month - 1) // 3 + 1
        
        url = f"{self.base_url}/{year}/QTR{qtr}/master.{date_str}.idx"
        logger.info(f"Reconciling Index: {url}")
        
        try:
            resp = self.client.get(url)
            # Parse Lines
            lines = resp.text.splitlines()
            logger.info(f"Downloaded Index. Lines: {len(lines)}")
            
            # 1. Parse all accessions from file
            file_accessions = {} # accession -> {cik, form, ...}
            
            start_parsing = False
            for line in lines:
                if "CIK|Company Name" in line:
                    start_parsing = True
                    continue
                if not start_parsing or not line.strip():
                    continue

                parts = line.split("|")
                if len(parts) < 5:
                    continue
                
                cik = parts[0]
                form_type = parts[2]
                filename = parts[4]
                accession = filename.split("/")[-1].replace(".txt", "")
                
                file_accessions[accession] = {
                    "cik": cik,
                    "form_type": form_type,
                    "filename": filename,
                    "filed_at": date_obj
                }
            
            # 2. Bulk Fetch Existing
            existing_accessions = set()
            # Chunking for VERY large datasets, but for sprint proof 100k is fine in memory for set
            # Or query just accessions
            existing_query = self.session.query(Filing.accession_number).all()
            existing_accessions = {r[0] for r in existing_query}
            
            # 3. Determine Missing
            missing = [acc for acc in file_accessions if acc not in existing_accessions]
            
            # 4. Bulk Insert
            logger.info(f"Found {len(missing)} missing filings (from {len(file_accessions)} total)")
            
            batch = []
            new_count = 0
            for acc in missing:
                meta = file_accessions[acc]
                full_url = f"https://www.sec.gov/Archives/{meta['filename']}"
                
                filing = Filing(
                    accession_number=acc,
                    cik=meta["cik"],
                    form_type=meta["form_type"],
                    filed_at=meta["filed_at"],
                    url=full_url,
                    state=FilingState.PENDING
                )
                self.session.add(filing)
                new_count += 1
                
                if new_count % 1000 == 0:
                    self.session.commit()
            
            self.session.commit()
            logger.info(f"Reconciliation Complete. Added {new_count}")
            return new_count
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Index not found for {date_str} (Weekends/Holidays?): {e}")
                return 0
            raise
        except Exception as e:
            logger.error(f"Reconcile Failed: {e}")
            raise

    def reconcile_backfill(self, start_date: str, end_date: str):
        """
        Reconciles a range of dates [start_date, end_date].
        """
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")
        
        current = start
        total_added = 0
        from datetime import timedelta
        
        while current <= end:
            date_str = current.strftime("%Y%m%d")
            try:
                count = self.reconcile_date(date_str)
                total_added += count
            except Exception as e:
                logger.error(f"Failed to reconcile {date_str}: {e}")
                # Continue to next day
            
            current += timedelta(days=1)
            
        return total_added
