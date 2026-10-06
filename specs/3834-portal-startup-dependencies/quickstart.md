# Quickstart: Verify portal request resources

Run the focused tests:

```bash
python -m pytest tests/integration/upgrade_portal/issue_3834 -q
```

Run the changed-file quality, security, complexity, symbol, prose, and
test-quality gates from the issue handoff.

Confirm the committed path list:

```bash
git diff --name-only origin/main...HEAD
```

The output must contain the 14 authorized paths only. It must contain no route
file.
