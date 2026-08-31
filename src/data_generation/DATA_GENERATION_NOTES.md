# Data Generation Notes

How `generate_sample_data.py` builds the CSVs and why each seeded defect
exists. Counts live in `data-quality-strategy.md`.

## Output

| File | Rows |
|---|---|
| `data/customers.csv` | 10,000 |
| `data/orders.csv` | 100,000 |
| `data/products.csv` | 500 |

Schemas follow `data-model.md`. Names and emails are synthetic
(`example.com`). Money is written with two decimals (DECIMAL(12,2)).

```
python src/data_generation/generate_sample_data.py
```

The script checks every seeded count and the 700 distinct-bad-row
target before writing. The same seed produces byte-identical files.

## How generation works

**Clean rows first.** Products, customers, then orders are created as
valid records. Orders join only to clean, unique parent IDs so later
orphans cannot accidentally match a duplicated parent. `payment_date` is
filled for Completed orders and left empty otherwise (allowed, not a
quality failure).

**Faker and seed.** Default seed is `20260831` (`--seed` to override).
`random.Random(seed)` drives dates, amounts, categories, status
weights, and defect indices. `Faker.seed_instance(seed)` drives names and
email local-parts. Both must be seeded or runs will diverge. As-of date
is `2026-08-31`; clean dates never go past it.

**Disjoint indices.** `reserve_disjoint_indices` shuffles `0..n-1` once
per table and slices blocks of the requested sizes so each issue lands on
a different row. That keeps distinct bad rows at 700, keeps NULL email
separate from malformed email, and keeps product `price = 0` off
`cost > price`. Mutations isolate one failure (zero `unit_price` also
zeros `total_amount` so the row is not also an amount mismatch).

**Duplicates without extra volume.** Ten customer uniqueness rows and
20 order uniqueness rows are five and ten ID pairs, not extra CSV
lines. Table sizes stay 10k / 100k / 500. Every member of a pair fails
uniqueness.

## Why each issue exists

**Completeness.** NULL `email` (50) proves the check fires on absence,
not format. NULL order `customer_id` (100) and NULL `product_id` (200)
are the critical-field cases; RI is not applicable on NULLs.

**Uniqueness.** Duplicate `customer_id` (10) and `order_id` (20) exist
because Silver flags every member of a key group rather than picking a
winner.

**Referential integrity.** Orphan `customer_id` (50) and `product_id`
(30) are non-NULL keys outside the generated parent ranges, so they fail
“parent unique key exists,” not completeness.

**Validity (Check 4, supplemental).** Malformed email (40) is present
but fails `local@domain`, which completeness cannot catch. Future
`signup_date` (20) is after as-of. Invalid `customer_segment` (20) and
`order_status` (10) test allowed-value lists. `quantity` ≤ 0 (50) and
`unit_price` = 0 (40) would distort Gold if treated as valid. Amount ≠
qty × price (40) is arithmetic drift at DECIMAL(12,2). Product `price`
= 0 (10) and `cost` > `price` (10) put Check 4 on a catalog the guide
left clean.

## Accounting

140 customers + 540 orders + 20 products = **700** distinct rows (460
exercise-required + 240 supplemental). Silver rules and thresholds stay
in `data-quality-strategy.md`.
