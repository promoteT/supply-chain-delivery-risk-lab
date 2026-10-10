# Methodology

## 1. Data & ingestion

- Source: Olist Brazilian E-Commerce Public Dataset (Kaggle, ~100k orders).
- `src/supply_chain_lab/ingestion.py`: prefers `data/raw/*.csv` (real mode),
  falls back to deterministic synthetic fixtures (demo mode). Mandatory-column
  checks; per-table row/column audit.
- Raw data never committed (`data/raw/`, `data/processed/` gitignored).

## 2. Quality control (`validation.py`, `sql/data_quality.sql`)

Identifiers, duplicates, timestamp ordering (purchase ≤ approval ≤ carrier ≤
delivered), invalid values, join cardinality (orders 1–N items), missingness
table, and an eligibility audit. Canceled/unavailable/undelivered orders are
excluded from late-rate denominators — never labeled on-time.

## 3. Aggregation (`features.py`)

One-to-many items aggregated to one row per order (counts, sellers, value,
freight, modal category group) before any rate is computed. Seller region =
dominant (max-price) seller state — an order-level attribute, not an outcome.

## 4. Diagnostics (`diagnostics.py`, `sql/operational_kpis.sql`, `seller_diagnostics.sql`)

Headline KPIs, lead-time/severity distributions, segment late rates with sample
sizes, seller Pareto. Associations reported as potential contributing factors.

## 5. Risk model (`modelling.py`)

- Prediction time: immediately after `order_approved_at`; target = actual >
  estimate among eligible delivered orders.
- Features: approval-known only (listed in DATA_DICTIONARY); leakage columns
  rejected programmatically (`assert_no_leakage` + frame allow-list).
- Chronological 60/20/20 split on approval time; preprocessing fit on train;
  threshold (Youden's J) chosen on validation; test held out. Metrics: ROC-AUC,
  PR-AUC, precision/recall, confusion matrix, calibration deciles, recall@k.

## 6. Simulation (`simulation.py`)

Random vs business-rule vs model ranking at 20/50/100 reviews/day; low/base/high
assumed effectiveness (10/25/45%); Monte Carlo (1000 runs, seed 42); illustrative
cost per review. No-intervention baseline included. All projections hypothetical.

## 7. Reporting (`excel_reporting.py`, `pipeline.py`)

One command (`python -m supply_chain_lab.pipeline --mode [auto|demo|real]`)
produces the 9-sheet Excel workbook, 4 charts, JSON audits, CSVs, and a 5-slide
deck. Excel inputs (yellow) vs calculated outputs are separated; numbers are
cross-checked against Python KPIs.
