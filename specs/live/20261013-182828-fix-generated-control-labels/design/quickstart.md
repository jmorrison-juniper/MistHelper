# Validation Guide

If `.venv` is absent, run `python3 scripts/bootstrap_worktree.py`.
Use the worktree interpreter for each command.

```bash
.venv/bin/python -m pytest tests/e2e/web_portal/test_operations_accessible_names.py tests/e2e/web_portal/test_operations_panel_workflow.py tests/unit/web_portal/test_operations_msp_selector.py tests/unit/web_portal/test_operations_silent_failure.py tests/guardrails/test_operations_panel_visibility.py -q --tracing=retain-on-failure --output=test-artifacts/4059-after
.venv/bin/python -m ruff check tests/e2e/web_portal/test_operations_accessible_names.py
.venv/bin/python -m black --check tests/e2e/web_portal/test_operations_accessible_names.py
node --check web_portal/static/js/operations.js
```

Expect all examined labels to reference their controls, including endpoint replacements.
Use the isolated Flask fixture only. Do not run live operations.
See [the label contract](contracts/labels.md) for the required behavior.
