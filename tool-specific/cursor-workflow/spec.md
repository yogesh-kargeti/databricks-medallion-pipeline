# Databricks Medallion Sales Pipeline Specification

## 1. Problem Summary

An e-commerce company receives daily CSV extracts from a customer database, an
order system, and a product catalog. The pipeline must ingest these files into
Databricks, preserve an auditable raw copy, identify data quality problems
without losing records, and publish business-ready sales and customer
aggregations. Databricks SQL will expose those aggregations through a dashboard
for business stakeholders.

The required flow is:

`customers.csv / orders.csv / products.csv → Bronze → Silver → Gold → Dashboard`

The exercise also requires visible evidence of data generation, validation,
testing, debugging, documentation, and responsible use of AI.

## 2. Scope

### In scope

- Generate synthetic CSV data for customers, orders, and products at the
  volumes defined in the requirements.
- Add the exercise-required quality issues from the participant guide, plus
  the separately listed supplemental issues needed to reach ~700 distinct
  problematic rows.
- Ingest all source rows from S3 or DBFS into Bronze Delta tables.
- Apply schema and ingestion metadata in Bronze without changing source data.
- Create Silver Delta tables that retain every Bronze row and flag failed
  quality checks.
- Report pass counts, fail counts, and pass percentages for each quality check.
- Create three Gold aggregation tables from valid Silver records.
- Provide at least three Databricks SQL dashboard queries and visualization
  instructions.
- Provide schema/setup scripts, validation and error handling, tests, setup
  instructions, and the required lifecycle documentation.

### Out of scope

- Production deployment, orchestration, alerting, and service-level objectives.
- Streaming or near-real-time ingestion; the exercise uses daily batch files.
- Incremental change-data capture from operational systems.
- Identity resolution, master data management, or correction of source-system
  records.
- A production security model, row-level access controls, or masking policies.
- Use of real customer data or personally identifiable information.
- Gold tables other than the three explicitly defined in Section 7.

The participant guide has an inconsistent general reference to “all 4
aggregations” and includes a suggested `daily_weekly_trends` filename, but its
detailed Gold requirements, acceptance criteria, and summary specify three
aggregation tables. This specification treats those three named tables as the
authoritative Core scope.

## 3. Data Sources & Schema

All inputs are CSV files stored in S3 or DBFS. The paths must be supplied
through configuration rather than hardcoded in pipeline logic. Decimal
precision and scale are not specified by the requirements; the implementation
must choose and document them consistently in the data contract before code is
generated.

### `customers.csv`

Expected base volume: 10,000 customers; approximate size: 500 KB.

| Field | Type | Constraint or meaning |
|---|---|---|
| `customer_id` | INT | Primary key |
| `customer_name` | STRING | Customer name |
| `email` | STRING | Customer email |
| `country` | STRING | Customer country |
| `signup_date` | DATE | Signup date |
| `customer_segment` | STRING | `Premium`, `Standard`, or `Basic` |
| `lifetime_value` | DECIMAL | Source-provided lifetime value |

Exercise-required issues (from the participant guide):

- 50 rows with NULL `email` values (completeness).
- 10 rows with duplicate `customer_id` values (uniqueness).

Supplemental issues (added in this spec; see the count reconciliation below):

- 40 rows with a non-NULL but malformed `email` (format / validity).
- 20 rows with `signup_date` after the generation as-of date (validity).
- 20 rows with `customer_segment` outside `Premium` / `Standard` / `Basic`.

### `orders.csv`

Expected base volume: 100,000 orders; approximate size: 2–3 MB.

| Field | Type | Constraint or meaning |
|---|---|---|
| `order_id` | INT | Primary key |
| `customer_id` | INT | Foreign key to `customers.customer_id` |
| `order_date` | DATE | Order date |
| `product_id` | INT | Foreign key to `products.product_id` |
| `quantity` | INT | Ordered quantity |
| `unit_price` | DECIMAL | Unit selling price |
| `total_amount` | DECIMAL | Order-line total |
| `order_status` | STRING | `Pending`, `Completed`, or `Cancelled` |
| `payment_date` | DATE | Nullable |

Exercise-required issues (from the participant guide):

- 100 rows with NULL `customer_id` values (completeness).
- 200 rows with NULL `product_id` values (completeness).
- 50 rows with a `customer_id` absent from customers (referential integrity).
- 30 rows with a `product_id` absent from products (referential integrity).
- 20 rows with duplicate `order_id` values (uniqueness).

Supplemental issues (added in this spec; see the count reconciliation below):

- 50 rows with `quantity` less than or equal to zero.
- 40 rows with `unit_price` equal to zero.
- 40 rows where `total_amount` does not equal `quantity × unit_price`.
- 10 rows with `order_status` outside `Pending` / `Completed` / `Cancelled`.

### `products.csv`

Expected volume: 500 products; approximate size: 50 KB.

| Field | Type | Constraint or meaning |
|---|---|---|
| `product_id` | INT | Primary key |
| `product_name` | STRING | Product name |
| `category` | STRING | Product category |
| `price` | DECIMAL | Product selling price |
| `cost` | DECIMAL | Product cost |
| `stock_quantity` | INT | Units currently in stock |
| `reorder_level` | INT | Stock threshold for reordering |

Exercise-required issues: none. The participant guide does not inject product
defects.

Supplemental issues (added in this spec; see the count reconciliation below):

- 10 rows with `price` equal to zero.
- 10 rows with `cost` greater than `price` (negative margin).

### Issue-count reconciliation (460 specified vs ~700 referenced)

The individually specified exercise-required counts sum to **460**
issue-bearing rows if those injected sets do not overlap: 60 customer
issues and 400 order issues. The guide also states “~700 problematic rows
out of ~100,000 (0.7% — realistic data quality).” This spec keeps the
exercise-required counts unchanged and adds **240** non-overlapping
supplemental defects so the distinct problematic-row total is **700**.

| Origin | Table | Issue | Count | Silver check |
|---|---|---|---|---|
| Exercise-required | customers | NULL `email` | 50 | Completeness |
| Exercise-required | customers | Duplicate `customer_id` | 10 | Uniqueness |
| Exercise-required | orders | NULL `customer_id` | 100 | Completeness |
| Exercise-required | orders | NULL `product_id` | 200 | Completeness |
| Exercise-required | orders | Orphan `customer_id` | 50 | Referential integrity |
| Exercise-required | orders | Orphan `product_id` | 30 | Referential integrity |
| Exercise-required | orders | Duplicate `order_id` | 20 | Uniqueness |
| **Exercise-required subtotal** |  |  | **460** |  |
| Supplemental | customers | Malformed `email` | 40 | Validity (Check 4) |
| Supplemental | customers | Future `signup_date` | 20 | Validity (Check 4) |
| Supplemental | customers | Invalid `customer_segment` | 20 | Validity (Check 4) |
| Supplemental | orders | `quantity` ≤ 0 | 50 | Validity (Check 4) |
| Supplemental | orders | `unit_price` = 0 | 40 | Validity (Check 4) |
| Supplemental | orders | `total_amount` mismatch | 40 | Validity (Check 4) |
| Supplemental | orders | Invalid `order_status` | 10 | Validity (Check 4) |
| Supplemental | products | `price` = 0 | 10 | Validity (Check 4) |
| Supplemental | products | `cost` > `price` | 10 | Validity (Check 4) |
| **Supplemental subtotal** |  |  | **240** |  |
| **Target distinct problematic rows** |  |  | **700** |  |

Why these supplemental types, rather than inflating the required NULL or
orphan counts:

- **Malformed emails** exercise a format rule that NULL-email completeness
  cannot catch. A present but unusable address is a common CRM extract
  defect.
- **Future `signup_date`** is a temporal-validity defect; the guide's own
  prompt examples mention it, but it is not in the required issue list.
- **Invalid `customer_segment` / `order_status`** test allowed-value
  constraints that otherwise exist only as documentation.
- **Negative or zero quantity, zero unit price, and amount mismatch** give
  Check 4 real failures to detect, so Gold revenue is protected by something
  other than structural keys.
- **Product `price` = 0 and `cost` > `price`** put a quality signal on the
  catalog, which the exercise otherwise leaves entirely clean.

Generation rules for the gap-closing rows:

- Inject supplemental defects on rows that do **not** already carry an
  exercise-required issue, so 460 + 240 remains 700 distinct bad rows.
- Keep the two product issue sets on disjoint product IDs.
- For malformed emails, use clearly synthetic invalid values (for example
  `not-an-email`, `user@`, `user@example`). Do not invent real-looking
  personal addresses.
- Tests must assert exercise-required counts and supplemental counts
  separately, then assert that distinct affected rows equal 700.

## 4. Architecture

1. **Synthetic source generation:** Produce reproducible CSV files for the
   three source entities. Inject the exercise-required issues and the
   documented supplemental issues as two separately counted sets.
2. **Bronze:** Apply explicit schemas, append ingestion metadata, and persist
   each complete source extract unchanged as a Delta table.
3. **Silver:** Evaluate quality rules, retain every Bronze row, add quality
   flags, and publish quality metrics.
4. **Gold:** Read only Silver tables, select analytically valid records, and
   create the three required aggregations.
5. **Dashboard:** Query Gold tables with Databricks SQL and present at least
   three stakeholder visualizations.

Each layer must be implemented in separate scripts or notebooks. Gold must
never read Bronze directly.

## 5. Bronze Layer Design

Bronze contains one table for each source: `bronze_customers`,
`bronze_orders`, and `bronze_products`.

- Read configured CSV locations from S3 or DBFS.
- Use explicit schemas based on Section 3. The requirement says to handle
  schema inference and data types; explicit schemas are the judgment call for
  repeatability and to prevent inference changing between batches.
- Preserve all source columns, names, values, duplicates, and NULLs. Bronze
  performs no filtering, cleaning, deduplication, or business transformation.
- Add only operational metadata, including at minimum:
  - `ingestion_timestamp`
  - `source_file`
  - `batch_id`
- Log source name, batch ID, source row count, written row count, timestamp,
  and status. Source and written counts must match.
- Validate that a configured path exists, required headers are present, and a
  file can be read. Fail with a clear error rather than silently writing an
  incomplete table.
- Write Delta tables idempotently by `batch_id`: rerunning the same batch must
  replace or merge that batch, not duplicate it. This is necessary because
  daily jobs are commonly retried.

## 6. Silver Layer Design

Silver contains `silver_customers`, `silver_orders`, and `silver_products`.
Every Bronze row must remain represented. Failed records are flagged, never
deleted.

Each Silver table will include:

- Source fields with their declared types.
- Bronze ingestion metadata for lineage.
- One Boolean flag per applicable check, using names such as
  `completeness_passed`, `uniqueness_passed`,
  `referential_integrity_passed`, and `business_logic_passed`.
- `quality_check_result`, containing `PASS` when all applicable checks pass or
  a deterministic, delimited list of failed checks otherwise. Per-check flags
  are retained because one text result alone is difficult to aggregate and
  test.

### Check 1: Completeness

- Customers fail when `email` is NULL. A non-NULL malformed email does **not**
  fail completeness; it fails Check 4 instead, so NULL and format defects are
  not mixed.
- Orders fail when `customer_id` or `product_id` is NULL.
- Products have no critical completeness field specified by the source
  document, so completeness remains not applicable for products. Zero-price
  catalog rows fail Check 4 rather than completeness.

### Check 2: Uniqueness

- All occurrences of a duplicated `customer_id` fail in customers.
- All occurrences of a duplicated `order_id` fail in orders.
- No product duplicate issue is required by the document. Product primary-key
  uniqueness may be monitored, but it must be reported as an additional
  defensive metric rather than an intentional-issue acceptance criterion.

Flagging every member of a duplicate group is chosen over arbitrarily treating
the first row as valid, because the pipeline cannot know which source record is
authoritative.

### Check 3: Referential integrity

- A non-NULL orders `customer_id` passes only when it exists in Silver
  customers.
- A non-NULL orders `product_id` passes only when it exists in Silver products.
- NULL foreign keys fail completeness and are marked not applicable for the
  referential check, preventing one defect from being misleadingly counted as
  two distinct root causes.

Reference membership uses the parent key set from Silver. Because duplicated
parent IDs are not authoritative, an order referencing a duplicated
`customer_id` must not be treated as analytically valid even though the value
exists.

### Check 4: Validity / business logic — proposed

The three required checks are structural (NULL keys, duplicate keys, orphan
keys). The fourth check is validity: values that are present and well-keyed
but still unusable for analytics. Arithmetic was the original reason for this
check; the supplemental issues extend the same flag rather than adding a
fifth check.

**Customers** fail Check 4 when any of the following is true:

- `email` is non-NULL and does not match a simple `local@domain` pattern
  (must contain `@` and a domain with a dot; this is a learning-project
  rule, not a full RFC 5322 parser).
- `signup_date` is after the configured generation as-of date.
- `customer_segment` is not one of `Premium`, `Standard`, `Basic`.

**Orders** fail Check 4 when any of the following is true:

- `quantity` is less than or equal to zero.
- `unit_price` is less than or equal to zero.
- `total_amount` does not equal `quantity × unit_price` within the chosen
  decimal rounding precision.
- `order_status` is not one of `Pending`, `Completed`, `Cancelled`.

**Products** fail Check 4 when any of the following is true:

- `price` is less than or equal to zero.
- `cost` is greater than `price`.

A row can be complete, unique, and referentially valid while still distorting
revenue or segmentation. That is why this fourth check exists. The exact
decimal precision and comparison tolerance must match the documented DECIMAL
scale; floating-point comparison must not be used. NULL emails are
completeness failures only; format is not applicable when `email` is NULL.

### Quality metrics report

Publish one row per `batch_id`, table, check, and checked field or relationship,
including:

- `records_evaluated`
- `records_passed`
- `records_failed`
- `pass_percentage`
- `metric_timestamp`

The report must distinguish failed-check occurrences from distinct bad rows,
since one row may fail multiple checks. The guide suggests quality thresholds
of greater than 99% for completeness, 100% for uniqueness, and greater than
99.9% for referential integrity. These are reporting/alert thresholds only;
rows are still flagged based on row-level rules and are never removed from
Silver.

## 7. Gold Layer Design

Gold reads only Silver tables. It excludes rows whose applicable quality flags
do not all pass, but the rejected records remain available in Silver and in the
quality report. This keeps business metrics trustworthy without violating the
requirement to retain bad source rows.

Only `Completed` orders contribute to revenue and order metrics. The source
document does not define status handling; excluding `Pending` and `Cancelled`
orders is the judgment call because neither represents settled revenue.
`total_orders` means the count of distinct valid, completed `order_id` values,
and `avg_order_value` means `total_revenue / total_orders`.

### A. `gold_sales_by_product`

Columns specified by the requirements:

- `product_id`
- `product_name`
- `category`
- `total_orders`
- `total_revenue`
- `avg_order_value`

Group valid completed orders by their valid Silver product. Use
`orders.total_amount` for revenue after the arithmetic check passes.

### B. `gold_revenue_by_customer`

Columns specified by the requirements:

- `customer_id`
- `customer_name`
- `customer_segment`
- `total_orders`
- `total_revenue`
- `avg_order_value`
- `lifetime_value_actual`

Include every valid Silver customer, including customers with no valid
completed orders, using zero for order count and revenue. Define
`lifetime_value_actual` as cumulative valid completed-order revenue in the
available dataset. This separates calculated actual value from the
source-provided `lifetime_value` attribute.

### C. `gold_customer_segmentation`

Columns specified by the requirements:

- `segment_type` (`High-Value`, `Repeat`, `One-Time`, or `Inactive`)
- `customer_count`
- `avg_revenue`
- `total_revenue`

Assign exactly one segment to each valid customer, in this precedence order:

1. **High-Value:** `total_revenue >= 1,000`, regardless of order count.
2. **Repeat:** `total_revenue < 1,000` and `total_orders >= 2`.
3. **One-Time:** `total_orders = 1`.
4. **Inactive:** `total_orders = 0`.

The requirements do not define thresholds. A fixed currency threshold of 1,000
is selected because it is transparent, deterministic, and easy to validate in
this synthetic learning project; precedence keeps categories mutually
exclusive. The value must be a named configuration setting, not embedded
throughout SQL. Before production use, it would be replaced by a
business-approved, currency-aware threshold or a distribution-based rule
validated against real commercial behavior.

Aggregate the assigned customer rows by `segment_type`. `avg_revenue` is
average customer revenue in the segment, and `total_revenue` is the sum of
customer revenue in the segment.

## 8. Dashboard Design

Create a Databricks SQL dashboard backed only by Gold tables, with at least:

1. **Top 10 products by revenue — bar chart**
   - Source: `gold_sales_by_product`.
   - Sort by `total_revenue` descending and limit to 10.
   - Product name is the category axis; total revenue is the value axis.
2. **Customer revenue distribution — histogram**
   - Source: `gold_revenue_by_customer`.
   - Plot customer counts over revenue bins using `total_revenue`.
   - Include zero-revenue customers so inactivity remains visible.
3. **Customer segmentation — pie chart**
   - Source: `gold_customer_segmentation`.
   - Segment by `segment_type` and size by `customer_count`.

Add filters for customer segment and product category where the selected
visualization's Gold source contains those dimensions. A date filter is not
included because none of the required Gold schemas contains a date field;
adding one would require an out-of-scope trend aggregation.

## 9. Testing Strategy

### Data-generation tests

- Assert the configured base volumes are generated.
- Assert each schema, type, allowed categorical value, and nullable field
  matches Section 3.
- Assert the exercise-required issue counts separately from supplemental
  counts: 50 NULL emails, 10 duplicated customer IDs, 100 NULL order customer
  IDs, 200 NULL order product IDs, 50 orphan customer IDs, 30 orphan product
  IDs, and 20 duplicated order IDs.
- Assert the supplemental counts: 40 malformed emails, 20 future signup
  dates, 20 invalid customer segments, 50 non-positive quantities, 40
  zero unit prices, 40 amount mismatches, 10 invalid order statuses, 10
  zero product prices, and 10 `cost` > `price` rows.
- Assert the two origin sets do not overlap, and that distinct affected rows
  equal 700.
- Use a fixed random seed so failures are reproducible.

### Bronze tests

- Assert source and Bronze row counts match for every batch.
- Assert source fields and values are unchanged after type parsing.
- Assert ingestion metadata is populated.
- Rerun the same `batch_id` and assert no duplicate batch rows are created.
- Test missing files, malformed headers, and type-conversion failures.

### Silver tests

- Unit-test each quality rule with passing, failing, NULL, duplicate, and
  boundary cases.
- Assert all duplicate-group members are flagged.
- Assert NULL foreign keys are completeness failures and are not double-counted
  as orphan failures.
- Assert all exercise-required defects and all supplemental defects are
  detected at their exact expected counts, reported as two separate tallies.
- Assert Silver row counts equal Bronze row counts.
- Assert no failed rows are dropped and `quality_check_result` agrees with the
  Boolean flags.
- Test arithmetic values exactly on and just outside the configured decimal
  tolerance.
- Reconcile quality-report counts and percentages to Silver flags.

### Gold tests

- Use a small hand-calculated fixture to verify sums, distinct counts,
  averages, left joins, and zero-order customers.
- Assert no Gold calculation reads Bronze.
- Assert invalid, pending, and cancelled orders do not affect revenue.
- Assert Gold revenue reconciles between product, customer, and segmentation
  totals.
- Test segmentation at 0 orders, 1 order, 2 orders, revenue 999.99, and revenue
  1,000, ensuring every valid customer belongs to exactly one segment.

### End-to-end and dashboard validation

- Run generation through Gold for a fixed batch and reconcile row counts at
  each boundary.
- Run the same batch twice and verify stable results.
- Execute all dashboard SQL queries successfully.
- Verify the top-10 ordering, histogram inclusion of zero-revenue customers,
  pie totals, filters, labels, and currency formatting.

## 10. Non-Functional Notes

- **Synthetic data only:** Do not use real customer PII. Generated names and
  emails must be clearly synthetic; reserved domains such as `example.com`
  should be used for emails.
- **Idempotency:** Every layer must be safely rerunnable by `batch_id`.
  Reprocessing a batch must not duplicate rows or inflate metrics.
- **Documented transformations:** Each function requires an intent-focused
  docstring. Comments must explain why a quality rule exists, especially where
  it corresponds to an intentional source issue. Business definitions,
  assumptions, and configurable thresholds must be documented alongside the
  implementation.
- **Traceability:** Preserve `batch_id`, source-file lineage, and ingestion
  timestamps through Silver; quality metrics must be attributable to a batch.
- **Configuration:** Paths, catalog/schema names, decimal definitions, batch
  IDs, and the High-Value threshold must be configured at the top level rather
  than hardcoded in transformation logic.
- **Maintainability:** Use readable Python/PySpark for full datasets and
  formatted SQL for aggregations and dashboard queries. Keep Bronze, Silver,
  Gold, and dashboard logic in separate files.
- **Error handling:** Validate inputs and fail with actionable messages. Never
  silently skip an unreadable source, schema mismatch, or failed write.

