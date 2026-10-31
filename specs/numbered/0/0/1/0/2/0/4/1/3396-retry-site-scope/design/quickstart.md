# Retry scope validation

## Prerequisites

Use the isolated worktree environment from `python3 scripts/bootstrap_worktree.py`.
Do not load live Mist credentials or start the portal against production.

## Focused tests

```text
.venv/bin/python -m pytest -q tests/contract/upgrade_portal/test_org_child_controls_routes.py tests/unit/upgrade_portal/test_org_precheck.py tests/unit/upgrade_portal/test_org_site_records.py tests/unit/firmware/test_aggregate_upgrade_service.py
```

Expect the cleared-family retry to save, confirm, check, and lock B only.
Expect plain saves and complete retries to retain both planned sites.
The contract fixture blocks external connections.

## Test-quality procedure

Run the input preflight from the repository instructions.
Commit the intended tests before the committed-difference gate.
Use verified `origin/main` for the comparison, with a clean relevant worktree.
Do not change the test-quality baseline.

## Review

Read [the route contract](contracts/retry-scope.md) and [the data model](data-model.md).
Open a draft pull request with `needs-human-review`.
Leave auto-merge disabled and execute no live firmware action.
