"""
pipeline/transform/transform_order_items.py
Clean raw order_items data for the staging layer.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean order items: Ensure price and shipping are non-negative and add total value.
    """
    logger.info(f"[TRANSFORM] order_items — start: {len(df):,} rows")
    df = df.copy()

    # Ensure valid numbers
    for col in ["price", "shipping_charges"]:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)
            df.loc[df[col] < 0, col] = 0.0

    # Calculate item_total
    if "price" in df.columns and "shipping_charges" in df.columns:
        df["item_total"] = df["price"] + df["shipping_charges"]

    logger.info(f"[TRANSFORM] order_items — done: {len(df):,} rows")
    return df
