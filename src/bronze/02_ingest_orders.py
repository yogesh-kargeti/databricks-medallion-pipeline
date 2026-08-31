# Databricks notebook source
"""Ingest orders.csv into bronze_orders with no source transformations.

Bronze applies the data-model schema and ingestion metadata only. Rows are
not filtered, cleaned, or renamed. A rerun of the same batch_id replaces that
batch instead of appending a second copy.
"""

from __future__ import annotations

import logging
import re

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp, lit
from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)
from pyspark.sql.utils import AnalysisException

LOGGER = logging.getLogger(__name__)

CSV_PATH = "/Volumes/workspace/default/databricks_assess/orders.csv"
BRONZE_TABLE = "bronze_orders"
BATCH_ID = "20260831"

ORDER_SCHEMA = StructType(
    [
        StructField("order_id", IntegerType(), True),
        StructField("customer_id", IntegerType(), True),
        StructField("order_date", DateType(), True),
        StructField("product_id", IntegerType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("unit_price", DecimalType(12, 2), True),
        StructField("total_amount", DecimalType(12, 2), True),
        StructField("order_status", StringType(), True),
        StructField("payment_date", DateType(), True),
    ]
)
SOURCE_COLUMNS = [field.name for field in ORDER_SCHEMA]
BATCH_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def get_spark() -> SparkSession:
    """Reuse the Databricks session, or build a local Spark session with Delta."""
    builder = SparkSession.builder.appName("bronze_ingest_orders")
    spark = builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    return spark


def resolve_config(spark: SparkSession) -> tuple[str, str, str]:
    """Read path, table, and batch_id from Spark conf when set, else module defaults."""
    csv_path = spark.conf.get("pipeline.csv.orders", CSV_PATH)
    bronze_table = spark.conf.get("pipeline.bronze.orders", BRONZE_TABLE)
    batch_id = spark.conf.get("pipeline.batch_id", BATCH_ID)
    if not BATCH_ID_PATTERN.fullmatch(batch_id):
        raise ValueError(
            f"batch_id {batch_id!r} must match {BATCH_ID_PATTERN.pattern}"
        )
    return csv_path, bronze_table, batch_id


def assert_source_readable(spark: SparkSession, csv_path: str) -> None:
    """Fail before table writes if the CSV path cannot be read."""
    try:
        spark.read.format("text").option("header", "false").load(csv_path).take(1)
    except AnalysisException as exc:
        raise FileNotFoundError(
            f"orders source is missing or unreadable: {csv_path}"
        ) from exc


def assert_headers_match(spark: SparkSession, csv_path: str) -> None:
    """Require the CSV header row to contain every contract column name."""
    first_row = spark.read.format("text").load(csv_path).first()
    if first_row is None:
        raise ValueError(f"orders.csv is empty: {csv_path}")
    actual = [name.strip() for name in first_row[0].split(",")]
    missing = [name for name in SOURCE_COLUMNS if name not in actual]
    if missing:
        raise ValueError(
            f"orders.csv is missing required headers {missing}; found {actual}"
        )


def read_orders(spark: SparkSession, csv_path: str) -> DataFrame:
    """Load the CSV with an explicit schema so types do not depend on inference."""
    assert_source_readable(spark, csv_path)
    assert_headers_match(spark, csv_path)
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("mode", "FAILFAST")
        .option("dateFormat", "yyyy-MM-dd")
        .schema(ORDER_SCHEMA)
        .load(csv_path)
        .select(*SOURCE_COLUMNS)
    )


def add_ingestion_metadata(
    dataframe: DataFrame,
    csv_path: str,
    batch_id: str,
) -> DataFrame:
    """Attach lineage columns without changing source field names or values."""
    return (
        dataframe.withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source_file", lit(csv_path))
        .withColumn("batch_id", lit(batch_id))
    )


def write_bronze_idempotent(
    dataframe: DataFrame,
    bronze_table: str,
    batch_id: str,
) -> int:
    """Replace any existing rows for this batch_id, then append the new batch."""
    spark = dataframe.sparkSession
    if spark.catalog.tableExists(bronze_table):
        spark.sql(
            f"DELETE FROM {bronze_table} WHERE batch_id = '{batch_id}'"
        )
        (
            dataframe.write.format("delta")
            .mode("append")
            .saveAsTable(bronze_table)
        )
    else:
        (
            dataframe.write.format("delta")
            .mode("overwrite")
            .saveAsTable(bronze_table)
        )

    written_count = (
        spark.table(bronze_table)
        .where(col("batch_id") == batch_id)
        .count()
    )
    return written_count


def ingest_orders(spark: SparkSession) -> None:
    """Run one orders Bronze load and require source count to equal written count."""
    csv_path, bronze_table, batch_id = resolve_config(spark)
    source_df = read_orders(spark, csv_path)
    source_count = source_df.count()
    bronze_df = add_ingestion_metadata(source_df, csv_path, batch_id)
    written_count = write_bronze_idempotent(
        dataframe=bronze_df,
        bronze_table=bronze_table,
        batch_id=batch_id,
    )

    LOGGER.info(
        "bronze orders ingest complete | source=orders | batch_id=%s | "
        "source_rows=%s | written_rows=%s | table=%s | path=%s",
        batch_id,
        source_count,
        written_count,
        bronze_table,
        csv_path,
    )
    if written_count != source_count:
        raise RuntimeError(
            f"bronze_orders row count mismatch for batch_id={batch_id}: "
            f"source={source_count}, written={written_count}"
        )


def main() -> None:
    """Entry point for Databricks jobs and local Spark sessions."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    spark = get_spark()
    ingest_orders(spark)


if __name__ == "__main__":
    main()
