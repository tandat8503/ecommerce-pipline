"""
transform/build_fact_tables.py

Nhiệm vụ: Xây dựng Fact table và Dimension tables cho Data Warehouse.

Đây là bước quan trọng nhất của pipeline — biến staging data
thành mô hình Star Schema phục vụ analytics.

Star Schema:
                     dim_date
                        │
    dim_customers ──→ fact_orders ←── dim_products
                        │
                     dim_payments (embedded)

fact_orders columns:
    order_id, customer_id, product_id, order_date, order_year,
    order_month, order_quarter, payment_type, revenue,
    shipping_cost, total_revenue, total_payment_value
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


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
    Build fact_orders — bảng trung tâm của Star Schema.

    Granularity (độ chi tiết): 1 row = 1 sản phẩm trong 1 đơn hàng.

    JOIN flow:
        order_items
            └── JOIN orders      ON order_id
            └── JOIN payments    ON order_id
            └── JOIN products    ON product_id

    Args:
        orders:      cleaned orders DataFrame (từ staging)
        order_items: raw order_items DataFrame
        payments:    cleaned payments DataFrame (đã aggregate)
        products:    cleaned products DataFrame

    Returns:
        fact_orders DataFrame → lưu vào warehouse/fact_orders.parquet
    """
    logger.info("[BUILD] fact_orders — starting...")

    # Chỉ giữ order_items của các đơn hàng hợp lệ (delivered)
    valid_order_ids = set(orders["order_id"])
    items = order_items[order_items["order_id"].isin(valid_order_ids)].copy()
    logger.info(f"[BUILD] fact_orders — valid order_items: {len(items):,} rows")

    # Tính total_amount per item
    items["total_amount"] = items["price"].fillna(0) + items["shipping_charges"].fillna(0)

    # JOIN: items ← orders (lấy customer_id, order_date, time columns)
    order_cols = [
        "order_id", "customer_id",
        "order_date", "order_year", "order_month", "order_quarter", "order_dow",
    ]
    fact = items.merge(
        orders[order_cols],
        on="order_id",
        how="left",
    )

    # JOIN: fact ← payments (lấy payment_type, total_payment_value)
    fact = fact.merge(
        payments[["order_id", "payment_type", "total_payment_value", "is_installment"]],
        on="order_id",
        how="left",
    )

    # JOIN: fact ← products (lấy category)
    fact = fact.merge(
        products[["product_id", "product_category_name"]],
        on="product_id",
        how="left",
    )

    # Rename cho rõ ràng
    fact = fact.rename(columns={
        "price":              "revenue",
        "shipping_charges":   "shipping_cost",
        "total_amount":       "total_revenue",
        "product_category_name": "category",
    })

    logger.info(f"[BUILD] fact_orders — done: {len(fact):,} rows × {fact.shape[1]} cols")
    return fact


# ─────────────────────────────────────────────────────────────────────────────
# DIMENSION TABLES
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_customers(customers: pd.DataFrame) -> pd.DataFrame:
    """
    Build dim_customers từ bảng customers đã clean.

    Returns:
        dim_customers → warehouse/dim_customers.parquet
    """
    logger.info(f"[BUILD] dim_customers — {len(customers):,} rows")
    dim = customers[["customer_id", "customer_city", "customer_state"]].copy()
    dim = dim.drop_duplicates(subset=["customer_id"])
    logger.info(f"[BUILD] dim_customers — done: {len(dim):,} rows")
    return dim


def build_dim_products(products: pd.DataFrame) -> pd.DataFrame:
    """
    Build dim_products từ bảng products đã clean.

    Returns:
        dim_products → warehouse/dim_products.parquet
    """
    logger.info(f"[BUILD] dim_products — {len(products):,} rows")
    dim = products[[
        "product_id", "product_category_name",
        "product_weight_g", "product_length_cm",
        "product_height_cm", "product_width_cm",
    ]].copy()
    dim = dim.rename(columns={"product_category_name": "category"})
    logger.info(f"[BUILD] dim_products — done: {len(dim):,} rows")
    return dim


def build_all_tables(
    orders:      pd.DataFrame,
    order_items: pd.DataFrame,
    customers:   pd.DataFrame,
    payments:    pd.DataFrame,
    products:    pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """
    Convenience: Build tất cả warehouse tables cùng lúc.

    Returns:
        {
            "fact_orders":    DataFrame,
            "dim_customers":  DataFrame,
            "dim_products":   DataFrame,
        }
    """
    logger.info("[BUILD] ── Building warehouse tables ──")
    return {
        "fact_orders":   build_fact_orders(orders, order_items, payments, products),
        "dim_customers": build_dim_customers(customers),
        "dim_products":  build_dim_products(products),
    }
