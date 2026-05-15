"""
load/load_local.py — Load data xuống local filesystem dưới dạng Parquet.

Tại sao Parquet thay vì CSV trong production?
    ✅ Đọc nhanh hơn CSV 10-100x (columnar format)
    ✅ Giữ nguyên kiểu dữ liệu (datetime, int, float, bool)
    ✅ Tự động nén → nhỏ hơn CSV ~5x với compression=snappy
    ✅ Tương thích: Spark, BigQuery, DuckDB, Athena, Redshift, Pandas

Output:
    staging/   → data sau clean (intermediate)
    warehouse/ → fact + dim tables (final, dùng cho analytics)
"""

import pandas as pd

from pipeline.utils.config import get_staging_path, get_warehouse_path
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def _save_parquet(df: pd.DataFrame, path, label: str) -> None:
    """Helper: ghi DataFrame ra Parquet + log kết quả."""
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    size_mb = path.stat().st_size / 1_048_576
    logger.info(
        f"[LOAD LOCAL] ✅ {label} → {path.name} | "
        f"{len(df):,} rows | {size_mb:.2f} MB"
    )


# ─────────────────────────────────────────────────────────────────────────────
# STAGING (sau clean)
# ─────────────────────────────────────────────────────────────────────────────

def load_staging(table_name: str, df: pd.DataFrame) -> None:
    """Lưu 1 bảng cleaned vào data/staging/."""
    path = get_staging_path(table_name)
    logger.info(f"[LOAD LOCAL] staging/{table_name} ← {len(df):,} rows")
    _save_parquet(df, path, f"staging/{table_name}")


def load_all_staging(tables: dict[str, pd.DataFrame]) -> None:
    """Lưu tất cả bảng staging cùng lúc."""
    logger.info("[LOAD LOCAL] ── Saving to staging ──")
    for name, df in tables.items():
        load_staging(name, df)
    logger.info("[LOAD LOCAL] ── Staging done ──")


# ─────────────────────────────────────────────────────────────────────────────
# WAREHOUSE (fact + dim)
# ─────────────────────────────────────────────────────────────────────────────

def load_warehouse(table_name: str, df: pd.DataFrame) -> None:
    """Lưu 1 bảng fact/dim vào data/warehouse/."""
    path = get_warehouse_path(table_name)
    logger.info(f"[LOAD LOCAL] warehouse/{table_name} ← {len(df):,} rows")
    _save_parquet(df, path, f"warehouse/{table_name}")


def load_all_warehouse(tables: dict[str, pd.DataFrame]) -> None:
    """Lưu tất cả warehouse tables (fact + dim) cùng lúc."""
    logger.info("[LOAD LOCAL] ── Saving to warehouse ──")
    for name, df in tables.items():
        load_warehouse(name, df)
    logger.info("[LOAD LOCAL] ── Warehouse done ──")
