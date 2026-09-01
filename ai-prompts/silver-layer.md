# AI Prompts — Silver Layer

## Prompt 1: Completeness check (first draft had an architecture flaw)

**PROMPT SENT:** "let's start silver. write
01_quality_completeness.py based on data-quality-strategy.md"

**AI RESPONSE SUMMARY:** The initial approach read from Bronze and wrote directly to Silver within the individual check script.

**EVALUATION — CAUGHT BEFORE BUILDING FURTHER:**
This approach was identified as a design issue because the remaining quality checks could overwrite results from earlier checks. Since all quality results need to exist together in the same Silver record, a single-writer approach was more appropriate.

**FOLLOW-UP PROMPT:** Asked Cursor to propose a fix before building the
other three checks.

**DECISION:** The revised design was accepted. I also reviewed how non-applicable checks were represented and changed them from being marked as passed to being treated as NULL, so they would not be incorrectly considered evaluated.

## Prompt 2: Remaining check scripts

**PROMPT SENT:** "Implement the remaining data quality checks using the established approach. Keep each check focused on 
generating its validation result, and follow the existing project structure and requirements. 
Make sure the individual results are combined correctly in the final Silver output."