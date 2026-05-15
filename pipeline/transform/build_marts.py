"""
pipeline/transform/build_marts.py
Build mart tables for the dashboard layer.
"""

import pandas as pd
from pipeline.utils.config import config
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def build_mart_revenue_by_day(fact_orders: pd.DataFrame) -> pd.DataFrame:
    """Revenue aggregated by day."""
    df = fact_orders[fact_orders["order_status"] == config.revenue_status]
    mart = df.groupby("order_date").agg(
        revenue=("total_order_value", "sum"),
        orders=("order_id", "count")
    ).reset_index()
    return mart

def build_mart_revenue_by_month(fact_orders: pd.DataFrame) -> pd.DataFrame:
    """Revenue aggregated by year-month."""
    df = fact_orders[fact_orders["order_status"] == config.revenue_status]
    mart = df.groupby(["order_year", "order_month"]).agg(
        revenue=("total_order_value", "sum"),
        orders=("order_id", "count")
    ).reset_index()
    return mart

def build_mart_revenue_by_category(fact_order_items: pd.DataFrame) -> pd.DataFrame:
    """Revenue aggregated by product category."""
    df = fact_order_items[fact_order_items["order_status"] == config.revenue_status]
    mart = df.groupby("product_category_name").agg(
        revenue=("item_total", "sum"),
        items_sold=("order_id", "count")
    ).reset_index()
    return mart

def build_mart_payment_method_summary(fact_payments: pd.DataFrame) -> pd.DataFrame:
    """Summary of payment methods used."""
    mart = fact_payments.groupby("payment_type").agg(
        total_value=("payment_value", "sum"),
        transaction_count=("order_id", "count")
    ).reset_index()
    return mart

def build_mart_order_status_daily(fact_orders: pd.DataFrame) -> pd.DataFrame:
    """Daily count of orders by status."""
    mart = fact_orders.groupby(["order_date", "order_status"]).agg(
        order_count=("order_id", "count")
    ).reset_index()
    return mart

def build_mart_top_products(fact_order_items: pd.DataFrame) -> pd.DataFrame:
    """Top products by revenue."""
    df = fact_order_items[fact_order_items["order_status"] == config.revenue_status]
    mart = df.groupby(["product_id", "product_category_name"]).agg(
        revenue=("item_total", "sum"),
        quantity=("order_id", "count")
    ).sort_values(by="revenue", ascending=False).reset_index()
    return mart

def build_mart_customer_geo(fact_orders: pd.DataFrame, dim_customers: pd.DataFrame) -> pd.DataFrame:
    """Customer distribution and revenue by geography."""
    df = fact_orders.merge(dim_customers[["customer_id", "customer_city", "customer_state"]], on="customer_id", how="inner")
    df = df[df["order_status"] == config.revenue_status]
    mart = df.groupby(["customer_state", "customer_city"]).agg(
        revenue=("total_order_value", "sum"),
        orders=("order_id", "count"),
        unique_customers=("customer_id", "nunique")
    ).reset_index()
    return mart
