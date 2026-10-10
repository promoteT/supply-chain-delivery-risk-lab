# Interview Guide — 5-minute business-case walkthrough

(For a CEL Supply Chain Analyst interview. All demo numbers below are SYNTHETIC
fixture outputs used to show the machinery; real-data findings are pending the
Olist download.)

## 1. The problem (45s)

"An e-commerce marketplace has high order volumes and rising late deliveries.
Management asked five questions: where delays occur, what predicts them, whether
we can flag risk at approval time, how to spend a small daily review capacity,
and what can responsibly be concluded. I built a reproducible lab around the
public Olist dataset (~100k Brazilian e-commerce orders) to answer exactly that."

## 2. Data engineering I stand behind (60s)

"First, quality control. I validate identifiers, duplicates, timestamp order,
and join cardinality — order items are one-to-many, so I aggregate to one row
per order before any order-level rate. Canceled, unavailable and undelivered
orders are excluded from late-rate denominators and counted in an audit trail;
missing delivery dates are never treated as on-time. Every KPI definition and
denominator is documented. SQL cross-checks run in DuckDB."

## 3. Diagnostics (60s)

"On the demo fixture (600 synthetic orders, 346 eligible): late rate ~54%,
mean lead time ~14 days, split into ~5 days approval-to-carrier and ~10 days
carrier-to-delivered. Pareto shows concentration across sellers; MG/SP states
and short promised windows show higher late rates — but I report these as
potential contributing factors requiring operational validation, never proven
root causes, and I flag small samples."

## 4. Early-warning model (60s)

"Prediction time is fixed at order approval, using only approval-known
features — calendar, item/value/freight, category, regions, promised duration.
Strict leakage ban, chronological 60/20/20 split, preprocessing fit on train
only, threshold picked on validation, test held out. On the tiny synthetic test
set (n=68): logistic ROC-AUC 0.63, HGB 0.59, business rule 0.59. Honest read:
modest signal — ranking helps a little at tight capacity (recall@20: model 0.35
vs random 0.30) but this needs real-data validation before any deployment."

## 5. Decision support + close (45s)

"With 20/50/100 reviews per day and low/base/high assumed fix rates, Monte Carlo
simulation compares random, rule and model ranking. Model ranking looks most
promising but all rescued-order projections are hypothetical — no observed
intervention data exists. My recommendation: pilot model-ranked reviews, measure
actual rescue rates, validate seller patterns on the ground, and only then talk
about savings. From GRC I bring process mapping, control-style validation, and
risk-based prioritization — the same discipline, applied to operations data."

## Likely follow-ups

- "Why chronological split?" — prevents using future patterns to predict the past.
- "Why exclude undelivered?" — their outcome is unobserved; including them as
  on-time would bias rates downward.
- "Would you deploy this model?" — not on this evidence; needs real data,
  larger test coverage, calibration checks, and a measured pilot.
