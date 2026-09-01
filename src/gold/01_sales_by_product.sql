-- Gold sales by product from passing Silver orders and products only.
-- Pending/Cancelled are excluded because they are not settled revenue.
-- total_orders is distinct completed order_id; avg_order_value is revenue / that count.
-- {batch_id} is filled by create_gold_tables.py.

SELECT
    '{batch_id}' AS batch_id,
    p.product_id,
    p.product_name,
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_revenue,
    SUM(o.total_amount) / COUNT(DISTINCT o.order_id) AS avg_order_value
FROM silver_orders AS o
INNER JOIN silver_products AS p
    ON o.product_id = p.product_id
WHERE o.quality_check_result = 'PASS'
    AND p.quality_check_result = 'PASS'
    AND o.order_status = 'Completed'
    AND o.batch_id = '{batch_id}'
    AND p.batch_id = '{batch_id}'
GROUP BY
    p.product_id,
    p.product_name,
    p.category
;
