# AI Prompts — Silver Layer

## Prompt 1: Completeness check (first draft — had an architecture flaw)

**PROMPT SENT:**
"ok let's start silver. write 01_quality_completeness.py based on
data-quality-strategy.md check 1"

**AI RESPONSE SUMMARY:**
Cursor generated a script that read Bronze, flagged completeness, and
wrote directly to silver_customers/silver_orders — a full read-Bronze,
write-Silver cycle in one script.

**EVALUATION — CAUGHT BEFORE BUILDING FURTHER:**
✗ Architecture flaw identified before writing the other 3 check scripts:
  if uniqueness, referential integrity, and business logic each followed
  the same "read Bronze, write Silver" pattern independently, each would
  overwrite the previous check's flag column. The design in
  data-quality-strategy.md requires one Silver row carrying all four
  check results plus a combined quality_check_result — the current
  pattern couldn't produce that.

**FOLLOW-UP PROMPT:**
Asked Cursor to propose a fix before building the remaining checks:
"...how should this actually work — should each check script read from
silver (not bronze) and add its column via merge, should
create_silver_tables.py be the only thing that writes silver, or
something else? propose an approach before I build the other three checks"

**AI PROPOSAL:**
Check scripts become pure flag functions (DataFrame in, DataFrame out,
no persistence). create_silver_tables.py becomes the single writer:
reads Bronze once per entity, applies all four flags in order
(completeness → uniqueness → referential integrity → business logic, in
that order so RI can rely on uniqueness-passing parent keys), builds
quality_check_result, writes Silver once, idempotent by batch_id.

**DECISION:** Accepted the redesign. Rejected the "each check reads
Silver and merges" alternative Cursor also offered, since Delta MERGE
operates on rows, not columns — would have required overwriting the
table 4 times with a strict run order for no benefit over the chosen
approach.

**PUSHBACK — products completeness_passed:**
Cursor's first implementation defaulted non-applicable checks
(completeness_passed for products, referential_integrity_passed for
customers/products) to lit(True). Flagged this as misleading — querying
silver_products directly would show completeness_passed=true for a check
that was never evaluated, and would silently inflate a future quality
metrics report's pass rate for that check.

**CORRECTED PROMPT:**
"...change these to lit(None) (nullable boolean) instead of lit(True)...
update add_quality_check_result if needed so NULL flags are correctly
excluded from the failure list (not treated as failing ~NULL)"

**RESULT:** Cursor switched to lit(None).cast("boolean") and changed the
failure-detection logic from `~col(flag)` to `col(flag).eqNullSafe(False)`
— correctly distinguishes NULL (not applicable, excluded), True (passed,
excluded), and False (failed, included).

## Prompt 2: Remaining check scripts (uniqueness, referential integrity,
business logic)

Built as pure flag functions from the start, following the corrected
architecture — no repeat of the overwrite bug.

## Validation — Databricks run

Ran create_silver_tables.py on Databricks Free Edition (Serverless).
Row counts preserved exactly across all four chained checks:
customers 10000->10000, orders 100000->100000, products 500->500 — no
rows dropped or duplicated.

Queried quality_check_result distribution and compared against seeded
issue counts in data-quality-strategy.md:

**silver_customers:** PASS=9860, business_logic=80, completeness=50,
uniqueness=10 — exact match (50 NULL email, 10 duplicate customer_id,
80 supplemental validity issues).

**silver_orders:** PASS=99460, completeness=300, business_logic=140,
referential_integrity=80, uniqueness=20 — exact match (300 = 100 NULL
customer_id + 200 NULL product_id; 140 = 50+40+40+10 business logic
issues; 80 = 50+30 orphan FKs; 20 duplicate order_id).

No combined-failure rows in either table, confirming the generator's
disjoint-index design (each seeded defect isolated to one row) worked
correctly end-to-end from generation through Bronze into Silver.