"""
pipeline/transform/transform_orders.py
Clean raw orders data for the staging layer.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

TIMESTAMP_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_timestamp",
    "order_estimated_delivery_date",
]

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean orders: Convert timestamps, extract date components, and deduplicate.
    IMPORTANT: We keep ALL order_statuses here for complete funnel analysis.
    """
    logger.info(f"[TRANSFORM] orders — start: {len(df):,} rows")
    df = df.copy()

    # Deduplicate by order_id
    before_len = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    if before_len > len(df):
        logger.warning(f"[TRANSFORM] orders — dropped {before_len - len(df)} duplicate order_ids")

    # Convert timestamps
    for col in TIMESTAMP_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Extract date components based on purchase timestamp
    ref_col = "order_purchase_timestamp"
    if ref_col in df.columns:
        df["order_date"] = df[ref_col].dt.date
        df["order_year"] = df[ref_col].dt.year
        df["order_month"] = df[ref_col].dt.month
        df["order_quarter"] = df[ref_col].dt.quarter
        df["order_dow"] = df[ref_col].dt.day_name()

    logger.info(f"[TRANSFORM] orders — done: {len(df):,} rows")
    return df
