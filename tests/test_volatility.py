
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from pipelines.analytics.volatility import RiskEngine

def test_risk_calculation():
    # Mock Data
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="B")
    # Low Volatility Asset (Close price oscillating slightly)
    # Vol ~ 1% daily? No, that's high. 1% annual? 
    # Let's simple randn * 0.01 (1% daily std -> 16% annual)
    np.random.seed(42)
    returns = np.random.normal(0, 0.01, len(dates))
    price = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({"Close": price, "Date": dates}).set_index("Date")
    
    with patch("pipelines.analytics.volatility.RiskEngine._get_price_series") as mock_get:
        # Mock _get_price_series to return a df that computes the return column internally?
        # No, the logic inside _get_price_series computes Return.
        # But we are mocking _get_price_series directly.
        # So we must provide a df WITH 'Return' col or let the mock return raw price df and we test the calc logic separately?
        # The class method calls _get_price_series then computes logic?
        # Wait, _get_price_series computes return. So we mock it to return a df with returns.
        
        df['Return'] = np.log(df['Close'] / df['Close'].shift(1))
        mock_get.return_value = df
        
        engine = RiskEngine()
        metrics = engine.calculate_volatility("TEST")
        
        assert "risk_score" in metrics
        assert metrics["volatility_annual"] > 0
        # 1% daily * sqrt(252) approx 15.8%
        assert 0.10 < metrics["volatility_annual"] < 0.25
        assert 0 <= metrics["risk_score"] <= 100
