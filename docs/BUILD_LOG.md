# Build Log

## 2026-10-10 — M1 Scaffold
- Inspected empty `D:\supply-chain-delivery-risk-lab`; Python 3.12.10, git + gh
  (authed) available; pandas/numpy/sklearn/matplotlib/openpyxl/pytest/duckdb/
  python-pptx pre-installed; installed `ruff` + project (`pip install -e .`).
- Wrote PLAN.md; created structure (src/supply_chain_lab, data/{raw,processed,
  fixtures}, sql, tests, reports, docs, outputs, .github/workflows).
- Decision: repo root = working dir; DuckDB engine; synthetic fixtures for
  demo/tests; real-data path via `data/raw/`.

## 2026-10-10 — M2/M3 Core modules
- Implemented config, ingestion, validation, features (leakage-safe frame),
  diagnostics (+charts), modelling (baselines/logistic/HGB, chronological
  split, validation-chosen threshold), simulation (Monte Carlo policies).
- Wrote sql/{data_quality,operational_kpis,seller_diagnostics}.sql (DuckDB).
- Wrote excel_reporting (9 sheets), pipeline (demo/real/auto + pptx deck),
  make_fixtures (seed 42, n=600).

## 2026-10-10 — M4 Tests & fixes (all 21 pass)
- Failures found and fixed:
  1. Object-dtype timestamps → defensive `pd.to_datetime` coercion in
     features/validation + fixture fix.
  2. Leakage guard tripped on raw columns → model frame now keeps only key +
     approval time + safe features + target.
  3. SQL runner split on `;` inside `--` comments → strip comments first.
  4. `julianday` not in DuckDB → epoch-based fractional-day diffs.
  5. pptx title placeholder API → use `.text_frame`.
- `ruff check` + `ruff format --check`: clean. `pytest`: **21 passed**.
- Demo run: logistic ROC-AUC 0.634 / HGB 0.586 / rule 0.593 (test n=68);
  Excel verified (9 sheets, chart, editable assumptions, dashboard late rate
  0.5405 = Python KPI); deck 5 slides; 4 charts rendered.

## 2026-10-10 — M5/M6 Docs & deliverables (this session)
- reports/{executive_summary,methodology,limitations}.md; docs/{DATA_DICTIONARY,
  BUSINESS_CASE,INTERVIEW_GUIDE}.md; README.md; CI workflow; docs/img charts.
- Real-data mode implemented but not yet exercised (no Kaggle CSVs locally).

## Blockers / pending
- Real Olist CSVs unavailable in this environment (need Kaggle download) →
  empirical findings marked PENDING; demo outputs labeled synthetic.
- Remote `origin https://github.com/promoteT/supply-chain-delivery-risk-lab.git`
  configured 2026-10-13; review fixes applied (freight_share NaN, hermetic
  pipeline, leakage guard, Excel regression, train-fit rule, single-class guard).

## 2026-10-13 — Review fixes + GitHub polish
- TDD RED→GREEN: itemless-order NaNs, leakage full-frame guard, hermetic
  pipeline (`processed_dir`/`deck_path`), Excel values/chart/inputs regression,
  train-fit business rule, single-class NaN guard. 27 tests pass, ruff clean.
- Docs: corrected lead-time numbers to demo KPIs (15.6 / 4.87 / 9.72);
  `.gitignore` += `.ruff_cache/`; README visual polish (badges, tables, charts).
