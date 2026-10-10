"""Phase 5: professional Excel reporting workbook (openpyxl).

Sheets: Executive Dashboard, Operational KPIs, Seller Analysis, Regional
Analysis, Delivery Delays, Risk Prioritization, Scenario Analysis, Assumptions,
Data Dictionary. Inputs (assumptions) vs calculated outputs clearly separated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

NAVY = "1F3864"
ACCENT = "2E75B6"
LIGHT = "DDEBF7"
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
HEADER_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(name="Calibri", bold=True, color=NAVY, size=14)
SUBTLE = Font(name="Calibri", color="595959", size=9, italic=True)
THIN = Side(style="thin", color="B4C6E7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _header(ws, row: int, cols: list[str]) -> None:
    for j, c in enumerate(cols, start=1):
        cell = ws.cell(row=row, column=j, value=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def _frame(ws, df: pd.DataFrame, start_row: int = 3, number_formats: dict | None = None) -> int:
    _header(ws, start_row, list(df.columns))
    for i, row in enumerate(df.itertuples(index=False), start=start_row + 1):
        for j, val in enumerate(row, start=1):
            cell = ws.cell(row=i, column=j, value=val)
            cell.border = BORDER
            if number_formats and df.columns[j - 1] in number_formats:
                cell.number_format = number_formats[df.columns[j - 1]]
    for j, col in enumerate(df.columns, start=1):
        width = max(12, min(34, max(len(str(col)), *(len(str(v)) for v in df[col].head(30))) + 2))
        ws.column_dimensions[get_column_letter(j)].width = width
    # Excel Table object for filters.
    end = get_column_letter(len(df.columns)) + str(start_row + len(df))
    tab = Table(
        displayName=f"T_{ws.title.replace(' ', '')[:20]}_{start_row}", ref=f"A{start_row}:{end}"
    )
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    ws.add_table(tab)
    return start_row + len(df) + 3


def _title_block(ws, title: str, subtitle: str, mode: str) -> None:
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = subtitle + (
        "  |  SOURCE: SYNTHETIC DEMO DATA (not real findings)"
        if mode == "demo"
        else "  |  SOURCE: Olist real data"
    )
    ws["A2"].font = SUBTLE
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def _bar_chart(ws, title: str, data_row_end: int, cat_col: int, val_col: int, pos: str) -> None:
    chart = BarChart()
    chart.type = "col"
    chart.title = title
    chart.y_axis.title = "Late rate"
    data = Reference(ws, min_col=val_col, min_row=3, max_row=data_row_end)
    cats = Reference(ws, min_col=cat_col, min_row=4, max_row=data_row_end)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.height, chart.width = 7.5, 14
    ws.add_chart(chart, pos)


def build_workbook(
    out_path: Path,
    mode: str,
    period: str,
    kpis: dict[str, Any],
    seg_state: pd.DataFrame,
    seg_category: pd.DataFrame,
    pareto: pd.DataFrame,
    model_results: list[dict],
    scenario_df: pd.DataFrame,
    assumptions_note: str,
    data_dict: pd.DataFrame,
    delay_table: pd.DataFrame,
) -> Path:
    wb = Workbook()

    # 1. Executive Dashboard
    ws = wb.active
    ws.title = "Executive Dashboard"
    _title_block(
        ws,
        "Executive Dashboard — Delivery Risk Lab",
        f"Period: {period}. Eligible orders: {kpis.get('n_eligible')}.",
        mode,
    )
    kpi_rows = [
        (
            "Late-delivery rate (eligible)",
            kpis.get("late_rate"),
            "share of eligible delivered orders arriving after estimate",
        ),
        (
            "On-time delivery rate (eligible)",
            kpis.get("on_time_rate"),
            "1 - late rate; eligible denominator only",
        ),
        ("Eligible orders", kpis.get("n_eligible"), "delivered with actual + estimated dates"),
        ("Late orders", kpis.get("n_late"), "eligible orders arriving after estimate"),
        ("Mean lead time (days)", kpis.get("mean_lead_time_days"), "purchase -> delivered"),
        ("Median lead time (days)", kpis.get("median_lead_time_days"), "purchase -> delivered"),
        (
            "Mean approval->carrier (days)",
            kpis.get("mean_approval_to_carrier_days"),
            "fulfillment stage 1, where available",
        ),
        (
            "Mean carrier->delivered (days)",
            kpis.get("mean_carrier_to_delivered_days"),
            "fulfillment stage 2, where available",
        ),
        (
            "Mean delay, late only (days)",
            kpis.get("mean_delay_days_late_only"),
            "severity among late orders",
        ),
    ]
    ws["A4"] = (
        "Key figures are calculated outputs (not editable). Editable inputs live on Assumptions."
    )
    ws["A4"].font = SUBTLE
    _header(ws, 5, ["KPI", "Value", "Definition"])
    for i, (k, v, d) in enumerate(kpi_rows, start=6):
        ws.cell(row=i, column=1, value=k).border = BORDER
        c = ws.cell(row=i, column=2, value=v)
        c.border = BORDER
        if isinstance(v, float) and v < 1:
            c.number_format = "0.0%"
        ws.cell(row=i, column=3, value=d).border = BORDER
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 60

    # 2. Operational KPIs
    ws2 = wb.create_sheet("Operational KPIs")
    _title_block(ws2, "Operational KPIs", f"Period: {period}. Denominator: eligible orders.", mode)
    kpi_df = pd.DataFrame([{"metric": k, "value": v} for k, v in kpis.items()])
    _frame(ws2, kpi_df)

    # 3. Seller Analysis
    ws3 = wb.create_sheet("Seller Analysis")
    _title_block(
        ws3,
        "Seller Analysis — concentration of delays",
        "Unit: seller (order-level outcome attributed via items). Small samples flagged.",
        mode,
    )
    _frame(ws3, pareto.head(100), number_formats={"late_rate": "0.0%", "cum_late_share": "0.0%"})

    # 4. Regional Analysis
    ws4 = wb.create_sheet("Regional Analysis")
    _title_block(
        ws4,
        "Regional Analysis — late rate by customer state",
        f"Period: {period}. Small samples flagged.",
        mode,
    )
    end_row = _frame(ws4, seg_state, number_formats={"late_rate": "0.0%"}) - 3
    _bar_chart(ws4, "Late rate by state", end_row, 1, 3, f"A{end_row + 2}")

    # 5. Delivery Delays
    ws5 = wb.create_sheet("Delivery Delays")
    _title_block(
        ws5,
        "Delivery Delays — severity & category patterns",
        "Late-only severity plus late rate by product category group.",
        mode,
    )
    _frame(ws5, delay_table)
    _frame(ws5, seg_category, start_row=len(delay_table) + 7, number_formats={"late_rate": "0.0%"})

    # 6. Risk Prioritization
    ws6 = wb.create_sheet("Risk Prioritization")
    _title_block(
        ws6,
        "Risk Prioritization — model vs baselines (TEST set)",
        "Thresholds chosen on validation; test held out. Empirical, not hypothetical.",
        mode,
    )
    rows = []
    for r in model_results:
        rows.append(
            {
                "model": r.get("model"),
                "roc_auc": r.get("roc_auc"),
                "pr_auc": r.get("pr_auc"),
                "precision": r.get("precision"),
                "recall": r.get("recall"),
                "threshold": r.get("threshold"),
                "n_test": r.get("n_test"),
            }
        )
    _frame(
        ws6,
        pd.DataFrame(rows),
        number_formats={"roc_auc": "0.00", "pr_auc": "0.00", "precision": "0.0%", "recall": "0.0%"},
    )

    # 7. Scenario Analysis (hypothetical)
    ws7 = wb.create_sheet("Scenario Analysis")
    _title_block(
        ws7,
        "Scenario Analysis — HYPOTHETICAL projections",
        "Illustrative intervention effects. Not observed savings.",
        mode,
    )
    ws7["A4"] = (
        "YELLOW cells are editable assumptions. "
        "Changing them does not alter other sheets automatically — rerun the pipeline."
    )
    ws7["A4"].font = SUBTLE
    ws7["A5"] = "assumption: cost_per_review (USD)"
    ws7["B5"] = 2.0
    ws7["B5"].fill = INPUT_FILL
    ws7["A6"] = "assumption: effectiveness low/base/high"
    for j, v in enumerate([0.10, 0.25, 0.45], start=2):
        c = ws7.cell(row=6, column=j, value=v)
        c.fill = INPUT_FILL
        c.number_format = "0%"
    _frame(ws7, scenario_df, start_row=8)

    # 8. Assumptions
    ws8 = wb.create_sheet("Assumptions")
    _title_block(ws8, "Assumptions & Limitations", "Read before citing any number.", mode)
    for i, line in enumerate(assumptions_note.splitlines(), start=4):
        ws8.cell(row=i, column=1, value=line)
    ws8.column_dimensions["A"].width = 150

    # 9. Data Dictionary
    ws9 = wb.create_sheet("Data Dictionary")
    _title_block(ws9, "Data Dictionary", "KPI definitions with denominators.", mode)
    _frame(ws9, data_dict)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path
