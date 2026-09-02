# Candidate Information

**Name:**
Yogesh Kargeti

**Role:**
SSE

**Primary Technology Stack:**
Python, PySpark, SQL, Databricks

**Primary AI Tool Used:**
Cursor

**Project Option Selected:**
Data Pipeline (Medallion Architecture)

**Assessment Start Date:**
2026-08-22

**Submission Date:**
2026-09-02

## Tools & Environment

**Databricks:**
Free Edition (Serverless compute, Unity Catalog)

**Languages:**
Python, PySpark, SQL

**Libraries:**
PySpark, Delta Lake, Faker

**AI Tool:**
Cursor

## Setup Summary

Clone this repo into Databricks Repos, upload the three
generated CSVs to a Unity Catalog volume, then run
`src/bronze/ingest_all.py` → `src/silver/create_silver_tables.py` →
`src/gold/create_gold_tables.py` in order (each is a Databricks notebook,
run with Serverless compute). Full instructions in `README.md`.
