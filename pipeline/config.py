"""
config.py — Cấu hình tập trung cho toàn bộ pipeline.

Rule #1 của production: KHÔNG hardcode path/giá trị ở bất kỳ file nào khác.
Tất cả settings đều import từ đây.
"""

from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# ROOT PATHS
# ─────────────────────────────────────────────────────────────────────────────

# Thư mục chứa project này (ecommerce-pipeline/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Raw data nằm ở project dataset-ecommerce (cùng cấp với project này)
DATASET_ROOT = PROJECT_ROOT.parent / "dataset-ecommerce"
RAW_DIR      = DATASET_ROOT / "data" / "raw" / "ecommerce"

# Output của pipeline này
STAGING_DIR  = PROJECT_ROOT / "data" / "staging"
WAREHOUSE_DIR= PROJECT_ROOT / "data" / "warehouse"
MART_DIR     = PROJECT_ROOT / "data" / "mart"
LOG_DIR      = PROJECT_ROOT / "logs"

# ─────────────────────────────────────────────────────────────────────────────
# RAW FILE MAPPING
# Key = tên bảng, Value = đường dẫn tới folder chứa file CSV
# ─────────────────────────────────────────────────────────────────────────────
RAW_TABLE_DIRS = {
    "orders":       RAW_DIR / "orders",
    "order_items":  RAW_DIR / "order_items",
    "customers":    RAW_DIR / "customers",
    "payments":     RAW_DIR / "payments",
    "products":     RAW_DIR / "products",
}

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
DATA_SPLIT          = "train"       # "train" | "test"
ORDER_STATUS_FILTER = "delivered"   # Chỉ xử lý đơn đã giao thành công
MIN_PRICE           = 0.0           # Giá hợp lệ tối thiểu

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_raw_csv(table: str, split: str = DATA_SPLIT) -> Path:
    """
    Trả về đường dẫn tới file CSV thô của một bảng.

    Args:
        table : tên bảng ("orders", "customers", ...)
        split : "train" hoặc "test"

    Returns:
        Path tới file CSV

    Raises:
        KeyError  : nếu table không tồn tại trong mapping
        FileNotFoundError : nếu file không tồn tại trên disk
    """
    if table not in RAW_TABLE_DIRS:
        raise KeyError(
            f"Table '{table}' không tồn tại. "
            f"Các bảng hợp lệ: {list(RAW_TABLE_DIRS.keys())}"
        )
    path = RAW_TABLE_DIRS[table] / f"{table}_{split}.csv"
    if not path.exists():
        raise FileNotFoundError(f"File không tìm thấy: {path}")
    return path


def get_staging_path(table: str) -> Path:
    """Trả về đường dẫn output Parquet trong staging layer."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    return STAGING_DIR / f"{table}.parquet"


def ensure_dirs() -> None:
    """Tạo tất cả output directories nếu chưa tồn tại."""
    for d in [STAGING_DIR, WAREHOUSE_DIR, MART_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
