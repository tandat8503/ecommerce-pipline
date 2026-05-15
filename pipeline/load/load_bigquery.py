"""
load/load_bigquery.py — Load data lên Google BigQuery.

Đây là bước cuối trong production pipeline thực tế.
Thay vì lưu Parquet local, data được push thẳng lên BigQuery
để team BI/Analytics query bằng Looker, Data Studio, Metabase...

Cách dùng trong production:
    1. Cài: pip install google-cloud-bigquery pandas-gbq pyarrow
    2. Set credentials: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    3. Gọi: load_to_bigquery(df, "dataset.table_name")

Hiện tại file này là TEMPLATE — bạn sẽ dùng khi học GCP.
"""

import pandas as pd

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# ── BigQuery Config ───────────────────────────────────────────────────────────
# Trong production, lấy từ environment variables hoặc Secret Manager
GCP_PROJECT_ID = "your-gcp-project-id"   # TODO: thay bằng project thật
BQ_DATASET     = "ecommerce_warehouse"    # Dataset trên BigQuery


def load_to_bigquery(
    df:         pd.DataFrame,
    table_name: str,
    if_exists:  str = "replace",          # "replace" | "append"
) -> None:
    """
    Load DataFrame lên BigQuery table.

    Args:
        df:         DataFrame cần upload
        table_name: Tên bảng (vd: "fact_orders" → project.dataset.fact_orders)
        if_exists:  "replace" = xoá bảng cũ + tạo mới
                    "append"  = thêm vào bảng đang có (dùng cho incremental load)

    Requires:
        pip install pandas-gbq google-cloud-bigquery pyarrow
        GOOGLE_APPLICATION_CREDENTIALS environment variable

    Example:
        load_to_bigquery(fact_orders_df, "fact_orders")
    """
    # Lazy import — chỉ import khi thật sự cần (không bắt buộc cài nếu dùng local)
    try:
        import pandas_gbq
    except ImportError:
        logger.error(
            "[LOAD BQ] ❌ pandas-gbq chưa được cài. "
            "Chạy: pip install pandas-gbq google-cloud-bigquery"
        )
        raise

    destination = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{table_name}"
    logger.info(f"[LOAD BQ] Uploading {len(df):,} rows → {destination}")

    pandas_gbq.to_gbq(
        dataframe    = df,
        destination_table = destination,
        project_id   = GCP_PROJECT_ID,
        if_exists    = if_exists,
        progress_bar = False,
    )

    logger.info(f"[LOAD BQ] ✅ {table_name} uploaded to BigQuery — {len(df):,} rows")


def load_all_to_bigquery(
    tables:    dict[str, pd.DataFrame],
    if_exists: str = "replace",
) -> None:
    """
    Upload tất cả warehouse tables lên BigQuery.

    Args:
        tables:    {"fact_orders": df, "dim_customers": df, ...}
        if_exists: "replace" hoặc "append"
    """
    logger.info(f"[LOAD BQ] ── Uploading {len(tables)} tables to BigQuery ──")
    for table_name, df in tables.items():
        load_to_bigquery(df, table_name, if_exists=if_exists)
    logger.info("[LOAD BQ] ── All tables uploaded ✅ ──")
