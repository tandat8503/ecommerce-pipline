"""
pipeline/load/load_bigquery.py
Template to load data into Google BigQuery.
"""

import pandas as pd
import os
from pipeline.utils.config import config
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def load_all_to_bigquery(tables: dict):
    if not config.bq_enabled:
        logger.info("[LOAD BQ] BigQuery is disabled in config.yaml. Skipping.")
        return

    logger.info("[LOAD BQ] ── Starting BigQuery Load ──")
    
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS env var is not set. Load might fail.")

    try:
        import pandas_gbq
    except ImportError:
        logger.error("pandas-gbq is not installed. Please add it to requirements.txt.")
        raise

    project_id = config.bq_project_id
    dataset = config.bq_dataset

    if not project_id:
        logger.error("BigQuery project_id is empty in config.yaml")
        raise ValueError("Missing project_id")

    for table_name, df in tables.items():
        destination = f"{project_id}.{dataset}.{table_name}"
        logger.info(f"[LOAD BQ] Uploading {table_name} ({len(df):,} rows) to {destination}...")
        try:
            pandas_gbq.to_gbq(
                dataframe=df,
                destination_table=destination,
                project_id=project_id,
                if_exists="replace",
                location=config.bq_location,
                progress_bar=False,
            )
            logger.info(f"[LOAD BQ] ✅ {table_name} uploaded successfully.")
        except Exception as e:
            logger.error(f"[LOAD BQ] ❌ Failed to upload {table_name}: {e}")
            raise
