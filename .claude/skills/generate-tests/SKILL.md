---
name: generate-tests
description: Generate unit tests for newly written Python functions and modules in this project.
---
1. Read the target file(s) to understand all public functions, classes, and their signatures.
2. Identify the test file location: `tests/test_<module_name>.py`. Create it if it does not exist.
3. For each function, generate a `pytest` test case covering:
   - The happy path with realistic inputs.
   - Edge cases (empty inputs, None, boundary values).
   - Error paths (expected exceptions).
4. For Airflow DAGs: test DAG structure (task count, dependencies) separately from task callable logic.
5. For Neo4j queries: mock the driver using `unittest.mock.MagicMock` — never use the real database.
6. For LLM extraction functions: mock `ChatOllama` / `with_structured_output` responses.
7. Run `pytest <new_test_file> -v` to verify all generated tests pass before finishing.
