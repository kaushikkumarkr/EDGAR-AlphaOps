
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from pipelines.analytics.event_study import EventStudy
from pipelines.models import Filing, Company
from datetime import datetime, timedelta

def test_event_study_calculation(db_session):
    # 1. Setup Data
    # Filing
    filing = Filing(
        accession_number="001",
        cik="100",
        state="PROCESSED",
        filed_at=datetime(2023, 6, 1)
    )
    # Company
    company = Company(cik="100", ticker="TEST")
    db_session.add(filing)
    db_session.add(company)
    db_session.commit()
    
    # Mock Data Frames
    dates = pd.date_range(start="2023-01-01", end="2023-07-01", freq="B")
    
    # Market (Spy) - Up 1% daily
    market_data = pd.DataFrame({
        "Close": np.linspace(100, 200, len(dates)),
        "Date": dates
    }).set_index("Date")
    
    # Stock (Test) - perfectly correlated (Beta=2, Alpha=0)
    stock_data = pd.DataFrame({
        "Close": np.linspace(10, 40, len(dates)), # steeper slope
        "Date": dates 
    }).set_index("Date")
    
    # 2. Mock EventStudy dependencies
    with patch("pipelines.analytics.event_study.EventStudy._get_price_series") as mock_get_price:
        def side_effect(ticker):
             # Need to return df with "Return" column calculated as in _get_price_series
             if ticker == "SPY":
                 df = market_data.copy()
             else:
                 df = stock_data.copy()
             df['Return'] = np.log(df['Close'] / df['Close'].shift(1))
             return df
             
        mock_get_price.side_effect = side_effect
        
        # 3. Run
        study = EventStudy(db_session)
        result = study.calculate_car("001")
        
        assert "CAR" in result
        
        # Verify Analysis Model Saved
        from pipelines.models import FilingAnalysis
        analysis = db_session.query(FilingAnalysis).filter_by(filing_accession="001").first()
        assert analysis is not None
        assert analysis.beta > 0
        # Beta approx 1.x?
