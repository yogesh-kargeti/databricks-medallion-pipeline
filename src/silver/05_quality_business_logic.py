# Databricks notebook source
"""Flag validity / business logic. Does not write Silver tables.

Structural keys can be fine while values are still unusable for Gold.
NULL/blank email is completeness only; format is checked when email is present.
"""

from datetime import date

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit

if "AS_OF_DATE" not in globals():
    AS_OF_DATE = date(2026, 8, 31)

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")


def flag_customer_business_logic(customers: DataFrame) -> DataFrame:
    """Fail malformed emails, future signup dates, and illegal segments."""
    as_of = globals().get("AS_OF_DATE", AS_OF_DATE)
    email_present = col("email").isNotNull() & (col("email") != "")
    malformed_email = email_present & (~col("email").rlike(EMAIL_PATTERN))
    future_signup = col("signup_date") > lit(as_of)
    bad_segment = ~col("customer_segment").isin(*CUSTOMER_SEGMENTS)
    return customers.withColumn(
        "business_logic_passed",
        ~(malformed_email | future_signup | bad_segment),
    )


def flag_order_business_logic(orders: DataFrame) -> DataFrame:
    """Fail non-positive qty/price, amount mismatch at DECIMAL(12,2), bad status."""
    bad_quantity = col("quantity") <= 0
    bad_unit_price = col("unit_price") <= 0
    amount_mismatch = col("total_amount") != (col("unit_price") * col("quantity"))
    bad_status = ~col("order_status").isin(*ORDER_STATUSES)
    return orders.withColumn(
        "business_logic_passed",
        ~(bad_quantity | bad_unit_price | amount_mismatch | bad_status),
    )


def flag_product_business_logic(products: DataFrame) -> DataFrame:
    """Fail non-positive catalog price and cost above price."""
    bad_price = col("price") <= 0
    negative_margin = col("cost") > col("price")
    return products.withColumn(
        "business_logic_passed",
        ~(bad_price | negative_margin),
    )
