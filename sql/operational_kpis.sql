-- operational_kpis.sql : headline delivery KPIs over ELIGIBLE delivered orders.
-- Eligible = status 'delivered' AND actual + estimated dates present.
-- Denominator for late/on-time rates = eligible orders only.
-- Engine: DuckDB. Day differences use (epoch(a) - epoch(b)) / 86400.0
-- (fractional days; SQLite equivalent is julianday(a) - julianday(b)).

-- 1. On-time vs late rates (eligible denominator)
SELECT
  COUNT(*) AS n_eligible,
  SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) AS n_late,
  ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_rate_pct,
  ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_rate_pct
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL;

-- 2. Lead-time distribution (days, purchase -> delivered)
SELECT
  AVG((epoch(order_delivered_customer_date) - epoch(order_purchase_timestamp)) / 86400.0) AS mean_lead_days,
  MIN((epoch(order_delivered_customer_date) - epoch(order_purchase_timestamp)) / 86400.0) AS min_lead_days,
  MAX((epoch(order_delivered_customer_date) - epoch(order_purchase_timestamp)) / 86400.0) AS max_lead_days
FROM orders
WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL;

-- 3. Fulfillment-stage split (approval->carrier vs carrier->delivered), where available
SELECT
  AVG((epoch(order_delivered_carrier_date) - epoch(order_approved_at)) / 86400.0) AS mean_approval_to_carrier_days,
  AVG((epoch(order_delivered_customer_date) - epoch(order_delivered_carrier_date)) / 86400.0) AS mean_carrier_to_delivered_days,
  COUNT(*) AS n_with_both_stages
FROM orders
WHERE order_status = 'delivered'
  AND order_approved_at IS NOT NULL
  AND order_delivered_carrier_date IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL;

-- 4. Delay severity among late orders (days past estimate)
SELECT
  AVG((epoch(order_delivered_customer_date) - epoch(order_estimated_delivery_date)) / 86400.0) AS mean_delay_days,
  MAX((epoch(order_delivered_customer_date) - epoch(order_estimated_delivery_date)) / 86400.0) AS max_delay_days,
  COUNT(*) AS n_late
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date > order_estimated_delivery_date;

-- 5. Late rate by customer region
SELECT c.customer_state AS region, COUNT(*) AS n_eligible,
  ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_rate_pct
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
GROUP BY c.customer_state ORDER BY late_rate_pct DESC;

-- 6. Late rate by promised-duration bucket
SELECT
  CASE WHEN (epoch(order_estimated_delivery_date) - epoch(order_purchase_timestamp)) / 86400.0 <= 7 THEN '0-7d'
       WHEN (epoch(order_estimated_delivery_date) - epoch(order_purchase_timestamp)) / 86400.0 <= 14 THEN '8-14d'
       WHEN (epoch(order_estimated_delivery_date) - epoch(order_purchase_timestamp)) / 86400.0 <= 21 THEN '15-21d'
       ELSE '22d+' END AS promised_bucket,
  COUNT(*) AS n,
  ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_rate_pct
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL AND order_estimated_delivery_date IS NOT NULL
GROUP BY promised_bucket ORDER BY promised_bucket;
