# Databricks notebook source
"""Publish Silver quality metrics. Does not rewrite entity Silver tables.

One row per batch_id, table, check, and field/relationship. N/A checks are
omitted (NULL flags), not reported as 100% passed. Distinct bad-row counts
are extra rows so failed-check occurrences stay separate from bad-row totals.
"""

from __future__ import annotations

import logging
from datetime import date

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp, lit
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

LOGGER = logging.getLogger(__name__)

if "BATCH_ID" not in globals():
    BATCH_ID = "20260831"
if "AS_OF_DATE" not in globals():
    AS_OF_DATE = date(2026, 8, 31)

SILVER_CUSTOMERS = "silver_customers"
SILVER_ORDERS = "silver_orders"
SILVER_PRODUCTS = "silver_products"
METRICS_TABLE = "silver_quality_metrics"

THRESHOLDS = {
    "completeness": 99.0,
    "uniqueness": 100.0,
    "referential_integrity": 99.9,
    "business_logic": 99.0,
}
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")

METRICS_SCHEMA = StructType(
    [
        StructField("batch_id", StringType(), False),
        StructField("table_name", StringType(), False),
        StructField("check_name", StringType(), False),
        StructField("check_target", StringType(), False),
        StructField("records_evaluated", LongType(), False),
        StructField("records_passed", LongType(), False),
        StructField("records_failed", LongType(), False),
        StructField("pass_percentage", DoubleType(), True),
        StructField("threshold_pct", DoubleType(), True),
        StructField("threshold_met", BooleanType(), True),
        StructField("metric_timestamp", TimestampType(), True),
    ]
)


def get_spark() -> SparkSession:
    """Reuse the Databricks session for the metrics write."""
    spark = SparkSession.builder.appName("silver_quality_metrics").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    return spark


def _metric_row(
    batch_id: str,
    table_name: str,
    check_name: str,
    check_target: str,
    evaluated: int,
    failed: int,
) -> dict:
    """Build one report row, leaving percentage null when nothing was evaluated."""
    passed = evaluated - failed
    threshold = THRESHOLDS.get(check_name)
    if evaluated == 0 or threshold is None:
        pass_pct = None if evaluated == 0 else round(100.0 * passed / evaluated, 4)
        threshold_met = None
    else:
        pass_pct = round(100.0 * passed / evaluated, 4)
        if check_name == "uniqueness":
            threshold_met = pass_pct >= threshold
        else:
            threshold_met = pass_pct > threshold
    return {
        "batch_id": batch_id,
        "table_name": table_name,
        "check_name": check_name,
        "check_target": check_target,
        "records_evaluated": int(evaluated),
        "records_passed": int(passed),
        "records_failed": int(failed),
        "pass_percentage": pass_pct,
        "threshold_pct": threshold,
        "threshold_met": threshold_met,
        "metric_timestamp": None,
    }


def _count(dataframe: DataFrame, condition=None) -> int:
    """Count rows, optionally restricted to a boolean condition."""
    if condition is None:
        return dataframe.count()
    return dataframe.where(condition).count()


def _check_metrics(
    dataframe: DataFrame,
    batch_id: str,
    table_name: str,
    check_name: str,
    check_target: str,
    failed_when,
    evaluated_when=None,
) -> dict:
    """Evaluate one field-level check, excluding N/A rows from the denominator."""
    scoped = dataframe if evaluated_when is None else dataframe.where(evaluated_when)
    evaluated = scoped.count()
    failed = _count(scoped, failed_when)
    return _metric_row(
        batch_id, table_name, check_name, check_target, evaluated, failed
    )


def _distinct_bad_row(
    dataframe: DataFrame,
    batch_id: str,
    table_name: str,
) -> dict:
    """Count rows with any applicable failure, not failed-check occurrences."""
    evaluated = dataframe.count()
    failed = _count(dataframe, col("quality_check_result") != "PASS")
    row = _metric_row(
        batch_id, table_name, "distinct_bad_rows", "quality_check_result", evaluated, failed
    )
    row["threshold_pct"] = None
    row["threshold_met"] = None
    return row


def collect_quality_metrics(
    spark: SparkSession,
    batch_id: str,
) -> list[dict]:
    """Compute field-level and distinct-bad-row metrics from Silver tables."""
    customers = spark.table(SILVER_CUSTOMERS).where(col("batch_id") == batch_id)
    orders = spark.table(SILVER_ORDERS).where(col("batch_id") == batch_id)
    products = spark.table(SILVER_PRODUCTS).where(col("batch_id") == batch_id)
    as_of = globals().get("AS_OF_DATE", AS_OF_DATE)

    email_missing = col("email").isNull() | (col("email") == "")
    email_present = ~email_missing
    unique_customer_ids = (
        customers.where(col("uniqueness_passed").eqNullSafe(lit(True)))
        .select(col("customer_id").alias("_id"))
        .distinct()
    )
    unique_product_ids = (
        products.where(col("uniqueness_passed").eqNullSafe(lit(True)))
        .select(col("product_id").alias("_id"))
        .distinct()
    )
    orders_with_parents = orders.join(
        unique_customer_ids.withColumnRenamed("_id", "_valid_customer_id"),
        orders["customer_id"] == col("_valid_customer_id"),
        "left",
    ).join(
        unique_product_ids.withColumnRenamed("_id", "_valid_product_id"),
        orders["product_id"] == col("_valid_product_id"),
        "left",
    )

    rows = [
        _check_metrics(
            customers, batch_id, "customers", "completeness", "email", email_missing
        ),
        _check_metrics(
            customers,
            batch_id,
            "customers",
            "uniqueness",
            "customer_id",
            col("uniqueness_passed").eqNullSafe(lit(False)),
        ),
        _check_metrics(
            customers,
            batch_id,
            "customers",
            "business_logic",
            "email",
            email_present & (~col("email").rlike(EMAIL_PATTERN)),
            email_present,
        ),
        _check_metrics(
            customers,
            batch_id,
            "customers",
            "business_logic",
            "signup_date",
            col("signup_date") > lit(as_of),
        ),
        _check_metrics(
            customers,
            batch_id,
            "customers",
            "business_logic",
            "customer_segment",
            ~col("customer_segment").isin(*CUSTOMER_SEGMENTS),
        ),
        _check_metrics(
            orders,
            batch_id,
            "orders",
            "completeness",
            "customer_id",
            col("customer_id").isNull(),
        ),
        _check_metrics(
            orders,
            batch_id,
            "orders",
            "completeness",
            "product_id",
            col("product_id").isNull(),
        ),
        _check_metrics(
            orders,
            batch_id,
            "orders",
            "uniqueness",
            "order_id",
            col("uniqueness_passed").eqNullSafe(lit(False)),
        ),
        _check_metrics(
            orders_with_parents,
            batch_id,
            "orders",
            "referential_integrity",
            "orders.customer_id",
            col("_valid_customer_id").isNull(),
            col("customer_id").isNotNull(),
        ),
        _check_metrics(
            orders_with_parents,
            batch_id,
            "orders",
            "referential_integrity",
            "orders.product_id",
            col("_valid_product_id").isNull(),
            col("product_id").isNotNull(),
        ),
        _check_metrics(
            orders,
            batch_id,
            "orders",
            "business_logic",
            "quantity",
            col("quantity") <= 0,
        ),
        _check_metrics(
            orders,
            batch_id,
            "orders",
            "business_logic",
            "unit_price",
            col("unit_price") <= 0,
        ),
        _check_metrics(
            orders,
            batch_id,
            "orders",
            "business_logic",
            "total_amount",
            col("total_amount") != (col("unit_price") * col("quantity")),
        ),
        _check_metrics(
            orders,
            batch_id,
            "orders",
            "business_logic",
            "order_status",
            ~col("order_status").isin(*ORDER_STATUSES),
        ),
        _check_metrics(
            products,
            batch_id,
            "products",
            "uniqueness",
            "product_id",
            col("uniqueness_passed").eqNullSafe(lit(False)),
        ),
        _check_metrics(
            products,
            batch_id,
            "products",
            "business_logic",
            "price",
            col("price") <= 0,
        ),
        _check_metrics(
            products,
            batch_id,
            "products",
            "business_logic",
            "cost",
            col("cost") > col("price"),
        ),
        _distinct_bad_row(customers, batch_id, "customers"),
        _distinct_bad_row(orders, batch_id, "orders"),
        _distinct_bad_row(products, batch_id, "products"),
    ]

    distinct_total = (
        rows[-3]["records_failed"]
        + rows[-2]["records_failed"]
        + rows[-1]["records_failed"]
    )
    evaluated_total = (
        rows[-3]["records_evaluated"]
        + rows[-2]["records_evaluated"]
        + rows[-1]["records_evaluated"]
    )
    batch_row = _metric_row(
        batch_id,
        "_all",
        "distinct_bad_rows",
        "quality_check_result",
        evaluated_total,
        distinct_total,
    )
    batch_row["threshold_pct"] = None
    batch_row["threshold_met"] = None
    rows.append(batch_row)
    return rows


def write_quality_metrics_report(spark: SparkSession) -> DataFrame:
    """Replace this batch_id in silver_quality_metrics and return the new rows."""
    batch_id = globals().get("BATCH_ID", "20260831")
    rows = collect_quality_metrics(spark, batch_id)
    report = spark.createDataFrame(rows, schema=METRICS_SCHEMA).withColumn(
        "metric_timestamp",
        current_timestamp(),
    )

    if spark.catalog.tableExists(METRICS_TABLE):
        spark.sql(f"DELETE FROM {METRICS_TABLE} WHERE batch_id = '{batch_id}'")
        report.write.format("delta").mode("append").saveAsTable(METRICS_TABLE)
    else:
        report.write.format("delta").mode("overwrite").saveAsTable(METRICS_TABLE)

    distinct_total = next(
        row["records_failed"]
        for row in rows
        if row["table_name"] == "_all" and row["check_name"] == "distinct_bad_rows"
    )
    LOGGER.info(
        "quality metrics written | table=%s | batch_id=%s | metric_rows=%s | "
        "distinct_bad_rows=%s",
        METRICS_TABLE,
        batch_id,
        len(rows),
        distinct_total,
    )
    return spark.table(METRICS_TABLE).where(col("batch_id") == batch_id)


def main() -> None:
    """Entry point for the Databricks metrics notebook."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    write_quality_metrics_report(get_spark())


# COMMAND ----------

main()
