# Validation: Traceback log redaction

## Environment

If the worktree has no environment, restore the locked dependencies without the credential-changing bootstrap:

```bash
uv sync --locked --extra dev
```

## Focused Regression

```bash
.venv/bin/python -m pytest -q tests/unit/test_logger_utils.py tests/unit/upgrade_portal/test_logging_contract.py
```

Before the source repair, the new traceback cases must fail.
After the repair, all cases must pass.
Use synthetic values and in-memory streams only.

## File Gates

Run compile, Ruff, Black, mypy, Bandit, complexity, docstring, and symbol checks on the owned files.
Run the test-quality preflight and committed-difference check before any future publication.
Record exact commands and results in `../analysis.md`.

## Publication Hold

Commit locally with `Refs #4704` and the required author trailer.
Do not push, create a PR, rebase, merge, or change credentials.
