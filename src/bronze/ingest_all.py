# Databricks notebook source
"""Run all three Bronze ingests in one session with a shared batch_id.

Use this file as a Databricks notebook in Repos or Workspace. %run loads
each numbered sibling into this session; the ingest_* calls then run in
order and stop on the first error.

importlib + __file__ is not used here: Databricks notebooks often have no
__file__, so dynamic file loads fail. If %run already executed main(), the
second call is a no-op for data because each ingest is idempotent by
batch_id.
"""

# COMMAND ----------

BATCH_ID = "20260831"

# COMMAND ----------

# MAGIC %run ./01_ingest_customers

# COMMAND ----------

ingest_customers(spark)

# COMMAND ----------

# MAGIC %run ./02_ingest_orders

# COMMAND ----------

ingest_orders(spark)

# COMMAND ----------

# MAGIC %run ./03_ingest_products

# COMMAND ----------

ingest_products(spark)
