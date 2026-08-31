# Databricks notebook source
"""Build Silver tables from Bronze by applying all quality flags, then write once.

Check notebooks only add columns. This notebook is the only Silver writer.
"""

# COMMAND ----------

if "BATCH_ID" not in globals():
    BATCH_ID = "20260831"

BRONZE_CUSTOMERS = "bronze_customers"
BRONZE_ORDERS = "bronze_orders"
BRONZE_PRODUCTS = "bronze_products"
SILVER_CUSTOMERS = "silver_customers"
SILVER_ORDERS = "silver_orders"
SILVER_PRODUCTS = "silver_products"

# COMMAND ----------

# MAGIC %run ./01_quality_completeness

# COMMAND ----------

# MAGIC %run ./02_quality_uniqueness

# COMMAND ----------

# MAGIC %run ./04_quality_referential_integrity

# COMMAND ----------

# MAGIC %run ./05_quality_business_logic

# COMMAND ----------

import logging

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, concat_ws, lit, when

LOGGER = logging.getLogger(__name__)


def get_spark() -> SparkSession:
    """Reuse the Databricks session for the Silver write."""
    spark = SparkSession.builder.appName("create_silver_tables").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    return spark


def add_quality_check_result(dataframe: DataFrame, check_columns: tuple[str, ...]) -> DataFrame:
    """Set PASS, or a comma-separated list of failed checks in fixed order.

    NULL flags mean the check is not applicable and are omitted from the list.
    Only an explicit false is a failure (~NULL must not count as failed).
    """
    name_by_flag = {
        "completeness_passed": "completeness",
        "uniqueness_passed": "uniqueness",
        "referential_integrity_passed": "referential_integrity",
        "business_logic_passed": "business_logic",
    }
    failed_parts = [
        when(col(flag).eqNullSafe(lit(False)), lit(name_by_flag[flag]))
        for flag in check_columns
    ]
    failed = concat_ws(",", *failed_parts)
    return dataframe.withColumn(
        "quality_check_result",
        when(failed == "", lit("PASS")).otherwise(failed),
    )


def write_silver_idempotent(
    dataframe: DataFrame,
    table_name: str,
    batch_id: str,
) -> int:
    """Replace this batch_id in Silver and keep every input row."""
    spark = dataframe.sparkSession
    if spark.catalog.tableExists(table_name):
        spark.sql(f"DELETE FROM {table_name} WHERE batch_id = '{batch_id}'")
        dataframe.write.format("delta").mode("append").saveAsTable(table_name)
    else:
        dataframe.write.format("delta").mode("overwrite").saveAsTable(table_name)
    return spark.table(table_name).where(col("batch_id") == batch_id).count()


def create_silver_tables(spark: SparkSession) -> None:
    """Flag all Bronze rows for one batch_id and write each Silver table once."""
    batch_id = globals().get("BATCH_ID", "20260831")

    customers = spark.table(BRONZE_CUSTOMERS).where(col("batch_id") == batch_id)
    orders = spark.table(BRONZE_ORDERS).where(col("batch_id") == batch_id)
    products = spark.table(BRONZE_PRODUCTS).where(col("batch_id") == batch_id)

    customer_source = customers.count()
    order_source = orders.count()
    product_source = products.count()

    customers = flag_customer_completeness(customers)
    customers = flag_customer_uniqueness(customers)
    customers = flag_customer_business_logic(customers)
    customers = customers.withColumn(
        "referential_integrity_passed",
        lit(None).cast("boolean"),
    )
    customers = add_quality_check_result(
        customers,
        (
            "completeness_passed",
            "uniqueness_passed",
            "referential_integrity_passed",
            "business_logic_passed",
        ),
    )

    products = flag_product_uniqueness(products)
    products = flag_product_business_logic(products)
    products = products.withColumn(
        "completeness_passed",
        lit(None).cast("boolean"),
    ).withColumn(
        "referential_integrity_passed",
        lit(None).cast("boolean"),
    )
    products = add_quality_check_result(
        products,
        (
            "completeness_passed",
            "uniqueness_passed",
            "referential_integrity_passed",
            "business_logic_passed",
        ),
    )

    orders = flag_order_completeness(orders)
    orders = flag_order_uniqueness(orders)
    orders = flag_order_referential_integrity(orders, customers, products)
    orders = flag_order_business_logic(orders)
    orders = add_quality_check_result(
        orders,
        (
            "completeness_passed",
            "uniqueness_passed",
            "referential_integrity_passed",
            "business_logic_passed",
        ),
    )

    customer_written = write_silver_idempotent(customers, SILVER_CUSTOMERS, batch_id)
    order_written = write_silver_idempotent(orders, SILVER_ORDERS, batch_id)
    product_written = write_silver_idempotent(products, SILVER_PRODUCTS, batch_id)

    LOGGER.info(
        "silver write complete | batch_id=%s | customers %s -> %s | "
        "orders %s -> %s | products %s -> %s",
        batch_id,
        customer_source,
        customer_written,
        order_source,
        order_written,
        product_source,
        product_written,
    )
    if (
        customer_written != customer_source
        or order_written != order_source
        or product_written != product_source
    ):
        raise RuntimeError(
            "Silver write dropped or duplicated rows: "
            f"customers {customer_source}->{customer_written}, "
            f"orders {order_source}->{order_written}, "
            f"products {product_source}->{product_written}"
        )


def main() -> None:
    """Entry point for the Databricks Silver notebook."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    create_silver_tables(get_spark())


# COMMAND ----------

main()
