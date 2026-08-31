# Databricks notebook source
"""Flag type/format/enum validity. Does not write Silver tables.

These rules are half of Check 4 (business_logic_passed). Numeric rules live
in 05_quality_business_logic.py; create_silver_tables.py ANDs both sides.
"""

from datetime import date

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit

if "AS_OF_DATE" not in globals():
    AS_OF_DATE = date(2026, 8, 31)

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")


def flag_customer_type_validation(customers: DataFrame) -> DataFrame:
    """Fail malformed emails, future signup dates, and illegal segments."""
    as_of = globals().get("AS_OF_DATE", AS_OF_DATE)
    email_present = col("email").isNotNull() & (col("email") != "")
    malformed_email = email_present & (~col("email").rlike(EMAIL_PATTERN))
    future_signup = col("signup_date") > lit(as_of)
    bad_segment = ~col("customer_segment").isin(*CUSTOMER_SEGMENTS)
    return customers.withColumn(
        "type_validation_passed",
        ~(malformed_email | future_signup | bad_segment),
    )


def flag_order_type_validation(orders: DataFrame) -> DataFrame:
    """Fail order_status values outside Pending / Completed / Cancelled."""
    bad_status = ~col("order_status").isin(*ORDER_STATUSES)
    return orders.withColumn("type_validation_passed", ~bad_status)
