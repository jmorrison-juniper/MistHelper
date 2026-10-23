# Quickstart: Validate Mist Token Conflict Handling

## Prerequisites

- Use the repository virtual environment created by `python3 scripts/bootstrap_worktree.py`.
- Keep Mist API credentials unset. These tests use local fake values and make no Mist API request.

## Run the Focused Tests

```bash
.venv/bin/python -m pytest tests/unit/test_credential_preflight.py
```

Expected result: all tests pass, including conflict refusal, equal values, either variable alone, delimiter-only canonical input, login mode, secret redaction, and refusal before organization or session construction.

## Run Quality Checks

```bash
.venv/bin/python -m py_compile MistHelper.py
.venv/bin/ruff check MistHelper.py tests/unit/test_credential_preflight.py
.venv/bin/black --check MistHelper.py tests/unit/test_credential_preflight.py
.venv/bin/symbol-diff --base origin/main MistHelper.py
```

Expected result: each command exits with status zero. The symbol check reports no module-level name change.

After committing the test update, run the test-quality preflight and the required changed-from ratchet documented in `AGENTS.md`.
