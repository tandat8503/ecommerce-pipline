import pandas as pd
from pipeline.transform.transform_orders import clean_orders

def test_clean_orders_keeps_full_status():
    df = pd.DataFrame({
        "order_id": ["1", "2", "3"],
        "customer_id": ["c1", "c2", "c3"],
        "order_status": ["delivered", "canceled", "shipped"],
        "order_purchase_timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"]
    })
    result = clean_orders(df)
    assert len(result) == 3
    statuses = set(result["order_status"].unique())
    assert statuses == {"delivered", "canceled", "shipped"}

def test_clean_orders_generates_date_parts():
    df = pd.DataFrame({
        "order_id": ["1"],
        "customer_id": ["c1"],
        "order_status": ["delivered"],
        "order_purchase_timestamp": ["2023-05-15 10:00:00"]
    })
    result = clean_orders(df)
    assert result["order_year"].values[0] == 2023
    assert result["order_month"].values[0] == 5
    assert "order_date" in result.columns
    assert "order_quarter" in result.columns
    assert "order_dow" in result.columns
