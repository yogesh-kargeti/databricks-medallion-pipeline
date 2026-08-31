## Issue: CSV path mismatch — DBFS vs Unity Catalog Volumes

**What happened:** Bronze scripts were written assuming classic DBFS
(`dbfs:/FileStore/...`) paths. When uploading sample CSVs in Databricks
Free Edition, the "Add Data" UI only offered Unity Catalog Volumes as a
destination — no classic DBFS FileStore option was available.

**Root cause:** Databricks Free Edition uses Unity Catalog by default;
classic DBFS FileStore isn't the standard upload path in this environment.

**Fix:** Uploaded CSVs to a Unity Catalog volume
(`/Volumes/workspace/default/databricks_assess/`) and updated `CSV_PATH`
in all three Bronze ingest scripts to point at the Volumes path.

**Lesson:** Confirm the target Databricks environment's storage model
(DBFS vs Unity Catalog) before hardcoding paths, rather than assuming
classic DBFS everywhere.

---

## Issue: Serverless compute rejects custom spark.conf keys

**What happened:** `ingest_all.py` failed on
`spark.conf.set("pipeline.batch_id", ...)` with
`CONFIG_NOT_AVAILABLE.WITHOUT_SUGGESTION`.

**Root cause:** Databricks Serverless compute only allows a fixed set of
Spark configuration keys; arbitrary custom keys are rejected. This would
have worked on a classic cluster but not Serverless, which Databricks
Free Edition provisions by default.

**Fix:** Replaced `spark.conf`-based config passing (`pipeline.batch_id`,
`pipeline.csv.*`, `pipeline.bronze.*`) with plain Python global variables.
`%run` already shares the notebook namespace, so Spark conf was never
necessary for this — a simpler mechanism that also isn't restricted on
Serverless.

**Lesson:** Serverless compute has stricter Spark configuration
restrictions than classic clusters. Verified end-to-end on Databricks
Free Edition after the fix — `ingest_all.py` ran cleanly and
`bronze_customers` / `bronze_orders` / `bronze_products` were created
with correct schemas and row counts.