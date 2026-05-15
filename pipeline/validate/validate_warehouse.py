"""
pipeline/validate/validate_warehouse.py
Validation rules for the warehouse and mart layers.
"""

import pandas as pd
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def check_nulls(df: pd.DataFrame, col: str) -> list:
    nulls = df[col].isnull().sum()
    return [f"{col} has {nulls} nulls"] if nulls > 0 else []

def check_duplicates(df: pd.DataFrame, col: str) -> list:
    dups = df[col].duplicated().sum()
    return [f"{col} has {dups} duplicates"] if dups > 0 else []

def validate_fact_orders(df: pd.DataFrame):
    errors = check_nulls(df, "order_id") + check_duplicates(df, "order_id") + check_nulls(df, "customer_id")
    if (df["total_order_value"] < 0).sum() > 0:
        errors.append("total_order_value contains negative values")
    if errors:
        raise ValueError(f"fact_orders validation failed: {errors}")

def validate_fact_order_items(df: pd.DataFrame):
    errors = check_nulls(df, "order_id") + check_nulls(df, "product_id")
    if (df["item_total"] < 0).sum() > 0:
        errors.append("item_total contains negative values")
    if errors:
        raise ValueError(f"fact_order_items validation failed: {errors}")

def validate_fact_payments(df: pd.DataFrame):
    errors = check_nulls(df, "order_id")
    if (df["payment_value"] < 0).sum() > 0:
        errors.append("payment_value contains negative values")
    if errors:
        raise ValueError(f"fact_payments validation failed: {errors}")

def validate_warehouse(warehouse_tables: dict, mart_tables: dict):
    logger.info("[VALIDATE] ── Warehouse Layer ──")
    validate_fact_orders(warehouse_tables["fact_orders"])
    validate_fact_order_items(warehouse_tables["fact_order_items"])
    validate_fact_payments(warehouse_tables["fact_payments"])
    
    errors = check_nulls(warehouse_tables["dim_customers"], "customer_id") + check_duplicates(warehouse_tables["dim_customers"], "customer_id")
    if errors: raise ValueError(f"dim_customers failed: {errors}")
        
    errors = check_nulls(warehouse_tables["dim_products"], "product_id") + check_duplicates(warehouse_tables["dim_products"], "product_id")
    if errors: raise ValueError(f"dim_products failed: {errors}")

    for name, df in mart_tables.items():
        if df.empty:
            raise ValueError(f"Mart table {name} is empty")
            
    logger.info("[VALIDATE] Warehouse validation passed ✅")
