# AI Prompts — Gold Layer

### Prompt 1: Sales by product

**PROMPT SENT:**
Create the product-level sales analysis based on the project specification. Use the relevant Silver tables and calculate the required order and revenue metrics by product.

**RESPONSE SUMMARY:**
The query followed the expected filtering and aggregation logic and used the correct Silver tables.

**EVALUATION:**
The logic was accepted after review.

### Prompt 2: Customer revenue and segmentation

**PROMPT SENT:**
Create the customer revenue and segmentation queries based on the project specification. Follow the above mentioned pattern for first file. Also create a file to run for the Gold tables with appropriate idempotency.

**RESPONSE SUMMARY:**
The implementation was correct and accepted.

**EVALUATION — SEGMENTATION THRESHOLD ISSUE:**
The first version applied a $1,000 "High‑Value" cutoff. When I looked at the segment counts 99.6% of customers fell into the High‑Value group. That followed the rule. The approach was not useful, for segmentation. I asked Cursor to examine the distribution of customer revenue and suggest a threshold that would create a meaningful spread instead of a flat guess.

**RESULT:** The revised threshold produced a spread across all four segments—Inactive, One‑Time, Repeat, High‑Value. This matched the shape of the data. On average customers placed ten orders so most of them fall into the Repeat segment.

**DECISION:** I accepted the revised threshold after reviewing the distribution not merely the final counts.
