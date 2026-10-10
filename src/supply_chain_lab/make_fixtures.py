"""Deterministic synthetic fixture generator (DEMO only).

Creates small Olist-like CSVs in data/fixtures/ with a fixed seed so tests and
the demo pipeline run without Kaggle credentials. Outputs are clearly synthetic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import FIXTURES_DIR, RANDOM_SEED

N_ORDERS = 600
STATES = ["SP", "RJ", "MG", "RS", "BA", "PR"]
CATEGORIES = [
    "bed_bath_table",
    "electronics",
    "fashion_shoes",
    "health_beauty",
    "sports_leisure",
    "books_general_interest",
    "toys",
    "housewares",
]


def generate(seed: int = RANDOM_SEED, n_orders: int = N_ORDERS) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    base = pd.Timestamp("2017-01-01")
    purchase = (
        base
        + pd.to_timedelta(rng.integers(0, 540, n_orders), unit="D")
        + pd.to_timedelta(rng.integers(0, 24, n_orders), unit="h")
    )
    approved_lag = rng.integers(0, 48, n_orders)
    approved = purchase + pd.to_timedelta(approved_lag, unit="h")
    promised_days = rng.choice([7, 10, 14, 21, 28], n_orders, p=[0.15, 0.25, 0.3, 0.2, 0.1])
    estimated = purchase + pd.to_timedelta(promised_days, unit="D")

    statuses = rng.choice(
        ["delivered", "delivered", "delivered", "delivered", "shipped", "canceled", "unavailable"],
        n_orders,
    )
    carrier_lag = rng.integers(1, 10, n_orders)
    carrier = approved + pd.to_timedelta(carrier_lag, unit="D")
    # Late risk rises with short promised window + certain states (synthetic pattern).
    risk = 0.25 + 0.25 * (promised_days <= 10) + rng.normal(0, 0.08, n_orders)
    actual_lead = promised_days + rng.normal(0, 3.5, n_orders) + (risk - 0.3) * 16
    delivered = purchase + pd.to_timedelta(np.clip(actual_lead, 1, 60).round(), unit="D")

    orders = pd.DataFrame(
        {
            "order_id": [f"ord_{i:05d}" for i in range(n_orders)],
            "customer_id": [f"cus_{rng.integers(0, 300):05d}" for _ in range(n_orders)],
            "order_status": statuses,
            "order_purchase_timestamp": purchase,
            "order_approved_at": approved,
            "order_delivered_carrier_date": np.where(statuses == "canceled", pd.NaT, carrier),
            "order_delivered_customer_date": np.where(
                np.isin(statuses, ["delivered"]), delivered, pd.NaT
            ),
            "order_estimated_delivery_date": estimated,
        }
    )
    # A few missing approvals to exercise validation.
    orders.loc[rng.choice(n_orders, 8, replace=False), "order_approved_at"] = pd.NaT

    n_items_total = 0
    item_rows = []
    for i, oid in enumerate(orders["order_id"]):
        n_items = int(rng.choice([1, 1, 1, 2, 3], p=[0.6, 0.15, 0.1, 0.1, 0.05]))
        for j in range(n_items):
            item_rows.append(
                {
                    "order_id": oid,
                    "order_item_id": j + 1,
                    "product_id": f"prod_{rng.integers(0, 60):04d}",
                    "seller_id": f"sel_{rng.integers(0, 40):04d}",
                    "price": round(float(rng.uniform(15, 400)), 2),
                    "freight_value": round(float(rng.uniform(5, 60)), 2),
                    "shipping_limit_date": purchase[i] + pd.Timedelta(days=int(rng.integers(2, 8))),
                }
            )
            n_items_total += 1
    order_items = pd.DataFrame(item_rows)

    customers = pd.DataFrame(
        {
            "customer_id": [f"cus_{i:05d}" for i in range(300)],
            "customer_state": rng.choice(STATES, 300),
            "customer_city": "fixture_city",
        }
    )
    sellers = pd.DataFrame(
        {
            "seller_id": [f"sel_{i:04d}" for i in range(40)],
            "seller_state": rng.choice(STATES, 40),
            "seller_city": "fixture_city",
        }
    )
    products = pd.DataFrame(
        {
            "product_id": [f"prod_{i:04d}" for i in range(60)],
            "product_category_name": rng.choice(CATEGORIES, 60),
        }
    )
    return {
        "orders": orders,
        "order_items": order_items,
        "customers": customers,
        "sellers": sellers,
        "products": products,
    }


def write_fixtures(out_dir=FIXTURES_DIR, seed: int = RANDOM_SEED) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "customers": "olist_customers_dataset.csv",
        "sellers": "olist_sellers_dataset.csv",
        "products": "olist_products_dataset.csv",
    }
    tables = generate(seed=seed)
    written = []
    for key, fname in mapping.items():
        path = out_dir / fname
        tables[key].to_csv(path, index=False)
        written.append(str(path))
    return written


if __name__ == "__main__":
    for p in write_fixtures():
        print(f"wrote {p}")
