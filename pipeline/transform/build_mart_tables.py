"""
transform/build_mart_tables.py

Xây dựng tầng Mart — Các bảng đã được aggregate sẵn phục vụ Dashboard cực nhanh.
Nhiệm vụ: Aggregate dữ liệu từ Warehouse (Fact/Dim) thành các báo cáo cụ thể.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def build_mart_revenue_daily(fact_orders: pd.DataFrame) -> pd.DataFrame:
    """Doanh thu & số lượng đơn theo ngày (Executive Overview)."""
    mart = fact_orders[fact_orders["order_status"] == "delivered"].groupby("order_date").agg(
        daily_revenue=("total_item_revenue", "sum"),
        order_count=("order_id", "count"),
        avg_order_value=("total_order_value", "mean")
    ).reset_index()
    return mart


def build_mart_category_performance(fact_order_items: pd.DataFrame) -> pd.DataFrame:
    """Hiệu suất bán hàng theo Category."""
    mart = fact_order_items.groupby("category").agg(
        total_revenue=("revenue", "sum"),
        total_items_sold=("order_id", "count"),
        avg_price=("revenue", "mean")
    ).sort_values("total_revenue", ascending=False).reset_index()
    return mart


def build_mart_payment_summary(fact_payments: pd.DataFrame) -> pd.DataFrame:
    """Thống kê phương thức thanh toán phổ biến."""
    mart = fact_payments.groupby("payment_type").agg(
        transaction_count=("order_id", "count"),
        total_value=("payment_value", "sum")
    ).sort_values("transaction_count", ascending=False).reset_index()
    return mart


def build_all_marts(warehouse: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Tạo tất cả các bảng mart."""
    logger.info("[BUILD] ── Starting Mart Layer ──")
    return {
        "mart_revenue_daily":        build_mart_revenue_daily(warehouse["fact_orders"]),
        "mart_category_performance": build_mart_category_performance(warehouse["fact_order_items"]),
        "mart_payment_summary":      build_mart_payment_summary(warehouse["fact_payments"]),
    }
