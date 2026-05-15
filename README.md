# Ecommerce Data Pipeline

A production-like ETL pipeline and Data Warehouse project for E-commerce data.

## Architecture

The pipeline processes raw CSV files through several layers to build a fully modeled Data Warehouse and analytics Marts.

```
data/raw/ (Raw CSV)
  ↓
[Extract & Clean]
  ↓
data/staging/ (Cleaned parquet files)
  ↓
[Model: Dims & Facts]
  ↓
data/warehouse/ (Star Schema parquet files)
  ↓
[Aggregate: Marts]
  ↓
data/warehouse/ (Mart parquet files)
  ↓
[Optional: BigQuery Load]
```

## Data Model

### Warehouse Layer (Star Schema)
- **`fact_orders`**: Order-level granularity.
- **`fact_order_items`**: Item-level granularity.
- **`fact_payments`**: Transaction-level granularity.
- **`dim_customers`**: Customer dimensions.
- **`dim_products`**: Product dimensions.
- **`dim_date`**: Date dimension generated from order dates.

### Mart Layer (Analytics Ready)
- `mart_revenue_by_day`
- `mart_revenue_by_month`
- `mart_revenue_by_category`
- `mart_payment_method_summary`
- `mart_order_status_daily`
- `mart_top_products`
- `mart_customer_geo`

## Configuration
All paths, business rules, and pipeline settings are managed in `config.yaml`. No paths are hardcoded in the Python scripts.

## How to Run

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the pipeline locally:**
   ```bash
   python -m pipeline.run_pipeline
   ```

3. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

## BigQuery (Optional)
This project includes a template for loading the final warehouse tables to Google BigQuery. 
To enable:
1. Edit `config.yaml`: Set `load.target: bigquery` and `bigquery.enabled: true`. Provide your `project_id`.
2. Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set in your environment.
