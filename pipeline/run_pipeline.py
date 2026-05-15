"""
pipeline/run_pipeline.py
Orchestrator for the entire ETL pipeline.
"""

import sys
import time
from datetime import datetime

from pipeline.utils.config import config
from pipeline.utils.logger import get_logger

# Extract
from pipeline.extract.extract_csv import extract_all

# Transform - Staging
from pipeline.transform.transform_orders import clean_orders
from pipeline.transform.transform_customers import clean_customers
from pipeline.transform.transform_products import clean_products
from pipeline.transform.transform_payments import clean_payments
from pipeline.transform.transform_order_items import clean_order_items

# Transform - Warehouse
from pipeline.transform.build_dimensions import build_dim_customers, build_dim_products, build_dim_date
from pipeline.transform.build_facts import build_fact_orders, build_fact_order_items, build_fact_payments

# Transform - Mart
from pipeline.transform.build_marts import (
    build_mart_revenue_by_day,
    build_mart_revenue_by_month,
    build_mart_revenue_by_category,
    build_mart_payment_method_summary,
    build_mart_order_status_daily,
    build_mart_top_products,
    build_mart_customer_geo
)

# Validate
from pipeline.validate.validate_staging import validate_staging
from pipeline.validate.validate_warehouse import validate_warehouse

# Load
from pipeline.load.load_local import load_staging, load_warehouse
from pipeline.load.load_bigquery import load_all_to_bigquery

logger = get_logger(__name__)

def run_pipeline():
    t0 = time.time()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 70)
    logger.info(f"🚀 PIPELINE START | run_id={run_id} | date={config.pipeline_date}")
    logger.info("=" * 70)

    try:
        # 1. EXTRACT
        raw_tables = extract_all()

        # 2. TRANSFORM (Staging)
        logger.info("── STEP 2: TRANSFORM (Staging) ─────────────────────────")
        staging_tables = {
            "orders": clean_orders(raw_tables["orders"]),
            "customers": clean_customers(raw_tables["customers"]),
            "products": clean_products(raw_tables["products"]),
            "payments": clean_payments(raw_tables["payments"]),
            "order_items": clean_order_items(raw_tables["order_items"]),
        }

        # 3. VALIDATE & LOAD (Staging)
        logger.info("── STEP 3: VALIDATE & LOAD (Staging) ───────────────────")
        validate_staging(staging_tables)
        load_staging(staging_tables)

        # 4. BUILD WAREHOUSE (Dim/Fact)
        logger.info("── STEP 4: BUILD (Warehouse - Dim/Fact) ────────────────")
        warehouse_tables = {
            "dim_customers": build_dim_customers(staging_tables["customers"]),
            "dim_products": build_dim_products(staging_tables["products"]),
            "dim_date": build_dim_date(staging_tables["orders"]),
            "fact_payments": build_fact_payments(staging_tables["payments"]),
            "fact_order_items": build_fact_order_items(
                staging_tables["order_items"], staging_tables["orders"], staging_tables["products"]
            ),
            "fact_orders": build_fact_orders(
                staging_tables["orders"], staging_tables["order_items"], staging_tables["payments"]
            ),
        }

        # 5. BUILD MART
        logger.info("── STEP 5: BUILD (Warehouse - Marts) ───────────────────")
        mart_tables = {
            "mart_revenue_by_day": build_mart_revenue_by_day(warehouse_tables["fact_orders"]),
            "mart_revenue_by_month": build_mart_revenue_by_month(warehouse_tables["fact_orders"]),
            "mart_revenue_by_category": build_mart_revenue_by_category(warehouse_tables["fact_order_items"]),
            "mart_payment_method_summary": build_mart_payment_method_summary(warehouse_tables["fact_payments"]),
            "mart_order_status_daily": build_mart_order_status_daily(warehouse_tables["fact_orders"]),
            "mart_top_products": build_mart_top_products(warehouse_tables["fact_order_items"]),
            "mart_customer_geo": build_mart_customer_geo(warehouse_tables["fact_orders"], warehouse_tables["dim_customers"]),
        }

        # 6. VALIDATE & LOAD (Warehouse/Mart)
        logger.info("── STEP 6: VALIDATE & LOAD (Warehouse) ─────────────────")
        validate_warehouse(warehouse_tables, mart_tables)
        load_warehouse(warehouse_tables, mart_tables)

        # 7. LOAD BIGQUERY (Optional)
        if config.load_target == "bigquery" or config.bq_enabled:
            logger.info("── STEP 7: LOAD BIGQUERY ───────────────────────────────")
            all_warehouse_tables = {**warehouse_tables, **mart_tables}
            load_all_to_bigquery(all_warehouse_tables)
        else:
            logger.info("── STEP 7: BIGQUERY SKIPPED (target=local) ─────────────")

        elapsed = time.time() - t0
        logger.info("=" * 70)
        logger.info(f"✅ PIPELINE COMPLETED | {elapsed:.1f}s")
        logger.info("=" * 70)

    except Exception as e:
        logger.exception(f"❌ PIPELINE FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
