
import pytest
from unittest.mock import MagicMock, patch
from pipelines.features import FeatureStore

def test_feature_store_build():
    """
    Partial test to verify SQL generation and execution flow.
    We mock the DuckDB connection to avoid needing real Postgres/MinIO.
    """
    with patch("duckdb.connect") as mock_connect:
        mock_db = MagicMock()
        mock_connect.return_value = mock_db
        
        store = FeatureStore()
        store.build_financial_ratios()
        
        # Verify calls
        # 1. Extensions loaded
        assert mock_db.execute.call_count >= 5 
        # 2. Attach Postgres
        mock_db.execute.assert_any_call("INSTALL httpfs; LOAD httpfs;")
        # 3. Validation: Verify COPY command was attempted (Parquet export)
        start_calls = [c[0][0] for c in mock_db.execute.call_args_list if "COPY features TO" in str(c[0][0])]
        assert len(start_calls) == 1
