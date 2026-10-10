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
