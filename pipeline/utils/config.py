"""
utils/config.py — Single source of truth cho toàn bộ pipeline.

Architecture:
    Raw CSV (data/raw/)
        → Staging Data Lake  (data/staging/ecommerce/dt=YYYY-MM-DD/ + latest/)
        → Warehouse          (data/warehouse/ecommerce/dt=YYYY-MM-DD/ + latest/)
        → BigQuery DWH       (ecommerce_dwh.fact_orders, dim_*, ...)
"""

from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT ROOT
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT  = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# DATA LAKE PATHS
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR      = PROJECT_ROOT / "data"
RAW_DIR       = DATA_DIR / "raw"
STAGING_BASE  = DATA_DIR / "staging"  / "ecommerce"
WAREHOUSE_BASE= DATA_DIR / "warehouse" / "ecommerce"
LOG_DIR       = PROJECT_ROOT / "logs"

# ─────────────────────────────────────────────────────────────────────────────
# RAW FILE MAPPING
# ─────────────────────────────────────────────────────────────────────────────
RAW_FILES: dict[str, Path] = {
    "orders":      RAW_DIR / "orders"      / "orders.csv",
    "order_items": RAW_DIR / "order_items" / "order_items.csv",
    "customers":   RAW_DIR / "customers"   / "customers.csv",
    "payments":    RAW_DIR / "payments"    / "payments.csv",
    "products":    RAW_DIR / "products"    / "products.csv",
}

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
PIPELINE_DATE       = datetime.now().strftime("%Y-%m-%d")  # Ngày chạy pipeline
REVENUE_STATUS      = "delivered"                           # Status để tính doanh thu
MIN_PRICE           = 0.0

# BigQuery
GCP_PROJECT_ID      = "your-gcp-project-id"   # TODO: thay bằng project thật
BQ_DATASET          = "ecommerce_dwh"

# ─────────────────────────────────────────────────────────────────────────────
# PATH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_raw_path(table: str) -> Path:
    """Trả về path tới raw CSV. Raise nếu file không tồn tại."""
    if table not in RAW_FILES:
        raise KeyError(f"Unknown table '{table}'. Valid: {list(RAW_FILES)}")
    path = RAW_FILES[table]
    if not path.exists():
        raise FileNotFoundError(f"Raw file not found: {path}")
    return path


def get_staging_path(table: str, date: str = PIPELINE_DATE) -> Path:
    """
    Trả về path Parquet trong staging layer.

    Output: data/staging/ecommerce/dt=YYYY-MM-DD/{table}.parquet
    """
    partition_dir = STAGING_BASE / f"dt={date}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    return partition_dir / f"{table}.parquet"


def get_staging_latest_path(table: str) -> Path:
    """
    Trả về path Parquet trong staging/latest/.
    latest/ luôn chứa bản mới nhất để dễ đọc.

    Output: data/staging/ecommerce/latest/{table}.parquet
    """
    latest_dir = STAGING_BASE / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    return latest_dir / f"{table}.parquet"


def get_warehouse_path(table: str, date: str = PIPELINE_DATE) -> Path:
    """
    Trả về path Parquet trong warehouse layer.

    Output: data/warehouse/ecommerce/dt=YYYY-MM-DD/{table}.parquet
    """
    partition_dir = WAREHOUSE_BASE / f"dt={date}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    return partition_dir / f"{table}.parquet"


def get_warehouse_latest_path(table: str) -> Path:
    """
    Trả về path Parquet trong warehouse/latest/.

    Output: data/warehouse/ecommerce/latest/{table}.parquet
    """
    latest_dir = WAREHOUSE_BASE / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    return latest_dir / f"{table}.parquet"


def ensure_dirs() -> None:
    """Đảm bảo tất cả output dirs tồn tại trước khi pipeline chạy."""
    for d in [
        STAGING_BASE / f"dt={PIPELINE_DATE}",
        STAGING_BASE / "latest",
        WAREHOUSE_BASE / f"dt={PIPELINE_DATE}",
        WAREHOUSE_BASE / "latest",
        LOG_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
