# Requirement Analysis

## Problem Statement

An e-commerce company lands daily CSV extracts from a customer database, an
order system, and a product catalog. Stakeholders need trustworthy sales and
customer metrics, but the extracts contain realistic defects (missing keys,
duplicates, orphans, and invalid values).

The pipeline must:

1. Keep an auditable raw copy of every ingested row (Bronze).
2. Detect and flag quality failures without deleting rows (Silver).
3. Publish business-ready aggregations from records that pass quality checks
   (Gold).
4. Expose those aggregations in a Databricks SQL dashboard.

Required flow:

`customers.csv / orders.csv / products.csv → Bronze → Silver → Gold → Dashboard`

This is a learning/demo project with synthetic data only. The Core delivery is
the working medallion pipeline plus lifecycle artifacts (analysis, design,
prompt history, tests, debugging, reflection). Production orchestration,
CDC, and real PII are out of scope.

Authoritative design lives in `spec.md`. Field types and money precision live
in `data-model.md`. Quality-issue inventories belong in
`data-quality-strategy.md`.

## Functional Requirements

### Data generation

- Generate three CSVs at the volumes in `spec.md`: 10,000 customers, 100,000
  orders, 500 products.
- Inject **460 exercise-required** defects exactly as the participant guide
  lists them.
- Inject **240 supplemental** defects so distinct problematic rows total
  **700**, on rows that do not already carry an exercise-required issue.
- Use a fixed random seed so generation is reproducible.
- Use clearly synthetic names and emails (for example `example.com`).

### Bronze

- Ingest all three sources from configured S3 or DBFS paths into
  `bronze_customers`, `bronze_orders`, and `bronze_products`.
- Apply the explicit schemas in `data-model.md`. Do not rely on inference
  as the source of truth.
- Preserve every source column, name, value, duplicate, and NULL. No
  filtering, cleaning, or renaming.
- Add only `ingestion_timestamp`, `source_file`, and `batch_id`.
- Log source name, batch ID, source row count, written row count, timestamp,
  and status. Source and written counts must match.
- Fail clearly on missing paths, missing headers, or unreadable files.
- Rerunning the same `batch_id` must not duplicate that batch.

### Silver

- Create `silver_customers`, `silver_orders`, and `silver_products` with one
  Silver row for every Bronze row.
- Flag failures; never delete rows. Store per-check Booleans and
  `quality_check_result` (`PASS` or a deterministic list of failed checks).
- Implement four checks:
  1. Completeness (NULL `email` on customers; NULL `customer_id` or
     `product_id` on orders).
  2. Uniqueness (duplicate `customer_id` and `order_id`; flag every member
     of a duplicate group).
  3. Referential integrity (non-NULL order FKs must exist on unique parent
     keys; NULL FKs are completeness-only, not orphans).
  4. Validity / business logic (email format, future signup dates, allowed
     enums, quantity and price rules, amount = quantity × unit price,
     product price and margin rules).
- Publish a quality metrics report per `batch_id`, table, check, and
  field/relationship: evaluated, passed, failed, pass percentage, timestamp.
- Report failed-check occurrences and distinct bad rows separately.

### Gold

- Read Silver only. Never read Bronze.
- Include only rows whose applicable quality flags all pass.
- Include only `Completed` orders in revenue and order metrics.
- Build three tables:
  - `gold_sales_by_product`: `product_id`, `product_name`, `category`,
    `total_orders`, `total_revenue`, `avg_order_value`.
  - `gold_revenue_by_customer`: `customer_id`, `customer_name`,
    `customer_segment`, `total_orders`, `total_revenue`, `avg_order_value`,
    `lifetime_value_actual` (valid customers with no completed orders stay
    at zero).
  - `gold_customer_segmentation`: `segment_type`, `customer_count`,
    `avg_revenue`, `total_revenue`, with mutually exclusive segments
    High-Value / Repeat / One-Time / Inactive.
- `total_orders` is distinct valid completed `order_id`. `avg_order_value`
  is `total_revenue / total_orders`. Revenue uses `orders.total_amount`
  after the arithmetic check passes.

### Dashboard

- Databricks SQL dashboard backed only by Gold, with at least:
  - Top 10 products by revenue (bar).
  - Customer revenue distribution (histogram), including zero-revenue
    customers.
  - Customer segmentation (pie) sized by `customer_count`.
- Filters for customer segment and product category where those dimensions
  exist on the Gold source. No date filter, because the three Gold tables
  have no date column.

### Testing and delivery

- Tests must catch the intentional defects at their specified counts
  (exercise-required and supplemental tallied separately).
- Provide schema/setup scripts, README setup that runs end to end, and the
  required lifecycle documentation.

## Non-Functional Requirements

- **No real PII.** Synthetic data only; do not prompt AI with real customer
  records.
- **Idempotency.** Every layer is safely rerunnable by `batch_id` without
  duplicating rows or inflating Gold metrics.
- **Traceability.** `batch_id`, source file, and ingestion timestamp persist
  through Silver; quality metrics are batch-attributable.
- **Configuration over hardcoding.** Paths, catalog/schema names, decimal
  type, batch IDs, as-of date, and the High-Value percentile live in config.
- **Documented transforms.** Intent-focused docstrings; comments explain
  why a check exists, especially when it maps to an injected issue.
- **Layer separation.** Bronze, Silver, Gold, and dashboard stay in
  separate files. PySpark for full-dataset work; formatted SQL for Gold and
  dashboard queries.
- **Fail loud.** No silent skip of unreadable sources, schema mismatches, or
  failed writes.
- **Quality reporting thresholds** from the guide (>99% completeness, 100%
  uniqueness, >99.9% referential integrity) are reporting/alert targets only.
  They do not cause Silver to drop rows.
- **Out of scope:** production deploy, orchestration, alerting, SLOs,
  streaming, CDC, MDM, production security, and extra Gold tables.

## Assumptions

These are judgment calls already recorded in `spec.md` / `data-model.md`.
Treat them as requirements unless a later decision changes them.

1. **Three Gold tables, not four.** The guide’s detailed Gold design and
   acceptance criteria name three aggregations. The “four aggregations”
   / `daily_weekly_trends` filename is treated as a template leftover.
2. **Issue counts.** Exercise-required defects stay at 460. Supplemental
   defects close the gap to 700 distinct bad rows. Tests assert both origins.
3. **Money type is DECIMAL(12,2)** for all monetary fields (`data-model.md`).
4. **Explicit Bronze schemas** rather than inference, for repeatable types.
5. **Duplicate groups:** every row that shares a duplicated PK fails
   uniqueness; none is treated as the “good” copy.
6. **Orphan vs NULL:** a NULL FK fails completeness only. Referential
   integrity is not applicable on NULL FKs.
7. **Parent uniqueness:** an order whose `customer_id` exists only as a
   duplicated customer key is not analytically valid.
8. **Gold uses passing Silver rows and Completed orders only.** Pending and
   Cancelled are not settled revenue.
9. **`lifetime_value_actual`** is summed valid completed-order revenue in this
   dataset, not the source `lifetime_value` column.
10. **Segmentation precedence and High-Value at or above the batch revenue
    P80** (configurable). Each valid customer gets exactly one segment.
11. **Valid customers with no completed orders** still appear in
    `gold_revenue_by_customer` and count as Inactive.
12. **Check 4** is the single fourth quality check (validity/business logic),
    not a fifth check, even though it covers several rule types.
13. **Product completeness** is not applicable; zero price and negative
    margin fail Check 4.
14. **Environment:** development and validation target Databricks Community
    Edition (or equivalent) with the repo cloned into the workspace. Local
    generation of CSVs is acceptable before upload to DBFS/S3.
15. **`payment_date` NULL** is allowed and is not a quality failure by
    itself.

## Edge Cases

- Duplicate PK appears twice vs more than twice; all members fail uniqueness.
- One row fails several checks; `quality_check_result` lists all of them,
  and the metrics report does not treat that as several distinct bad rows.
- Order with NULL `customer_id` and a valid `product_id` (and the reverse).
- Order whose FK is non-NULL but missing from the parent table.
- Order that points at a duplicated parent `customer_id`.
- Malformed email that is non-NULL vs NULL email (format vs completeness).
- `quantity` = 0 vs negative; `unit_price` = 0 vs negative.
- `total_amount` off by one cent vs exact `quantity × unit_price` at
  DECIMAL(12,2).
- `order_status` / `customer_segment` with unexpected casing or extra spaces.
- Customer with only Pending or Cancelled orders (Inactive for Gold, revenue
  zero).
- Customer immediately below vs exactly at the calculated P80 cutoff.
- Customer with two completed orders below P80 (Repeat).
- Customer with one completed order at or above P80 (High-Value, not One-Time).
- Product with `price` = 0 vs `cost` > `price` on different product IDs.
- Rerun of the same `batch_id`; missing CSV; extra or missing header columns;
  a value that cannot cast to the declared type.
- Empty extract (zero-row file with a valid header).
- Gold average when `total_orders` is zero (customer or product with no
  completed valid orders): `avg_order_value` must be defined (NULL or 0)
  consistently — see open questions.

## Open Questions

Most ambiguities in the participant guide are already closed in `spec.md`.
These are the items still worth confirming before implementation, or that a
reviewer might still interpret differently.

1. **Duplicate-row mechanics.** Does “10 rows with duplicate `customer_id`”
   mean 10 extra copied rows (10 IDs appearing twice → 20 flagged rows) or
   10 rows that share IDs in some other pattern? Same question for the 20
   duplicate `order_id` rows. Default if unspecified: copy 10 (or 20) existing
   keys onto additional rows so those keys appear twice.
2. **`avg_order_value` when `total_orders` = 0.** Spec defines the ratio but
   not divide-by-zero. Preference: NULL for products with no valid completed
   orders; 0 for customers included in the customer grain with zero orders.
3. **Histogram bins.** The guide asks for a customer-revenue histogram but
   does not define bin edges. Needs a documented binning choice in the
   dashboard guide.
4. **Unity Catalog vs hive_metastore / Community Edition.** Catalog and
   schema names are configurable, but the default target (Community Edition
   `hive_metastore` vs a Unity Catalog catalog) is not fixed.
5. **S3 vs DBFS in the README path.** Spec allows either. Default for the
   exercise: generate locally, land on DBFS, keep S3 as an optional
   configured prefix.
6. **Whether source `lifetime_value` is displayed anywhere.** Gold uses
  `lifetime_value_actual`. Confirm it is acceptable not to chart the
   source column.
7. **Dashboard delivery format.** Queries plus `DASHBOARD_GUIDE.md` are
   required; exporting a Databricks dashboard JSON/DBSQL asset is not
   specified. Default: documented SQL and setup steps, not a binary
   dashboard export.

If any of these change, update `spec.md` first, then this file.
