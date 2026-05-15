"""
pipeline/transform/build_dimensions.py
Build dimension tables for the warehouse layer.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def build_dim_customers(customers: pd.DataFrame) -> pd.DataFrame:
    """Build dim_customers: 1 row = 1 customer."""
    logger.info(f"[BUILD] dim_customers — input {len(customers):,} rows")
    dim = customers.copy()
    dim = dim.drop_duplicates(subset=["customer_id"])
    logger.info(f"[BUILD] dim_customers — output {len(dim):,} rows")
    return dim

def build_dim_products(products: pd.DataFrame) -> pd.DataFrame:
    """Build dim_products: 1 row = 1 product."""
    logger.info(f"[BUILD] dim_products — input {len(products):,} rows")
    dim = products.copy()
    dim = dim.drop_duplicates(subset=["product_id"])
    logger.info(f"[BUILD] dim_products — output {len(dim):,} rows")
    return dim

def build_dim_date(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Build dim_date based on the range of order purchase timestamps.
    """
    logger.info("[BUILD] dim_date — starting...")
    if "order_purchase_timestamp" not in orders.columns:
        logger.warning("order_purchase_timestamp not found. Cannot build dim_date.")
        return pd.DataFrame()

    min_date = orders["order_purchase_timestamp"].min()
    max_date = orders["order_purchase_timestamp"].max()

    if pd.isna(min_date) or pd.isna(max_date):
        logger.warning("Invalid min/max dates. Cannot build dim_date.")
        return pd.DataFrame()

    # Generate date range
    date_range = pd.date_range(start=min_date.date(), end=max_date.date())
    dim = pd.DataFrame({"date": date_range})

    dim["date_id"] = dim["date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["date"].dt.year
    dim["quarter"] = dim["date"].dt.quarter
    dim["month"] = dim["date"].dt.month
    dim["month_name"] = dim["date"].dt.month_name()
    dim["day"] = dim["date"].dt.day
    dim["day_of_week"] = dim["date"].dt.dayofweek
    dim["week_of_year"] = dim["date"].dt.isocalendar().week
    dim["is_weekend"] = dim["day_of_week"].isin([5, 6])

    logger.info(f"[BUILD] dim_date — output {len(dim):,} rows")
    return dim
