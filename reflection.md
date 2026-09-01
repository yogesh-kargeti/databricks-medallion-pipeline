# Reflection

## What I Built

A Databricks medallion pipeline (Bronze → Silver → Gold → Dashboard) for
e-commerce sales data using Cursor as the main AI tool. The pipeline
loads raw data into Bronze, applies quality checks in Silver, and
creates three Gold aggregation tables feeding a dashboard.

## How I Used AI (Across the Lifecycle)

I used Cursor throughout the project. For planning, I worked back and
forth with Cursor to create the documents and reviewed its suggestions
carefully. For implementation, I created and reviewed each layer, and
also used a pattern for creating similar files with simpler prompts.
This helped maintain quality while saving time and reducing Cursor
usage.

## What AI Helped With Most

- Setting up the Bronze, Silver, and Gold layers.
- Creating validation checks for sample data to catch issues early
  before they moved downstream.
- Troubleshooting environment-specific issues, identifying the root
  cause, and adjusting the approach.
- Identifying and raising inconsistencies in the requirements instead
  of making assumptions or silently changing them.

## What AI Got Wrong

AI made a few incorrect assumptions during the implementation. Some of
the initial designs could have caused validation results to be
overwritten, and some checks were marked as passed even when they were
not applicable. It also suggested a segmentation rule that was
technically valid but not meaningful for the actual data, and made
assumptions about the target environment. I reviewed these outputs,
identified the issues, and adjusted the implementation accordingly.

## How I Validated AI Output

I validated the AI-generated work by running it in the actual
Databricks environment and comparing the results with the expected
outcomes. I also checked the data quality results against the
predefined test cases and used automated tests to verify the key
metrics. This helped ensure the implementation worked correctly in
practice rather than relying only on code review or AI-generated
output.

## What I Would Improve Next

I would improve the process by spending more time upfront defining the
expected design, business rules, and validation criteria before asking
the AI agent to implement them. I would also break the work into
smaller stages and validate each stage before moving to the next. This
would make it easier to catch incorrect assumptions early and reduce
the need for rework later.

## Reusable Workflow

The most effective workflow was to establish and review a clear pattern
for each stage, then apply it consistently across the rest of the
pipeline. I focused deeper review on important design and business
decisions rather than reviewing every part in the same way. Running and
validating the pipeline with real data in the target environment also
helped catch issues that would not have been obvious from reviewing the
code alone.
