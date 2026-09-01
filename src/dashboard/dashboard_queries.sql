-- Databricks SQL queries for the Core dashboard (Gold tables only).
-- Batch is fixed to the demo run 20260831. No dashboard parameters.

-- ---------------------------------------------------------------------------
-- Tile 1: Top 10 products by revenue (bar chart)
-- X: product_name  Y: total_revenue
-- ---------------------------------------------------------------------------
SELECT
    product_name,
    category,
    total_revenue,
    total_orders,
    avg_order_value
FROM gold_sales_by_product
WHERE batch_id = '20260831'
ORDER BY
    total_revenue DESC
LIMIT 10
;

-- ---------------------------------------------------------------------------
-- Tile 2: Customer revenue distribution (histogram)
-- One row per customer, including total_revenue = 0 so Inactive stays visible.
-- Plot: histogram of total_revenue (count of customers).
-- ---------------------------------------------------------------------------
SELECT
    customer_id,
    customer_name,
    customer_segment,
    total_orders,
    total_revenue
FROM gold_revenue_by_customer
WHERE batch_id = '20260831'
;

-- ---------------------------------------------------------------------------
-- Tile 2b: Pre-binned counts if the warehouse has no histogram viz
-- Zero-revenue customers are the first bucket. Use as a bar chart.
-- ---------------------------------------------------------------------------
SELECT
    CASE
        WHEN total_revenue = 0
            THEN '0'
        WHEN total_revenue < 5000
            THEN '0–5k'
        WHEN total_revenue < 10000
            THEN '5k–10k'
        WHEN total_revenue < 15000
            THEN '10k–15k'
        WHEN total_revenue < 20000
            THEN '15k–20k'
        ELSE '20k+'
    END AS revenue_bucket,
    COUNT(*) AS customer_count
FROM gold_revenue_by_customer
WHERE batch_id = '20260831'
GROUP BY
    CASE
        WHEN total_revenue = 0
            THEN '0'
        WHEN total_revenue < 5000
            THEN '0–5k'
        WHEN total_revenue < 10000
            THEN '5k–10k'
        WHEN total_revenue < 15000
            THEN '10k–15k'
        WHEN total_revenue < 20000
            THEN '15k–20k'
        ELSE '20k+'
    END
ORDER BY
    MIN(total_revenue)
;

-- ---------------------------------------------------------------------------
-- Tile 3: Customer segmentation (pie)
-- Slice: segment_type  Size: customer_count
-- ---------------------------------------------------------------------------
SELECT
    segment_type,
    customer_count,
    avg_revenue,
    total_revenue
FROM gold_customer_segmentation
WHERE batch_id = '20260831'
;
