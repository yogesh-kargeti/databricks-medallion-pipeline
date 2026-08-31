# AI Prompts — Bronze Layer

## Prompt 1: Initial customers ingestion script

**PROMPT SENT:**
"write 01_ingest_customers.py in src/bronze/ — reads customers.csv per
data-model.md, writes bronze_customers as Delta, adds ingestion_timestamp/
source_file/batch_id, logs source vs written row counts, idempotent by
batch_id. keep comments minimal, code should mostly speak for itself"

**AI RESPONSE SUMMARY:**
Cursor generated a script with explicit schema (no inference), a
DELETE-by-batch_id + append pattern for idempotency, header/readability
pre-checks (FAILFAST mode), and a hard row-count assertion
(source vs written) that raises RuntimeError on mismatch.

**EVALUATION:**
✓ Idempotency logic verified correct — DELETE + append, with overwrite
  fallback on first run
✓ Explicit schema matched data-model.md exactly, including DECIMAL(12,2)
✓ Row-count check was a real assertion, not just a log line
△ Minor: header-match check uses naive comma-split rather than a real CSV
  parser — accepted as-is since no field values in this dataset contain
  commas

**DECISION:** Accepted as the pattern for all three Bronze scripts.

---

## Prompt 2: Orders and products scripts (pattern reuse)

**PROMPT SENT:**
"same pattern as 01_ingest_customers.py — write 02_ingest_orders.py for
orders.csv (bronze_orders) and 03_ingest_products.py for products.csv
(bronze_products), matching their schemas from data-model.md"

**AI RESPONSE SUMMARY:**
Both scripts followed the established pattern exactly, with correct
per-table schemas (orders: 9 fields incl. nullable payment_date;
products: 7 fields).

**EVALUATION:** ✓ Accepted without changes — cheap, low-risk reuse of an
already-reviewed pattern.

---

## Prompt 3: Orchestrator script

**PROMPT SENT:**
"write ingest_all.py that calls all three ingestion scripts in sequence
with one batch_id, keep it short"

**AI RESPONSE SUMMARY:**
First version used `importlib` + `__file__` to dynamically load the
numbered scripts, since their filenames aren't valid Python import names.

**EVALUATION:**
✗ Flagged as risky before testing: Databricks notebooks often have no
  `__file__`, so dynamic imports could fail silently in that environment.

**FOLLOW-UP PROMPT:**
"ingest_all.py uses importlib to load numbered filenames since they can't
be imported normally. will this work when run as a Databricks notebook or
Repos Python file? if there's a risk, suggest a simpler fallback"

**RESULT:** Cursor rewrote the script to use Databricks' `%run` magic
command instead, with a notebook-source header, and explained the
`__file__` limitation directly in the docstring. Also required adding the
`# Databricks notebook source` header to 01/02/03 so `%run` would
recognize them as notebooks.

**DECISION:** Accepted the `%run`-based rewrite.

---

## Debugging round 1: DBFS vs Unity Catalog Volumes

First live Databricks run failed at CSV upload — Free Edition only
offered Unity Catalog Volumes, not classic DBFS FileStore. Uploaded CSVs
to `/Volumes/workspace/default/databricks_assess/` and prompted Cursor to
update `CSV_PATH` across all three scripts. See `debugging-notes.md` for
full root-cause writeup.

## Debugging round 2: Serverless spark.conf restriction

Second live run failed with `CONFIG_NOT_AVAILABLE.WITHOUT_SUGGESTION` on
`spark.conf.set("pipeline.batch_id", ...)`. Root cause: Databricks
Serverless compute rejects custom Spark conf keys. Prompted Cursor to
replace all `spark.conf` config-passing with shared Python globals
(since `%run` already shares the notebook namespace). See
`debugging-notes.md` for full writeup.

## Outcome

`ingest_all.py` ran end-to-end successfully on Databricks Free Edition
(Serverless compute) after both fixes. Verified: `bronze_customers`,
`bronze_orders`, `bronze_products` created with correct schemas (matching
`data-model.md` plus the three lineage columns) and correct row counts
(10,000 / 100,000 / 500).