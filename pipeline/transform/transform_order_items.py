"""
transform_order_items.py — Transform layer cho bảng Order Items.

Nhiệm vụ:
  1. Drop rows có price <= 0 (invalid)
  2. Tính total_amount = price + shipping_charges
  3. Drop duplicate (order_id + product_id)
"""

import pandas as pd

from pipeline.config import MIN_PRICE
from pipeline.logger import get_logger

logger = get_logger(__name__)


def _drop_invalid_price(df: pd.DataFrame) -> pd.DataFrame:
    """Loại bỏ dòng có giá không hợp lệ (price <= 0)."""
    before = len(df)
    df = df[df["price"] > MIN_PRICE].copy()
    dropped = before - len(df)
    if dropped:
        logger.warning(
            f"[TRANSFORM order_items] Dropped {dropped} rows with price <= {MIN_PRICE}"
        )
    return df


def _add_total_amount(df: pd.DataFrame) -> pd.DataFrame:
    """Tạo cột total_amount = price + shipping_charges."""
    df["total_amount"] = df["price"].fillna(0) + df["shipping_charges"].fillna(0)
    return df


def _drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate (order_id, product_id) — giữ dòng đầu tiên."""
    before = len(df)
    df = df.drop_duplicates(subset=["order_id", "product_id"], keep="first")
    dropped = before - len(df)
    if dropped:
        logger.warning(
            f"[TRANSFORM order_items] Dropped {dropped} duplicate (order_id, product_id) rows"
        )
    return df


def transform_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hàm chính: nhận raw order_items DataFrame, trả về cleaned DataFrame.

    Args:
        df: DataFrame thô từ extract layer

    Returns:
        DataFrame đã được làm sạch
    """
    logger.info(f"[TRANSFORM order_items] Start — {len(df):,} rows")

    df = (
        df
        .pipe(_drop_invalid_price)
        .pipe(_add_total_amount)
        .pipe(_drop_duplicates)
    )

    logger.info(f"[TRANSFORM order_items] Done — {len(df):,} rows")
    return df
