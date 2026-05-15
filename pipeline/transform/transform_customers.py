"""
pipeline/transform/transform_customers.py
Clean raw customers data for the staging layer.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean customers: Deduplicate and normalize location text.
    """
    logger.info(f"[TRANSFORM] customers — start: {len(df):,} rows")
    df = df.copy()

    # Deduplicate by customer_id
    before_len = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    if before_len > len(df):
        logger.warning(f"[TRANSFORM] customers — dropped {before_len - len(df)} duplicate customer_ids")

    # Normalize text
    if "customer_city" in df.columns:
        df["customer_city"] = df["customer_city"].fillna("unknown").astype(str).str.lower().str.strip()
    
    if "customer_state" in df.columns:
        df["customer_state"] = df["customer_state"].fillna("unknown").astype(str).str.upper().str.strip()

    logger.info(f"[TRANSFORM] customers — done: {len(df):,} rows")
    return df
