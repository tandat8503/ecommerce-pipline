"""
validate/validate_orders.py

Kiểm tra chất lượng bảng orders SAU khi clean, TRƯỚC khi load staging.

2 mức severity:
    CRITICAL → raise Exception → dừng pipeline ngay
    WARNING  → log cảnh báo   → pipeline tiếp tục chạy
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def validate_orders(df: pd.DataFrame) -> None:
    """
    Chạy tất cả data quality checks cho bảng orders.

    Raises:
        ValueError nếu có bất kỳ lỗi CRITICAL nào
    """
    logger.info(f"[VALIDATE] orders — running checks on {len(df):,} rows...")
    errors: list[str] = []

    # ── CRITICAL: order_id ────────────────────────────────────────────
    null_ids = df["order_id"].isnull().sum()
    if null_ids > 0:
        errors.append(f"order_id: {null_ids} null values")

    dup_ids = df["order_id"].duplicated().sum()
    if dup_ids > 0:
        errors.append(f"order_id: {dup_ids} duplicates")

    # ── CRITICAL: Chỉ được có 'delivered' sau filter ──────────────────
    bad_status = (df["order_status"] != "delivered").sum()
    if bad_status > 0:
        errors.append(f"order_status: {bad_status} rows != 'delivered'")

    # ── CRITICAL: customer_id không được null ─────────────────────────
    null_cust = df["customer_id"].isnull().sum()
    if null_cust > 0:
        errors.append(f"customer_id: {null_cust} null values")

    # Raise nếu có lỗi CRITICAL
    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] orders ❌ {err}")
        raise ValueError(
            f"[VALIDATE] orders FAILED — {len(errors)} critical error(s): {errors}"
        )

    # ── WARNING: timestamp ────────────────────────────────────────────
    null_ts = df["order_purchase_timestamp"].isnull().sum()
    if null_ts > 0:
        logger.warning(f"[VALIDATE] orders ⚠️  {null_ts} null order_purchase_timestamp")

    # ── WARNING: derived columns ──────────────────────────────────────
    for col in ["order_date", "order_year", "order_month", "order_quarter"]:
        if col not in df.columns:
            logger.warning(f"[VALIDATE] orders ⚠️  missing derived column '{col}'")

    logger.info(f"[VALIDATE] orders ✅ PASSED")


def validate_customers(df: pd.DataFrame) -> None:
    logger.info(f"[VALIDATE] customers — running checks on {len(df):,} rows...")
    errors: list[str] = []

    if df["customer_id"].isnull().sum() > 0:
        errors.append(f"customer_id: {df['customer_id'].isnull().sum()} nulls")
    if df["customer_id"].duplicated().sum() > 0:
        errors.append(f"customer_id: {df['customer_id'].duplicated().sum()} duplicates")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] customers ❌ {err}")
        raise ValueError(f"[VALIDATE] customers FAILED: {errors}")

    logger.info(f"[VALIDATE] customers ✅ PASSED")


def validate_products(df: pd.DataFrame) -> None:
    logger.info(f"[VALIDATE] products — running checks on {len(df):,} rows...")
    errors: list[str] = []

    if df["product_id"].isnull().sum() > 0:
        errors.append(f"product_id: {df['product_id'].isnull().sum()} nulls")
    if df["product_id"].duplicated().sum() > 0:
        errors.append(f"product_id: {df['product_id'].duplicated().sum()} duplicates")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] products ❌ {err}")
        raise ValueError(f"[VALIDATE] products FAILED: {errors}")

    logger.info(f"[VALIDATE] products ✅ PASSED")


def validate_payments(df: pd.DataFrame) -> None:
    logger.info(f"[VALIDATE] payments — running checks on {len(df):,} rows...")
    errors: list[str] = []

    if df["order_id"].isnull().sum() > 0:
        errors.append(f"order_id: {df['order_id'].isnull().sum()} nulls")
    if (df["total_payment_value"] <= 0).sum() > 0:
        errors.append(
            f"total_payment_value: {(df['total_payment_value'] <= 0).sum()} rows <= 0"
        )

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] payments ❌ {err}")
        raise ValueError(f"[VALIDATE] payments FAILED: {errors}")

    logger.info(f"[VALIDATE] payments ✅ PASSED")


def validate_staging(tables: dict[str, pd.DataFrame]) -> None:
    """Validate tất cả staging tables cùng lúc."""
    logger.info("[VALIDATE] ── Validating staging tables ──")
    validate_orders(tables["orders"])
    validate_customers(tables["customers"])
    validate_products(tables["products"])
    validate_payments(tables["payments"])
    logger.info("[VALIDATE] ── All staging tables PASSED ✅ ──")
