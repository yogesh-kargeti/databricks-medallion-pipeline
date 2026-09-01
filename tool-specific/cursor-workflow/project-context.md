# Project Context — How I Set Up Cursor

## Persistent Context
I maintained persistent context by keeping the key project guidelines, design decisions, and data definitions in shared project documents. These references helped the AI agent consistently follow the agreed architecture, schemas, and quality rules without having to repeat the same instructions in every prompt. This also helped maintain consistency across different stages of the pipeline.


## How I Re-Established Context Across Sessions
I kept the AI agent focused by providing the relevant context for each task instead of relying on previous conversation history. For each stage, I referred to the appropriate design or requirements document and, when troubleshooting, shared the specific error and related code or file. This made the responses more focused and reduced unnecessary context.

## What I Deliberately Did Not Share
No real customer data, credentials, or internal system details were ever
included in any prompt — all sample data is synthetic and generated
locally with Faker.
