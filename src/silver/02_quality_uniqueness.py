# Databricks notebook source
"""Flag uniqueness on business keys. Does not write Silver tables.

Every row in a duplicate key group fails. No winner is chosen.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count
from pyspark.sql.window import Window


def _flag_unique_key(dataframe: DataFrame, key: str) -> DataFrame:
    """Fail uniqueness for every row whose key value appears more than once."""
    key_count = count("*").over(Window.partitionBy(key))
    return dataframe.withColumn("uniqueness_passed", key_count == 1)


def flag_customer_uniqueness(customers: DataFrame) -> DataFrame:
    """Fail all customers that share a customer_id."""
    return _flag_unique_key(customers, "customer_id")


def flag_order_uniqueness(orders: DataFrame) -> DataFrame:
    """Fail all orders that share an order_id."""
    return _flag_unique_key(orders, "order_id")


def flag_product_uniqueness(products: DataFrame) -> DataFrame:
    """Defensive product_id uniqueness; no duplicate products are seeded."""
    return _flag_unique_key(products, "product_id")
