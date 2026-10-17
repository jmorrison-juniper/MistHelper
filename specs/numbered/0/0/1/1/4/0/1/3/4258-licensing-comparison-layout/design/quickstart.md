# Offline Validation

Use the worktree virtual environment. No production credentials are required.

```sh
.venv/bin/python -m pytest tests/integration/web_portal/licensing_comparison tests/e2e/web_portal/licensing_comparison -q
```

The browser fixture serves synthetic responses on loopback.
Verify the shared shell, numeric result columns, totals, descriptions, purchases, manual rows, reload persistence, failures, and export.
Browser evidence belongs in ignored `test-artifacts/`, not in the source tree.
See [UI contract](contracts.md) and [data model](data-model.md) for the expected results.
