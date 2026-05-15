"""
extract/extract_csv.py — Extract layer.

Nhiệm vụ DUY NHẤT: Đọc raw CSV → DataFrame.
KHÔNG transform, KHÔNG filter, KHÔNG làm gì thêm.

Trong production, extract layer còn có thể đọc từ:
    - PostgreSQL / MySQL       → extract_db.py
    - Google Cloud Storage     → extract_gcs.py
    - REST API                 → extract_api.py
    - Kafka stream             → extract_kafka.py
"""

import pandas as pd

from pipeline.utils.config import get_raw_path
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def read_orders() -> pd.DataFrame:
    path = get_raw_path("orders")
    logger.info(f"[EXTRACT] orders ← {path.name}")
    df = pd.read_csv(path)
    logger.info(f"[EXTRACT] orders: {len(df):,} rows × {df.shape[1]} cols")
    return df


def read_order_items() -> pd.DataFrame:
    path = get_raw_path("order_items")
    logger.info(f"[EXTRACT] order_items ← {path.name}")
    df = pd.read_csv(path)
    logger.info(f"[EXTRACT] order_items: {len(df):,} rows × {df.shape[1]} cols")
    return df


def read_customers() -> pd.DataFrame:
    path = get_raw_path("customers")
    logger.info(f"[EXTRACT] customers ← {path.name}")
    df = pd.read_csv(path)
    logger.info(f"[EXTRACT] customers: {len(df):,} rows × {df.shape[1]} cols")
    return df


def read_payments() -> pd.DataFrame:
    path = get_raw_path("payments")
    logger.info(f"[EXTRACT] payments ← {path.name}")
    df = pd.read_csv(path)
    logger.info(f"[EXTRACT] payments: {len(df):,} rows × {df.shape[1]} cols")
    return df


def read_products() -> pd.DataFrame:
    path = get_raw_path("products")
    logger.info(f"[EXTRACT] products ← {path.name}")
    df = pd.read_csv(path)
    logger.info(f"[EXTRACT] products: {len(df):,} rows × {df.shape[1]} cols")
    return df


def extract_all() -> dict[str, pd.DataFrame]:
    """
    Đọc tất cả 5 bảng cùng lúc.

    Returns:
        {"orders": df, "order_items": df, "customers": df,
         "payments": df, "products": df}
    """
    logger.info("[EXTRACT] ── Starting full extract ──")
    tables = {
        "orders":      read_orders(),
        "order_items": read_order_items(),
        "customers":   read_customers(),
        "payments":    read_payments(),
        "products":    read_products(),
    }
    total = sum(df.shape[0] for df in tables.values())
    logger.info(f"[EXTRACT] Done — {len(tables)} tables | {total:,} total rows")
    return tables
