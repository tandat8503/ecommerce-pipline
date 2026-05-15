"""
load/load_local.py — Load data xuống local filesystem dưới dạng Parquet.

Architecture:
    Lưu vào 2 nơi:
    1. dt=YYYY-MM-DD/  → Partitioned storage (để audit/replay/history)
    2. latest/         → Current state (để query nhanh/dashboard)

Format: Parquet (Snappy compression)
"""

import pandas as pd
from pathlib import Path

from pipeline.utils.config import (
    get_staging_path, 
    get_staging_latest_path,
    get_warehouse_path,
    get_warehouse_latest_path
)
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def _save_parquet(df: pd.DataFrame, path: Path, label: str) -> None:
    """Helper: ghi DataFrame ra Parquet + log kết quả."""
    path.parent.mkdir(parents=True, exist_ok=True)
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
    """Lưu bảng staging vào cả partition folder và latest folder."""
    # 1. Save to partition
    partition_path = get_staging_path(table_name)
    _save_parquet(df, partition_path, f"staging/{table_name} (partition)")
    
    # 2. Save to latest
    latest_path = get_staging_latest_path(table_name)
    _save_parquet(df, latest_path, f"staging/{table_name} (latest)")


def load_all_staging(tables: dict[str, pd.DataFrame]) -> None:
    """Lưu tất cả bảng staging."""
    logger.info("[LOAD LOCAL] ── Saving to Staging Layer (Data Lake) ──")
    for name, df in tables.items():
        load_staging(name, df)


# ─────────────────────────────────────────────────────────────────────────────
# WAREHOUSE (fact + dim)
# ─────────────────────────────────────────────────────────────────────────────

def load_warehouse(table_name: str, df: pd.DataFrame) -> None:
    """Lưu bảng warehouse vào cả partition folder và latest folder."""
    # 1. Save to partition
    partition_path = get_warehouse_path(table_name)
    _save_parquet(df, partition_path, f"warehouse/{table_name} (partition)")
    
    # 2. Save to latest
    latest_path = get_warehouse_latest_path(table_name)
    _save_parquet(df, latest_path, f"warehouse/{table_name} (latest)")


def load_all_warehouse(tables: dict[str, pd.DataFrame]) -> None:
    """Lưu tất cả warehouse tables."""
    logger.info("[LOAD LOCAL] ── Saving to Warehouse Layer ──")
    for name, df in tables.items():
        load_warehouse(name, df)
