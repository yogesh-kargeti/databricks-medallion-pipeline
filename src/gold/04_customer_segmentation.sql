-- Gold customer segments from gold_revenue_by_customer (one segment per customer).
-- Precedence: High-Value, then Repeat, then One-Time, then Inactive.
-- {batch_id} and {high_value_threshold} are filled by create_gold_tables.py.

SELECT
    '{batch_id}' AS batch_id,
    segmented.segment_type,
    COUNT(*) AS customer_count,
    AVG(segmented.total_revenue) AS avg_revenue,
    SUM(segmented.total_revenue) AS total_revenue
FROM (
    SELECT
        CASE
            WHEN r.total_revenue >= {high_value_threshold}
                THEN 'High-Value'
            WHEN r.total_orders >= 2
                THEN 'Repeat'
            WHEN r.total_orders = 1
                THEN 'One-Time'
            ELSE 'Inactive'
        END AS segment_type,
        r.total_revenue
    FROM gold_revenue_by_customer AS r
    WHERE r.batch_id = '{batch_id}'
) AS segmented
GROUP BY
    segmented.segment_type
;
