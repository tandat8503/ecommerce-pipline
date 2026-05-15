import pandas as pd
from pipeline.transform.transform_products import clean_products

def test_clean_products_deduplicate():
    df = pd.DataFrame({
        "product_id": ["p1", "p1", "p2"],
        "product_category_name": ["Toys", "Toys", None],
        "product_weight_g": [1, 1, None],
    })
    result = clean_products(df)
    assert len(result) == 2
    assert result["product_id"].is_unique

def test_clean_products_fill_unknown():
    df = pd.DataFrame({
        "product_id": ["p1", "p2"],
        "product_category_name": ["Toys", None],
        "product_weight_g": [1, 1],
    })
    result = clean_products(df)
    assert result.loc[result["product_id"] == "p2", "product_category_name"].values[0] == "unknown"

def test_clean_products_median_imputation():
    df = pd.DataFrame({
        "product_id": ["p1", "p2", "p3"],
        "product_weight_g": [10.0, 30.0, None],
    })
    result = clean_products(df)
    # Median of 10 and 30 is 20
    assert result.loc[result["product_id"] == "p3", "product_weight_g"].values[0] == 20.0
