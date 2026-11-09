# Validation Guide: Upgrade Lock Retention

## Prerequisites

Use the repository Python 3.13 environment. If the worktree has no `.venv`, run `python3 scripts/bootstrap_worktree.py` and then `source .venv/bin/activate`.

## Offline Scenarios

1. Run the aggregate firmware unit tests with mocked cloud responses.
2. Run the portal lock-release tests with lock-release and persistence callbacks intercepted.
3. Run the cancellation outcome tests for HTTP 4xx, HTTP 5xx, malformed HTTP 200, and known non-submission.
4. Confirm the uncertain cases keep locks and provide no retry. Confirm a known refusal retains the existing release behavior.

Run the focused checks from the repository root:

```sh
python -m pytest tests/unit/firmware/test_aggregate_upgrade_service.py tests/unit/upgrade_portal/test_org_upgrade_lock_release.py tests/unit/upgrade_portal/test_org_cancel_outcomes.py
python -m ruff check src/operations/execution/firmware/aggregate_upgrade_service.py src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py tests/unit/firmware/test_aggregate_upgrade_service.py tests/unit/upgrade_portal/test_org_upgrade_lock_release.py tests/unit/upgrade_portal/test_org_cancel_outcomes.py
python -m black --check src/operations/execution/firmware/aggregate_upgrade_service.py src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py tests/unit/firmware/test_aggregate_upgrade_service.py tests/unit/upgrade_portal/test_org_upgrade_lock_release.py tests/unit/upgrade_portal/test_org_cancel_outcomes.py
```

## Safety Check

Use only mocked response objects. Do not run a portal action against Mist. Do not connect to a lock store. The tests must show zero cloud requests and zero lock-release callbacks for uncertain submissions.
