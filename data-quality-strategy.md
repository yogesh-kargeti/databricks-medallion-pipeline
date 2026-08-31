# Data Quality Strategy

Silver flags quality failures and keeps every Bronze row. Gold reads only
rows whose applicable checks pass. Thresholds below are reporting/alert
targets from the participant guide (or proposed for Check 4). They never
cause Silver to drop rows.

Counting rules used everywhere:

- One row may fail more than one check. Metrics report both failed-check
  occurrences and distinct bad rows.
- NULL foreign keys fail completeness only. Referential integrity is not
  applicable on those rows.
- Every member of a duplicate key group fails uniqueness.
- An order whose parent key exists only as a duplicated parent ID is not
  referentially valid for analytics.
- Completeness and validity stay separate: NULL `email` is completeness;
  a present but malformed email is Check 4.

## Quality Checks Overview

### 1. Completeness Check

- **What:** Critical fields are populated. Missing values in those fields
  make the row unusable for contact or joins.
- **How:**
  - Customers: `email` IS NULL.
  - Orders: `customer_id` IS NULL OR `product_id` IS NULL.
  - Products: not applicable (the source document names no required
    product field for this check). Zero `price` is Check 4, not
    completeness.
- **Threshold:** >99% complete (participant guide).
- **Result:** Set `completeness_passed = false` and append `completeness`
  to `quality_check_result`. Do not delete the row.

Expected exercise-required failures if issue sets do not overlap: 50
customer rows (NULL email) and 300 order rows (100 NULL `customer_id` +
200 NULL `product_id`).

### 2. Uniqueness Check

- **What:** Business keys are unique. Duplicate IDs make it impossible to
  treat a parent or order as a single entity.
- **How:**
  - Customers: `customer_id` appears more than once. Flag every row in the
    group.
  - Orders: `order_id` appears more than once. Flag every row in the
    group.
  - Products: optional defensive count only; not an acceptance criterion
    (no product duplicates are seeded).
- **Threshold:** 100% unique (participant guide).
- **Result:** Set `uniqueness_passed = false` and append `uniqueness` to
  `quality_check_result`. Do not pick a “winning” duplicate.

Expected exercise-required failures: 10 customer rows with duplicate
`customer_id`, 20 order rows with duplicate `order_id`.

### 3. Referential Integrity

- **What:** Non-NULL order foreign keys exist on an authoritative parent
  key. Orphans break customer and product aggregations.
- **How:**
  - Orders `customer_id` (when not NULL) must exist on Silver customers
    with a unique `customer_id`.
  - Orders `product_id` (when not NULL) must exist on Silver products with
    a unique `product_id`.
  - NULL FKs: mark referential integrity as not applicable; completeness
    already failed.
- **Threshold:** >99.9% valid (participant guide).
- **Result:** Set `referential_integrity_passed = false` and append
  `referential_integrity` to `quality_check_result`.

Expected exercise-required failures: 50 orders with orphan `customer_id`,
30 orders with orphan `product_id`.

### 4. Validity / Business Logic Check (proposed)

- **What:** Values that are present and well-keyed can still be unusable
  for analytics (bad email format, future dates, illegal enums, non-positive
  quantity or price, amount not equal to quantity × unit price, zero catalog
  price, cost above price). This is the fourth check required by the
  exercise; the participant guide specified only the first three.
- **How:** Fail Check 4 when any applicable rule is true.

  Customers:

  - `email` is non-NULL and does not match a simple `local@domain`
    pattern (`@` plus a domain containing a `.`). Not RFC 5322.
  - `signup_date` is after the configured generation as-of date.
  - `customer_segment` is not one of `Premium`, `Standard`, `Basic`.

  Orders:

  - `quantity` <= 0.
  - `unit_price` <= 0.
  - `total_amount` ≠ `quantity × unit_price` at DECIMAL(12,2).
  - `order_status` is not one of `Pending`, `Completed`, `Cancelled`.

  Products:

  - `price` <= 0.
  - `cost` > `price`.

  NULL `email` does not fail this check (completeness only).
- **Threshold:** >99% of evaluated rows pass (proposed). The guide does
  not give a validity threshold. 99% matches completeness and still
  leaves room for the 240 seeded validity defects (~0.22% of all rows
  across the three tables). Like the other thresholds, this is a report
  target only.
- **Result:** Set `business_logic_passed = false` and append
  `business_logic` to `quality_check_result`.

Expected supplemental failures if those sets do not overlap: 80
customer rows, 140 order rows, 20 product rows.

## Quality Metrics Report

Publish one metrics row per `batch_id`, table, check, and checked field
or relationship:

| Column | Meaning |
|---|---|
| `batch_id` | Ingestion batch |
| `table_name` | `customers` / `orders` / `products` |
| `check_name` | `completeness` / `uniqueness` / `referential_integrity` / `business_logic` |
| `check_target` | Field or relationship (for example `email`, `orders.customer_id`) |
| `records_evaluated` | Rows where the check applies (exclude N/A) |
| `records_passed` | Rows that passed |
| `records_failed` | Rows that failed |
| `pass_percentage` | `100.0 * records_passed / records_evaluated` |
| `metric_timestamp` | When the metric was computed |
| `threshold_pct` | Reporting target for that check |
| `threshold_met` | Whether `pass_percentage` meets the target |

Also publish a batch-level distinct-bad-row count. Target after seeding:
**700** distinct problematic rows (460 exercise-required + 240
supplemental, non-overlapping).

`quality_check_result` on each Silver row:

- `PASS` when every applicable check passed.
- Otherwise a deterministic, delimited list of failed check names (same
  order every time: completeness, uniqueness, referential_integrity,
  business_logic).

## Sample Data Quality Issues

Injected in the generator. Exercise-required counts come from the
participant guide. Supplemental issues were added in `spec.md` so the
distinct bad-row total matches the guide’s “~700” reference. Supplemental
rows must not already carry an exercise-required issue. Product price=0
and cost>price use disjoint product IDs.

### Exercise-required (460)

| Table | Issue | Count | Check |
|---|---|---|---|
| customers | NULL `email` | 50 | Completeness |
| customers | Duplicate `customer_id` | 10 | Uniqueness |
| orders | NULL `customer_id` | 100 | Completeness |
| orders | NULL `product_id` | 200 | Completeness |
| orders | `customer_id` not in customers | 50 | Referential integrity |
| orders | `product_id` not in products | 30 | Referential integrity |
| orders | Duplicate `order_id` | 20 | Uniqueness |
| **Subtotal** |  | **460** |  |

### Supplemental (240)

| Table | Issue | Count | Check |
|---|---|---|---|
| customers | Malformed non-NULL `email` | 40 | Validity |
| customers | `signup_date` after as-of date | 20 | Validity |
| customers | Invalid `customer_segment` | 20 | Validity |
| orders | `quantity` <= 0 | 50 | Validity |
| orders | `unit_price` = 0 | 40 | Validity |
| orders | `total_amount` ≠ quantity × unit_price | 40 | Validity |
| orders | Invalid `order_status` | 10 | Validity |
| products | `price` = 0 | 10 | Validity |
| products | `cost` > `price` | 10 | Validity |
| **Subtotal** |  | **240** |  |

### Combined target

| Origin | Distinct problematic rows |
|---|---|
| Exercise-required | 460 |
| Supplemental | 240 |
| **Total** | **700** |

Malformed emails use clearly synthetic invalid values (for example
`not-an-email`, `user@`, `user@example`). Tests must assert the two origin
tallies separately, then assert distinct affected rows equal 700.
