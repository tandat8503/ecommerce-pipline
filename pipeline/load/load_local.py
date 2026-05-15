"""
load/load_local.py — Load data xuống local filesystem dưới dạng Parquet.

Architecture:
    Lưu vào 2 nơi:
    1. dt=YYYY-MM-DD/  → Partitioned storage
    2. latest/         → Current state

Layers:
    - Staging
    - Warehouse (Fact/Dim)
    - Mart (Aggregated)
"""

import pandas as pd
from pathlib import Path
from pipeline.utils.config import (
    get_staging_path, 
    get_staging_latest_path,
    get_warehouse_path,
    get_warehouse_latest_path,
    PROJECT_ROOT
)
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# MART PATH HELPERS (Thêm vào đây cho nhanh, đúng ra nên có trong config.py)
# ─────────────────────────────────────────────────────────────────────────────
def get_mart_path(table: str, date: str) -> Path:
    p = PROJECT_ROOT / "data" / "mart" / "ecommerce" / f"dt={date}" / f"{table}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def get_mart_latest_path(table: str) -> Path:
    p = PROJECT_ROOT / "data" / "mart" / "ecommerce" / "latest" / f"{table}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _save_parquet(df: pd.DataFrame, path: Path, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    size_mb = path.stat().st_size / 1_048_576
    logger.info(f"[LOAD LOCAL] ✅ {label} → {path.name} | {len(df):,} rows | {size_mb:.2f} MB")


def load_all_staging(tables: dict[str, pd.DataFrame]) -> None:
    logger.info("[LOAD LOCAL] ── Saving to Staging Layer ──")
    for name, df in tables.items():
        _save_parquet(df, get_staging_path(name), f"staging/{name} (partition)")
        _save_parquet(df, get_staging_latest_path(name), f"staging/{name} (latest)")


def load_all_warehouse(tables: dict[str, pd.DataFrame]) -> None:
    logger.info("[LOAD LOCAL] ── Saving to Warehouse Layer ──")
    for name, df in tables.items():
        _save_parquet(df, get_warehouse_path(name), f"warehouse/{name} (partition)")
        _save_parquet(df, get_warehouse_latest_path(name), f"warehouse/{name} (latest)")


def load_all_mart(tables: dict[str, pd.DataFrame], date: str) -> None:
    logger.info("[LOAD LOCAL] ── Saving to Mart Layer ──")
    for name, df in tables.items():
        _save_parquet(df, get_mart_path(name, date), f"mart/{name} (partition)")
        _save_parquet(df, get_mart_latest_path(name), f"mart/{name} (latest)")
