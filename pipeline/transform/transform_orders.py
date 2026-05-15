"""
transform/transform_orders.py

Nhiệm vụ: Làm sạch bảng orders raw → staging.

Lưu ý thiết kế (quan trọng):
    - KHÔNG filter order_status ở đây
    - Giữ full status (delivered, canceled, processing, shipped...) để
      phục vụ cả revenue analysis lẫn funnel/cancel analysis
    - Filter delivered chỉ xảy ra tại tầng WAREHOUSE khi build fact_orders

Steps:
    1. Parse timestamp columns → datetime
    2. Tạo cột derived: order_date, order_year, order_month, order_quarter, order_dow
    3. Drop duplicate order_id
"""

import pandas as pd

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
    Làm sạch bảng orders — giữ nguyên toàn bộ order_status.

    Args:
        df: output của read_orders()

    Returns:
        Cleaned DataFrame lưu vào staging/orders.parquet
    """
    df = df.copy()
    logger.info(f"[TRANSFORM] orders — start: {len(df):,} rows")

    # 1. Parse timestamps
    for col in _TIMESTAMP_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 2. Derived time columns từ order_purchase_timestamp
    ref = "order_purchase_timestamp"
    df["order_date"]    = df[ref].dt.date
    df["order_year"]    = df[ref].dt.year
    df["order_month"]   = df[ref].dt.month
    df["order_quarter"] = df[ref].dt.quarter
    df["order_dow"]     = df[ref].dt.day_name()   # Monday, Tuesday...

    # 3. Dedup — giữ lần đầu tiên
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    if (dropped := before - len(df)):
        logger.warning(f"[TRANSFORM] orders — dropped {dropped} duplicate order_id")

    # Log phân phối status để monitoring
    status_dist = df["order_status"].value_counts().to_dict()
    logger.info(f"[TRANSFORM] orders — status distribution: {status_dist}")
    logger.info(f"[TRANSFORM] orders — done: {len(df):,} rows")
    return df
