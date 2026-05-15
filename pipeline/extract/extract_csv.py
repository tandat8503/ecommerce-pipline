"""
pipeline/extract/extract_csv.py
Extract raw CSV files into pandas DataFrames.
"""

import pandas as pd
from typing import Dict
from pipeline.utils.config import config, get_raw_path
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

def extract_all() -> Dict[str, pd.DataFrame]:
    """
    Read all CSV files mapped in config.yaml.
    Raises FileNotFoundError if any expected file is missing.
    """
    logger.info("[EXTRACT] ── Starting CSV Extraction ──")
    raw_data = {}
    
    for table_name in config.raw_files.keys():
        path = get_raw_path(table_name)
        if not path.exists():
            error_msg = f"Raw CSV file missing for table '{table_name}' at: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        logger.info(f"[EXTRACT] Reading {table_name} from {path.name}...")
        df = pd.read_csv(path)
        logger.info(f"[EXTRACT] Loaded {table_name}: {len(df):,} rows.")
        raw_data[table_name] = df
        
    logger.info("[EXTRACT] ── Extraction Complete ──")
    return raw_data
