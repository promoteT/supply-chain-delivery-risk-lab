-- data_quality.sql : reproducible quality checks (DuckDB/SQLite compatible).
-- Run against raw tables: orders, order_items.

-- 1. Missing identifiers
SELECT COUNT(*) AS n_missing_order_id FROM orders WHERE order_id IS NULL;

-- 2. Duplicate order records
SELECT order_id, COUNT(*) AS n
FROM orders GROUP BY order_id HAVING COUNT(*) > 1;

-- 3. Order status mix (canceled/unavailable/undelivered handled explicitly downstream)
SELECT order_status, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM orders GROUP BY order_status ORDER BY n DESC;

-- 4. Missing timestamps per column
SELECT
  SUM(CASE WHEN order_purchase_timestamp IS NULL THEN 1 ELSE 0 END) AS miss_purchase,
  SUM(CASE WHEN order_approved_at IS NULL THEN 1 ELSE 0 END) AS miss_approved,
  SUM(CASE WHEN order_delivered_carrier_date IS NULL THEN 1 ELSE 0 END) AS miss_carrier,
  SUM(CASE WHEN order_delivered_customer_date IS NULL THEN 1 ELSE 0 END) AS miss_delivered,
  SUM(CASE WHEN order_estimated_delivery_date IS NULL THEN 1 ELSE 0 END) AS miss_estimated,
  COUNT(*) AS n
FROM orders;

-- 5. Timestamp inconsistencies (purchase > approval; approval > carrier; carrier > delivered)
SELECT COUNT(*) AS n_inconsistent
FROM orders
WHERE (order_purchase_timestamp > order_approved_at)
   OR (order_approved_at > order_delivered_carrier_date)
   OR (order_delivered_carrier_date > order_delivered_customer_date);

-- 6. Join cardinality: items per order + orphans
SELECT AVG(cnt) AS mean_items_per_order, MAX(cnt) AS max_items_per_order
FROM (SELECT order_id, COUNT(*) AS cnt FROM order_items GROUP BY order_id);
SELECT COUNT(*) AS orphan_items FROM order_items
WHERE order_id NOT IN (SELECT order_id FROM orders);

-- 7. Eligible vs excluded (missing delivery dates are NEVER treated as on-time)
SELECT
  SUM(CASE WHEN order_status = 'delivered'
            AND order_delivered_customer_date IS NOT NULL
            AND order_estimated_delivery_date IS NOT NULL THEN 1 ELSE 0 END) AS n_eligible,
  SUM(CASE WHEN NOT (order_status = 'delivered'
            AND order_delivered_customer_date IS NOT NULL
            AND order_estimated_delivery_date IS NOT NULL) THEN 1 ELSE 0 END) AS n_excluded,
  COUNT(*) AS n_total
FROM orders;
