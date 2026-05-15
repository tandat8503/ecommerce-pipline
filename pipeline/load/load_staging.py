"""
load_staging.py — Load layer.

Nhiệm vụ DUY NHẤT của file này:
  Nhận DataFrame đã transform → lưu xuống staging layer dưới dạng Parquet.

Tại sao dùng Parquet thay vì CSV trong production?
  ✅ Nhanh hơn CSV 10-100x khi đọc (columnar storage)
  ✅ Giữ nguyên kiểu dữ liệu (datetime, int, float)
  ✅ Nén tự động → nhỏ hơn CSV ~5x
  ✅ Tương thích với Spark, BigQuery, DuckDB, Athena, Redshift
"""

import pandas as pd

from pipeline.config import get_staging_path
from pipeline.logger import get_logger

logger = get_logger(__name__)


def load_to_parquet(df: pd.DataFrame, table_name: str) -> None:
    """
    Lưu DataFrame vào staging layer dưới dạng Parquet.

    Args:
        df         : DataFrame đã qua transform
        table_name : Tên bảng, dùng làm tên file (vd: "orders" → orders.parquet)

    Output:
        Tạo file tại: data/staging/{table_name}.parquet
    """
    output_path = get_staging_path(table_name)

    logger.info(f"[LOAD] {table_name} → {output_path.name} ({len(df):,} rows)...")

    df.to_parquet(
        output_path,
        index=False,
        engine="pyarrow",
        compression="snappy",   # Nhanh nhất, phù hợp cho analytics workload
    )

    # Verify sau khi ghi — đây là pattern quan trọng trong production
    file_size_mb = output_path.stat().st_size / 1_048_576
    logger.info(
        f"[LOAD] ✅ {table_name} saved — "
        f"{len(df):,} rows | {file_size_mb:.2f} MB | {output_path}"
    )


def load_all(tables: dict[str, pd.DataFrame]) -> None:
    """
    Lưu tất cả các bảng trong dict vào staging layer.

    Args:
        tables: dict với key = tên bảng, value = DataFrame đã transform

    Example:
        load_all({
            "orders":      orders_df,
            "customers":   customers_df,
            ...
        })
    """
    logger.info(f"[LOAD] Starting bulk load — {len(tables)} tables...")

    for table_name, df in tables.items():
        load_to_parquet(df, table_name)

    logger.info(f"[LOAD] ✅ All {len(tables)} tables saved to staging")
