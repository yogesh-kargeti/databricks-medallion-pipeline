# Databricks notebook source
"""Flag order referential integrity. Does not write Silver tables.

A non-NULL FK passes only when it exists on a unique parent key. NULL FKs
are completeness failures, so RI is treated as not applicable (passed).
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col


def flag_order_referential_integrity(
    orders: DataFrame,
    customers: DataFrame,
    products: DataFrame,
) -> DataFrame:
    """Require non-NULL order FKs to match a uniqueness-passing parent row."""
    valid_customers = (
        customers.where(col("uniqueness_passed"))
        .select(col("customer_id").alias("_valid_customer_id"))
        .distinct()
    )
    valid_products = (
        products.where(col("uniqueness_passed"))
        .select(col("product_id").alias("_valid_product_id"))
        .distinct()
    )

    flagged = (
        orders.join(
            valid_customers,
            orders["customer_id"] == col("_valid_customer_id"),
            "left",
        )
        .join(
            valid_products,
            orders["product_id"] == col("_valid_product_id"),
            "left",
        )
    )

    customer_ok = col("customer_id").isNull() | col("_valid_customer_id").isNotNull()
    product_ok = col("product_id").isNull() | col("_valid_product_id").isNotNull()
    return (
        flagged.withColumn("referential_integrity_passed", customer_ok & product_ok)
        .drop("_valid_customer_id", "_valid_product_id")
    )
