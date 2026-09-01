-- Gold revenue by customer: every passing Silver customer, including zeros.
-- lifetime_value_actual is summed valid completed-order revenue, not source lifetime_value.
-- avg_order_value is 0 when the customer has no valid completed orders.
-- {batch_id} is filled by create_gold_tables.py.

SELECT
    '{batch_id}' AS batch_id,
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), CAST(0 AS DECIMAL(12, 2))) AS total_revenue,
    CASE
        WHEN COUNT(DISTINCT o.order_id) = 0
            THEN CAST(0 AS DECIMAL(12, 2))
        ELSE SUM(o.total_amount) / COUNT(DISTINCT o.order_id)
    END AS avg_order_value,
    COALESCE(SUM(o.total_amount), CAST(0 AS DECIMAL(12, 2))) AS lifetime_value_actual
FROM silver_customers AS c
LEFT JOIN silver_orders AS o
    ON c.customer_id = o.customer_id
    AND o.quality_check_result = 'PASS'
    AND o.order_status = 'Completed'
    AND o.batch_id = '{batch_id}'
WHERE c.quality_check_result = 'PASS'
    AND c.batch_id = '{batch_id}'
GROUP BY
    c.customer_id,
    c.customer_name,
    c.customer_segment
;
