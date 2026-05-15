"""
transform/transform_payments.py

Nhiệm vụ: Làm sạch bảng payments raw → staging.

Steps:
    1. Normalize payment_type (lowercase + strip)
    2. Drop rows payment_value <= 0
    3. Thêm cột is_installment
    4. Aggregate: nhiều payment_sequential → 1 dòng per order_id
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nhận raw payments DataFrame → trả về cleaned + aggregated DataFrame.

    Lý do aggregate: 1 đơn có thể thanh toán nhiều lần (voucher + credit card).
    Ta gộp lại thành 1 dòng/order để dễ JOIN với fact_orders.

    Args:
        df: output của read_payments()

    Returns:
        Cleaned DataFrame (1 row per order_id) lưu vào staging/payments.parquet
    """
    logger.info(f"[TRANSFORM] payments — start: {len(df):,} rows")

    # 1. Normalize payment_type
    df["payment_type"] = (
        df["payment_type"].str.lower().str.strip().fillna("not_defined")
    )

    # 2. Drop invalid payment value
    before = len(df)
    df = df[df["payment_value"] > 0].copy()
    if (dropped := before - len(df)):
        logger.warning(
            f"[TRANSFORM] payments — dropped {dropped} rows with payment_value <= 0"
        )

    # 3. Installment flag
    df["is_installment"] = df["payment_installments"] > 1

    # 4. Aggregate → 1 row per order_id
    df = df.groupby("order_id", as_index=False).agg(
        payment_type        =("payment_type",         "first"),
        total_payment_value =("payment_value",         "sum"),
        max_installments    =("payment_installments",  "max"),
        is_installment      =("is_installment",        "any"),
    )

    logger.info(f"[TRANSFORM] payments — done: {len(df):,} rows (1 per order)")
    return df
