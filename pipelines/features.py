
import duckdb
import logging
from config import get_settings
from pipelines.storage import MinIOClient

logger = logging.getLogger(__name__)
settings = get_settings()

class FeatureStore:
    def __init__(self):
        self.db = duckdb.connect(database=":memory:")
        self._setup_extensions()
        
    def _setup_extensions(self):
        self.db.execute("INSTALL httpfs; LOAD httpfs;")
        self.db.execute("INSTALL postgres; LOAD postgres;")
        
        # MinIO Config
        self.db.execute(f"""
            SET s3_endpoint='{settings.MINIO_ENDPOINT.replace('http://', '')}';
            SET s3_access_key_id='{settings.MINIO_ACCESS_KEY}';
            SET s3_secret_access_key='{settings.MINIO_SECRET_KEY}';
            SET s3_use_ssl=false;
            SET s3_url_style='path';
        """)

    def build_financial_ratios(self):
        """
        Joins Postgres Facts with Market Data (Parquet/CSV) to compute ratios.
        """
        # 1. Attach Postgres (for Facts)
        # Note: In docker, host is 'postgres'. Locally 'localhost'.
        # We need a connection string that works from where this runs (Worker).
        pg_dsn = f"dbname=edgar_ops user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} host={settings.POSTGRES_HOST} port=5432"
        
        try:
            self.db.execute(f"ATTACH '{pg_dsn}' AS pg (TYPE POSTGRES);")
        except Exception as e:
            logger.error(f"Failed to attach Postgres: {e}")
            raise

        # 2. SQL Feature Engineering
        # We join Market Data (CSV via httpfs) with Fundamental Facts (Postgres)
        # Note: We assume Ticker-CIK mapping exists in 'companies' table or we just loop known tickers for this Sprint.
        
        logger.info("Building Feature Store via DuckDB...")
        
        # Load market data from MinIO (Wildcard)
        # Assuming market/*.csv
        market_path = f"s3://{settings.MINIO_BUCKET_RAW}/market/*.csv"
        
        query = f"""
        CREATE OR REPLACE TABLE features AS
        WITH market_data AS (
            SELECT 
                replace(filename, '.csv', '') as ticker, -- Extract ticker from filename logic roughly
                Date as date,
                Close as close_price,
                Volume as volume
            FROM read_csv_auto('{market_path}', filename=true)
        ),
        fundamentals AS (
            SELECT 
                f.cik,
                fact.period_end as date,
                fact.concept,
                CAST(fact.value AS DOUBLE) as val
            FROM pg.facts fact
            JOIN pg.filings f ON fact.filing_accession = f.accession_number
            WHERE fact.period_end IS NOT NULL
        ),
        pivoted_funds AS (
            SELECT 
                cik, 
                date,
                MAX(CASE WHEN concept='us-gaap:Assets' THEN val END) as assets,
                MAX(CASE WHEN concept='us-gaap:NetIncomeLoss' THEN val END) as net_income,
                MAX(CASE WHEN concept='us-gaap:StockholdersEquity' THEN val END) as equity
            FROM fundamentals
            GROUP BY 1, 2
        ),
        -- We need CIK-Ticker Map. For Sprint 2/3 we might lack a robust one locally.
        -- Let's assume we have it in 'pg.companies' or we do a best effort join if possible.
        -- If not, we just output market features for now.
        enriched AS (
            SELECT 
                m.ticker,
                m.date,
                m.close_price,
                m.volume,
                f.assets,
                f.net_income,
                -- Derived Ratios (Lagged fundamentals usually, but doing direct join for simplicity)
                (m.close_price / NULLIF(f.net_income, 0)) as pe_ratio_approx
            FROM market_data m
            LEFT JOIN pg.companies c ON lower(c.ticker) = lower(m.ticker) -- Ticker map
            LEFT JOIN pivoted_funds f ON f.cik = c.cik AND f.date = m.date
        )
        SELECT 
            *,
            -- Simple RSI Implementation (Window Function)
            -- checking if we can do this in DuckDB SQL directly usually requires more verbose SQL
            -- or python UDF. For now, let's just output the base features.
            row_number() OVER (PARTITION BY ticker ORDER BY date) as rn
        FROM enriched
        ORDER BY ticker, date
        """
        
        try:
            self.db.execute(query)
            
            # Export to Parquet
            export_key = f"s3://{settings.MINIO_BUCKET_RAW}/features/daily_v1.parquet"
            self.db.execute(f"COPY features TO '{export_key}' (FORMAT PARQUET)")
            logger.info(f"Features built and exported to {export_key}")
            
        except Exception as e:
            logger.error(f"Feature Build Failed: {e}")
            raise

