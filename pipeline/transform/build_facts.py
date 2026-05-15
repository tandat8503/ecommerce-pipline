"""
pipeline/transform/build_facts.py
Build fact tables for the warehouse layer.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def build_payment_summary(payments: pd.DataFrame) -> pd.DataFrame:
    """
    Create payment summary at the order level.
    """
    if payments.empty:
        return pd.DataFrame(columns=[
            "order_id", "total_payment_value", "payment_methods_count", 
            "has_voucher", "has_credit_card", "is_installment"
        ])
        
    agg = payments.groupby("order_id").agg(
        total_payment_value=("payment_value", "sum"),
        payment_methods_count=("payment_type", "nunique"),
        max_installments=("payment_installments", "max")
    ).reset_index()

    # Create flags
    voucher_orders = set(payments[payments["payment_type"] == "voucher"]["order_id"])
    credit_orders = set(payments[payments["payment_type"] == "credit_card"]["order_id"])

    agg["has_voucher"] = agg["order_id"].isin(voucher_orders)
    agg["has_credit_card"] = agg["order_id"].isin(credit_orders)
    agg["is_installment"] = agg["max_installments"] > 1

    return agg

def build_fact_orders(orders: pd.DataFrame, order_items: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
    """
    Build fact_orders: 1 row = 1 order.
    """
    logger.info(f"[BUILD] fact_orders — input {len(orders):,} orders")
    fact = orders.copy()

    # Item level aggregations
    if not order_items.empty:
        items_agg = order_items.groupby("order_id").agg(
            total_item_revenue=("price", "sum"),
            total_shipping_cost=("shipping_charges", "sum"),
            item_count=("product_id", "count")
        ).reset_index()
        fact = fact.merge(items_agg, on="order_id", how="left")
    else:
        fact["total_item_revenue"] = 0.0
        fact["total_shipping_cost"] = 0.0
        fact["item_count"] = 0

    # Payment level aggregations
    pay_summary = build_payment_summary(payments)
    fact = fact.merge(pay_summary, on="order_id", how="left")

    # Order total value
    fact["total_item_revenue"] = fact["total_item_revenue"].fillna(0.0)
    fact["total_shipping_cost"] = fact["total_shipping_cost"].fillna(0.0)
    fact["total_order_value"] = fact["total_item_revenue"] + fact["total_shipping_cost"]
    
    # Fill payment nulls
    fact["total_payment_value"] = fact["total_payment_value"].fillna(0.0)
    fact["payment_diff"] = fact["total_payment_value"] - fact["total_order_value"]

    # Fill boolean flags
    for col in ["has_voucher", "has_credit_card", "is_installment"]:
        fact[col] = fact[col].fillna(False)

    fact["payment_methods_count"] = fact["payment_methods_count"].fillna(0)
    fact["item_count"] = fact["item_count"].fillna(0)

    logger.info(f"[BUILD] fact_orders — output {len(fact):,} rows")
    return fact

def build_fact_order_items(order_items: pd.DataFrame, orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """
    Build fact_order_items: 1 row = 1 order item.
    """
    logger.info(f"[BUILD] fact_order_items — input {len(order_items):,} items")
    fact = order_items.copy()

    # Add order level context
    order_context = orders[["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_date"]]
    fact = fact.merge(order_context, on="order_id", how="inner")

    # Add product context
    if "product_category_name" in products.columns:
        prod_context = products[["product_id", "product_category_name"]]
        fact = fact.merge(prod_context, on="product_id", how="left")

    logger.info(f"[BUILD] fact_order_items — output {len(fact):,} rows")
    return fact

def build_fact_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """
    Build fact_payments: 1 row = 1 payment transaction.
    """
    logger.info(f"[BUILD] fact_payments — input {len(payments):,} transactions")
    fact = payments.copy()
    logger.info(f"[BUILD] fact_payments — output {len(fact):,} rows")
    return fact
