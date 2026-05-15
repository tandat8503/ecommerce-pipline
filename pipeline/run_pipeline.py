"""
pipeline/run_pipeline.py — Orchestrator của toàn bộ ETL pipeline.

Flow:
    RAW CSV
        ↓ EXTRACT
    Raw DataFrames
        ↓ TRANSFORM (clean từng bảng)
    Staging DataFrames
        ↓ VALIDATE staging
        ↓ LOAD → data/staging/
        ↓ BUILD (fact + dim tables)
    Warehouse DataFrames
        ↓ VALIDATE warehouse
        ↓ LOAD → data/warehouse/

Chạy:
    python pipeline/run_pipeline.py

Trong production, file này được gọi bởi:
    - Apache Airflow  → PythonOperator / BashOperator
    - Cron job        → 0 2 * * * python pipeline/run_pipeline.py
    - Docker          → CMD ["python", "pipeline/run_pipeline.py"]
"""

import sys
import time
from datetime import datetime

# ── Utils ─────────────────────────────────────────────────────────────────────
from pipeline.utils.config import ensure_dirs
from pipeline.utils.logger import get_logger

# ── Extract ───────────────────────────────────────────────────────────────────
from pipeline.extract.extract_csv import extract_all

# ── Transform ─────────────────────────────────────────────────────────────────
from pipeline.transform.transform_orders      import clean_orders
from pipeline.transform.transform_customers   import clean_customers
from pipeline.transform.transform_products    import clean_products
from pipeline.transform.transform_payments    import clean_payments
from pipeline.transform.build_fact_tables     import build_all_tables

# ── Validate ──────────────────────────────────────────────────────────────────
from pipeline.validate.validate_orders      import validate_staging
from pipeline.validate.validate_fact_orders import validate_fact_orders

# ── Load ──────────────────────────────────────────────────────────────────────
from pipeline.load.load_local import load_all_staging, load_all_warehouse

logger = get_logger(__name__)


def run_pipeline() -> None:
    """Chạy toàn bộ ETL pipeline: Extract → Transform → Validate → Load."""
    t0     = time.time()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 65)
    logger.info(f"  🚀 PIPELINE START  |  run_id={run_id}")
    logger.info("=" * 65)

    ensure_dirs()

    # ─────────────────────────────────────────────────────────────────
    # STEP 1 — EXTRACT: Đọc raw CSV
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 1: EXTRACT ──────────────────────────────────────")
    raw = extract_all()

    # ─────────────────────────────────────────────────────────────────
    # STEP 2 — TRANSFORM: Làm sạch từng bảng
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 2: TRANSFORM (staging) ──────────────────────────")
    staging = {
        "orders":      clean_orders(raw["orders"]),
        "customers":   clean_customers(raw["customers"]),
        "products":    clean_products(raw["products"]),
        "payments":    clean_payments(raw["payments"]),
        # order_items dùng raw trực tiếp trong build_fact_tables
    }

    # ─────────────────────────────────────────────────────────────────
    # STEP 3 — VALIDATE staging
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 3: VALIDATE (staging) ───────────────────────────")
    validate_staging(staging)

    # ─────────────────────────────────────────────────────────────────
    # STEP 4 — LOAD staging → data/staging/
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 4: LOAD (staging) ───────────────────────────────")
    load_all_staging(staging)

    # ─────────────────────────────────────────────────────────────────
    # STEP 5 — BUILD warehouse: fact + dim tables
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 5: BUILD (warehouse) ────────────────────────────")
    warehouse = build_all_tables(
        orders      = staging["orders"],
        order_items = raw["order_items"],    # raw — chưa aggregate
        customers   = staging["customers"],
        payments    = staging["payments"],
        products    = staging["products"],
    )

    # ─────────────────────────────────────────────────────────────────
    # STEP 6 — VALIDATE warehouse
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 6: VALIDATE (warehouse) ─────────────────────────")
    validate_fact_orders(
        fact      = warehouse["fact_orders"],
        customers = warehouse["dim_customers"],
        products  = warehouse["dim_products"],
    )

    # ─────────────────────────────────────────────────────────────────
    # STEP 7 — LOAD warehouse → data/warehouse/
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 7: LOAD (warehouse) ─────────────────────────────")
    load_all_warehouse(warehouse)

    elapsed = time.time() - t0
    logger.info("=" * 65)
    logger.info(f"  ✅ PIPELINE DONE  |  {elapsed:.1f}s  |  run_id={run_id}")
    logger.info("=" * 65)


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        logger.error(f"❌ PIPELINE FAILED: {exc}")
        sys.exit(1)
