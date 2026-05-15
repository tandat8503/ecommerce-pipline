"""
transform/transform_customers.py

Nhiệm vụ: Làm sạch bảng customers raw → staging.

Steps:
    1. Drop duplicate customer_id
    2. Normalize city (lowercase + strip)
    3. Normalize state (uppercase + strip)
    4. Fillna unknown
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nhận raw customers DataFrame → trả về cleaned DataFrame.

    Args:
        df: output của read_customers()

    Returns:
        Cleaned DataFrame lưu vào staging/customers.parquet
    """
    logger.info(f"[TRANSFORM] customers — start: {len(df):,} rows")

    # 1. Dedup
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    if (dropped := before - len(df)):
        logger.warning(f"[TRANSFORM] customers — dropped {dropped} duplicate customer_id")

    # 2. Normalize city
    if "customer_city" in df.columns:
        df["customer_city"] = (
            df["customer_city"].fillna("unknown").str.lower().str.strip()
        )

    # 3. Normalize state
    if "customer_state" in df.columns:
        df["customer_state"] = (
            df["customer_state"].fillna("unknown").str.upper().str.strip()
        )

    logger.info(f"[TRANSFORM] customers — done: {len(df):,} rows")
    return df
