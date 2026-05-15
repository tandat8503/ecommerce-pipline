"""
validate/validate_fact_orders.py

Kiểm tra chất lượng của fact_orders SAU khi build, TRƯỚC khi load warehouse.

Đây là bước quan trọng nhất — fact_orders là bảng analytics dùng để
trả lời tất cả business questions. Sai ở đây = sai toàn bộ dashboard.

Checks:
    - Không null ở các cột FK và metric quan trọng
    - Revenue phải > 0
    - Referential integrity: customer_id, product_id phải tồn tại
    - Không duplicate (order_id + product_id)
    - Khoảng thời gian hợp lý
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def validate_fact_orders(
    fact:      pd.DataFrame,
    customers: pd.DataFrame,
    products:  pd.DataFrame,
) -> None:
    """
    Validate fact_orders trước khi load vào warehouse.

    Args:
        fact:      fact_orders DataFrame
        customers: dim_customers (để check referential integrity)
        products:  dim_products  (để check referential integrity)

    Raises:
        ValueError nếu có lỗi CRITICAL
    """
    logger.info(f"[VALIDATE] fact_orders — running checks on {len(fact):,} rows...")
    errors: list[str] = []

    # ── CRITICAL: Không được null ở các cột chính ─────────────────────
    required_not_null = ["order_id", "customer_id", "product_id", "order_date"]
    for col in required_not_null:
        null_count = fact[col].isnull().sum()
        if null_count > 0:
            errors.append(f"'{col}': {null_count} null values")

    # ── CRITICAL: Revenue phải > 0 ────────────────────────────────────
    if "revenue" in fact.columns:
        neg_revenue = (fact["revenue"] <= 0).sum()
        if neg_revenue > 0:
            errors.append(f"revenue: {neg_revenue} rows <= 0")

    # ── CRITICAL: Không duplicate (order_id + product_id) ────────────
    dups = fact.duplicated(subset=["order_id", "product_id"]).sum()
    if dups > 0:
        errors.append(f"(order_id, product_id): {dups} duplicate rows")

    if errors:
        for err in errors:
            logger.error(f"[VALIDATE] fact_orders ❌ {err}")
        raise ValueError(
            f"[VALIDATE] fact_orders FAILED — {len(errors)} error(s): {errors}"
        )

    # ── WARNING: Referential integrity ────────────────────────────────
    valid_customers = set(customers["customer_id"])
    orphan_customers = (~fact["customer_id"].isin(valid_customers)).sum()
    if orphan_customers > 0:
        logger.warning(
            f"[VALIDATE] fact_orders ⚠️  {orphan_customers} customer_id "
            "không tồn tại trong dim_customers"
        )

    valid_products = set(products["product_id"])
    orphan_products = (~fact["product_id"].isin(valid_products)).sum()
    if orphan_products > 0:
        logger.warning(
            f"[VALIDATE] fact_orders ⚠️  {orphan_products} product_id "
            "không tồn tại trong dim_products"
        )

    # ── WARNING: Khoảng thời gian hợp lý ─────────────────────────────
    if "order_year" in fact.columns:
        years = fact["order_year"].dropna().unique()
        logger.info(f"[VALIDATE] fact_orders — order_year range: {sorted(years)}")

    # ── Summary metrics ───────────────────────────────────────────────
    if "revenue" in fact.columns:
        total_rev = fact["revenue"].sum()
        logger.info(
            f"[VALIDATE] fact_orders — total revenue: {total_rev:,.2f} | "
            f"avg: {fact['revenue'].mean():,.2f}"
        )

    logger.info(f"[VALIDATE] fact_orders ✅ PASSED — {len(fact):,} rows")
