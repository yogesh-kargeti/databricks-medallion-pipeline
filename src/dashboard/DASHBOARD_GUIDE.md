# Dashboard Guide

How to turn `dashboard_queries.sql` into a Databricks SQL dashboard. Queries
read **Gold tables only**. The batch is hardcoded as `20260831`. There are
no dashboard parameters and no date filter (none of the Core Gold tables
has a date column).

## Prerequisites

1. Run Bronze → Silver → `create_gold_tables.py` for `BATCH_ID` `20260831`.
2. Confirm `gold_sales_by_product`, `gold_revenue_by_customer`, and
   `gold_customer_segmentation` have rows for that batch.
3. Open a SQL warehouse you can query from Databricks SQL.

## Create the queries

In **SQL Editor**, create one saved query per tile. Copy the matching
block from `dashboard_queries.sql`, run it, and save it. Do not add
query parameters.

| Query name | Source table | Viz |
|---|---|---|
| Top 10 products by revenue | `gold_sales_by_product` | Bar |
| Customer revenue distribution | `gold_revenue_by_customer` | Histogram (or bar from Tile 2b) |
| Customer segmentation | `gold_customer_segmentation` | Pie |

Use Tile 2b only if the warehouse has no histogram visualization.

## Build the dashboard

1. **SQL** → **Dashboards** → **Create dashboard**.
2. Add a tile for each saved query.
3. Set the visualization as below.

### Tile 1 — Top 10 products by revenue (bar)

- Visualization: **Bar**
- X / grouping: `product_name`
- Y / values: `total_revenue` (sum is fine; the query already returns 10
  rows)
- Sort: `total_revenue` descending (the SQL already does this)
- Format `total_revenue` as currency

### Tile 2 — Customer revenue distribution (histogram)

- Visualization: **Histogram** (or **Distribution**) on `total_revenue`
- Count of rows = customer count. Do **not** exclude `total_revenue = 0`;
  Inactive customers are in Gold with zero revenue and must show up.

If there is no histogram visualization, use **Tile 2b** as a bar chart:
X = `revenue_bucket`, Y = `customer_count`. The `0` bucket is zero-revenue
customers. Keep the SQL `ORDER BY MIN(total_revenue)` so buckets stay in
dollar order.

### Tile 3 — Customer segmentation (pie)

- Visualization: **Pie**
- Slice / group: `segment_type`
- Size / value: `customer_count` (not `total_revenue`, or High-Value will
  dominate the pie for the wrong reason)
- Expect four slices: High-Value, Repeat, One-Time, Inactive. One-Time and
  Inactive are small because most valid customers have several completed
  orders; that is data shape, not a missing tile.

## What not to add

- Date / order_date filters — would need an extra Gold trend table (out of
  Core scope).
- Bronze or Silver as a dashboard source.
- Dashboard or query parameters (`batch_id`, category, segment).

## Quick checks after publish

- Top 10 bar has at most 10 bars and matches
  `SELECT * FROM gold_sales_by_product WHERE batch_id = '20260831' ORDER BY
  total_revenue DESC LIMIT 10`.
- Histogram (or 2b) customer counts sum to the Gold customer row count for
  `20260831`, including zeros.
- Pie `customer_count` sums to the same Gold customer row count.
