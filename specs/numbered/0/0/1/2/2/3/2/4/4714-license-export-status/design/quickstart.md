# Local validation

Use the worktree environment. Do not load credentials or run a live menu.

```text
.venv/bin/python -m pytest tests/unit/export/test_org_admin_exporter.py tests/unit/export/test_issue_4714_org_licenses_status.py -q --no-cov
.venv/bin/python -m ruff check src/operations/exporting/export/org_admin_exporter.py tests/unit/export/test_org_admin_exporter.py tests/unit/export/test_issue_4714_org_licenses_status.py
.venv/bin/python -m black --check src/operations/exporting/export/org_admin_exporter.py tests/unit/export/test_org_admin_exporter.py tests/unit/export/test_issue_4714_org_licenses_status.py
```

The regression fixture rejects socket creation and DNS resolution and verifies zero attempts.
The original-source run must fail the failure-status, writer rejection, and empty-result checks.
The repaired-source run must pass.
Use the session evidence command record for exact gate commands and results.
