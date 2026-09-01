# Databricks notebook source
"""Build Gold tables from the three Gold SQL files. Writes each table once.

Check SQL stays in 01/02/04. This notebook substitutes batch_id (and the
High-Value threshold) and is the only Gold writer. 03_daily_weekly_trends is
out of Core scope.
"""

# COMMAND ----------

from pathlib import Path

if "BATCH_ID" not in globals():
    BATCH_ID = "20260831"
if "HIGH_VALUE_THRESHOLD" not in globals():
    HIGH_VALUE_THRESHOLD = 1000

GOLD_SALES_BY_PRODUCT = "gold_sales_by_product"
GOLD_REVENUE_BY_CUSTOMER = "gold_revenue_by_customer"
GOLD_CUSTOMER_SEGMENTATION = "gold_customer_segmentation"

GOLD_STEPS = (
    ("01_sales_by_product.sql", GOLD_SALES_BY_PRODUCT),
    ("02_revenue_by_customer.sql", GOLD_REVENUE_BY_CUSTOMER),
    ("04_customer_segmentation.sql", GOLD_CUSTOMER_SEGMENTATION),
)

# COMMAND ----------

import logging

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col

LOGGER = logging.getLogger(__name__)


def get_spark() -> SparkSession:
    """Reuse the Databricks session for the Gold write."""
    spark = SparkSession.builder.appName("create_gold_tables").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    return spark


def gold_sql_dir() -> Path:
    """Resolve the folder that holds the Gold SQL files."""
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path(".")


def load_gold_sql(filename: str, batch_id: str, high_value_threshold: int) -> str:
    """Read a Gold SELECT and fill batch_id plus the High-Value threshold."""
    sql_text = (gold_sql_dir() / filename).read_text(encoding="utf-8")
    return (
        sql_text.format(
            batch_id=batch_id,
            high_value_threshold=high_value_threshold,
        )
        .strip()
        .rstrip(";")
    )


def write_gold_idempotent(
    dataframe: DataFrame,
    table_name: str,
    batch_id: str,
) -> int:
    """Replace this batch_id in a Gold table."""
    spark = dataframe.sparkSession
    if spark.catalog.tableExists(table_name):
        spark.sql(f"DELETE FROM {table_name} WHERE batch_id = '{batch_id}'")
        dataframe.write.format("delta").mode("append").saveAsTable(table_name)
    else:
        dataframe.write.format("delta").mode("overwrite").saveAsTable(table_name)
    return spark.table(table_name).where(col("batch_id") == batch_id).count()


def create_gold_tables(spark: SparkSession) -> None:
    """Run sales-by-product, revenue-by-customer, then segmentation for one batch."""
    batch_id = globals().get("BATCH_ID", "20260831")
    high_value_threshold = int(globals().get("HIGH_VALUE_THRESHOLD", 1000))

    for filename, table_name in GOLD_STEPS:
        query = load_gold_sql(filename, batch_id, high_value_threshold)
        result = spark.sql(query)
        written = write_gold_idempotent(result, table_name, batch_id)
        LOGGER.info(
            "gold write complete | table=%s | batch_id=%s | rows=%s",
            table_name,
            batch_id,
            written,
        )


def main() -> None:
    """Entry point for the Databricks Gold notebook."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    create_gold_tables(get_spark())


# COMMAND ----------

main()
