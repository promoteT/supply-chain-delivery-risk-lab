"""Dataset ingestion: locate, load, and document Olist (or fixture) tables.

Priority: data/raw/*.csv (real Olist) -> data/fixtures/*.csv (synthetic demo).
Never commits raw data; fixtures are synthetic and clearly labeled.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import EXPECTED_FILES, FIXTURES_DIR, MANDATORY_COLUMNS, RAW_DIR

logger = logging.getLogger(__name__)

TIMESTAMP_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "shipping_limit_date",
]


def resolve_source(data_dir: Path | None = None) -> tuple[Path, str]:
    """Return (directory, mode) where mode is 'real' or 'demo'."""
    raw = (data_dir / "raw") if data_dir else RAW_DIR
    fixtures = (data_dir / "fixtures") if data_dir else FIXTURES_DIR
    if raw.exists() and (raw / EXPECTED_FILES["orders"]).exists():
        return raw, "real"
    return fixtures, "demo"


def _read_csv(path: Path, parse_dates: bool = False) -> pd.DataFrame:
    df = pd.read_csv(path)
    if parse_dates:
        for col in TIMESTAMP_COLS:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_tables(data_dir: Path | None = None) -> tuple[dict[str, pd.DataFrame], str]:
    """Load all available tables. Returns (tables, mode)."""
    directory, mode = resolve_source(data_dir)
    if data_dir is not None:
        # allow tests to point at an arbitrary folder containing the csvs directly
        direct = data_dir / EXPECTED_FILES["orders"]
        if direct.exists():
            directory = data_dir
    tables: dict[str, pd.DataFrame] = {}
    for key, fname in EXPECTED_FILES.items():
        path = directory / fname
        if path.exists():
            tables[key] = _read_csv(path, parse_dates=(key in ("orders", "order_items")))
            logger.info("Loaded %s: %s rows from %s", key, len(tables[key]), path)
        else:
            logger.warning("Missing table %s (expected at %s)", key, path)
    if "orders" not in tables:
        raise FileNotFoundError(
            f"orders table not found in {directory}. "
            "See data/README.md for download instructions or use --mode demo."
        )
    return tables, mode


def check_mandatory_columns(tables: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """Return {table: [missing columns]} for mandatory columns."""
    missing: dict[str, list[str]] = {}
    for table, cols in MANDATORY_COLUMNS.items():
        if table not in tables:
            missing[table] = cols
            continue
        absent = [c for c in cols if c not in tables[table].columns]
        if absent:
            missing[table] = absent
    return missing


def tables_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Row/column counts per table for the audit trail."""
    return pd.DataFrame(
        [
            {"table": name, "rows": len(df), "columns": len(df.columns)}
            for name, df in tables.items()
        ]
    )
