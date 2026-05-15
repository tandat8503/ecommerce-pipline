"""
transform/transform_orders.py

Nhiệm vụ: Làm sạch bảng orders raw → orders sạch trong staging.

Steps:
    1. Parse timestamp columns → datetime
    2. Filter chỉ giữ status = 'delivered'
    3. Tạo cột derived: order_date, order_year, order_month, order_quarter
    4. Drop duplicate order_id
"""

import pandas as pd

from pipeline.utils.config import ORDER_STATUS_FILTER
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

_TIMESTAMP_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_timestamp",
    "order_estimated_delivery_date",
]


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nhận raw orders DataFrame → trả về cleaned DataFrame.

    Args:
        df: output của read_orders()

    Returns:
        Cleaned DataFrame lưu vào staging/orders.parquet
    """
    logger.info(f"[TRANSFORM] orders — start: {len(df):,} rows")

    # 1. Parse timestamps
    for col in _TIMESTAMP_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 2. Filter delivered
    before = len(df)
    df = df[df["order_status"] == ORDER_STATUS_FILTER].copy()
    logger.info(
        f"[TRANSFORM] orders — filter '{ORDER_STATUS_FILTER}': "
        f"{before:,} → {len(df):,} rows (removed {before - len(df):,})"
    )

    # 3. Derived columns
    ref = "order_purchase_timestamp"
    df["order_date"]    = df[ref].dt.date
    df["order_year"]    = df[ref].dt.year
    df["order_month"]   = df[ref].dt.month
    df["order_quarter"] = df[ref].dt.quarter
    df["order_dow"]     = df[ref].dt.day_name()

    # 4. Dedup
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    if (dropped := before - len(df)):
        logger.warning(f"[TRANSFORM] orders — dropped {dropped} duplicate order_id")

    logger.info(f"[TRANSFORM] orders — done: {len(df):,} rows")
    return df
