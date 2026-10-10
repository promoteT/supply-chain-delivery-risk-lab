# Limitations & Interpretive Cautions

1. **No real data ingested yet.** All current numbers are synthetic-fixture
   demonstrations. Empirical findings: PENDING until `--mode real` runs.
2. **Coverage bias.** Late rates cover eligible delivered orders only.
   Undelivered/canceled orders are excluded; true service failure is understated.
3. **No causal identification.** Segment differences are associations. Seller,
   region, and category patterns need operational validation (capacity, carrier
   handoffs, address quality) before action.
4. **No inventory / capacity / routing data.** Nothing here optimizes stock,
   trucks, or warehouses — do not present it as such.
5. **No observed intervention outcomes.** Rescue projections and costs are
   hypothetical assumptions, not measured effects or savings.
6. **Small demo sample.** Test n=68; capacity-100 metrics saturate. Real-data
   rerun needs larger-sample confirmation and calibration review.
7. **Class & time effects.** ~50/50 demo late rate will not match reality;
   approval-time patterns may drift — monitor and retrain.
8. **Unit-of-analysis discipline.** Outcomes are order-level; seller/category
   views attribute (not transfer) outcomes — multi-seller orders counted per
   seller in Pareto inputs.
