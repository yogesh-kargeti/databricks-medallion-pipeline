# Databricks Medallion Sales Pipeline

E-commerce CSVs (customers, orders, products) through Bronze → Silver → Gold
→ a Databricks SQL dashboard. Synthetic data only.

Built and tested on **Databricks Free Edition**: serverless compute and
**Unity Catalog volumes**

## 1. Clone into Databricks Repos

1. In Databricks, open **Workspace** → **Repos** (or Git folders) → **Add
   repo**.
2. Clone this Git repository.
3. Confirm you can see `src/bronze`, `src/silver`, `src/gold`,
   `src/dashboard`, and `data/`.

Pipeline notebooks are Databricks `.py` notebooks (`# Databricks notebook
source`). Open them from the repo in the workspace; do not run them as
local `python` scripts.

## 2. Generate the CSVs (if needed)

If `data/customers.csv`, `data/orders.csv`, and `data/products.csv` are
already in the clone, skip this step.

On your laptop, from the repo root:

```text
python -m pip install -r requirements.txt
python src/data_generation/generate_sample_data.py
```

That writes the three files under `data/` (10,000 customers, 100,000
orders, 500 products) with a fixed seed. Notes:
`src/data_generation/DATA_GENERATION_NOTES.md`.

## 3. Upload CSVs to a Unity Catalog volume

Bronze reads:

```text
/Volumes/workspace/default/databricks_assess/customers.csv
/Volumes/workspace/default/databricks_assess/orders.csv
/Volumes/workspace/default/databricks_assess/products.csv
```

1. In Catalog, open (or create) volume `workspace.default.databricks_assess`.
2. Upload the three CSVs to that volume with **those exact file names**.

If your catalog, schema, or volume name is different, change `CSV_PATH` at
the top of:

- `src/bronze/01_ingest_customers.py`
- `src/bronze/02_ingest_orders.py`
- `src/bronze/03_ingest_products.py`

Attach a **serverless** SQL warehouse / compute that can read that volume.

## 4. Run the pipeline (this order)

Use serverless compute. Shared notebook global `BATCH_ID` defaults to
`20260831` if you do not set it first.

| Step | Notebook | What it writes |
|---|---|---|
| 1 | `src/bronze/ingest_all.py` | `bronze_customers`, `bronze_orders`, `bronze_products` |
| 2 | `src/silver/create_silver_tables.py` | `silver_*` tables and `silver_quality_metrics` |
| 3 | `src/gold/create_gold_tables.py` | `gold_sales_by_product`, `gold_revenue_by_customer`, `gold_customer_segmentation` |

`ingest_all.py` `%run`s the three ingest notebooks. `create_silver_tables.py`
`%run`s the quality-check notebooks, then `06_quality_metrics_report.py`.
`create_gold_tables.py` must be run from `src/gold/` so it can load the
sibling `.sql` files.

Rerunning the same `BATCH_ID` replaces that batch; it does not duplicate
rows.

Quick checks:

- Bronze counts: 10,000 / 100,000 / 500.
- Silver counts match Bronze; `quality_check_result` is `PASS` or a list of
  failed checks (rows are flagged, not dropped).
- Gold customer count equals Silver customers with `quality_check_result =
  'PASS'`.

## 5. Run the Silver quality-metrics test

After `create_silver_tables.py`, `silver_quality_metrics` must exist and
the notebook must be attached to **serverless compute** so Spark is
active. This is not a local `pytest` run.

Install pytest on the cluster once (the only extra test dependency;
`requirements-dev.txt` pins it and also pulls `requirements.txt`):

```text
%pip install -r requirements-dev.txt
```

In a new notebook in the repo (same compute), `%run` the test module so
its functions load into the session, then call the assertion:

```text
%run ../tests/test_silver_quality_metrics
test_seeded_quality_metric_counts()
```

Adjust the `%run` path if your notebook is not next to `src/` (from
`src/silver/` use `../../tests/test_silver_quality_metrics`). Defaults
are `batch_id=20260831` and table `silver_quality_metrics`. Override with
environment variables `SILVER_TEST_BATCH_ID` or `SILVER_METRICS_TABLE`
before calling the test.

A passing run means every seeded field-level `records_failed` count
matches `data-quality-strategy.md` and `_all` distinct bad rows equal
**700**.

## 6. Dashboard

1. Open Databricks SQL.
2. Follow `src/dashboard/DASHBOARD_GUIDE.md`.
3. Paste each query from `src/dashboard/dashboard_queries.sql` into a saved
   query (`batch_id = '20260831'` is already in the SQL).
4. Build tiles: top 10 products (bar), customer revenue (histogram or tile
   2b bar), segmentation (pie).

## Layout

| Path | Role |
|---|---|
| `src/data_generation/` | CSV generator |
| `src/bronze/` | Raw ingest |
| `src/silver/` | Quality flags + metrics |
| `src/gold/` | Aggregations |
| `src/dashboard/` | SQL + dashboard guide |
| `tests/` | Silver metrics integration test |
| `requirements-dev.txt` | pytest (plus Faker via `requirements.txt`) |
| `data/` | Generated CSVs |
| `data-model.md` | Schemas |
| `data-quality-strategy.md` | Quality checks and seeded issues |
| `tool-specific/cursor-workflow/spec.md` | Full design spec |

Do not use real customer PII. Generated emails use `example.com`.
