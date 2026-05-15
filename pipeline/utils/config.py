"""
pipeline/utils/config.py
Reads configuration from config.yaml and provides settings for the pipeline.
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Resolve project root dynamically (assuming pipeline/utils/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

class PipelineConfig:
    def __init__(self, config_dict: Dict[str, Any]):
        self._cfg = config_dict
        
        # Paths
        self.raw_dir = PROJECT_ROOT / self._cfg.get("data", {}).get("raw_path", "data/raw")
        self.staging_base = PROJECT_ROOT / self._cfg.get("data", {}).get("staging_path", "data/staging/ecommerce")
        self.warehouse_base = PROJECT_ROOT / self._cfg.get("data", {}).get("warehouse_path", "data/warehouse/ecommerce")
        self.log_dir = PROJECT_ROOT / self._cfg.get("logging", {}).get("log_dir", "logs")
        
        # Pipeline Date
        pipeline_date_str = self._cfg.get("data", {}).get("pipeline_date", "auto")
        if pipeline_date_str == "auto":
            self.pipeline_date = datetime.now().strftime("%Y-%m-%d")
        else:
            self.pipeline_date = pipeline_date_str
            
        # Files Mapping
        self.raw_files = {}
        files_config = self._cfg.get("files", {})
        for table, rel_path in files_config.items():
            self.raw_files[table] = self.raw_dir / rel_path

        # Business Rules
        self.revenue_status = self._cfg.get("business", {}).get("revenue_status", "delivered")
        self.valid_order_statuses = set(self._cfg.get("business", {}).get("valid_order_statuses", []))
        
        # Load Targets
        self.load_target = self._cfg.get("load", {}).get("target", "local")
        self.write_latest = self._cfg.get("load", {}).get("write_latest", True)
        self.write_partitioned = self._cfg.get("load", {}).get("write_partitioned", True)
        
        # BigQuery
        self.bq_enabled = self._cfg.get("bigquery", {}).get("enabled", False)
        self.bq_project_id = self._cfg.get("bigquery", {}).get("project_id", "")
        self.bq_dataset = self._cfg.get("bigquery", {}).get("dataset", "ecommerce_dwh")
        self.bq_location = self._cfg.get("bigquery", {}).get("location", "US")

def load_config() -> PipelineConfig:
    """Load config.yaml and return a PipelineConfig object."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)
        
    return PipelineConfig(config_dict)

# Global config instance
config = load_config()

def get_raw_path(table: str) -> Path:
    """Get the absolute path to a raw CSV file."""
    if table not in config.raw_files:
        raise KeyError(f"Unknown table '{table}' in config.yaml under 'files'")
    return config.raw_files[table]

def get_staging_path(table: str, partitioned: bool = True) -> Path:
    """Get path for staging output (partitioned or latest)."""
    if partitioned:
        p = config.staging_base / f"dt={config.pipeline_date}" / f"{table}.parquet"
    else:
        p = config.staging_base / "latest" / f"{table}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def get_warehouse_path(table: str, partitioned: bool = True) -> Path:
    """Get path for warehouse output (partitioned or latest)."""
    if partitioned:
        p = config.warehouse_base / f"dt={config.pipeline_date}" / f"{table}.parquet"
    else:
        p = config.warehouse_base / "latest" / f"{table}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
