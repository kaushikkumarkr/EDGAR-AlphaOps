
import pytest
from unittest.mock import patch, MagicMock
from pipelines.market.stooq import StooqClient

def test_stooq_download_success():
    # Mock requests.get
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Valid CSV
        mock_resp.content = b"Date,Open,High,Low,Close,Volume\n2023-01-01,100,110,90,105,1000"
        mock_get.return_value = mock_resp
        
        # Mock MinIO
        with patch("pipelines.storage.MinIOClient.put_object") as mock_put:
            client = StooqClient()
            success = client.download_daily_ohlc("AAPL")
            
            assert success is True
            mock_put.assert_called_once()
            args, _ = mock_put.call_args
            assert args[0] == "market/aapl.csv"

def test_stooq_download_no_data():
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = b"No data"
        mock_get.return_value = mock_resp
        
        client = StooqClient()
        success = client.download_daily_ohlc("INVALID")
        
        assert success is False
