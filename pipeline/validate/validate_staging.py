"""
pipeline/validate/validate_staging.py
Validation rules for the staging layer.
"""

import pandas as pd
from pipeline.utils.config import config
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def check_nulls(df: pd.DataFrame, col: str) -> list:
    nulls = df[col].isnull().sum()
    return [f"{col} has {nulls} nulls"] if nulls > 0 else []

def check_duplicates(df: pd.DataFrame, col: str) -> list:
    dups = df[col].duplicated().sum()
    return [f"{col} has {dups} duplicates"] if dups > 0 else []

def validate_orders(df: pd.DataFrame):
    logger.info("[VALIDATE] staging orders...")
    errors = check_nulls(df, "order_id") + check_duplicates(df, "order_id") + check_nulls(df, "customer_id")
    
    invalid_status = ~df["order_status"].isin(config.valid_order_statuses)
    if invalid_status.sum() > 0:
        bad = df.loc[invalid_status, "order_status"].unique().tolist()
        errors.append(f"order_status has invalid values: {bad}")
        
    if errors:
        raise ValueError(f"Staging orders validation failed: {errors}")

def validate_customers(df: pd.DataFrame):
    logger.info("[VALIDATE] staging customers...")
    errors = check_nulls(df, "customer_id") + check_duplicates(df, "customer_id")
    if errors:
        raise ValueError(f"Staging customers validation failed: {errors}")

def validate_products(df: pd.DataFrame):
    logger.info("[VALIDATE] staging products...")
    errors = check_nulls(df, "product_id") + check_duplicates(df, "product_id")
    if errors:
        raise ValueError(f"Staging products validation failed: {errors}")

def validate_payments(df: pd.DataFrame):
    logger.info("[VALIDATE] staging payments...")
    errors = check_nulls(df, "order_id")
    if (df["payment_value"] < 0).sum() > 0:
        errors.append("payment_value contains negative values")
    if errors:
        raise ValueError(f"Staging payments validation failed: {errors}")

def validate_order_items(df: pd.DataFrame):
    logger.info("[VALIDATE] staging order_items...")
    errors = check_nulls(df, "order_id") + check_nulls(df, "product_id")
    if (df["price"] < 0).sum() > 0 or (df["shipping_charges"] < 0).sum() > 0:
        errors.append("Price or shipping_charges contains negative values")
    if errors:
        raise ValueError(f"Staging order_items validation failed: {errors}")

def validate_staging(tables: dict):
    logger.info("[VALIDATE] ── Staging Layer ──")
    validate_orders(tables["orders"])
    validate_customers(tables["customers"])
    validate_products(tables["products"])
    validate_payments(tables["payments"])
    validate_order_items(tables["order_items"])
    logger.info("[VALIDATE] Staging validation passed ✅")
