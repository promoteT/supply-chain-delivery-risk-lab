"""Shared fixtures for tests: tiny synthetic Olist-like tables (in-memory)."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def tables():
    base = pd.Timestamp("2017-03-01")
    n = 120
    rng = np.random.default_rng(7)
    purchase = base + pd.to_timedelta(rng.integers(0, 200, n), unit="D")
    approved = purchase + pd.to_timedelta(rng.integers(0, 24, n), unit="h")
    promised = rng.choice([7, 14, 21], n)
    estimated = purchase + pd.to_timedelta(promised, unit="D")
    statuses = np.where(rng.random(n) < 0.85, "delivered", rng.choice(["shipped", "canceled"], n))
    delivered = purchase + pd.to_timedelta(
        (promised + rng.normal(0, 6, n)).round().clip(1, 60), unit="D"
    )
    carrier = approved + pd.to_timedelta(rng.integers(1, 6, n), unit="D")
    orders = pd.DataFrame(
        {
            "order_id": [f"t{i:04d}" for i in range(n)],
            "customer_id": [f"c{i % 20:04d}" for i in range(n)],
            "order_status": statuses,
            "order_purchase_timestamp": purchase,
            "order_approved_at": approved,
            "order_delivered_carrier_date": pd.to_datetime(
                np.where(statuses == "canceled", pd.NaT, carrier)
            ),
            "order_delivered_customer_date": pd.to_datetime(
                np.where(statuses == "delivered", delivered, pd.NaT)
            ),
            "order_estimated_delivery_date": estimated,
        }
    )
    rows = []
    for i, oid in enumerate(orders["order_id"]):
        for j in range(int(rng.choice([1, 2]))):
            rows.append(
                {
                    "order_id": oid,
                    "order_item_id": j + 1,
                    "product_id": f"p{j % 5:03d}",
                    "seller_id": f"s{rng.integers(0, 8):03d}",
                    "price": 50.0,
                    "freight_value": 10.0,
                    "shipping_limit_date": purchase[i] + pd.Timedelta(days=3),
                }
            )
    order_items = pd.DataFrame(rows)
    customers = pd.DataFrame(
        {
            "customer_id": [f"c{i:04d}" for i in range(20)],
            "customer_state": rng.choice(["SP", "RJ", "MG"], 20),
            "customer_city": "x",
        }
    )
    sellers = pd.DataFrame(
        {
            "seller_id": [f"s{i:03d}" for i in range(8)],
            "seller_state": rng.choice(["SP", "RJ"], 8),
            "seller_city": "y",
        }
    )
    products = pd.DataFrame(
        {
            "product_id": [f"p{i:03d}" for i in range(5)],
            "product_category_name": [
                "electronics",
                "toys",
                "books_general_interest",
                "fashion_shoes",
                "health_beauty",
            ],
        }
    )
    return {
        "orders": orders,
        "order_items": order_items,
        "customers": customers,
        "sellers": sellers,
        "products": products,
    }
