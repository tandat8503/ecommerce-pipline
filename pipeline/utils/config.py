"""
utils/config.py — Single source of truth cho toàn bộ pipeline.

Rule #1 production: KHÔNG hardcode path ở bất kỳ file nào khác.
Tất cả module đều import từ đây.
"""

from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

# ecommerce-pipeline/ (2 levels up từ utils/)
PROJECT_ROOT  = Path(__file__).resolve().parent.parent.parent

DATA_DIR      = PROJECT_ROOT / "data"
RAW_DIR       = DATA_DIR / "raw"
STAGING_DIR   = DATA_DIR / "staging"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
LOG_DIR       = PROJECT_ROOT / "logs"

# ─────────────────────────────────────────────────────────────────────────────
# RAW FILE MAPPING  →  table_name : path tới file CSV
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
ORDER_STATUS_FILTER = "delivered"   # Chỉ giữ đơn đã giao
MIN_PRICE           = 0.0           # Giá hợp lệ tối thiểu

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_raw_path(table: str) -> Path:
    """Trả về Path tới raw CSV. Raise nếu file không tồn tại."""
    if table not in RAW_FILES:
        raise KeyError(f"Unknown table '{table}'. Valid: {list(RAW_FILES)}")
    path = RAW_FILES[table]
    if not path.exists():
        raise FileNotFoundError(f"Raw file not found: {path}")
    return path


def get_staging_path(table: str) -> Path:
    """Trả về Path output Parquet trong staging/."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    return STAGING_DIR / f"{table}.parquet"


def get_warehouse_path(table: str) -> Path:
    """Trả về Path output Parquet trong warehouse/."""
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    return WAREHOUSE_DIR / f"{table}.parquet"


def ensure_dirs() -> None:
    """Đảm bảo tất cả output dirs tồn tại trước khi pipeline chạy."""
    for d in [STAGING_DIR, WAREHOUSE_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
