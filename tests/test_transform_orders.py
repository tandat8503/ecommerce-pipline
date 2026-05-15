"""
tests/test_transform_orders.py

Unit tests cho transform_orders.clean_orders().

Nguyên tắc test trong DE:
    - Test trên DataFrame nhỏ tự tạo (không dùng file thật)
    - Mỗi test chỉ kiểm tra 1 behaviour
    - Test tên rõ ràng: test_<function>_<behaviour>
"""

import pandas as pd
import pytest
import sys
from pathlib import Path

# Thêm project root vào sys.path để import được pipeline
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.transform.transform_orders import clean_orders


def _make_orders(**kwargs) -> pd.DataFrame:
    """Helper: tạo DataFrame orders mẫu để test."""
    defaults = {
        "order_id":                    ["o1", "o2", "o3"],
        "customer_id":                 ["c1", "c2", "c3"],
        "order_status":                ["delivered", "canceled", "shipped"],
        "order_purchase_timestamp":    ["2023-01-15 10:00:00", "2023-03-20 14:30:00", "2023-06-05 09:15:00"],
        "order_approved_at":           ["2023-01-15 10:05:00", None, "2023-06-05 09:20:00"],
        "order_delivered_timestamp":   ["2023-01-20 18:00:00", None, None],
        "order_estimated_delivery_date": ["2023-01-25", "2023-03-30", "2023-06-15"],
    }
    defaults.update(kwargs)
    return pd.DataFrame(defaults)


class TestCleanOrders:

    def test_timestamps_parsed_to_datetime(self):
        """Các cột timestamp phải được parse thành datetime."""
        df = clean_orders(_make_orders())
        assert pd.api.types.is_datetime64_any_dtype(df["order_purchase_timestamp"])
        assert pd.api.types.is_datetime64_any_dtype(df["order_approved_at"])

    def test_derived_columns_created(self):
        """Phải có đủ cột derived: order_date, year, month, quarter, dow."""
        df = clean_orders(_make_orders())
        for col in ["order_date", "order_year", "order_month", "order_quarter", "order_dow"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_derived_year_correct(self):
        """order_year phải đúng."""
        df = clean_orders(_make_orders())
        assert list(df["order_year"]) == [2023, 2023, 2023]

    def test_derived_month_correct(self):
        """order_month phải đúng."""
        df = clean_orders(_make_orders())
        assert list(df["order_month"]) == [1, 3, 6]

    def test_full_status_kept(self):
        """KHÔNG filter order_status — giữ cả delivered, canceled, shipped."""
        df = clean_orders(_make_orders())
        assert len(df) == 3
        assert set(df["order_status"]) == {"delivered", "canceled", "shipped"}

    def test_duplicate_order_id_dropped(self):
        """Duplicate order_id phải bị drop, giữ lần đầu tiên."""
        orders = _make_orders(
            order_id=["o1", "o1", "o2"],
            customer_id=["c1", "c1_dup", "c2"],
            order_status=["delivered", "delivered", "canceled"],
        )
        df = clean_orders(orders)
        assert len(df) == 2
        assert df["order_id"].is_unique

    def test_invalid_timestamp_becomes_nat(self):
        """Timestamp không hợp lệ phải thành NaT (errors='coerce')."""
        orders = _make_orders(
            order_purchase_timestamp=["2023-01-15 10:00:00", "INVALID_DATE", "2023-06-05 09:15:00"]
        )
        df = clean_orders(orders)
        assert pd.isna(df.loc[1, "order_purchase_timestamp"])
