from supply_chain_lab import validation as V


def test_validate_orders_keys(tables):
    rep = V.validate_orders(tables["orders"])
    for k in (
        "n_input",
        "n_missing_order_id",
        "n_duplicate_order_id",
        "status_counts",
        "missing_timestamps",
        "timestamp_inconsistencies",
    ):
        assert k in rep
    assert rep["n_input"] == len(tables["orders"])


def test_join_cardinality(tables):
    rep = V.validate_join_cardinality(tables["orders"], tables["order_items"])
    assert rep["mean_items_per_order"] >= 1.0
    assert rep["orphan_items"] == 0


def test_eligible_excludes_missing_not_on_time(tables):
    elig, excluded, audit = V.split_eligible_orders(tables["orders"])
    assert audit["n_eligible"] + audit["n_excluded"] == audit["n_input"]
    assert elig["order_delivered_customer_date"].notna().all()
    # every non-delivered order must be excluded
    nondel = tables["orders"][tables["orders"]["order_status"] != "delivered"]
    assert len(excluded) >= len(nondel)


def test_missingness_sorted(tables):
    m = V.missingness_table(tables)
    assert "share_missing" in m.columns
    assert (m["share_missing"].diff().fillna(0) <= 1e-9).all(), "missingness not sorted desc"
