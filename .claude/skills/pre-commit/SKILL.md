---
name: pre-commit
description: Run related tests and type checks for changed files before committing. Invoke this before every git commit.
disable-model-invocation: true
---
1. Run `git diff --name-only HEAD` to identify changed Python files.
2. For each changed file, run `ruff check <file>` — fix any lint errors before continuing.
3. Run `mypy <changed_files>` for type checking — do not commit if there are type errors.
4. Identify test files related to the changed modules (same name with `test_` prefix or in the `tests/` directory).
5. Run `pytest <related_test_files> -v` — do not commit if any tests fail.
6. Report: files checked, lint status, type check status, test results.
