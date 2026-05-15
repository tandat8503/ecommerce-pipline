"""
pipeline/transform/transform_payments.py
Clean raw payments data for the staging layer.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean payments: Filter invalid values and format payment types.
    Maintains transaction-level granularity (1 row = 1 payment).
    """
    logger.info(f"[TRANSFORM] payments — start: {len(df):,} rows")
    df = df.copy()

    # Normalize payment type
    if "payment_type" in df.columns:
        df["payment_type"] = df["payment_type"].fillna("unknown").astype(str).str.lower().str.strip()

    # Drop invalid payments
    before_len = len(df)
    df = df[df["payment_value"] >= 0]
    if before_len > len(df):
        logger.warning(f"[TRANSFORM] payments — dropped {before_len - len(df)} rows with negative payment_value")

    # Flag installments
    if "payment_installments" in df.columns:
        df["is_installment"] = df["payment_installments"] > 1

    logger.info(f"[TRANSFORM] payments — done: {len(df):,} rows")
    return df
