"""
tests/test_transform_products.py

Unit tests cho transform_products.clean_products().
"""

import pandas as pd
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.transform.transform_products import clean_products


def _make_products(**kwargs) -> pd.DataFrame:
    defaults = {
        "product_id":            ["p1", "p2", "p3", "p1"],
        "product_category_name": ["Toys", None, "  Books  ", "Toys"],
        "product_weight_g":      [100.0, None, 200.0, 100.0],
        "product_length_cm":     [10.0, 20.0, None, 10.0],
        "product_height_cm":     [5.0, 8.0, 3.0, 5.0],
        "product_width_cm":      [7.0, 12.0, 9.0, 7.0],
    }
    defaults.update(kwargs)
    return pd.DataFrame(defaults)


class TestCleanProducts:

    def test_duplicate_product_id_dropped(self):
        """Duplicate product_id bị drop."""
        df = clean_products(_make_products())
        assert df["product_id"].is_unique
        assert len(df) == 3

    def test_category_null_filled_with_unknown(self):
        """Null category → 'unknown'."""
        df = clean_products(_make_products())
        assert "unknown" in df["product_category_name"].values
        assert df["product_category_name"].isnull().sum() == 0

    def test_category_lowercased_and_stripped(self):
        """Category phải lowercase và không có whitespace thừa."""
        df = clean_products(_make_products())
        assert "toys" in df["product_category_name"].values
        assert "books" in df["product_category_name"].values   # "  Books  " → "books"

    def test_numeric_nulls_filled_with_median(self):
        """Null ở numeric cols được điền bằng median."""
        df = clean_products(_make_products())
        for col in ["product_weight_g", "product_length_cm"]:
            assert df[col].isnull().sum() == 0, f"Còn null ở cột {col}"
