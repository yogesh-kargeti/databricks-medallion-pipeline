## Issue: CSV path mismatch — DBFS vs Unity Catalog Volumes

**What happened:** Bronze scripts were written assuming classic DBFS
(`dbfs:/FileStore/...`) paths, based on older Databricks documentation
patterns. When connecting to Databricks Free Edition and trying to upload
sample CSVs, the "Add Data" UI only offered Unity Catalog Volumes as a
destination — no classic DBFS FileStore option was available.

**Root cause:** Databricks Free Edition uses Unity Catalog by default;
classic DBFS FileStore isn't the standard upload path in this environment.

**Fix:** Uploaded CSVs to a Unity Catalog volume
(`/Volumes/workspace/default/databricks_assess/`) instead, and updated
`CSV_PATH` in `01_ingest_customers.py`, `02_ingest_orders.py`, and
`03_ingest_products.py` to point at the Volumes path.

**Lesson:** Confirm the target Databricks environment's storage model
(DBFS vs Unity Catalog) before hardcoding paths, rather than assuming
classic DBFS everywhere.