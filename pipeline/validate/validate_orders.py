"""
validate/validate_orders.py

Kiểm tra chất lượng bảng staging SAU transform, TRƯỚC khi load.

Nguyên tắc:
    - CRITICAL → raise ValueError → dừng pipeline
    - WARNING  → log cảnh báo   → pipeline tiếp tục

Lưu ý thiết kế:
    Validate staging KHÔNG check order_status == delivered.
    Staging giữ full status. Chỉ validate order_status nằm trong
    VALID_ORDER_STATUSES (whitelist) để phát hiện giá trị lạ/lỗi.
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Tất cả status hợp lệ trong dataset Olist
VALID_ORDER_STATUSES = {
    "delivered",
    "shipped",
    "canceled",
    "processing",
    "invoiced",
    "unavailable",
    "approved",
    "created",
}


def validate_orders(df: pd.DataFrame) -> None:
    """Validate bảng orders sau khi clean."""
    logger.info(f"[VALIDATE] orders — {len(df):,} rows")
    errors: list[str] = []

    # ── CRITICAL ──────────────────────────────────────────────────────
    null_ids = df["order_id"].isnull().sum()
    if null_ids:
        errors.append(f"order_id: {null_ids} null values")

    dup_ids = df["order_id"].duplicated().sum()
    if dup_ids:
        errors.append(f"order_id: {dup_ids} duplicates")

    null_cust = df["customer_id"].isnull().sum()
    if null_cust:
        errors.append(f"customer_id: {null_cust} null values")

    # Whitelist check — không bắt buộc phải là 'delivered'
    invalid_status = ~df["order_status"].isin(VALID_ORDER_STATUSES)
    if invalid_status.sum():
        bad = df.loc[invalid_status, "order_status"].unique().tolist()
        errors.append(f"order_status: {invalid_status.sum()} invalid values → {bad}")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] orders ❌ {err}")
        raise ValueError(f"orders FAILED — {errors}")

    # ── WARNING ───────────────────────────────────────────────────────
    null_ts = df["order_purchase_timestamp"].isnull().sum()
    if null_ts:
        logger.warning(f"[VALIDATE] orders ⚠️  {null_ts} null order_purchase_timestamp")

    for col in ["order_date", "order_year", "order_month", "order_quarter"]:
        if col not in df.columns:
            logger.warning(f"[VALIDATE] orders ⚠️  missing derived column '{col}'")

    logger.info(f"[VALIDATE] orders ✅ PASSED")


def validate_customers(df: pd.DataFrame) -> None:
    logger.info(f"[VALIDATE] customers — {len(df):,} rows")
    errors: list[str] = []

    if df["customer_id"].isnull().sum():
        errors.append(f"customer_id: {df['customer_id'].isnull().sum()} nulls")
    if df["customer_id"].duplicated().sum():
        errors.append(f"customer_id: {df['customer_id'].duplicated().sum()} duplicates")

    if errors:
        for e in errors: logger.error(f"[VALIDATE] customers ❌ {e}")
        raise ValueError(f"customers FAILED — {errors}")
    logger.info("[VALIDATE] customers ✅ PASSED")


def validate_products(df: pd.DataFrame) -> None:
    logger.info(f"[VALIDATE] products — {len(df):,} rows")
    errors: list[str] = []

    if df["product_id"].isnull().sum():
        errors.append(f"product_id: {df['product_id'].isnull().sum()} nulls")
    if df["product_id"].duplicated().sum():
        errors.append(f"product_id: {df['product_id'].duplicated().sum()} duplicates")

    if errors:
        for e in errors: logger.error(f"[VALIDATE] products ❌ {e}")
        raise ValueError(f"products FAILED — {errors}")
    logger.info("[VALIDATE] products ✅ PASSED")


def validate_payments(df: pd.DataFrame) -> None:
    logger.info(f"[VALIDATE] payments — {len(df):,} rows")
    errors: list[str] = []

    if df["order_id"].isnull().sum():
        errors.append(f"order_id: {df['order_id'].isnull().sum()} nulls")
    neg = (df["total_payment_value"] <= 0).sum()
    if neg:
        errors.append(f"total_payment_value: {neg} rows <= 0")

    if errors:
        for e in errors: logger.error(f"[VALIDATE] payments ❌ {e}")
        raise ValueError(f"payments FAILED — {errors}")
    logger.info("[VALIDATE] payments ✅ PASSED")


def validate_staging(tables: dict[str, pd.DataFrame]) -> None:
    """Validate tất cả staging tables."""
    logger.info("[VALIDATE] ── Staging tables ──")
    validate_orders(tables["orders"])
    validate_customers(tables["customers"])
    validate_products(tables["products"])
    validate_payments(tables["payments"])
    logger.info("[VALIDATE] ── All staging PASSED ✅ ──")
