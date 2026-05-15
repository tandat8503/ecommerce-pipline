"""
utils/config.py — Single source of truth cho toàn bộ pipeline.
Đọc cấu hình từ config.yaml.
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT ROOT & CONFIG LOAD
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH  = PROJECT_ROOT / "config.yaml"

def load_config() -> dict[str, Any]:
    """Đọc file config.yaml."""
    if not CONFIG_PATH.exists():
        # Fallback default nếu file config không tồn tại
        return {
            "data": {"raw_dir": "data/raw", "staging_dir": "data/staging", "warehouse_dir": "data/warehouse"},
            "pipeline": {"revenue_status": "delivered", "min_price": 0.0}
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

_cfg = load_config()

# ─────────────────────────────────────────────────────────────────────────────
# PATHS (đọc từ config.yaml)
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR       = PROJECT_ROOT / "data"
RAW_DIR        = PROJECT_ROOT / _cfg["data"]["raw_dir"]
STAGING_BASE   = PROJECT_ROOT / _cfg["data"]["staging_dir"] / "ecommerce"
WAREHOUSE_BASE = PROJECT_ROOT / _cfg["data"]["warehouse_dir"] / "ecommerce"
LOG_DIR        = PROJECT_ROOT / _cfg["logging"]["log_dir"]

# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
PIPELINE_DATE  = datetime.now().strftime("%Y-%m-%d")
REVENUE_STATUS = _cfg["pipeline"]["revenue_status"]
MIN_PRICE      = _cfg["pipeline"]["min_price"]

# BigQuery (TODO: update in config.yaml)
GCP_PROJECT_ID = _cfg.get("bigquery", {}).get("project_id", "your-gcp-project-id")
BQ_DATASET     = _cfg.get("bigquery", {}).get("dataset", "ecommerce_dwh")

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
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_raw_path(table: str) -> Path:
    if table not in RAW_FILES:
        raise KeyError(f"Unknown table '{table}'")
    path = RAW_FILES[table]
    if not path.exists():
        raise FileNotFoundError(f"Raw file not found: {path}")
    return path

def get_staging_path(table: str, date: str = PIPELINE_DATE) -> Path:
    partition_dir = STAGING_BASE / f"dt={date}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    return partition_dir / f"{table}.parquet"

def get_staging_latest_path(table: str) -> Path:
    latest_dir = STAGING_BASE / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    return latest_dir / f"{table}.parquet"

def get_warehouse_path(table: str, date: str = PIPELINE_DATE) -> Path:
    partition_dir = WAREHOUSE_BASE / f"dt={date}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    return partition_dir / f"{table}.parquet"

def get_warehouse_latest_path(table: str) -> Path:
    latest_dir = WAREHOUSE_BASE / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    return latest_dir / f"{table}.parquet"

def ensure_dirs() -> None:
    for d in [
        STAGING_BASE / f"dt={PIPELINE_DATE}",
        STAGING_BASE / "latest",
        WAREHOUSE_BASE / f"dt={PIPELINE_DATE}",
        WAREHOUSE_BASE / "latest",
        LOG_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
