"""
pipeline/run_pipeline.py — Orchestrator của toàn bộ ETL pipeline.

Architecture:
    Raw -> Staging -> Warehouse -> Mart -> BigQuery (Optional)
"""

import sys
import time
import yaml
from datetime import datetime

from pipeline.utils.config import ensure_dirs, PROJECT_ROOT, PIPELINE_DATE
from pipeline.utils.logger import get_logger

# Layers
from pipeline.extract.extract_csv import extract_all
from pipeline.transform.transform_orders import clean_orders
from pipeline.transform.transform_customers import clean_customers
from pipeline.transform.transform_products import clean_products
from pipeline.transform.transform_payments import clean_payments
from pipeline.transform.build_fact_tables import build_all_tables
from pipeline.transform.build_mart_tables import build_all_marts

from pipeline.validate.validate_orders import validate_staging
from pipeline.validate.validate_warehouse import validate_warehouse

from pipeline.load.load_local import load_all_staging, load_all_warehouse, load_all_mart
from pipeline.load.load_bigquery import load_all_to_bigquery

logger = get_logger(__name__)


def load_pipeline_config():
    with open(PROJECT_ROOT / "config.yaml", "r") as f:
        return yaml.safe_load(f)


def run_pipeline() -> None:
    t0 = time.time()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    cfg = load_pipeline_config()

    logger.info("=" * 65)
    logger.info(f"  🚀 PIPELINE START | run_id={run_id} | target={cfg['bigquery']['load_target']}")
    logger.info("=" * 65)

    ensure_dirs()

    # 1. EXTRACT
    logger.info("── STEP 1: EXTRACT ──────────────────────────────────────")
    raw = extract_all()

    # 2. TRANSFORM (Staging)
    logger.info("── STEP 2: TRANSFORM (Staging) ──────────────────────────")
    staging = {
        "orders":    clean_orders(raw["orders"]),
        "customers": clean_customers(raw["customers"]),
        "products":  clean_products(raw["products"]),
        "payments":  clean_payments(raw["payments"]),
    }

    # 3. VALIDATE & LOAD Staging
    validate_staging(staging)
    load_all_staging(staging)

    # 4. BUILD Warehouse (Fact/Dim)
    logger.info("── STEP 4: BUILD (Warehouse) ────────────────────────────")
    warehouse = build_all_tables(raw, staging)

    # 5. VALIDATE & LOAD Warehouse
    validate_warehouse(warehouse)
    load_all_warehouse(warehouse)

    # 6. BUILD & LOAD Mart
    logger.info("── STEP 6: BUILD (Mart) ─────────────────────────────────")
    marts = build_all_marts(warehouse)
    load_all_mart(marts, PIPELINE_DATE)

    # 7. LOAD TO BIGQUERY (Optional)
    if cfg["bigquery"]["load_target"] == "bigquery":
        logger.info("── STEP 7: LOAD TO BIGQUERY ─────────────────────────────")
        # Load warehouse + marts to BQ
        load_all_to_bigquery(warehouse)
        load_all_to_bigquery(marts)
    else:
        logger.info("── STEP 7: BIGQUERY LOAD SKIPPED (Target=local) ──────────")

    elapsed = time.time() - t0
    logger.info("=" * 65)
    logger.info(f"  ✅ PIPELINE DONE | {elapsed:.1f}s | run_id={run_id}")
    logger.info("=" * 65)


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        logger.error(f"❌ PIPELINE FAILED: {exc}")
        sys.exit(1)
