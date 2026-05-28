"""
scripts/check_warehouse_output.py
Validates the contents and quality of the warehouse output parquet files.
"""

import pandas as pd
from pathlib import Path
import sys

# Get project root to construct paths safely
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE_DIR = PROJECT_ROOT / "data" / "warehouse" / "ecommerce" / "latest"

def read_table(table_name: str) -> pd.DataFrame:
    """Read a parquet table from the warehouse latest directory."""
    path = WAREHOUSE_DIR / f"{table_name}.parquet"
    if not path.exists():
        raise ValueError(f"CRITICAL ERROR: Required file does not exist: {path}")
    return pd.read_parquet(path)

def print_table_overview(table_name: str, df: pd.DataFrame, business_keys: list = None) -> None:
    """Print an overview of a table."""
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")
    print(f"Shape:   {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"Columns: {', '.join(df.columns.tolist())}")
    
    print("\n--- Top 3 rows ---")
    print(df.head(3).to_string(index=False))
    
    print("\n--- Null counts ---")
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if null_counts.empty:
        print("No null values found.")
    else:
        print(null_counts.to_string())
        
    if business_keys and all(k in df.columns for k in business_keys):
        print(f"\n--- Duplicates by business key(s): {business_keys} ---")
        dup_count = df.duplicated(subset=business_keys).sum()
        print(f"Duplicates: {dup_count:,}")

def require_columns(table_name: str, df: pd.DataFrame, required_cols: list) -> None:
    """Verify that all required columns exist in the DataFrame."""
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"CRITICAL ERROR: {table_name} is missing required columns: {missing}")

def check_not_null(table_name: str, df: pd.DataFrame, cols: list) -> None:
    """Ensure specified columns do not contain null values."""
    for col in cols:
        if col in df.columns:
            nulls = df[col].isnull().sum()
            if nulls > 0:
                raise ValueError(f"CRITICAL ERROR: {table_name}.{col} contains {nulls} null values.")

def check_unique(table_name: str, df: pd.DataFrame, cols: list) -> None:
    """Ensure the combination of specified columns is unique."""
    if all(c in df.columns for c in cols):
        dups = df.duplicated(subset=cols).sum()
        if dups > 0:
            raise ValueError(f"CRITICAL ERROR: {table_name} has {dups} duplicates on {cols}.")

def check_non_negative(table_name: str, df: pd.DataFrame, cols: list) -> None:
    """Ensure specified columns do not contain negative values."""
    for col in cols:
        if col in df.columns:
            negatives = (df[col] < 0).sum()
            if negatives > 0:
                raise ValueError(f"CRITICAL ERROR: {table_name}.{col} contains {negatives} negative values.")

def check_fact_orders() -> None:
    name = "fact_orders"
    df = read_table(name)
    print_table_overview(name, df, ["order_id"])
    
    required_cols = [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp", 
        "order_date", "total_item_revenue", "total_shipping_cost", 
        "total_order_value", "total_payment_value", "payment_diff", "item_count"
    ]
    require_columns(name, df, required_cols)
    check_not_null(name, df, ["order_id"])
    check_unique(name, df, ["order_id"])
    
    print("\n--- order_status value_counts ---")
    print(df["order_status"].value_counts().to_string())
    
    print("\n--- Describe numeric columns ---")
    desc_cols = ["total_item_revenue", "total_shipping_cost", "total_order_value", "total_payment_value", "payment_diff", "item_count"]
    print(df[desc_cols].describe().to_string())
    
    print("\n--- Total Revenue (delivered) ---")
    delivered_df = df[df["order_status"] == "delivered"]
    print(f"total_order_value sum: {delivered_df['total_order_value'].sum():,.2f}")
    print(f"total_payment_value sum: {delivered_df['total_payment_value'].sum():,.2f}")

def check_fact_order_items() -> None:
    name = "fact_order_items"
    df = read_table(name)
    print_table_overview(name, df)
    
    required_cols = [
        "order_id", "product_id", "customer_id", "order_status",
        "order_purchase_timestamp", "order_date", "price", "shipping_charges",
        "item_total", "product_category_name"
    ]
    require_columns(name, df, required_cols)
    check_not_null(name, df, ["order_id", "product_id"])
    
    print("\n--- Describe numeric columns ---")
    desc_cols = ["price", "shipping_charges", "item_total"]
    print(df[desc_cols].describe().to_string())
    
    print("\n--- Top 10 product_category_name ---")
    print(df["product_category_name"].value_counts().head(10).to_string())

def check_fact_payments() -> None:
    name = "fact_payments"
    df = read_table(name)
    print_table_overview(name, df)
    
    required_cols = ["order_id", "payment_type", "payment_installments", "payment_value", "is_installment"]
    require_columns(name, df, required_cols)
    check_not_null(name, df, ["order_id"])
    check_non_negative(name, df, ["payment_value"])
    
    print("\n--- payment_type value_counts ---")
    print(df["payment_type"].value_counts().to_string())
    
    print("\n--- Describe numeric columns ---")
    print(df[["payment_value"]].describe().to_string())

def check_dim_customers() -> None:
    name = "dim_customers"
    df = read_table(name)
    print_table_overview(name, df, ["customer_id"])
    
    check_not_null(name, df, ["customer_id"])
    check_unique(name, df, ["customer_id"])
    
    if "customer_state" in df.columns:
        print("\n--- Top 10 customer_state ---")
        print(df["customer_state"].value_counts().head(10).to_string())

def check_dim_products() -> None:
    name = "dim_products"
    df = read_table(name)
    print_table_overview(name, df, ["product_id"])
    
    check_not_null(name, df, ["product_id", "product_category_name"])
    check_unique(name, df, ["product_id"])
    
    print("\n--- Top 10 product_category_name ---")
    print(df["product_category_name"].value_counts().head(10).to_string())

def check_dim_date() -> None:
    name = "dim_date"
    df = read_table(name)
    
    # either date or date_id should be unique
    if "date_id" in df.columns:
        print_table_overview(name, df, ["date_id"])
        check_unique(name, df, ["date_id"])
    elif "date" in df.columns:
        print_table_overview(name, df, ["date"])
        check_unique(name, df, ["date"])
    
    if "date" in df.columns:
        print(f"\nmin date: {df['date'].min()}")
        print(f"max date: {df['date'].max()}")

def check_marts() -> None:
    mart_tables = [
        "mart_revenue_by_day",
        "mart_revenue_by_month",
        "mart_revenue_by_category",
        "mart_payment_method_summary",
        "mart_order_status_daily",
        "mart_top_products",
        "mart_customer_geo"
    ]
    
    for mart_name in mart_tables:
        df = read_table(mart_name)
        if df.empty:
            raise ValueError(f"CRITICAL ERROR: Mart table {mart_name} is empty.")
        
        print(f"\n{'='*60}")
        print(f"MART: {mart_name}")
        print(f"{'='*60}")
        print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
        print("--- Head ---")
        print(df.head(3).to_string(index=False))
        
        # Check for negative revenue in marts
        for col in df.columns:
            if "revenue" in col.lower() or col.lower() == "total_value":
                check_non_negative(mart_name, df, [col])

def main() -> None:
    try:
        check_fact_orders()
        check_fact_order_items()
        check_fact_payments()
        check_dim_customers()
        check_dim_products()
        check_dim_date()
        check_marts()
        
        print("\n\n" + "*"*60)
        print("Warehouse output check completed successfully.")
        print("*"*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ CHECK FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
