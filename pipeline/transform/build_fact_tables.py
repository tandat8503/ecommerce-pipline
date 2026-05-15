"""
transform/build_fact_tables.py

Xây dựng Fact & Dimension tables cho tầng Warehouse.

Đây là nơi DUY NHẤT filter order_status == 'delivered':
    - Staging giữ full status để phân tích funnel/cancel
    - Warehouse fact_orders chỉ chứa delivered orders để tính revenue

Star Schema:
                     dim_date (derived)
                          │
    dim_customers ──→ fact_orders ←── dim_products
                          │
                   payment_type (embedded)

Granularity của fact_orders: 1 row = 1 item trong 1 đơn hàng (delivered).
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

ORDER_STATUS_FOR_REVENUE = "delivered"


# ─────────────────────────────────────────────────────────────────────────────
# FACT TABLE
# ─────────────────────────────────────────────────────────────────────────────

def build_fact_orders(
    orders:      pd.DataFrame,
    order_items: pd.DataFrame,
    payments:    pd.DataFrame,
    products:    pd.DataFrame,
) -> pd.DataFrame:
    """
    Build fact_orders — bảng trung tâm cho revenue analytics.

    Filter: Chỉ lấy orders có status = 'delivered'.
    Granularity: 1 row = 1 product trong 1 đơn hàng.

    JOIN flow:
        order_items (base)
            LEFT JOIN orders      ON order_id  → lấy customer, time cols
            LEFT JOIN payments    ON order_id  → lấy payment_type, total_payment_value
            LEFT JOIN products    ON product_id → lấy category

    Args:
        orders:      staging orders (full status)
        order_items: raw order_items
        payments:    staging payments (aggregated per order)
        products:    staging products

    Returns:
        fact_orders → warehouse/fact_orders.parquet
    """
    logger.info("[BUILD] fact_orders — starting...")

    # Filter delivered tại đây — không phải ở staging
    delivered = orders[orders["order_status"] == ORDER_STATUS_FOR_REVENUE]
    valid_ids  = set(delivered["order_id"])
    logger.info(
        f"[BUILD] fact_orders — delivered orders: "
        f"{len(delivered):,} / {len(orders):,} total"
    )

    # Chỉ giữ order_items của delivered orders
    items = order_items[order_items["order_id"].isin(valid_ids)].copy()
    items["total_amount"] = items["price"].fillna(0) + items["shipping_charges"].fillna(0)

    # Cột cần lấy từ orders
    order_cols = [
        "order_id", "customer_id",
        "order_date", "order_year", "order_month", "order_quarter", "order_dow",
    ]

    fact = (
        items
        .merge(delivered[order_cols],                                          on="order_id", how="left")
        .merge(payments[["order_id","payment_type","total_payment_value","is_installment"]], on="order_id", how="left")
        .merge(products[["product_id","product_category_name"]],               on="product_id", how="left")
    )

    fact = fact.rename(columns={
        "price":                 "revenue",
        "shipping_charges":      "shipping_cost",
        "total_amount":          "total_revenue",
        "product_category_name": "category",
    })

    logger.info(
        f"[BUILD] fact_orders — done: {len(fact):,} rows × {fact.shape[1]} cols"
    )
    return fact


# ─────────────────────────────────────────────────────────────────────────────
# DIMENSION TABLES
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_customers(customers: pd.DataFrame) -> pd.DataFrame:
    """dim_customers → warehouse/dim_customers.parquet"""
    logger.info(f"[BUILD] dim_customers — {len(customers):,} rows")
    dim = (
        customers[["customer_id", "customer_city", "customer_state"]]
        .drop_duplicates(subset=["customer_id"])
        .copy()
    )
    logger.info(f"[BUILD] dim_customers — done: {len(dim):,} rows")
    return dim


def build_dim_products(products: pd.DataFrame) -> pd.DataFrame:
    """dim_products → warehouse/dim_products.parquet"""
    logger.info(f"[BUILD] dim_products — {len(products):,} rows")
    dim = (
        products[[
            "product_id", "product_category_name",
            "product_weight_g", "product_length_cm",
            "product_height_cm", "product_width_cm",
        ]]
        .drop_duplicates(subset=["product_id"])
        .rename(columns={"product_category_name": "category"})
        .copy()
    )
    logger.info(f"[BUILD] dim_products — done: {len(dim):,} rows")
    return dim


# ─────────────────────────────────────────────────────────────────────────────
# BUILD ALL
# ─────────────────────────────────────────────────────────────────────────────

def build_all_tables(
    orders:      pd.DataFrame,
    order_items: pd.DataFrame,
    customers:   pd.DataFrame,
    payments:    pd.DataFrame,
    products:    pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """
    Build tất cả warehouse tables.

    Returns:
        {
            "fact_orders":   DataFrame,
            "dim_customers": DataFrame,
            "dim_products":  DataFrame,
        }
    """
    logger.info("[BUILD] ── Building warehouse tables ──")
    tables = {
        "fact_orders":   build_fact_orders(orders, order_items, payments, products),
        "dim_customers": build_dim_customers(customers),
        "dim_products":  build_dim_products(products),
    }
    logger.info("[BUILD] ── Warehouse tables done ✅ ──")
    return tables
