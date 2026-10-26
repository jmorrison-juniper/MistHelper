# Quickstart: Sign-in Credential Layout

## Prerequisites

- Build the worktree environment with `python3 scripts/bootstrap_worktree.py`.
- Activate the environment with `source .venv/bin/activate`.
- Ensure the Chromium browser is available through the project test setup.

## Validation

Run the sign-in browser tests:

```sh
python -m pytest tests/e2e/upgrade_portal/test_signin.py
```

The tests must confirm that the token label appears above its field, keyboard selection exposes and focuses the field, inactive token controls stay hidden, and both warning prefixes use the same weight.

Run Ruff and Black on changed Python tests:

```sh
python -m ruff check tests/e2e/upgrade_portal/test_signin.py
python -m black --check tests/e2e/upgrade_portal/test_signin.py
```

No test submits a credential or contacts Mist.
