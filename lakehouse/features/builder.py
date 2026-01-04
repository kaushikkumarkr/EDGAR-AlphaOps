import logging
import duckdb
from lakehouse.db import Database

class FeatureBuilder:
    def __init__(self) -> None:
        self.db = Database()

    def build_features(self, ticker: str) -> None:
        """
        Construct features for a ticker by joining filings, facts, and prices.
        """
        logging.info(f"Building features for {ticker}...")
        conn = self.db.get_connection()
        try:
            # 1. Get CIK for ticker
            res = conn.execute("SELECT cik FROM companies WHERE ticker = ?", [ticker]).fetchone()
            if not res:
                logging.warning(f"Ticker {ticker} not found.")
                return
            cik = res[0]

            # 2. Key Query: Fundamental Features (YoY Growth)
            # We target 'Revenues' and 'NetIncomeLoss' for Sprint 3 MVP
            # We want to pivot the facts to get (cik, period_end, revenue, net_income)
            
            # Note: "Revenues" tag might vary. Using 'Revenues' or 'RevenueFromContractWithCustomer...'
            # For this MVP, we rely on the data we saw in Sprint 2 (tag='Revenues').
            
            # Step A: Create a temp view of fundamentals
            conn.execute(f"""
                CREATE OR REPLACE TEMP TABLE tmp_fundamentals AS
                SELECT 
                    period_end,
                    MAX(CASE WHEN tag IN ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax') THEN value ELSE NULL END) as revenue,
                    MAX(CASE WHEN tag = 'NetIncomeLoss' THEN value ELSE NULL END) as net_income
                FROM xbrl_facts
                WHERE cik = '{cik}' AND period_end IS NOT NULL
                GROUP BY period_end
                ORDER BY period_end
            """)

            # Step B: Calculate Growth and Margin
            # Self-join for YoY
            conn.execute(f"""
                CREATE OR REPLACE TEMP TABLE tmp_feats AS
                SELECT
                    current.period_end,
                    current.revenue,
                    current.net_income,
                    (current.net_income / NULLIF(current.revenue, 0)) as net_margin,
                    (current.revenue - prev.revenue) / NULLIF(prev.revenue, 0) as revenue_growth_yoy
                FROM tmp_fundamentals current
                LEFT JOIN tmp_fundamentals prev 
                    ON current.period_end = prev.period_end + INTERVAL 1 YEAR
                    -- DuckDB interval math: check syntax. usually + INTERVAL '1' YEAR
            """)

            # Step C: Join with Prices
            # We want price at 'period_end' (or closest trading day after filing date... but let's use period_end for "asof" alignment simplicity in MVP, 
            # OR better: use FILING date. 
            # In Sprint 2 we saw 'filed_date' in facts.
            # Let's improve the aggregation to include filed_date.
            
            # Refined Approach: 
            # We need to output to 'features' table: cik, asof_date, period_end...
            # We'll simple INSERT based on available computations.
            
            # Let's pivot to using pure SQL Insert
            conn.execute(f"""
                INSERT INTO features (cik, ticker, asof_date, period_end, revenue_ttm, net_income_ttm, revenue_growth_yoy, net_margin, created_at)
                SELECT
                    '{cik}' as cik,
                    '{ticker}' as ticker,
                    f.period_end as asof_date, -- Using period end as proxy for now
                    f.period_end,
                    f.revenue,
                    f.net_income,
                    f.revenue_growth_yoy,
                    f.net_margin,
                    current_timestamp
                FROM tmp_feats f
                WHERE f.revenue IS NOT NULL
                ON CONFLICT (cik, asof_date) DO UPDATE SET
                    revenue_ttm = EXCLUDED.revenue_ttm,
                    revenue_growth_yoy = EXCLUDED.revenue_growth_yoy,
                    net_margin = EXCLUDED.net_margin
            """)
            
            logging.info(f"Features built for {ticker}.")

        except Exception as e:
            logging.error(f"Error building features for {ticker}: {e}")
        finally:
            conn.close()
