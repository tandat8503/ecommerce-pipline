"""
transform/build_fact_tables.py

Xây dựng Fact & Dimension tables cho tầng Warehouse.

Refactored for "Pro" Dashboard:
    1. fact_order_items: Chi tiết từng item (1 row = 1 item)
    2. fact_orders: Tổng quan từng đơn hàng (1 row = 1 order)
    3. fact_payments: Chi tiết từng giao dịch thanh toán (1 row = 1 payment)
    4. dim_customers / dim_products: Dimension tables
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

ORDER_STATUS_FOR_REVENUE = "delivered"


# ─────────────────────────────────────────────────────────────────────────────
# FACT ORDER ITEMS (1 row = 1 product in order)
# ─────────────────────────────────────────────────────────────────────────────

def build_fact_order_items(
    orders:      pd.DataFrame,
    order_items: pd.DataFrame,
    products:    pd.DataFrame,
) -> pd.DataFrame:
    """
    Build fact_order_items — Dùng cho phân tích category, product performance.
    """
    logger.info("[BUILD] fact_order_items — starting...")

    # Chỉ lấy đơn hàng đã giao để tính revenue chính xác
    delivered_orders = orders[orders["order_status"] == ORDER_STATUS_FOR_REVENUE]
    valid_ids = set(delivered_orders["order_id"])

    items = order_items[order_items["order_id"].isin(valid_ids)].copy()
    items["total_item_value"] = items["price"].fillna(0) + items["shipping_charges"].fillna(0)

    # Join với orders để lấy dimension thời gian
    fact = items.merge(
        delivered_orders[["order_id", "customer_id", "order_date", "order_year", "order_month"]],
        on="order_id",
        how="left"
    )

    # Join với products để lấy category
    fact = fact.merge(
        products[["product_id", "product_category_name"]],
        on="product_id",
        how="left"
    )

    fact = fact.rename(columns={
        "price": "revenue",
        "shipping_charges": "shipping_cost",
        "product_category_name": "category"
    })

    logger.info(f"[BUILD] fact_order_items — done: {len(fact):,} rows")
    return fact


# ─────────────────────────────────────────────────────────────────────────────
# FACT ORDERS (1 row = 1 order)
# ─────────────────────────────────────────────────────────────────────────────

def build_fact_orders(
    orders:      pd.DataFrame,
    order_items: pd.DataFrame,
    payments:    pd.DataFrame,
) -> pd.DataFrame:
    """
    Build fact_orders — Bảng trung tâm cho Executive Dashboard (1 row per order).
    """
    logger.info("[BUILD] fact_orders — starting...")

    # Base là bảng orders (giữ full status để phân tích funnel)
    fact = orders.copy()

    # Tính tổng giá trị từ order_items
    items_agg = order_items.groupby("order_id").agg(
        total_item_revenue = ("price", "sum"),
        total_shipping_cost = ("shipping_charges", "sum"),
        item_count = ("order_id", "count")
    ).reset_index()

    # Tính tổng thanh toán từ payments
    pay_agg = payments.groupby("order_id").agg(
        total_payment_value = ("payment_value", "sum"),
        payment_installments_max = ("payment_installments", "max"),
        payment_method_count = ("payment_sequential", "nunique")
    ).reset_index()

    fact = fact.merge(items_agg, on="order_id", how="left")
    fact = fact.merge(pay_agg, on="order_id", how="left")

    # Cột tính toán thêm
    fact["total_order_value"] = fact["total_item_revenue"].fillna(0) + fact["total_shipping_cost"].fillna(0)

    logger.info(f"[BUILD] fact_orders — done: {len(fact):,} rows")
    return fact


# ─────────────────────────────────────────────────────────────────────────────
# FACT PAYMENTS (1 row = 1 payment transaction)
# ─────────────────────────────────────────────────────────────────────────────

def build_fact_payments(
    payments_raw: pd.DataFrame,
    orders:       pd.DataFrame,
) -> pd.DataFrame:
    """
    Build fact_payments — Dùng cho phân tích phương thức thanh toán, trả góp.
    """
    logger.info("[BUILD] fact_payments — starting...")
    
    # Lấy thông tin ngày tháng từ orders join qua
    fact = payments_raw.merge(
        orders[["order_id", "order_date", "order_year", "order_month"]],
        on="order_id",
        how="left"
    )
    
    logger.info(f"[BUILD] fact_payments — done: {len(fact):,} rows")
    return fact


# ─────────────────────────────────────────────────────────────────────────────
# DIMENSIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_customers(customers: pd.DataFrame) -> pd.DataFrame:
    return customers[["customer_id", "customer_city", "customer_state"]].drop_duplicates().copy()

def build_dim_products(products: pd.DataFrame) -> pd.DataFrame:
    return products.rename(columns={"product_category_name": "category"}).copy()


def build_all_tables(
    raw: dict,
    staging: dict
) -> dict[str, pd.DataFrame]:
    """Build toàn bộ warehouse layer."""
    logger.info("[BUILD] ── Starting Warehouse Modeling ──")
    
    return {
        "fact_order_items": build_fact_order_items(staging["orders"], raw["order_items"], staging["products"]),
        "fact_orders":      build_fact_orders(staging["orders"], raw["order_items"], raw["payments"]),
        "fact_payments":    build_fact_payments(raw["payments"], staging["orders"]),
        "dim_customers":    build_dim_customers(staging["customers"]),
        "dim_products":     build_dim_products(staging["products"]),
    }
