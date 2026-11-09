# Quickstart: Site Lock Safety

**Feature**: [spec.md](../spec.md)

## Prerequisites

Use Python 3.13 or newer. In a new worktree, create the project environment before running tests:

```bash
python3 scripts/bootstrap_worktree.py
source .venv/bin/activate
```

## Offline validation

Run the focused unit tests:

```bash
python -B -m pytest -p no:cacheprovider -q \
  tests/unit/firmware/test_aggregate_upgrade_service.py \
  tests/unit/upgrade_portal/test_org_upgrade_lock_release.py \
  tests/unit/upgrade_portal/test_org_cancel_outcomes.py
```

Run the route contract test that proves an uncertain submission blocks a repeat:

```bash
python -B -m pytest -p no:cacheprovider -q \
  tests/contract/upgrade_portal/test_org_upgrade_routes.py::test_unknown_submission_blocks_a_repeat
```

Run lint and format checks on the changed Python files:

```bash
python -m ruff check \
  src/foundation/support/submission_certainty.py \
  src/operations/execution/firmware/aggregate_upgrade_service.py \
  src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py \
  src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py \
  tests/unit/firmware/test_aggregate_upgrade_service.py \
  tests/unit/upgrade_portal/test_org_upgrade_lock_release.py \
  tests/unit/upgrade_portal/test_org_cancel_outcomes.py

python -m black --check \
  src/foundation/support/submission_certainty.py \
  src/operations/execution/firmware/aggregate_upgrade_service.py \
  src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py \
  src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py \
  tests/unit/firmware/test_aggregate_upgrade_service.py \
  tests/unit/upgrade_portal/test_org_upgrade_lock_release.py \
  tests/unit/upgrade_portal/test_org_cancel_outcomes.py
```

## Expected results

- Every uncertain response keeps the site lock and blocks retry.
- Every allowlisted refusal can settle when all other operation steps end.
- Tests use offline stand-ins and do not call Mist Cloud or alter a production lock.
