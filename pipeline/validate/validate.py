"""
validate.py — Validate layer.

Nhiệm vụ: Kiểm tra chất lượng data SAU khi transform, TRƯỚC khi load.

Nguyên tắc "Fail Fast" trong production:
  - Phát hiện lỗi càng sớm càng tốt
  - Dừng pipeline ngay khi gặp lỗi nghiêm trọng
  - Log cảnh báo cho các vấn đề không nghiêm trọng

2 mức severity:
  - CRITICAL → raise Exception → dừng pipeline
  - WARNING  → log cảnh báo → tiếp tục chạy
"""

import pandas as pd

from pipeline.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATE ORDERS
# ─────────────────────────────────────────────────────────────────────────────

def validate_orders(df: pd.DataFrame) -> None:
    """
    Kiểm tra chất lượng bảng orders sau transform.

    Checks:
        [CRITICAL] order_id không được null
        [CRITICAL] order_id phải unique
        [CRITICAL] order_status phải là 'delivered' (sau filter)
        [WARNING]  order_purchase_timestamp không được null
    """
    logger.info("[VALIDATE] orders — running checks...")
    errors = []

    # ── CRITICAL checks ───────────────────────────────────────────────
    null_ids = df["order_id"].isnull().sum()
    if null_ids > 0:
        errors.append(f"order_id has {null_ids} null values (CRITICAL)")

    dup_ids = df["order_id"].duplicated().sum()
    if dup_ids > 0:
        errors.append(f"order_id has {dup_ids} duplicates (CRITICAL)")

    invalid_status = (df["order_status"] != "delivered").sum()
    if invalid_status > 0:
        errors.append(
            f"Found {invalid_status} rows with status != 'delivered' (CRITICAL)"
        )

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] orders ❌ {err}")
        raise ValueError(f"[VALIDATE] orders FAILED — {len(errors)} critical error(s)")

    # ── WARNING checks ────────────────────────────────────────────────
    null_ts = df["order_purchase_timestamp"].isnull().sum()
    if null_ts > 0:
        logger.warning(f"[VALIDATE] orders ⚠️  {null_ts} null order_purchase_timestamp")

    logger.info(f"[VALIDATE] orders ✅ PASSED — {len(df):,} rows")


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATE ORDER ITEMS
# ─────────────────────────────────────────────────────────────────────────────

def validate_order_items(df: pd.DataFrame) -> None:
    """
    Kiểm tra chất lượng bảng order_items sau transform.

    Checks:
        [CRITICAL] order_id không được null
        [CRITICAL] price phải > 0
        [WARNING]  total_amount phải tồn tại
    """
    logger.info("[VALIDATE] order_items — running checks...")
    errors = []

    null_order = df["order_id"].isnull().sum()
    if null_order > 0:
        errors.append(f"order_id has {null_order} nulls (CRITICAL)")

    neg_price = (df["price"] <= 0).sum()
    if neg_price > 0:
        errors.append(f"Found {neg_price} rows with price <= 0 (CRITICAL)")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] order_items ❌ {err}")
        raise ValueError(f"[VALIDATE] order_items FAILED — {len(errors)} critical error(s)")

    if "total_amount" not in df.columns:
        logger.warning("[VALIDATE] order_items ⚠️  'total_amount' column missing")

    logger.info(f"[VALIDATE] order_items ✅ PASSED — {len(df):,} rows")


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATE CUSTOMERS
# ─────────────────────────────────────────────────────────────────────────────

def validate_customers(df: pd.DataFrame) -> None:
    """Kiểm tra bảng customers."""
    logger.info("[VALIDATE] customers — running checks...")
    errors = []

    null_ids = df["customer_id"].isnull().sum()
    if null_ids > 0:
        errors.append(f"customer_id has {null_ids} nulls (CRITICAL)")

    dup_ids = df["customer_id"].duplicated().sum()
    if dup_ids > 0:
        errors.append(f"customer_id has {dup_ids} duplicates (CRITICAL)")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] customers ❌ {err}")
        raise ValueError(f"[VALIDATE] customers FAILED")

    logger.info(f"[VALIDATE] customers ✅ PASSED — {len(df):,} rows")


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATE PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────

def validate_products(df: pd.DataFrame) -> None:
    """Kiểm tra bảng products."""
    logger.info("[VALIDATE] products — running checks...")
    errors = []

    null_ids = df["product_id"].isnull().sum()
    if null_ids > 0:
        errors.append(f"product_id has {null_ids} nulls (CRITICAL)")

    dup_ids = df["product_id"].duplicated().sum()
    if dup_ids > 0:
        errors.append(f"product_id has {dup_ids} duplicates (CRITICAL)")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] products ❌ {err}")
        raise ValueError(f"[VALIDATE] products FAILED")

    logger.info(f"[VALIDATE] products ✅ PASSED — {len(df):,} rows")


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATE PAYMENTS
# ─────────────────────────────────────────────────────────────────────────────

def validate_payments(df: pd.DataFrame) -> None:
    """Kiểm tra bảng payments."""
    logger.info("[VALIDATE] payments — running checks...")
    errors = []

    null_order = df["order_id"].isnull().sum()
    if null_order > 0:
        errors.append(f"order_id has {null_order} nulls (CRITICAL)")

    neg_val = (df["total_payment_value"] <= 0).sum()
    if neg_val > 0:
        errors.append(f"Found {neg_val} rows with total_payment_value <= 0 (CRITICAL)")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] payments ❌ {err}")
        raise ValueError(f"[VALIDATE] payments FAILED")

    logger.info(f"[VALIDATE] payments ✅ PASSED — {len(df):,} rows")


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATE ALL
# ─────────────────────────────────────────────────────────────────────────────

def validate_all(tables: dict[str, pd.DataFrame]) -> None:
    """
    Chạy validate cho tất cả bảng.

    Args:
        tables: dict với key = tên bảng, value = DataFrame đã transform
    """
    validators = {
        "orders":      validate_orders,
        "order_items": validate_order_items,
        "customers":   validate_customers,
        "products":    validate_products,
        "payments":    validate_payments,
    }

    logger.info("[VALIDATE] === Starting full validation ===")
    for table_name, validate_fn in validators.items():
        if table_name in tables:
            validate_fn(tables[table_name])

    logger.info("[VALIDATE] === All tables PASSED ✅ ===")
