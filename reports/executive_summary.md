# Executive Summary

> **Data-status notice:** the real Olist dataset has not been ingested in this
> environment (see `data/README.md` for download steps). Empirical findings are
> therefore **PENDING**. Numbers in §4 are from the **synthetic demo fixture**
> (600 orders, seed 42) and illustrate the machinery only — they are not business
> findings. The client deck `reports/consulting_deck_demo.pptx` is likewise DEMO-labeled.

## 1. Business question

Where do delivery delays occur, what is associated with them, can risk be
flagged at approval time, and how should a small daily review capacity be spent?

## 2. Findings (demo fixture — illustrative, NOT empirical)

- Eligible delivered orders: 346 of 600 (canceled/unavailable/in-transit excluded).
- Late rate ~54%; mean lead time ~15.6 days (≈4.9d approval→carrier + ≈9.7d carrier→delivery).
- Higher late rates in MG/SP states and short promised windows; delays
  concentrated across a subset of sellers (Pareto). These are **potential
  contributing factors**, not proven causes.
- Approval-time model (test n=68): logistic ROC-AUC 0.63, HGB 0.59, rule 0.59.
  Modest signal: at 20 reviews/day the model catches ~35% of test lates vs ~30%
  random — directionally helpful, not deployment-grade on this evidence.
- Simulation (base 25% assumed fix rate, 50 reviews/day): model ranking rescues
  ~7.6 orders/day (P5–P95: 4–12) vs ~6.8 random — **hypothetical** projection.

## 3. Limitations

No inventory/capacity/cost/counterfactual data; undelivered orders excluded;
demo sample tiny; model needs real-data validation, calibration review, and a
measured pilot before any operational use.

## 4. Recommendations

1. Download Olist data and rerun (`--mode real`) to replace pending findings.
2. Pilot model-ranked reviews within existing capacity; measure actual rescue rate.
3. Operationally validate seller/segment patterns before renegotiations or SLAs.
4. Do not quote savings until intervention effects are observed.
