"""Integration assertions for seeded Silver quality-metric counts.

Run this test in Databricks after ``create_silver_tables.py`` so an active
Spark session and the ``silver_quality_metrics`` table are available.
"""

from __future__ import annotations

import os


BATCH_ID = os.getenv("SILVER_TEST_BATCH_ID", "20260831")
METRICS_TABLE = os.getenv("SILVER_METRICS_TABLE", "silver_quality_metrics")

# (table_name, check_name, check_target): expected records_failed
EXPECTED_FAILURES = {
    # Exercise-required customer issues.
    ("customers", "completeness", "email"): 50,
    ("customers", "uniqueness", "customer_id"): 10,
    # Supplemental customer issues (logical Check 4).
    ("customers", "business_logic", "email"): 40,
    ("customers", "business_logic", "signup_date"): 20,
    ("customers", "business_logic", "customer_segment"): 20,
    # Exercise-required order issues.
    ("orders", "completeness", "customer_id"): 100,
    ("orders", "completeness", "product_id"): 200,
    ("orders", "uniqueness", "order_id"): 20,
    ("orders", "referential_integrity", "orders.customer_id"): 50,
    ("orders", "referential_integrity", "orders.product_id"): 30,
    # Supplemental order issues (logical Check 4).
    ("orders", "business_logic", "quantity"): 50,
    ("orders", "business_logic", "unit_price"): 40,
    ("orders", "business_logic", "total_amount"): 40,
    ("orders", "business_logic", "order_status"): 10,
    # Product uniqueness is a defensive metric; no duplicates are seeded.
    ("products", "uniqueness", "product_id"): 0,
    # Supplemental product issues (logical Check 4).
    ("products", "business_logic", "price"): 10,
    ("products", "business_logic", "cost"): 10,
    # Distinct rows must not be confused with failed-check occurrences.
    ("customers", "distinct_bad_rows", "quality_check_result"): 140,
    ("orders", "distinct_bad_rows", "quality_check_result"): 540,
    ("products", "distinct_bad_rows", "quality_check_result"): 20,
    ("_all", "distinct_bad_rows", "quality_check_result"): 700,
}


def _active_spark():
    """Return the Databricks Spark session and fail clearly outside Spark."""
    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise AssertionError(
            "PySpark is unavailable; run this integration test in Databricks."
        ) from exc

    spark = SparkSession.getActiveSession()
    assert spark is not None, "No active Spark session; run this test in Databricks."
    return spark


def test_seeded_quality_metric_counts() -> None:
    """Require every field-level seeded count and the 700-row total."""
    spark = _active_spark()
    from pyspark.sql.functions import col

    assert spark.catalog.tableExists(
        METRICS_TABLE
    ), f"{METRICS_TABLE} does not exist; run create_silver_tables.py first."

    metric_rows = (
        spark.table(METRICS_TABLE)
        .where(col("batch_id") == BATCH_ID)
        .select(
            "table_name",
            "check_name",
            "check_target",
            "records_evaluated",
            "records_passed",
            "records_failed",
            "pass_percentage",
        )
        .collect()
    )
    assert metric_rows, f"No quality metrics found for batch_id={BATCH_ID}."

    actual_failures = {
        (row.table_name, row.check_name, row.check_target): row.records_failed
        for row in metric_rows
    }
    assert len(actual_failures) == len(
        metric_rows
    ), "Duplicate batch/table/check/target rows found in the metrics report."
    assert actual_failures == EXPECTED_FAILURES

    for row in metric_rows:
        assert row.records_passed + row.records_failed == row.records_evaluated
        if row.records_evaluated:
            expected_percentage = round(
                100.0 * row.records_passed / row.records_evaluated,
                4,
            )
            assert row.pass_percentage == expected_percentage
