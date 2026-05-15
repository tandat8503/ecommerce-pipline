# 🛒 Ecommerce Data Pipeline

ETL pipeline học **Data Engineering** thực chiến — xây dựng từ raw CSV lên Data Warehouse với kiến trúc module hoá chuẩn production.

---

## 📐 Architecture

```
Raw CSV (data/raw/)
      │
      ▼
  EXTRACT ──────────────────── extract_csv.py
      │
      ▼
  TRANSFORM (Staging) ──────── transform_orders.py
      │  clean timestamps        transform_customers.py
      │  normalize text          transform_products.py
      │  dedup                   transform_payments.py
      ▼
  VALIDATE Staging ─────────── validate_orders.py
      │
      ▼
  LOAD Staging ─────────────── load_local.py
      │  data/staging/*.parquet
      ▼
  BUILD Warehouse ──────────── build_fact_tables.py
      │  fact_orders             (filter delivered, JOIN 5 tables)
      │  dim_customers
      │  dim_products
      ▼
  VALIDATE Warehouse ───────── validate_fact_orders.py
      │
      ▼
  LOAD Warehouse ───────────── load_local.py
     data/warehouse/*.parquet
```

---

## 📊 Dataset

**Nguồn:** Olist Brazilian E-Commerce (Kaggle)

| Bảng | Mô tả | Rows (~) |
|------|-------|----------|
| `orders.csv` | Đơn hàng + timestamps + status | 99,000 |
| `order_items.csv` | Chi tiết sản phẩm trong mỗi đơn | 112,000 |
| `customers.csv` | Thông tin khách hàng | 99,000 |
| `payments.csv` | Thông tin thanh toán | 103,000 |
| `products.csv` | Danh mục sản phẩm | 32,000 |

---

## 📁 Folder Structure

```
ecommerce-pipeline/
│
├── data/
│   ├── raw/          ← Raw CSV (không commit lên Git)
│   ├── staging/      ← Cleaned Parquet (intermediate)
│   └── warehouse/    ← Fact + Dim tables (final)
│
├── pipeline/
│   ├── utils/
│   │   ├── config.py       ← Paths & settings
│   │   └── logger.py       ← Logging setup
│   │
│   ├── extract/
│   │   └── extract_csv.py  ← Đọc raw CSV
│   │
│   ├── transform/
│   │   ├── transform_orders.py       ← Clean orders
│   │   ├── transform_customers.py    ← Clean customers
│   │   ├── transform_products.py     ← Clean products
│   │   ├── transform_payments.py     ← Clean & aggregate payments
│   │   └── build_fact_tables.py      ← Build Star Schema
│   │
│   ├── validate/
│   │   ├── validate_orders.py        ← Validate staging
│   │   └── validate_fact_orders.py   ← Validate warehouse
│   │
│   ├── load/
│   │   ├── load_local.py      ← Save Parquet local
│   │   └── load_bigquery.py   ← Template: Upload to BigQuery
│   │
│   └── run_pipeline.py   ← Orchestrator (Entry point)
│
├── notebooks/        ← EDA Jupyter notebooks
├── tests/            ← Unit tests (pytest)
├── logs/             ← Pipeline logs (auto-generated)
│
├── config.yaml       ← Externalized configuration
├── requirements.txt
└── .gitignore
```

---

## 🌟 Data Model (Star Schema)

```
                    dim_customers
                    ─────────────
                    customer_id PK
                    customer_city
                    customer_state
                          │
                          │
dim_products         fact_orders              payments (embedded)
────────────         ─────────────────        ───────────────────
product_id PK ──→   order_id                  payment_type
category      ←──   product_id FK             total_payment_value
weight_g            customer_id FK            is_installment
                    order_date
                    order_year
                    order_month
                    order_quarter
                    revenue
                    shipping_cost
                    total_revenue
```

---

## 🚀 How to Run

### 1. Cài dependencies
```bash
pip install -r requirements.txt
```

### 2. Đặt raw data vào đúng chỗ
```
data/raw/orders/orders.csv
data/raw/order_items/order_items.csv
data/raw/customers/customers.csv
data/raw/payments/payments.csv
data/raw/products/products.csv
```

### 3. Chạy pipeline
```bash
python pipeline/run_pipeline.py
```

### 4. Output
```
data/staging/orders.parquet
data/staging/customers.parquet
data/staging/products.parquet
data/staging/payments.parquet
data/warehouse/fact_orders.parquet
data/warehouse/dim_customers.parquet
data/warehouse/dim_products.parquet
logs/pipeline_YYYY-MM-DD.log
```

---

## ✅ Data Quality Checks

### Staging layer
| Bảng | Checks |
|------|--------|
| orders | order_id not null, unique; order_status in whitelist |
| customers | customer_id not null, unique |
| products | product_id not null, unique |
| payments | order_id not null; payment_value > 0 |

### Warehouse layer
| Bảng | Checks |
|------|--------|
| fact_orders | No null FK; revenue > 0; no duplicate (order_id, product_id) |
| fact_orders | Referential integrity với dim_customers, dim_products |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 📈 Business Metrics Được Build

- Doanh thu theo ngày / tháng / năm
- Doanh thu theo khách hàng & top customers
- Doanh thu theo sản phẩm / category
- Tỷ lệ khách hàng quay lại (repeat rate)
- Top sản phẩm bán chạy
- Phân phối phương thức thanh toán
- Phân tích funnel theo order_status

---

## 🔮 Future Improvements

- [ ] Apache Airflow DAG để schedule pipeline
- [ ] Load lên BigQuery (`load_bigquery.py` đã có template)
- [ ] dbt models cho transformation
- [ ] Great Expectations cho data quality
- [ ] Docker + docker-compose
- [ ] CI/CD với GitHub Actions
