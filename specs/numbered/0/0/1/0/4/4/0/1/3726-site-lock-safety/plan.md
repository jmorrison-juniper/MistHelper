# Implementation Plan: Site Lock Safety for Uncertain Upgrade Replies

**Branch**: `jmorrison-juniper-3726-ambiguous-upgrade-submission` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `/specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/spec.md`.

## Summary

Keep site locks when a firmware reply does not prove acceptance or refusal. Mark uncertain replies as `submission_unknown`. Release locks for documented refusals only when the child has no upgrade identifier. Use one refusal policy for submission, lock release, and cancellation results.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi` SDK methods and portal services. No dependency changes.

**Storage**: Existing aggregate operation records and site locks. No schema change or migration.

**Testing**: `pytest`, Ruff, Black, mypy, Bandit, Radon, Vulture, and repository documentation checks.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Python service and web portal.

**Performance Goals**: Add no cloud call and no retry. Keep existing bounded lock and status behavior.

**Constraints**: Fail closed on uncertainty. Do not change timeout, retry, lease, or recovery behavior. Use offline tests only.

**Scale/Scope**: One aggregate firmware operation and its selected site locks. No new endpoint or user interface.

## Constitution Check

### Before Design

- The eight-level base-5 route for issue 3726 is `0/0/1/0/4/4/0/1`. The parent directory had four children before this feature. This route adds the fifth child and stays within the limit.
- The feature root will contain `spec.md`, `plan.md`, `tasks.md`, and `design/`. It will not exceed five children.
- The active `.specify/feature.json` points to issue 4653. This feature uses explicit paths and will not replace that shared pointer.
- `changelog.d/` contains 287 direct files. This change adds one required, unique issue fragment. Separate remediation action: reduce the existing release-fragment backlog in a release-coordinator-owned follow-up. This feature will not move or remove another fragment.
- Open PRs #4619 and #4208 both own `README.md`. This feature will not edit that shared file. It will update the dedicated upgrade portal guide and record the README summary as deferred until those PRs release the file.
- The implementation changes three existing production modules and three existing unit-test modules. It adds no package, dependency, API, database field, or test module.
- The dedicated portal guide will explain the retained-lock behavior. The README change is blocked by open file ownership and will not be made in this branch.
- The change keeps the existing Mist SDK methods and does not add a direct HTTP request or a WebSocket transport.
- The implementation keeps the existing broad exception handling, retry rules, timeout values, lock lease, and operator recovery controls.

### After Design

- The plan reuses one refusal policy from the aggregate service module. Existing portal modules already depend on that module, so this adds no dependency cycle.
- The refusal allowlist contains HTTP 400, 401, 403, and 404. The existing OpenAPI lists these codes for the organization, site, and SSR upgrade methods. It also lists HTTP 429, which remains uncertain.
- The code and tests will use inline comments on each new executable line. Existing external calls and log behavior remain unchanged.
- Focused offline unit and contract tests will prove that uncertainty retains locks and that a proven refusal can release them.
- The full deployment and merge steps will not run. The user prohibited production actions, merge, approval, auto-merge, and repository-setting changes.

## Design Decisions

1. Use HTTP 400, 401, 403, and 404 as the only proven refusal statuses. Require no upgrade identifier. Treat all other replies as uncertain.
2. Require an upgrade identifier before marking a device submission accepted. A success status without an identifier cannot support later status reads or cancellation.
3. Keep the existing operation-wide lock scope. One uncertain child keeps every selected site locked.
4. Evaluate earlier `rejected` records from their stored HTTP status and identifier. Do not migrate records.
5. Reuse the same certainty policy for cancellation results. Do not report that devices stopped when the submission outcome remains uncertain.

## Implementation Sequence

1. Add offline tests for accepted replies, the refusal allowlist, uncertain replies, legacy records, lock release, and cancellation lists.
2. Add the shared refusal policy and classify non-proven submission replies as unknown.
3. Require refusal evidence before lock release and before a cancellation result claims that no job exists.
4. Run the focused tests and each applicable local gate. Do not run live Mist requests or firmware operations.
5. Update the dedicated portal guide and add one release fragment for issue 3726.

## Validation

Run the three focused unit modules and the unknown-submission route contract. Run Ruff, Black, mypy, compile, Bandit, complexity, Vulture, documentation, and test-quality checks that apply to the changed files. Record exact results in the pull request. Do not run the full test suite or a production upgrade.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/
  spec.md
  plan.md
  tasks.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

### Source Code

```text
src/operations/execution/firmware/aggregate_upgrade_service.py
src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py
src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py
tests/unit/firmware/test_aggregate_upgrade_service.py
tests/unit/upgrade_portal/test_org_upgrade_lock_release.py
tests/unit/upgrade_portal/test_org_cancel_outcomes.py
documentation/upgrade_capture_portal.md
tests/contract/upgrade_portal/test_org_upgrade_routes.py  # Existing test only.
changelog.d/issue-3726-site-lock-safety.md
```

**Structure Decision**: Keep the behavior in the three existing firmware and portal modules. Keep tests in their existing unit modules. Update the dedicated portal guide. Do not edit `README.md` while open PRs own it.

## Complexity Tracking

No new module, service, dependency, or data store is required. The existing `changelog.d/` direct-child count is documented above. Its remediation remains a separate release-coordinator action. The README update remains blocked by open PR file ownership.
