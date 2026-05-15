"""
transform/transform_products.py

Nhiệm vụ: Làm sạch bảng products raw → staging.

Steps:
    1. Drop duplicate product_id
    2. Normalize category name
    3. Fillna numeric columns với median
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

_NUMERIC_COLS = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nhận raw products DataFrame → trả về cleaned DataFrame.

    Args:
        df: output của read_products()

    Returns:
        Cleaned DataFrame lưu vào staging/products.parquet
    """
    logger.info(f"[TRANSFORM] products — start: {len(df):,} rows")

    # 1. Dedup
    before = len(df)
    df = df.drop_duplicates(subset=["product_id"], keep="first")
    if (dropped := before - len(df)):
        logger.warning(f"[TRANSFORM] products — dropped {dropped} duplicate product_id")

    # 2. Normalize category
    df["product_category_name"] = (
        df["product_category_name"]
        .fillna("unknown")
        .str.lower()
        .str.strip()
    )

    # 3. Fillna numeric với median (ít bị ảnh hưởng bởi outlier hơn mean)
    for col in _NUMERIC_COLS:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                logger.info(
                    f"[TRANSFORM] products — '{col}': "
                    f"filled {null_count} nulls with median={median_val:.1f}"
                )

    logger.info(f"[TRANSFORM] products — done: {len(df):,} rows")
    return df
