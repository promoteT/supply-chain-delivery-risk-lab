# Data Dictionary & KPI Definitions

Source: Brazilian E-Commerce Public Dataset by Olist (Kaggle). Column names below
are the raw Olist names; derived fields are marked [derived].

## Raw inputs used

| Table | Key columns | Grain |
|---|---|---|
| `olist_orders_dataset.csv` | `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date` | 1 row / order |
| `olist_order_items_dataset.csv` | `order_id`, `order_item_id`, `product_id`, `seller_id`, `price`, `freight_value`, `shipping_limit_date` | 1 row / order item |
| `olist_customers_dataset.csv` | `customer_id`, `customer_state`, `customer_city` | 1 row / customer |
| `olist_sellers_dataset.csv` | `seller_id`, `seller_state`, `seller_city` | 1 row / seller |
| `olist_products_dataset.csv` | `product_id`, `product_category_name` | 1 row / product |

## Population: eligible vs excluded

- **Eligible order**: `order_status = 'delivered'` AND `order_delivered_customer_date`
  AND `order_estimated_delivery_date` both present.
- **Excluded**: everything else (canceled, unavailable, shipped/in-transit,
  delivered-but-missing-dates). Exclusions are counted in the audit trail
  (`validation_report.json`, `eligibility_audit`) and NEVER imputed as on-time.

## KPIs (all denominators explicit)

| KPI | Definition | Denominator | Unit |
|---|---|---|---|
| On-time delivery rate | eligible orders with actual ≤ estimate / eligible | eligible orders | share |
| Late-delivery rate | eligible orders with actual > estimate / eligible | eligible orders | share |
| Lead time | `order_delivered_customer_date − order_purchase_timestamp` | delivered, both timestamps | days |
| Approval → carrier | `order_delivered_carrier_date − order_approved_at` | orders with both timestamps | days |
| Carrier → delivered | `order_delivered_customer_date − order_delivered_carrier_date` | orders with both timestamps | days |
| Promised duration | `order_estimated_delivery_date − order_purchase_timestamp` | eligible | days |
| Delay severity | actual − estimate, late orders only | late eligible | days |
| Seller late rate | distinct late parent orders / distinct eligible parent orders | per-seller eligible | share |
| Recall@k | late orders caught in top-k risk ranks / all test lates | test lates | share |
| Precision@k | late orders in top-k / k reviewed | k | share |
| Expected rescued (scenario) | **HYPOTHETICAL** rescued lates under assumed effectiveness, Monte Carlo mean + P5–P95 | illustrative | orders |

## Model features (known at/before approval — `order_approved_at`)

`promised_days_at_approval`, `n_items`, `n_sellers`, `is_multi_seller`,
`log_order_value`, `log_freight_value`, `freight_share`, `approval_dow`,
`approval_month`, `approval_hour`, `is_weekend_approval`, `primary_category`,
`customer_state`, `seller_state`. Target `target_late` = actual > estimate.
Forbidden (leakage): actual/carrier timestamps, final status, reviews, any
post-approval or future-aggregated information.

## Demo-mode note

`data/fixtures/` holds small SYNTHETIC Olist-like tables (seed 42). Any number
produced from them is a technical demonstration, not a business finding.
