"""Central configuration: paths, constants, seeds, scenario assumptions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIXTURES_DIR = DATA_DIR / "fixtures"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"
SQL_DIR = PROJECT_ROOT / "sql"

RANDOM_SEED = 42

# Olist file names (Brazilian E-Commerce Public Dataset by Olist, Kaggle).
# Expected inside data/raw/ after following data/README.md instructions.
EXPECTED_FILES: dict[str, str] = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

# Mandatory columns per table (subset needed by this project).
MANDATORY_COLUMNS: dict[str, list[str]] = {
    "orders": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
        "freight_value",
    ],
    "customers": ["customer_id", "customer_state", "customer_city"],
    "sellers": ["seller_id", "seller_state", "seller_city"],
    "products": ["product_id", "product_category_name"],
}

# Prediction time: immediately after order approval. Only features known at or
# before order_approved_at may be used by the risk model.
PREDICTION_TIME_COL = "order_approved_at"

# Chronological split fractions on approval timestamp.
TRAIN_FRAC = 0.60
VALID_FRAC = 0.20  # remainder -> test

# Operational review capacities (orders/day) and intervention effectiveness scenarios.
REVIEW_CAPACITIES: list[int] = [20, 50, 100]
EFFECTIVENESS_SCENARIOS: dict[str, float] = {"low": 0.10, "base": 0.25, "high": 0.45}
MONTE_CARLO_RUNS = 1000


@dataclass(frozen=True)
class ScenarioAssumptions:
    """Editable hypothetical intervention assumptions (NOT observed data)."""

    cost_per_review: float = 2.0  # illustrative USD per proactively investigated order
    effectiveness: dict[str, float] = field(default_factory=lambda: dict(EFFECTIVENESS_SCENARIOS))
    capacities: tuple[int, ...] = (20, 50, 100)
    seed: int = RANDOM_SEED

    def describe(self) -> str:
        lines = [
            "Hypothetical intervention assumptions (illustrative only, not observed):",
            f"- cost_per_review = {self.cost_per_review} (illustrative USD/order)",
            "- effectiveness (share of flagged late orders rescued): "
            + ", ".join(f"{k}={v}" for k, v in self.effectiveness.items()),
            f"- daily review capacities = {list(self.capacities)}",
        ]
        return "\n".join(lines)
