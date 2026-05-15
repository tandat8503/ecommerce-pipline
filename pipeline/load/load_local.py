"""
pipeline/load/load_local.py
Save dataframes to local parquet files.
"""

import pandas as pd
from pathlib import Path
from pipeline.utils.config import config
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def save_parquet(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    size_mb = path.stat().st_size / 1_048_576
    logger.info(f"[LOAD LOCAL] ✅ Saved {path.name} ({len(df):,} rows, {size_mb:.2f} MB) to {path.parent}")

def load_staging(tables: dict):
    logger.info("[LOAD LOCAL] ── Saving Staging Layer ──")
    for name, df in tables.items():
        if config.write_partitioned:
            p = config.staging_base / f"dt={config.pipeline_date}" / f"{name}.parquet"
            save_parquet(df, p)
        if config.write_latest:
            p = config.staging_base / "latest" / f"{name}.parquet"
            save_parquet(df, p)

def load_warehouse(warehouse_tables: dict, mart_tables: dict):
    logger.info("[LOAD LOCAL] ── Saving Warehouse Layer ──")
    all_tables = {**warehouse_tables, **mart_tables}
    for name, df in all_tables.items():
        if config.write_partitioned:
            p = config.warehouse_base / f"dt={config.pipeline_date}" / f"{name}.parquet"
            save_parquet(df, p)
        if config.write_latest:
            p = config.warehouse_base / "latest" / f"{name}.parquet"
            save_parquet(df, p)
