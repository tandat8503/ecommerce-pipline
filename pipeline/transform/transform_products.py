"""
pipeline/transform/transform_products.py
Clean raw products data for the staging layer.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

NUMERIC_COLS = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean products: Deduplicate, handle null categories, and impute missing numerics.
    """
    logger.info(f"[TRANSFORM] products — start: {len(df):,} rows")
    df = df.copy()

    # Deduplicate by product_id
    before_len = len(df)
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    if before_len > len(df):
        logger.warning(f"[TRANSFORM] products — dropped {before_len - len(df)} duplicate product_ids")

    # Handle category
    if "product_category_name" in df.columns:
        df["product_category_name"] = df["product_category_name"].fillna("unknown").astype(str).str.lower().str.strip()

    # Impute numeric columns with median
    for col in NUMERIC_COLS:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    logger.info(f"[TRANSFORM] products — done: {len(df):,} rows")
    return df
