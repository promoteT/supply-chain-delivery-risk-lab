# Implementation Plan — Supply Chain Delivery Risk & Operational Improvement Lab

Date: 2026-10-10 | Owner-agent: OpenCode/Muse Spark | Working dir: `D:\supply-chain-delivery-risk-lab` (repo root)

## 0. Situation
- Empty directory, no git repo. Python 3.12.10, pip 25.0.1, git 2.53, gh 2.96 (authed as promoteT).
- Pre-installed: pandas, numpy, scikit-learn, matplotlib, openpyxl, pytest, duckdb, python-pptx. Missing: ruff (will `pip install ruff`).

## 1. Defaults & decisions (no repeated clarification questions)
- Repo root IS the working directory (no extra nesting).
- Python 3.12 (3.11+ requirement satisfied). DuckDB for SQL layer (SQLite-compatible SQL, file-optional/in-memory).
- Real Olist CSVs are NOT present and Kaggle download needs credentials → implement real-data ingestion path + clear download instructions, and ship small SYNTHETIC fixtures for tests/demo. All fixture outputs labeled DEMO/SYNTHETIC, never presented as findings.
- Prediction time: immediately after order approval (`order_approved_at`). Target: delivered order arrives after `order_estimated_delivery_date` (binary late flag).
- Chronological split on approval timestamp: train 60% / validation 20% / test 20%.
- Models: majority-class baseline + business-rule baseline + Logistic Regression + HistGradientBoosting.
- Scenario capacities: 20/50/100 orders/day; effectiveness scenarios low/base/high; Monte Carlo with fixed seeds.
- Excel via openpyxl; deck via python-pptx; charts via matplotlib (Agg backend).
- Public GitHub repo name: `supply-chain-delivery-risk-lab` (create via `gh repo create` if publish step reached).

## 2. Milestones
- M1 Scaffold: pyproject.toml, .gitignore, dirs, PLAN.md, BUILD_LOG.md stub. ✅ acceptance: `pip install -e .` works.
- M2 Phase 1: config.py, ingestion.py, validation.py, features.py + sql/*.sql + DATA_DICTIONARY.md stub. Tests: ingestion, validation, features.
- M3 Phase 2–4: diagnostics.py, modelling.py, simulation.py. Tests: modelling, simulation.
- M4 Plumbing: excel_reporting.py, pipeline.py (demo + real modes), fixtures (synthetic Olist-like CSVs), tests: pipeline.
- M5 Verification: `pytest` all green; `python -m supply_chain_lab.pipeline --mode demo` runs end-to-end; outputs/ + Excel + charts verified; SQL executes via DuckDB.
- M6 Deliverables: reports/*.md, docs/*, consulting_deck.pptx (DEMO-labeled), README.md, .github/workflows/ci.yml.
- M7 Git: init, commits, `gh repo create` public + push (only source/docs/tests, no raw data). If push fails, leave local repo + publish commands.

## 3. Risks / limitations
- No real data → empirical findings stay PENDING; demo numbers synthetic-only.
- No inventory/cost/counterfactual data → no inventory/routing optimization, no causal savings claims.
- Keep deps lean: pandas, numpy, scikit-learn, matplotlib, openpyxl, duckdb, python-pptx, pytest (+ruff dev).

## 4. Acceptance checklist (mirrors mission §ACCEPTANCE CRITERIA, 14 items)
Tracked in docs/BUILD_LOG.md; final response reports each item honestly.
