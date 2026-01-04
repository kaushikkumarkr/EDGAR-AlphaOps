import pandas as pd
import logging
from typing import List

class QualityGates:
    @staticmethod
    def run_gates(df: pd.DataFrame, context_str: str = "") -> pd.DataFrame:
        """
        Runs a series of checks on the facts DataFrame.
        Returns the cleaned DataFrame (rows might be dropped if critical, or just flags added).
        For this Sprint, we just log warnings for bad data.
        """
        if df.empty:
            return df
            
        # 1. Non-Negative Revenue Check (Example)
        # Assuming 'Revenue' columns exist or we check broadly.
        # Actually SEC data is raw. Some concepts like 'NetIncomeLoss' CAN be negative.
        # 'Revenues' generally shouldn't be negative, but sometimes reclassifications happen.
        # Let's just check for DUPLICATES, which is the most common issue in normalized data.
        
        initial_count = len(df)
        
        # Deduplication based on key columns
        # Key: cik, taxonomy, tag, period details, unit
        # Some filings amend previous ones. We usually want the LATEST filed_date.
        
        if "filed_date" in df.columns:
            # Sort by filed_date descending so we keep the latest
            df = df.sort_values("filed_date", ascending=False)
            
        # Dedupe
        # Identify "Unique Fact" keys
        subset_cols = ["cik", "taxonomy", "tag", "period_start", "period_end", "period_instant", "unit"]
        # Handle nan in key columns for dedupe (pandas handles nan==nan in drop_duplicates usually?)
        df = df.drop_duplicates(subset=subset_cols, keep="first")
        
        deduped_count = len(df)
        if deduped_count < initial_count:
            logging.info(f"[{context_str}] QualityGate: Dropped {initial_count - deduped_count} duplicate facts.")
            
        return df

    @staticmethod
    def check_units(df: pd.DataFrame) -> None:
        # Just a logger for unit variance
        if "unit" in df.columns:
            units = df["unit"].unique()
            if len(units) > 1:
                logging.debug(f"Mixed units found: {units}")
