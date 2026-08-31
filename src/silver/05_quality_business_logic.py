# Databricks notebook source
"""Flag numeric business rules. Does not write Silver tables.

These rules are half of Check 4 (business_logic_passed). Format/date/enum
rules live in 03_quality_type_validation.py; create_silver_tables.py ANDs
both sides.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col


def flag_order_business_logic(orders: DataFrame) -> DataFrame:
    """Fail non-positive qty/price and amount mismatch at DECIMAL(12,2)."""
    bad_quantity = col("quantity") <= 0
    bad_unit_price = col("unit_price") <= 0
    amount_mismatch = col("total_amount") != (col("unit_price") * col("quantity"))
    return orders.withColumn(
        "numeric_rules_passed",
        ~(bad_quantity | bad_unit_price | amount_mismatch),
    )


def flag_product_business_logic(products: DataFrame) -> DataFrame:
    """Fail non-positive catalog price and cost above price."""
    bad_price = col("price") <= 0
    negative_margin = col("cost") > col("price")
    return products.withColumn(
        "numeric_rules_passed",
        ~(bad_price | negative_margin),
    )
