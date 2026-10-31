# Busy-site refusal validation

If dependencies are absent, run `python3 scripts/bootstrap_worktree.py`.
Activate the worktree environment with `source .venv/bin/activate`.

Run the focused browser cases:

```bash
UPGRADE_PORTAL_JOURNEYS=1 python -m pytest -q tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py -k synthetic_busy_site
```

Each case must pass against the isolated stand-in portal.
No live cloud request or firmware write is required.
The journey recorder preserves failed-flow screenshots and reports under ignored test artifacts.
