"""
run_pipeline.py — Entry point của toàn bộ ETL pipeline.

Đây là file duy nhất bạn cần chạy:
    python run_pipeline.py

Luồng thực thi:
    EXTRACT → TRANSFORM → VALIDATE → LOAD

Trong production, file này thường được gọi bởi:
    - Apache Airflow (PythonOperator hoặc BashOperator)
    - Cron job
    - CI/CD pipeline
    - Docker container
"""

import sys
import time
from datetime import datetime

from pipeline.config import ensure_dirs
from pipeline.logger import get_logger

# ── Extract ───────────────────────────────────────────────────────────────────
from pipeline.extract.extract_csv import extract_all

# ── Transform ─────────────────────────────────────────────────────────────────
from pipeline.transform.transform_orders      import transform_orders
from pipeline.transform.transform_customers   import transform_customers
from pipeline.transform.transform_products    import transform_products
from pipeline.transform.transform_order_items import transform_order_items
from pipeline.transform.transform_payments    import transform_payments

# ── Validate ──────────────────────────────────────────────────────────────────
from pipeline.validate.validate import validate_all

# ── Load ──────────────────────────────────────────────────────────────────────
from pipeline.load.load_staging import load_all

logger = get_logger(__name__)


def run_pipeline() -> None:
    """
    Chạy toàn bộ ETL pipeline theo thứ tự:
        Extract → Transform → Validate → Load
    """
    start_time = time.time()
    run_id     = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 60)
    logger.info(f"  🚀 ETL PIPELINE STARTED  |  run_id={run_id}")
    logger.info("=" * 60)

    # ── 0. Chuẩn bị thư mục output ───────────────────────────────────
    ensure_dirs()

    # ─────────────────────────────────────────────────────────────────
    # STEP 1: EXTRACT
    # Đọc toàn bộ raw CSV từ data lake
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 1: EXTRACT ──────────────────────────────────────")
    raw = extract_all()

    # ─────────────────────────────────────────────────────────────────
    # STEP 2: TRANSFORM
    # Làm sạch & chuẩn hoá từng bảng độc lập
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 2: TRANSFORM ────────────────────────────────────")
    transformed = {
        "orders":      transform_orders(raw["orders"]),
        "customers":   transform_customers(raw["customers"]),
        "products":    transform_products(raw["products"]),
        "order_items": transform_order_items(raw["order_items"]),
        "payments":    transform_payments(raw["payments"]),
    }

    # ─────────────────────────────────────────────────────────────────
    # STEP 3: VALIDATE
    # Kiểm tra chất lượng — dừng pipeline nếu có lỗi CRITICAL
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 3: VALIDATE ─────────────────────────────────────")
    validate_all(transformed)

    # ─────────────────────────────────────────────────────────────────
    # STEP 4: LOAD
    # Lưu Parquet vào staging layer
    # ─────────────────────────────────────────────────────────────────
    logger.info("── STEP 4: LOAD ─────────────────────────────────────────")
    load_all(transformed)

    # ── Tổng kết ─────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"  ✅ PIPELINE COMPLETED  |  {elapsed:.1f}s  |  run_id={run_id}")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.error(f"❌ PIPELINE FAILED: {e}")
        sys.exit(1)   # Exit code 1 = lỗi → Airflow/cron biết pipeline thất bại
