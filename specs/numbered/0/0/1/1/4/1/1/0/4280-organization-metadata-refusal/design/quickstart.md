# Offline Validation

If the worktree has no environment, run `python3 scripts/bootstrap_worktree.py`.
Use `.venv/bin/python` on macOS or Linux.
Use `.venv\Scripts\python.exe` on Windows.

Run the focused lookup and export tests:

```text
.venv/bin/python -m pytest tests/unit/org/test_org_config_migration_workflow.py tests/unit/org/test_org_config_migration_conflicts.py -q
```

Expect every test to pass.
The tests replace the SDK endpoint and use temporary output paths.
Refusal tests must fail against the previous lookup.
Check successful labels, `Unknown` refusal labels, status warnings, and absence of sensitive markers.

Run the SDK contract:

```text
.venv/bin/python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -q
```

Run file-scoped Ruff, Black, mypy, Bandit, complexity, symbols, and docstring gates.
Run the documented test-quality preflight and committed comparison before any push.

Warning: menus 176 and 177 belong to destructive workflows.
Do not execute these menus against a production organization for this repair.
Obtain human review before merging.
