-- Gold customer segments from gold_revenue_by_customer (one segment per customer).
-- Precedence: High-Value, then Repeat, then One-Time, then Inactive.
-- High-Value uses the configured revenue percentile within the current batch.
-- {batch_id} and {high_value_percentile} are filled by create_gold_tables.py.

WITH revenue_distribution AS (
    SELECT
        PERCENTILE_APPROX(
            total_revenue,
            {high_value_percentile},
            10000
        ) AS high_value_cutoff
    FROM gold_revenue_by_customer
    WHERE batch_id = '{batch_id}'
),
segmented AS (
    SELECT
        CASE
            WHEN r.total_revenue >= d.high_value_cutoff
                THEN 'High-Value'
            WHEN r.total_orders >= 2
                THEN 'Repeat'
            WHEN r.total_orders = 1
                THEN 'One-Time'
            ELSE 'Inactive'
        END AS segment_type,
        r.total_revenue
    FROM gold_revenue_by_customer AS r
    CROSS JOIN revenue_distribution AS d
    WHERE r.batch_id = '{batch_id}'
)
SELECT
    '{batch_id}' AS batch_id,
    segmented.segment_type,
    COUNT(*) AS customer_count,
    AVG(segmented.total_revenue) AS avg_revenue,
    SUM(segmented.total_revenue) AS total_revenue
FROM segmented
GROUP BY
    segmented.segment_type
;
