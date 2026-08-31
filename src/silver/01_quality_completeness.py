# Databricks notebook source
"""Flag completeness on customers and orders. Does not write Silver tables.

Customers fail when email is missing. Orders fail when customer_id or
product_id is missing. Products have no completeness rule.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col


def flag_customer_completeness(customers: DataFrame) -> DataFrame:
    """Mark a customer complete only when email is present (NULL or blank fails)."""
    email_missing = col("email").isNull() | (col("email") == "")
    return customers.withColumn("completeness_passed", ~email_missing)


def flag_order_completeness(orders: DataFrame) -> DataFrame:
    """Mark an order complete only when both foreign keys are non-NULL."""
    key_missing = col("customer_id").isNull() | col("product_id").isNull()
    return orders.withColumn("completeness_passed", ~key_missing)
