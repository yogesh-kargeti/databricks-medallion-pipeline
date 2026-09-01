# Tool Workflow — AI Workflow Foundation

## Primary AI Tool Used
Cursor, for the whole build (planning docs, code, SQL, debugging).

## How I Provide Project Context to the Tool
- `.cursorrules` at the repo root — persistent, read automatically by
  Cursor on every prompt in the workspace. Contains architecture rules
  (Bronze = raw only, Silver flags don't delete, Gold reads Silver only),
  coding standards, and a no-real-PII rule.
- `spec.md` — the design document, referenced directly (`@spec.md`) when
  prompting for anything that needed the agreed design, rather than
  re-explaining requirements each time.
- `data-model.md` and `data-quality-strategy.md` — referenced the same way
  for schema and quality-check details once those documents were locked in.

## How I Use AI for Requirement Analysis
Had Cursor act as a assisting agent and read the actual exercise requirements document directly and
draft `requirements-analysis.md` from it, rather than pre-summarizing the
requirements into the prompt myself.

## How I Use AI for Pipeline Design (Medallion Architecture)
Built `spec.md` iteratively — schema first, then architecture, then each
layer's design — rather than one large one-shot prompt, so I could react
to and correct specific sections instead of accepting a complete answer.

## How I Use AI for Code Generation (Python/PySpark/SQL)
Established a reviewed pattern on the first file of each layer, then
reused that pattern with lighter prompts for the remaining files in the
same layer. This kept review effort concentrated on genuine
design decisions rather than spread evenly across repetitive files.

## How I Validate AI-Generated Code and Logic
Every layer was first validated by me and then run live on Databricks (not just read as code) and its
output cross-checked against exact expected values documented.

## How I Use AI for Testing and Validation
Had Cursor build an automated test that hardcodes all expected quality-check failure counts and asserts
them against the live Silver metrics table, turning manual SQL
verification into something repeatable.

## How I Use AI for Debugging (Issues, Root Causes)
Gave Cursor the actual error text and asked it to explain root cause
before proposing a fix, rather than asking it to just fix it.

## How I Use AI for Data Quality Checks
Had Cursor create the quality check with explicit reasoning, then reviewed and
 rather than accepting a default silently.