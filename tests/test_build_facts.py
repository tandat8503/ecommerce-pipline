import pandas as pd
from pipeline.transform.build_facts import build_fact_orders

def test_build_fact_orders_granularity():
    orders = pd.DataFrame({
        "order_id": ["1", "2"],
        "customer_id": ["c1", "c2"],
    })
    order_items = pd.DataFrame({
        "order_id": ["1", "1", "2"],
        "product_id": ["p1", "p2", "p3"],
        "price": [10.0, 20.0, 15.0],
        "shipping_charges": [5.0, 5.0, 5.0]
    })
    payments = pd.DataFrame({
        "order_id": ["1", "2", "2"],
        "payment_type": ["credit_card", "voucher", "credit_card"],
        "payment_value": [40.0, 10.0, 10.0],
        "payment_installments": [1, 1, 2]
    })
    
    result = build_fact_orders(orders, order_items, payments)
    
    assert len(result) == 2 # 1 row per order
    
    order_1 = result[result["order_id"] == "1"].iloc[0]
    assert order_1["item_count"] == 2
    assert order_1["total_item_revenue"] == 30.0
    assert order_1["total_shipping_cost"] == 10.0
    assert order_1["total_order_value"] == 40.0
    assert order_1["total_payment_value"] == 40.0
    assert order_1["payment_methods_count"] == 1
    assert order_1["has_voucher"] == False
    assert order_1["has_credit_card"] == True
    assert order_1["is_installment"] == False

    order_2 = result[result["order_id"] == "2"].iloc[0]
    assert order_2["item_count"] == 1
    assert order_2["payment_methods_count"] == 2
    assert order_2["has_voucher"] == True
    assert order_2["has_credit_card"] == True
    assert order_2["is_installment"] == True
