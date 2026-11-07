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

Warning: menu 187 writes configuration to a live organization and can cause an outage.
Do not execute menu 187 against a production organization for this repair.
Obtain human review before merging.

The lookup keeps response contents out of manager logs.
The Mist API SDK can print refused response data when SDK debug output is enabled.
This repair does not change the process-wide SDK debug setting.
