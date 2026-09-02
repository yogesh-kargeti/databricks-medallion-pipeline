# Final AI Usage Summary

Cursor was the primary AI tool for this project, used across every
stage — planning, code, SQL, debugging, and documentation.

## Prompt History by Activity

| File | Covers |
|---|---|
| `ai-prompts/data-generation.md` | Sample data generator |
| `ai-prompts/bronze-layer.md` | Ingestion scripts, `%run`/notebook fixes |
| `ai-prompts/silver-layer.md` | Quality checks, the architecture correction |
| `ai-prompts/gold-layer.md` | Aggregations, the segmentation threshold fix |
| `ai-prompts/dashboard.md` | Dashboard queries and tile build |

## Genuine Corrections Made (not just accepted output)

- Silver: redesigned from per-check Bronze→Silver writes (would have
  overwritten earlier checks' flags) to a single-writer pattern —
  `ai-prompts/silver-layer.md`.
- Gold: rejected an unjustified flat `$1,000` segmentation threshold
  after it put 99.6% of customers in one segment; replaced with a
  dynamic `PERCENTILE_APPROX`-based cutoff — `ai-prompts/gold-layer.md`.
- Caught and documented an inconsistency in the exercise's own
  requirements doc (460 vs. "~700" issue counts) rather than silently
  resolving it — `spec.md`.

## Validation

Every layer was run live on Databricks and checked against exact
expected values in `data-quality-strategy.md`. Environment issues found and fixed using AI debugging.

## What AI Was Not Used For

No real customer PII at any point (synthetic data only, `example.com`
emails). Git credential/account issues were resolved manually.
`reflection.md` and `candidate-info.md` reflect actual personal
experience, not AI-generated narrative.
