---
paths: ["**/tests/**", "**/*.test.py", "**/*_test.py", "**/*test_*.py"]
---

# Test Conventions & Guardrails

- **Idempotency:** Every test must be independently runnable. Do not share mutable state between tests.
- **Neo4j:** Use a dedicated test database or mock the driver at the session level. Never run tests against the production Neo4j instance.
- **Airflow DAGs:** Test DAG structure separately from task logic. Use `dag.test()` for full integration tests; use unit tests for individual PythonOperator callables.
- **LLM Extraction:** Mock Ollama responses in unit tests using `unittest.mock.patch`. Reserve real model calls for manual integration tests only.
- **Fixtures:** Use `pytest` fixtures for database connections and shared test data. Scope connection fixtures to `session` and data fixtures to `function`.
