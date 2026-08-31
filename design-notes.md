# Design Notes

Summary of `spec.md`, `data-model.md`, `requirements-analysis.md`, and
`data-quality-strategy.md`. Those files remain the source of truth; this
file is the design snapshot.

## Architecture Overview

Daily synthetic CSVs land in Databricks and move through four stages:

`customers / orders / products → Bronze → Silver → Gold → Dashboard`

- **Bronze:** raw Delta copies plus ingestion metadata. No cleaning.
- **Silver:** same grain as Bronze; quality flags, never deletes.
- **Gold:** three aggregations from Silver rows that pass all applicable
  checks. Never reads Bronze.
- **Dashboard:** Databricks SQL on Gold (top-10 products, revenue
  histogram, segmentation pie).

Layers stay in separate scripts. Paths, `batch_id`, DECIMAL type, as-of
date, and the High-Value threshold are configuration, not hardcoded
literals. Reruns of the same `batch_id` must not duplicate data.

Core scope is three Gold tables. The guide’s “four aggregations” /
`daily_weekly_trends` filename is treated as a template leftover.

## Data Model & Schema

Three entities. Full field lists live in `data-model.md`.

| Table | Grain | PK | Volume |
|---|---|---|---|
| `customers` | one customer | `customer_id` | 10,000 |
| `orders` | one order | `order_id` | 100,000 |
| `products` | one product | `product_id` | 500 |

FKs: `orders.customer_id` → `customers.customer_id`,
`orders.product_id` → `products.product_id`. `payment_date` is nullable.

Money fields are **DECIMAL(12,2)** so Silver can compare
`total_amount` to `quantity × unit_price` without floats.

Allowed values: `customer_segment` ∈ Premium / Standard / Basic;
`order_status` ∈ Pending / Completed / Cancelled.

## Bronze Layer Design

Tables: `bronze_customers`, `bronze_orders`, `bronze_products`.

- Read configured S3/DBFS CSVs with the explicit `data-model.md` schema
  (inference is not the contract).
- Keep source names and values, including NULLs and duplicates.
- Add only `ingestion_timestamp`, `source_file`, `batch_id`.
- Log source vs written counts; they must match.
- Fail on missing files, bad headers, or type-conversion errors.
- Idempotent write keyed by `batch_id`.

## Silver Layer Design

Tables: `silver_customers`, `silver_orders`, `silver_products` — one row
per Bronze row, plus lineage metadata, per-check Booleans, and
`quality_check_result` (`PASS` or a fixed-order list of failed checks).

Gold excludes a row when any applicable flag is false. Silver still
retains it. Quality metrics are published per batch, table, check, and
field, with distinct-bad-row counts kept separate from failed-check
occurrences.

## Gold Layer Design

Only passing Silver rows. Only `Completed` orders contribute to revenue.

- **`gold_sales_by_product`:** product attributes plus `total_orders`,
  `total_revenue`, `avg_order_value`.
- **`gold_revenue_by_customer`:** every valid customer (zeros if no
  completed orders). `lifetime_value_actual` is summed valid completed
  revenue, not source `lifetime_value`.
- **`gold_customer_segmentation`:** exactly one of High-Value
  (`total_revenue >= 1,000`), Repeat (2+ orders below that), One-Time
  (one order), Inactive (zero orders). Threshold is configurable.

`total_orders` is distinct completed `order_id`. `avg_order_value` is
`total_revenue / total_orders`. Dashboard queries Gold only; no date
filter because these tables have no date column.

## Data Quality Validation Strategy

Four checks. Full what/how/threshold/result and seed lists:
`data-quality-strategy.md`.

| Check | Core rule | Report threshold |
|---|---|---|
| Completeness | NULL `email`; NULL order FKs | >99% |
| Uniqueness | Duplicate `customer_id` / `order_id`; flag all members | 100% |
| Referential integrity | Non-NULL FKs exist on unique parents | >99.9% |
| Validity (proposed) | Format, dates, enums, qty/price/amount, catalog price/margin | >99% (proposed) |

NULL FKs are completeness, not orphans. Thresholds are report-only.

Seeded defects, non-overlapping: **460** exercise-required + **240**
supplemental = **700** distinct bad rows. Tests assert each origin
separately, then the 700 total.

## Debugging Approach

1. Reproduce with the same `batch_id` and generator seed.
2. Capture the full error or unexpected metric (layer, table, check,
   counts) before changing code.
3. Locate the layer: generator counts → Bronze source vs written → Silver
   flags vs seed inventory → Gold reconciling product, customer, and
   segment revenue.
4. Prefer a failing test that names the expected count or edge case
   (NULL vs orphan, 999.99 vs 1,000, duplicate-group members).
5. Change only the failing rule or transform; do not silently edit
   unrelated layers.
6. Re-run the targeted test, then the batch idempotency check.

Log ingestion metadata and quality metrics so “missing rows” vs
“flagged rows vs Gold filters” can be distinguished without guessing.
