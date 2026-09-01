# AI Prompts — Bronze Layer

### Prompt 1: Initial customer ingestion script

**PROMPT SENT:**
Create `01_ingest_customers.py` in `src/bronze/`. It should read the customer data 
according to `data-model.md`, write it as a Delta table, add the required ingestion 
metadata, track source and output row counts, and support idempotent processing.

**RESPONSE SUMMARY:**
The script used an explicit schema, included batch-based idempotency, validated the input before processing, and checked that the source and written row counts matched.

**EVALUATION:**
The idempotency logic and schema were verified against the requirements. The row-count validation was also confirmed to work as an actual check.

**DECISION:**
Accepted


### Prompt 2: Orders and products scripts

**PROMPT SENT:**
Use the same established pattern as `01_ingest_customers.py` to create the ingestion scripts for orders and products, following the schemas defined in `data-model.md`.

**RESULT:**
Both scripts followed the established pattern and matched the required schemas. They were reviewed and accepted without changes.

### Prompt 3: Final script

**PROMPT SENT:**
write ingest_all.py that calls all three ingestion scripts in sequence.

**RESULT:**
The initial approach relied on `__file__`, which could cause issues in the Databricks environment. This was identified before testing, and the approach was changed to use a more Databricks-native method. The related ingestion scripts were updated accordingly.