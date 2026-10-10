"""Data-quality validation: identifiers, duplicates, timestamps, joins, exclusions.

Every check returns records that feed the audit trail (validation_report dict)
so filtering exclusions are transparent and reproducible.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Order statuses that can never yield a delivered-late label.
NON_DELIVERED_STATUSES = {"canceled", "unavailable"}


def validate_orders(orders: pd.DataFrame) -> dict:
    """Run order-level quality checks. Returns a JSON-serializable report dict."""
    orders = orders.copy()
    for col in (
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ):
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors="coerce")
    report: dict = {"n_input": len(orders)}
    report["n_missing_order_id"] = int(orders["order_id"].isna().sum())
    report["n_duplicate_order_id"] = int(orders.duplicated(subset=["order_id"]).sum())
    report["status_counts"] = orders["order_status"].value_counts(dropna=False).to_dict()

    ts = orders[
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ]
    report["missing_timestamps"] = {c: int(ts[c].isna().sum()) for c in ts.columns}

    # Timestamp consistency: purchase <= approval <= carrier <= delivered.
    inconsistent = 0
    mask = ts["order_purchase_timestamp"].notna() & ts["order_approved_at"].notna()
    inconsistent += int(
        (ts.loc[mask, "order_purchase_timestamp"] > ts.loc[mask, "order_approved_at"]).sum()
    )
    mask2 = ts["order_approved_at"].notna() & ts["order_delivered_carrier_date"].notna()
    inconsistent += int(
        (ts.loc[mask2, "order_approved_at"] > ts.loc[mask2, "order_delivered_carrier_date"]).sum()
    )
    mask3 = ts["order_delivered_carrier_date"].notna() & ts["order_delivered_customer_date"].notna()
    inconsistent += int(
        (
            ts.loc[mask3, "order_delivered_carrier_date"]
            > ts.loc[mask3, "order_delivered_customer_date"]
        ).sum()
    )
    report["timestamp_inconsistencies"] = inconsistent

    # Invalid values.
    report["estimated_before_purchase"] = int(
        (
            ts["order_estimated_delivery_date"].notna()
            & ts["order_purchase_timestamp"].notna()
            & (ts["order_estimated_delivery_date"] < ts["order_purchase_timestamp"])
        ).sum()
    )
    return report


def validate_join_cardinality(orders: pd.DataFrame, order_items: pd.DataFrame) -> dict:
    """Check orders (1) - order_items (N) join cardinality to prevent duplication."""
    counts = order_items.groupby("order_id").size()
    orphan_items = int((~order_items["order_id"].isin(set(orders["order_id"]))).sum())
    orders_without_items = int((~orders["order_id"].isin(set(order_items["order_id"]))).sum())
    return {
        "n_order_items": len(order_items),
        "n_orders_with_items": int(counts.shape[0]),
        "mean_items_per_order": float(counts.mean()) if len(counts) else 0.0,
        "max_items_per_order": int(counts.max()) if len(counts) else 0,
        "orphan_items": orphan_items,
        "orders_without_items": orders_without_items,
    }


def split_eligible_orders(orders: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Split into eligible (delivered with actual + estimated dates) vs excluded.

    Missing delivery observations are NEVER treated as on-time; they are excluded
    from late-rate denominators and reported transparently.
    """
    delivered = orders[orders["order_status"] == "delivered"].copy()
    eligible_mask = (
        delivered["order_delivered_customer_date"].notna()
        & delivered["order_estimated_delivery_date"].notna()
    )
    eligible = delivered[eligible_mask].copy()
    excluded = orders[~orders.index.isin(eligible.index)].copy()

    exclusions = (
        excluded["order_status"].value_counts(dropna=False).to_dict() if len(excluded) else {}
    )
    audit = {
        "n_input": len(orders),
        "n_delivered": int((orders["order_status"] == "delivered").sum()),
        "n_eligible": len(eligible),
        "n_excluded": len(excluded),
        "excluded_by_status": {str(k): int(v) for k, v in exclusions.items()},
        "excluded_delivered_missing_dates": int(
            ((orders["order_status"] == "delivered") & ~orders.index.isin(eligible.index)).sum()
        ),
    }
    return eligible, excluded, audit


def missingness_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Share of missing values per column per table."""
    rows = []
    for name, df in tables.items():
        for col in df.columns:
            rows.append(
                {
                    "table": name,
                    "column": col,
                    "n_missing": int(df[col].isna().sum()),
                    "share_missing": round(float(df[col].isna().mean()), 4),
                }
            )
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values("share_missing", ascending=False).reset_index(drop=True)
    return out
