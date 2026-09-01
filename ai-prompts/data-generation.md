# AI Prompts — Data Generation

## Prompt: Sample data generator

**PROMPT SENT:**
can you write generate_sample_data.py
based on data-model.md and data-quality-strategy.md — needs to produce
customers.csv, orders.csv, products.csv at the specified volumes. The script should generate realistic 
sample data in the required structure and volume, while ensuring the output is reproducible 
and suitable for testing.

**RESPONSE SUMMARY:**
The data generation process creates clean records first and then introduces 
the required data quality issues in a controlled way. It also validates the expected issue counts before 
generating the final output.

**EVALUATION:**
The approach was evaluated by running the process and verifying that the expected 
quality issues were generated correctly. The generated data was also reviewed to ensure it matched 
the defined schema and requirements. Additional manual checks were performed to confirm the accuracy 
of the values and the relationships, between fields.

**DECISION:**
Accepted after validation and successful execution.