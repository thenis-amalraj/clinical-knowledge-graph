---
paths: ["api/**/*.py", "dags/**/*.py", "extraction/**/*.py"]
---

# Backend Conventions & Guardrails

- **Neo4j Transactions:** Never use string concatenation or f-strings for Cypher queries. Always pass parameters via dictionary to prevent injection.
- **Race Condition Prevention:** When writing concurrent batch ingestion functions, always separate your `MATCH` lock logic from your `MERGE` logic.
- **Airflow Idempotency:** Do not parse XML payloads directly into the database. Always stage data locally (JSON Lines) between extraction and load steps.
- **XML Parsing:** Use `xml.etree.ElementTree` with `XPath` to handle missing MEDLINE tags safely without raising `AttributeError`.
- **LangChain:** Force `temperature=0.0` on local Ollama models to ensure deterministic output for Pydantic parsers.
