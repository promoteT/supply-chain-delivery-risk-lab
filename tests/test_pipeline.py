"""Pipeline + diagnostics + SQL execution tests."""

from supply_chain_lab import diagnostics as D
from supply_chain_lab import features as F
from supply_chain_lab import pipeline as P


def test_headline_kpis_denominator(tables):
    agg = F.aggregate_items(tables["order_items"], tables["products"])
    ol = F.build_order_level(tables["orders"], agg, tables["customers"], tables["sellers"])
    k = D.headline_kpis(ol)
    assert k["n_eligible"] == int(ol["is_late"].notna().sum())
    assert abs(k["late_rate"] + k["on_time_rate"] - 1.0) < 1e-9


def test_sql_files_execute(tables):
    from supply_chain_lab.config import SQL_DIR

    for fname in ("data_quality.sql", "operational_kpis.sql", "seller_diagnostics.sql"):
        frames = D.run_sql_file(SQL_DIR / fname, tables)
        assert len(frames) > 0
        for f in frames:
            assert len(f) >= 0


def test_pipeline_demo_end_to_end(tmp_path):
    out = tmp_path / "outputs"
    res = P.run(mode="demo", out_dir=out)
    assert res["mode"] == "demo"
    assert (out / "delivery_risk_report_demo.xlsx").exists()
    assert (out / "scenario_comparison.csv").exists()
    assert (out / "model_results.json").exists()


def test_excel_workbook_sheets(tmp_path):
    from openpyxl import load_workbook

    out = tmp_path / "outputs"
    P.run(mode="demo", out_dir=out)
    wb = load_workbook(out / "delivery_risk_report_demo.xlsx")
    for sheet in (
        "Executive Dashboard",
        "Operational KPIs",
        "Seller Analysis",
        "Regional Analysis",
        "Delivery Delays",
        "Risk Prioritization",
        "Scenario Analysis",
        "Assumptions",
        "Data Dictionary",
    ):
        assert sheet in wb.sheetnames, f"missing sheet {sheet}"
