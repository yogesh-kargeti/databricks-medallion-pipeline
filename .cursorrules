# Cursor Rules — Databricks Medallion Sales Pipeline

You are assisting on a Databricks medallion architecture pipeline
(Bronze → Silver → Gold → Dashboard) for e-commerce sales data. Follow these
rules for every suggestion:

## Project Context
- Full spec lives in `spec.md` — read it before generating pipeline code.
- Data model: customers, orders, products (see `data-model.md`).
- This is a learning/demo project with synthetic data only — never generate
  or suggest real customer PII, and flag it if a prompt seems to be asking
  for it.

## Architecture Rules
- Bronze layer: raw ingestion only. No filtering, no cleaning, no dropped
  rows, no renamed columns. Just schema application + ingestion metadata.
- Silver layer: quality issues are FLAGGED, never deleted. Always add/update
  a `quality_check_result` column rather than filtering rows out.
- Gold layer: aggregations only read from Silver, never from Bronze directly.
- Keep layers in separate scripts/notebooks — don't collapse Bronze+Silver
  logic into one file.

## Code Standards
- Python/PySpark, not pandas, for anything operating on the full datasets
  (10K–100K+ rows).
- Every function needs a docstring explaining intent, not just parameters.
- Inline comments should explain *why* a quality check or transformation
  exists, especially when it maps to one of the intentional data issues.
- No hardcoded file paths — use variables/config at the top of each script.
- SQL files should be formatted with uppercase keywords and one clause per
  line for readability.

## When Generating Code
- If a request is ambiguous about schema or business logic, ask a clarifying
  question instead of guessing silently.
- Prefer explicit, verbose code over clever one-liners — this is meant to be
  readable by other engineers, not just functional.
- Always suggest how the output should be tested/validated, not just the
  implementation.

## When Debugging
- Ask for the actual error message/stack trace before proposing a fix.
- Explain the likely root cause, not just the patch.
- Don't silently change unrelated code while fixing a bug.

## What NOT to do
- Don't generate mock/fake data that resembles real people (use faker-style
  clearly-synthetic data only).
- Don't suggest deleting bad rows in Silver — flag them instead.
- Don't skip logging/metadata steps in Bronze ingestion "for simplicity."
