# Business Case

## Context

An e-commerce marketplace fulfils a high volume of orders through many sellers
and regions. Management sees late deliveries hurting customer experience and
wants evidence — not anecdotes — on where to act first.

## Decision questions

- **A. Where do delivery delays occur?** (seller / region / category / duration segments)
- **B. Which operational characteristics are associated with delays?**
- **C. Can late-delivery risk be flagged at approval time**, early enough to
  prioritize proactive order reviews?
- **D. With a team able to review only K orders/day and uncertain fix rates,
  which prioritization rule looks most promising?**
- **E. What can management responsibly conclude** given what the data cannot show?

## What this project delivers against each question

| Question | Deliverable | Where |
|---|---|---|
| A | Segment late rates, Pareto of sellers, lead-time/severity charts | Excel sheets 2–5, `outputs/charts/` |
| B | Segment comparisons with sample sizes; "potential contributing factor" language | `outputs/late_by_state.csv`, reports |
| C | Approval-time risk model, chronological evaluation, recall@capacity | Excel sheet 6, `outputs/model_results.json` |
| D | Random vs rule vs model simulation, capacities 20/50/100, low/base/high effectiveness | Excel sheet 7, `outputs/scenario_comparison.csv` |
| E | Limitations, audit trail, pending-real-data findings | `reports/limitations.md`, this doc set |

## What it deliberately does NOT claim

No inventory optimization, no route optimization, no warehouse sizing, no causal
cost savings — the source data contains no inventory/capacity histories, no
route-level costs, and no observed intervention outcomes. All savings-type
numbers are labeled hypothetical/illustrative.
