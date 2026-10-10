"""Phase 2 diagnostics: KPIs, distributions, Pareto, segment comparisons.

Language discipline: associations are reported as 'potential contributing
factors'; nothing is labeled a proven root cause without operational validation.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .config import SQL_DIR


def headline_kpis(order_level: pd.DataFrame) -> dict:
    """KPIs over eligible orders (delivered, both dates present)."""
    elig = order_level[order_level["is_late"].notna()].copy()
    n = len(elig)
    n_late = int((elig["is_late"] == True).sum())
    late_rate = n_late / n if n else float("nan")
    lead = elig["lead_time_days"].dropna()
    delay = elig.loc[elig["is_late"] == True, "delay_days"].dropna()
    return {
        "n_eligible": int(n),
        "n_late": n_late,
        "late_rate": round(float(late_rate), 4) if n else None,
        "on_time_rate": round(float(1 - late_rate), 4) if n else None,
        "mean_lead_time_days": round(float(lead.mean()), 2) if len(lead) else None,
        "median_lead_time_days": round(float(lead.median()), 2) if len(lead) else None,
        "mean_approval_to_carrier_days": round(
            float(elig["approval_to_carrier_days"].dropna().mean()), 2
        )
        if elig["approval_to_carrier_days"].notna().any()
        else None,
        "mean_carrier_to_delivered_days": round(float(elig["carrier_time_days"].dropna().mean()), 2)
        if elig["carrier_time_days"].notna().any()
        else None,
        "mean_delay_days_late_only": round(float(delay.mean()), 2) if len(delay) else None,
        "max_delay_days": round(float(delay.max()), 2) if len(delay) else None,
    }


def late_rate_by(order_level: pd.DataFrame, by: str, min_n: int = 30) -> pd.DataFrame:
    """Late rate per segment with sample-size column (small groups flagged)."""
    elig = order_level[order_level["is_late"].notna()].copy()
    elig["_late"] = (elig["is_late"] == True).astype(int)
    g = elig.groupby(by).agg(n=("order_id", "count"), late_rate=("_late", "mean"))
    g = g.reset_index().sort_values("late_rate", ascending=False)
    g["late_rate"] = g["late_rate"].round(4)
    g["small_sample"] = g["n"] < min_n
    return g


def pareto_sellers(
    order_level: pd.DataFrame, order_items: pd.DataFrame, min_n: int = 10
) -> pd.DataFrame:
    """Seller concentration of late orders (order-level outcome, seller attribute)."""
    elig_ids = set(order_level.loc[order_level["is_late"].notna(), "order_id"])
    late_ids = set(order_level.loc[order_level["is_late"] == True, "order_id"])
    items = order_items[order_items["order_id"].isin(elig_ids)].copy()
    items["parent_late"] = items["order_id"].isin(late_ids).astype(int)
    g = items.groupby("seller_id").agg(
        n_orders=("order_id", "nunique"), n_late=("parent_late", "sum")
    )
    g = g.reset_index().sort_values("n_late", ascending=False)
    g["late_rate"] = (g["n_late"] / g["n_orders"]).round(4)
    g["cum_late_share"] = (g["n_late"].cumsum() / g["n_late"].sum()).round(4)
    g["small_sample"] = g["n_orders"] < min_n
    return g


def run_sql_file(sql_path: Path, tables: dict[str, pd.DataFrame]) -> list[pd.DataFrame]:
    """Execute a multi-statement .sql file against in-memory DuckDB tables."""
    con = duckdb.connect()
    for name, df in tables.items():
        con.register(name, df)
    # Strip full-line comments FIRST (they may contain semicolons), then split.
    code_lines = [ln for ln in sql_path.read_text().splitlines() if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(code_lines).split(";") if s.strip()]
    out = []
    for stmt in statements:
        out.append(con.execute(stmt).df())
    con.close()
    return out


def run_kpi_sql(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    frames = run_sql_file(SQL_DIR / "operational_kpis.sql", tables)
    return {f"q{i + 1}": f for i, f in enumerate(frames)}


# ---------------- Charts (each with question/units/period/n + interpretation hook) ---
def _style(ax, xlabel: str, ylabel: str, title: str, note: str) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.text(
        0.0, -0.32, note, transform=ax.transAxes, fontsize=8, color="#444444", va="top", ha="left"
    )
    ax.figure.tight_layout()


def chart_lead_time_dist(order_level: pd.DataFrame, out: Path, period: str, mode: str) -> Path:
    elig = order_level[order_level["lead_time_days"].notna()]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(elig["lead_time_days"].clip(upper=60), bins=30, color="#2563eb", edgecolor="white")
    _style(
        ax,
        "Lead time, purchase→delivered (days)",
        "Orders",
        "Q: How long does end-to-end delivery take?",
        f"Note: eligible delivered orders, n={len(elig)}. Period: {period}. "
        f"Source: {'SYNTHETIC demo data' if mode == 'demo' else 'Olist'}. "
        "Interpretation: right-tail length shows delay exposure.",
    )
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def chart_delay_severity(order_level: pd.DataFrame, out: Path, period: str, mode: str) -> Path:
    late = order_level.loc[order_level["is_late"] == True, "delay_days"].dropna()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(late.clip(upper=30), bins=30, color="#dc2626", edgecolor="white")
    _style(
        ax,
        "Days past estimated delivery (late orders only)",
        "Late orders",
        "Q: How severe are late deliveries?",
        f"Note: late eligible orders, n={len(late)}. Period: {period}. "
        f"Source: {'SYNTHETIC demo data' if mode == 'demo' else 'Olist'}. "
        "Interpretation: severity tail guides SLA tolerance discussion.",
    )
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def chart_late_by_segment(
    seg: pd.DataFrame, segment_col: str, out: Path, period: str, mode: str, top: int = 15
) -> Path:
    top_seg = seg.head(top)
    fig, ax = plt.subplots(figsize=(8, max(3.5, 0.4 * len(top_seg))))
    ax.barh(top_seg[segment_col].astype(str), top_seg["late_rate"] * 100, color="#0d9488")
    ax.invert_yaxis()
    for i, (_, r) in enumerate(top_seg.iterrows()):
        ax.text(r["late_rate"] * 100 + 0.3, i, f"n={int(r['n'])}", va="center", fontsize=8)
    _style(
        ax,
        "Late rate (%)",
        segment_col,
        f"Q: Which {segment_col} segments show the highest late rates?",
        f"Note: eligible orders. Period: {period}. Source: {'SYNTHETIC demo data' if mode == 'demo' else 'Olist'}. "
        "Interpretation: small-n segments need validation before action.",
    )
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def chart_pareto(pareto: pd.DataFrame, out: Path, period: str, mode: str, top: int = 30) -> Path:
    top_p = pareto.head(top)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(range(len(top_p)), top_p["n_late"].values, color="#7c3aed", label="Late orders")
    ax2 = ax.twinx()
    ax2.plot(
        range(len(top_p)),
        top_p["cum_late_share"].values * 100,
        color="#111827",
        marker="o",
        markersize=3,
        label="Cumulative share",
    )
    ax.set_xlabel("Sellers ranked by late-order count")
    ax.set_ylabel("Late orders (seller-attributed)")
    ax2.set_ylabel("Cumulative share of late orders (%)")
    ax.set_title(
        "Q: Are delays concentrated in a few sellers? (Pareto)", fontsize=11, fontweight="bold"
    )
    fig.text(
        0.05,
        -0.02,
        f"Note: seller-attributed late orders; multi-seller orders count once per seller. "
        f"Period: {period}. Source: {'SYNTHETIC demo data' if mode == 'demo' else 'Olist'}. "
        "Interpretation: steep early curve = targeted seller engagement may help (requires operational validation).",
        fontsize=8,
        color="#444444",
        ha="left",
    )
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out
