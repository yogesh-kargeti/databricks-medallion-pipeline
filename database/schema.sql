-- Reference DDL for the medallion pipeline tables.
-- The pipeline itself creates these tables implicitly via
-- DataFrame.write.saveAsTable() in the Bronze/Silver/Gold notebooks
-- (see src/bronze/, src/silver/, src/gold/). This file documents the
-- resulting schemas for reference and manual setup/inspection; it is
-- not executed by the pipeline itself.

-- ============================================================
-- BRONZE — raw ingest, source columns unchanged + lineage columns
-- ============================================================

CREATE TABLE IF NOT EXISTS bronze_customers (
    customer_id INT,
    customer_name STRING,
    email STRING,
    country STRING,
    signup_date DATE,
    customer_segment STRING,
    lifetime_value DECIMAL(12, 2),
    ingestion_timestamp TIMESTAMP,
    source_file STRING,
    batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS bronze_orders (
    order_id INT,
    customer_id INT,
    order_date DATE,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(12, 2),
    total_amount DECIMAL(12, 2),
    order_status STRING,
    payment_date DATE,
    ingestion_timestamp TIMESTAMP,
    source_file STRING,
    batch_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS bronze_products (
    product_id INT,
    product_name STRING,
    category STRING,
    price DECIMAL(12, 2),
    cost DECIMAL(12, 2),
    stock_quantity INT,
    reorder_level INT,
    ingestion_timestamp TIMESTAMP,
    source_file STRING,
    batch_id STRING
) USING DELTA;

-- ============================================================
-- SILVER — Bronze columns + per-check flags + quality_check_result
-- Every Bronze row is retained; failures are flagged, not deleted.
-- NULL on a flag means that check does not apply to this table.
-- ============================================================

CREATE TABLE IF NOT EXISTS silver_customers (
    customer_id INT,
    customer_name STRING,
    email STRING,
    country STRING,
    signup_date DATE,
    customer_segment STRING,
    lifetime_value DECIMAL(12, 2),
    ingestion_timestamp TIMESTAMP,
    source_file STRING,
    batch_id STRING,
    completeness_passed BOOLEAN,
    uniqueness_passed BOOLEAN,
    referential_integrity_passed BOOLEAN, -- N/A for customers (NULL)
    business_logic_passed BOOLEAN,
    quality_check_result STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS silver_orders (
    order_id INT,
    customer_id INT,
    order_date DATE,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(12, 2),
    total_amount DECIMAL(12, 2),
    order_status STRING,
    payment_date DATE,
    ingestion_timestamp TIMESTAMP,
    source_file STRING,
    batch_id STRING,
    completeness_passed BOOLEAN,
    uniqueness_passed BOOLEAN,
    referential_integrity_passed BOOLEAN,
    business_logic_passed BOOLEAN,
    quality_check_result STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS silver_products (
    product_id INT,
    product_name STRING,
    category STRING,
    price DECIMAL(12, 2),
    cost DECIMAL(12, 2),
    stock_quantity INT,
    reorder_level INT,
    ingestion_timestamp TIMESTAMP,
    source_file STRING,
    batch_id STRING,
    completeness_passed BOOLEAN, -- N/A for products (NULL)
    uniqueness_passed BOOLEAN,
    referential_integrity_passed BOOLEAN, -- N/A for products (NULL)
    business_logic_passed BOOLEAN,
    quality_check_result STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS silver_quality_metrics (
    batch_id STRING,
    table_name STRING,
    check_name STRING,
    check_target STRING,
    records_evaluated BIGINT,
    records_passed BIGINT,
    records_failed BIGINT,
    pass_percentage DOUBLE,
    threshold_pct DOUBLE,
    threshold_met BOOLEAN,
    metric_timestamp TIMESTAMP
) USING DELTA;

-- ============================================================
-- GOLD — business-ready aggregations, PASS + Completed rows only
-- ============================================================

CREATE TABLE IF NOT EXISTS gold_sales_by_product (
    batch_id STRING,
    product_id INT,
    product_name STRING,
    category STRING,
    total_orders BIGINT,
    total_revenue DECIMAL(18, 2),
    avg_order_value DECIMAL(18, 2)
) USING DELTA;

CREATE TABLE IF NOT EXISTS gold_revenue_by_customer (
    batch_id STRING,
    customer_id INT,
    customer_name STRING,
    customer_segment STRING,
    total_orders BIGINT,
    total_revenue DECIMAL(18, 2),
    avg_order_value DECIMAL(18, 2),
    lifetime_value_actual DECIMAL(18, 2)
) USING DELTA;

CREATE TABLE IF NOT EXISTS gold_customer_segmentation (
    batch_id STRING,
    segment_type STRING, -- High-Value / Repeat / One-Time / Inactive
    customer_count BIGINT,
    avg_revenue DECIMAL(18, 2),
    total_revenue DECIMAL(18, 2)
) USING DELTA;
