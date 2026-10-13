"""Feature engineering: order-level aggregation + leakage-safe risk features.

Two outputs:
1. build_order_level() — clean order-level dataset with KPIs (uses all timestamps).
2. build_model_frame() — leakage-safe features known at/before order_approved_at.

Leakage prohibitions (enforced): actual delivery timestamp, carrier handover
timestamp, final order status, reviews, future seller stats, test-set stats.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Columns that must NEVER appear as model features.
LEAKAGE_COLUMNS = {
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_status",
    "delay_days",
    "is_late",
    "lead_time_days",
    "carrier_time_days",
    "approval_to_carrier_days",
}

# Coarse product-category rollup to keep dummies tractable.
CATEGORY_ROLLUP = {
    "bed_bath_table": "home",
    "furniture_decor": "home",
    "housewares": "home",
    "home_confort": "home",
    "garden_tools": "home",
    "computers_accessories": "electronics",
    "electronics": "electronics",
    "telephony": "electronics",
    "audio": "electronics",
    "consoles_games": "electronics",
    "fashion_bags_accessories": "fashion",
    "fashion_shoes": "fashion",
    "fashion_male_clothing": "fashion",
    "fashion_female_clothing": "fashion",
    "fashion_childrens_clothes": "fashion",
    "fashion_underwear_beach": "fashion",
    "fashion_sport": "fashion",
    "health_beauty": "beauty_health",
    "perfumery": "beauty_health",
    "sports_leisure": "leisure_sport",
    "toys": "leisure_sport",
    "baby": "leisure_sport",
    "books_general_interest": "media_books",
    "books_imported": "media_books",
    "books_technical": "media_books",
    "music": "media_books",
    "movies": "media_books",
}


def rollup_category(name: object) -> str:
    if pd.isna(name):
        return "unknown"
    return CATEGORY_ROLLUP.get(str(name), "other")


def aggregate_items(
    order_items: pd.DataFrame, products: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Aggregate one-to-many order_items to one row per order (no order duplication)."""
    items = order_items.copy()
    if products is not None and "product_category_name" in products.columns:
        items = items.merge(
            products[["product_id", "product_category_name"]].drop_duplicates("product_id"),
            on="product_id",
            how="left",
        )
    if "product_category_name" in items.columns:
        items["category_group"] = items["product_category_name"].apply(rollup_category)
    else:
        items["category_group"] = "unknown"

    agg = (
        items.groupby("order_id")
        .agg(
            n_items=("order_item_id", "count"),
            n_sellers=("seller_id", "nunique"),
            order_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
            primary_category=(
                "category_group",
                lambda s: s.mode().iloc[0] if len(s) else "unknown",
            ),
        )
        .reset_index()
    )
    return agg


def build_order_level(
    orders: pd.DataFrame,
    items_agg: pd.DataFrame,
    customers: pd.DataFrame | None = None,
    sellers: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Merge to a clean order-level table with lead-time KPIs (diagnostic use)."""
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
    df = orders.merge(items_agg, on="order_id", how="left")
    if customers is not None:
        df = df.merge(
            customers[["customer_id", "customer_state", "customer_city"]].drop_duplicates(
                "customer_id"
            ),
            on="customer_id",
            how="left",
        )
    # Seller region: dominant seller per order (largest price share) — order-level attribute.
    df["is_late"] = (
        df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
    ).astype("boolean")
    # Undelivered / missing dates -> NA label (never imputed as on-time).
    missing_label = (
        df["order_delivered_customer_date"].isna() | df["order_estimated_delivery_date"].isna()
    )
    df.loc[missing_label, "is_late"] = pd.NA

    df["lead_time_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    df["approval_to_carrier_days"] = (
        df["order_delivered_carrier_date"] - df["order_approved_at"]
    ).dt.total_seconds() / 86400
    df["carrier_time_days"] = (
        df["order_delivered_customer_date"] - df["order_delivered_carrier_date"]
    ).dt.total_seconds() / 86400
    df["delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    df["promised_days"] = (
        df["order_estimated_delivery_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    return df


def _seller_region_lookup(order_items: pd.DataFrame, sellers: pd.DataFrame | None) -> pd.DataFrame:
    """Dominant (max-price) seller state per order — leakage-safe (static attribute)."""
    if sellers is None or "seller_state" not in sellers.columns:
        return pd.DataFrame(columns=["order_id", "seller_state"])
    tmp = order_items.merge(
        sellers[["seller_id", "seller_state"]].drop_duplicates("seller_id"),
        on="seller_id",
        how="left",
    )
    idx = tmp.groupby("order_id")["price"].idxmax()
    return tmp.loc[idx, ["order_id", "seller_state"]].reset_index(drop=True)


NUMERIC_FEATURES = [
    "promised_days_at_approval",
    "n_items",
    "n_sellers",
    "is_multi_seller",
    "log_order_value",
    "log_freight_value",
    "freight_share",
    "approval_dow",
    "approval_month",
    "approval_hour",
    "is_weekend_approval",
]
CATEGORICAL_FEATURES = ["primary_category", "customer_state", "seller_state"]


def build_model_frame(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    customers: pd.DataFrame | None = None,
    sellers: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Leakage-safe modeling frame for eligible delivered orders.

    Uses ONLY information known at/before order_approved_at:
    approval calendar, item count/value/freight, product category,
    customer & seller region, promised duration.
    """
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
    eligible = orders[
        (orders["order_status"] == "delivered")
        & orders["order_delivered_customer_date"].notna()
        & orders["order_estimated_delivery_date"].notna()
        & orders["order_approved_at"].notna()
    ].copy()
    items_agg = aggregate_items(order_items, products)
    df = eligible.merge(items_agg, on="order_id", how="left")
    if customers is not None:
        df = df.merge(
            customers[["customer_id", "customer_state"]].drop_duplicates("customer_id"),
            on="customer_id",
            how="left",
        )
    df = df.merge(_seller_region_lookup(order_items, sellers), on="order_id", how="left")

    approved = pd.to_datetime(df["order_approved_at"])
    df["approval_dow"] = approved.dt.dayofweek
    df["approval_month"] = approved.dt.month
    df["approval_hour"] = approved.dt.hour
    df["is_weekend_approval"] = (approved.dt.dayofweek >= 5).astype(int)
    df["promised_days_at_approval"] = (
        pd.to_datetime(df["order_estimated_delivery_date"]) - approved
    ).dt.total_seconds() / 86400
    df["log_order_value"] = np.log1p(pd.to_numeric(df["order_value"], errors="coerce").fillna(0))
    df["log_freight_value"] = np.log1p(
        pd.to_numeric(df["freight_value"], errors="coerce").fillna(0)
    )
    df["freight_share"] = (
        pd.to_numeric(df["freight_value"], errors="coerce")
        / (
            pd.to_numeric(df["order_value"], errors="coerce")
            + pd.to_numeric(df["freight_value"], errors="coerce")
            + 1e-9
        )
    ).fillna(0)
    df["n_items"] = pd.to_numeric(df["n_items"], errors="coerce").fillna(0)
    df["n_sellers"] = pd.to_numeric(df["n_sellers"], errors="coerce").fillna(0)
    df["is_multi_seller"] = (df["n_sellers"] > 1).astype(int)
    df["customer_state"] = df.get("customer_state", pd.Series("unknown", index=df.index)).fillna(
        "unknown"
    )
    df["seller_state"] = df.get("seller_state", pd.Series("unknown", index=df.index)).fillna(
        "unknown"
    )
    df["primary_category"] = df.get(
        "primary_category", pd.Series("unknown", index=df.index)
    ).fillna("unknown")
    df["target_late"] = (
        pd.to_datetime(df["order_delivered_customer_date"])
        > pd.to_datetime(df["order_estimated_delivery_date"])
    ).astype(int)

    # Drop everything not known at/before approval: the frame keeps only the
    # order key, the approval timestamp (for chronological splitting), the
    # leakage-safe features, and the target.
    keep = (
        ["order_id", "order_approved_at", "target_late"] + NUMERIC_FEATURES + CATEGORICAL_FEATURES
    )
    df = df[[c for c in keep if c in df.columns]].copy()

    leak = LEAKAGE_COLUMNS.intersection(set(df.columns))
    if leak:
        raise ValueError(f"Leakage columns present in model frame: {sorted(leak)}")
    return df.reset_index(drop=True)
