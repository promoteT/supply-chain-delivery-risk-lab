from supply_chain_lab import features as F


def test_aggregate_no_order_duplication(tables):
    agg = F.aggregate_items(tables["order_items"], tables["products"])
    assert agg["order_id"].is_unique
    assert (agg["n_items"] >= 1).all()


def test_order_level_labels(tables):
    agg = F.aggregate_items(tables["order_items"], tables["products"])
    ol = F.build_order_level(tables["orders"], agg, tables["customers"], tables["sellers"])
    assert len(ol) == len(tables["orders"])
    assert set(ol["is_late"].dropna().unique()) <= {True, False}
    # undelivered rows must not be labeled on-time
    undel = ol[ol["order_status"] != "delivered"]
    assert undel["is_late"].isna().all()


def test_model_frame_leakage_safe(tables):
    frame = F.build_model_frame(
        tables["orders"],
        tables["order_items"],
        tables["customers"],
        tables["sellers"],
        tables["products"],
    )
    assert "target_late" in frame.columns
    assert not F.LEAKAGE_COLUMNS.intersection(frame.columns)
    for col in ("order_delivered_customer_date", "order_delivered_carrier_date", "order_status"):
        assert col not in frame.columns
    assert len(frame) > 0


def test_model_frame_no_nans_for_itemless_orders():
    import pandas as pd

    base = pd.Timestamp("2017-03-01")
    orders = pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(5)],
            "customer_id": ["c1"] * 5,
            "order_status": ["delivered"] * 5,
            "order_purchase_timestamp": [base] * 5,
            "order_approved_at": [base] * 5,
            "order_delivered_carrier_date": [base + pd.Timedelta(days=2)] * 5,
            "order_delivered_customer_date": [base + pd.Timedelta(days=10)] * 5,
            "order_estimated_delivery_date": [base + pd.Timedelta(days=7)] * 5,
        }
    )
    items = pd.DataFrame(
        {
            "order_id": ["o0"],
            "order_item_id": [1],
            "product_id": ["p1"],
            "seller_id": ["s1"],
            "price": [50.0],
            "freight_value": [10.0],
        }
    )
    frame = F.build_model_frame(orders, items, None, None, None)
    assert frame["freight_share"].isna().sum() == 0
    assert frame[F.NUMERIC_FEATURES].isna().sum().sum() == 0
