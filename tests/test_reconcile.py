
import pytest
from unittest.mock import MagicMock, patch
from pipelines.reconcile import Reconciler
from pipelines.models import Filing
from datetime import datetime

class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("HTTP Error")

def test_reconcile_date(db_session):
    # Mock SEC text response
    mock_idx = """Description:           Master Index of EDGAR Dissemination Feed
Last Data Received:    January 3, 2024
Comments:              webmaster@sec.gov
Anonymous FTP:         ftp.sec.gov Cloud HTTP: https://www.sec.gov/Archives/

CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
1000228|HENRY SCHEIN INC|8-K|20240103|edgar/data/1000228/0001000228-24-000001.txt
1000229|CORE LABORATORIES INC|8-K|20240103|edgar/data/1000229/0001000229-24-000001.txt
"""
    
    with patch("pipelines.sec.client.SecClient.get") as mock_get:
        mock_get.return_value = MockResponse(mock_idx)
        
        reconciler = Reconciler(db_session)
        count = reconciler.reconcile_date("20240103")
        
        assert count == 2
        
        # Verify DB
        filing = db_session.query(Filing).filter_by(accession_number="0001000228-24-000001").first()
        assert filing is not None
        assert filing.cik == "1000228"
        assert filing.form_type == "8-K"
        assert filing.url == "https://www.sec.gov/Archives/edgar/data/1000228/0001000228-24-000001.txt"

def test_reconcile_backfill(db_session):
    # Mock reconcile_date
    with patch.object(Reconciler, 'reconcile_date', return_value=5) as mock_date:
        reconciler = Reconciler(db_session)
        total = reconciler.reconcile_backfill("20240101", "20240103")
        
        assert total == 15 # 5 * 3 days
        assert mock_date.call_count == 3
