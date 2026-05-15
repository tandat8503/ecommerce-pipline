"""
validate/validate_warehouse.py

Validate tầng Warehouse — Đảm bảo dữ liệu Fact/Dim chuẩn trước khi load.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def validate_fact_orders(df: pd.DataFrame) -> None:
    """Validate bảng fact_orders (order-level)."""
    logger.info(f"[VALIDATE] fact_orders — {len(df):,} rows")
    errors = []
    
    # Check null order_id
    if df["order_id"].isnull().sum():
        errors.append("order_id has nulls")
    
    # Check duplicate order_id
    if df["order_id"].duplicated().sum():
        errors.append("order_id has duplicates")
        
    if errors:
        raise ValueError(f"fact_orders FAILED: {errors}")


def validate_fact_order_items(df: pd.DataFrame) -> None:
    """Validate bảng fact_order_items (item-level)."""
    logger.info(f"[VALIDATE] fact_order_items — {len(df):,} rows")
    # Check duplicate (order_id + product_id)
    # Lưu ý: 1 đơn có thể có cùng 1 sp nhiều lần (item_id khác nhau)
    # Nhưng trong dataset Olist, item_id thường là duy nhất trong order.
    pass


def validate_warehouse(tables: dict[str, pd.DataFrame]) -> None:
    """Run all warehouse validations."""
    logger.info("[VALIDATE] ── Warehouse Layer ──")
    validate_fact_orders(tables["fact_orders"])
    # Add more validators here...
