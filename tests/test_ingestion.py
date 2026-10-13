from supply_chain_lab import ingestion as I


def test_resolve_source_prefers_real_or_demo(tmp_path):
    directory, mode = I.resolve_source()
    assert mode in ("real", "demo")
    assert directory.exists() or mode == "demo"
    # tmp empty dir -> demo fixtures; raw with orders csv -> real
    _d2, m2 = I.resolve_source(tmp_path)
    assert m2 == "demo"
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "olist_orders_dataset.csv").write_text("order_id\n1\n")
    d3, m3 = I.resolve_source(tmp_path)
    assert m3 == "real"
    assert d3 == raw


def test_mandatory_columns_detected(tables):
    assert I.check_mandatory_columns(tables) == {}


def test_mandatory_columns_missing(tables):
    bad = dict(tables)
    bad["orders"] = tables["orders"].drop(columns=["order_approved_at"])
    missing = I.check_mandatory_columns(bad)
    assert missing["orders"] == ["order_approved_at"]


def test_tables_summary(tables):
    s = I.tables_summary(tables)
    assert set(s["table"]) >= {"orders", "order_items"}
    assert (s["rows"] > 0).all()
