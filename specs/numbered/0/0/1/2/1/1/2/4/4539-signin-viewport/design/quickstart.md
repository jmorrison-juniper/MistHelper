# Validation guide

If the worktree has no environment, run `python3 scripts/bootstrap_worktree.py`.

Run the reported browser journey:

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -m pytest tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py -k history_comparison_errors_and_viewports --browser chromium -q --tb=short --timeout 300
```

Expect one passing journey. The phone and tablet checks must both run.
The sign-in document must measure at most 390 pixels at the phone size.
No live system is required.

Run Ruff and Black against the changed Python test.
Run the local test-quality preflight and committed-difference gate before any push.
