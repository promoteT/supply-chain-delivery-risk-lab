-- seller_diagnostics.sql : seller-level delay concentration (Pareto inputs).
-- Unit of analysis: seller via order_items; outcome: parent order lateness.
-- Small-sample sellers flagged via n_eligible (interpret with care).

-- 1. Seller late-rate table (eligible delivered orders only)
SELECT i.seller_id,
  COUNT(DISTINCT o.order_id) AS n_eligible_orders,
  SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS n_late_orders,
  ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END)
    / COUNT(DISTINCT o.order_id), 2) AS late_rate_pct
FROM orders o JOIN order_items i ON o.order_id = i.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
GROUP BY i.seller_id
ORDER BY n_late_orders DESC;

-- 2. Pareto: cumulative share of late orders by seller (rank largest contributors first)
SELECT seller_id, n_late_orders,
  SUM(n_late_orders) OVER (ORDER BY n_late_orders DESC) AS cum_late,
  ROUND(100.0 * SUM(n_late_orders) OVER (ORDER BY n_late_orders DESC)
    / SUM(n_late_orders) OVER (), 2) AS cum_late_pct
FROM (
  SELECT i.seller_id AS seller_id,
    SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS n_late_orders
  FROM orders o JOIN order_items i ON o.order_id = i.order_id
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
  GROUP BY i.seller_id
) ORDER BY n_late_orders DESC;

-- 3. Seller region performance
SELECT s.seller_state AS region, COUNT(DISTINCT o.order_id) AS n_orders,
  ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END)
    / COUNT(DISTINCT o.order_id), 2) AS late_rate_pct
FROM orders o JOIN order_items i ON o.order_id = i.order_id
JOIN sellers s ON i.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL AND o.order_estimated_delivery_date IS NOT NULL
GROUP BY s.seller_state ORDER BY late_rate_pct DESC;
