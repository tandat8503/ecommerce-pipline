# 🛒 Ecommerce Data Pipeline (Pro Edition)

Hệ thống ETL pipeline hoàn chỉnh phục vụ phân tích dữ liệu E-commerce chuyên sâu.

---

## 📐 Architecture

Hệ thống được thiết kế theo mô hình **Snapshot-based Data Lakehouse**:

1.  **Raw Layer**: Dữ liệu gốc từ CSV.
2.  **Staging Layer**: Dữ liệu được làm sạch, giữ nguyên lịch sử (full status).
3.  **Warehouse Layer**: Mô hình hoá Star Schema với `fact_orders` (order-level) và `fact_order_items` (item-level).
4.  **Mart Layer**: Các bảng đã được aggregate sẵn phục vụ Dashboard nhanh chóng.
5.  **Serving Layer**: Hỗ trợ lưu trữ Local Parquet và load lên Google BigQuery.

---

## 📁 Data Modeling (Pro)

### Fact Tables
- **`fact_orders`**: 1 dòng = 1 đơn hàng. Chứa tổng giá trị, số lượng item, phí ship.
- **`fact_order_items`**: 1 dòng = 1 sản phẩm trong đơn hàng. Dùng để phân tích Category/Product.
- **`fact_payments`**: 1 dòng = 1 giao dịch thanh toán. Phân tích phương thức và trả góp.

### Mart Tables
- **`mart_revenue_daily`**: Doanh thu & AOV theo ngày.
- **`mart_category_performance`**: Hiệu suất theo danh mục sản phẩm.
- **`mart_payment_summary`**: Thống kê phương thức thanh toán.

---

## 🚀 Getting Started

### 1. Cấu hình
Chỉnh sửa `config.yaml` để thay đổi đường dẫn hoặc đích đến (local / bigquery).

### 2. Chạy Pipeline
```bash
make run
```

### 3. Kiểm tra kết quả
Dữ liệu sẽ được lưu tại `data/mart/ecommerce/latest/` và phân đoạn theo ngày tại `dt=YYYY-MM-DD/`.

---

## ✅ Điểm nâng cấp so với bản cũ
- [x] **Granularity chuẩn**: Tách biệt Fact Orders và Fact Order Items.
- [x] **Mart Layer**: Tối ưu tốc độ cho Dashboard.
- [x] **Config-Driven**: Điều khiển pipeline qua `config.yaml`.
- [x] **Date Partitioning**: Lưu trữ dữ liệu snapshot theo ngày.
- [x] **BigQuery Ready**: Sẵn sàng chuyển đổi target sang Cloud chỉ bằng 1 flag.
