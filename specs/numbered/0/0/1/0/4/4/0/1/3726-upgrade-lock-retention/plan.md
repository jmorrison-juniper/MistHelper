# Implementation Plan: Upgrade Lock Retention

**Branch**: `jmorrison-juniper-fix-3726-upgrade-lock-retention` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/0/4/4/0/1/3726-upgrade-lock-retention/spec.md`.

## Summary

Classify confirmed HTTP 4xx refusals as rejected and treat other unaccepted responses as uncertain. Keep site locks and block retries for uncertain child submissions. Reuse the same refusal rule for cancellation lists and lock release. Preserve current cloud reads, lease timing, phase watches, and post-check behavior.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi` SDK and Flask portal dependencies. No dependency changes.

**Storage**: Existing aggregate operation records and site locks. No schema changes.

**Testing**: `pytest` with mocked submission results and intercepted lock callbacks.

**Target Platform**: Existing local portal and supported Windows, macOS, and Linux deployments.

**Project Type**: Python service and web portal.

**Performance Goals**: No new requests, retries, or polling. Keep current runtime bounds.

**Constraints**: Run tests offline. Do not write to a live Mist service or lock store. Keep the existing lease duration and status-read behavior.

**Scale/Scope**: Three existing production modules, their focused tests, one release note, and the routed Spec Kit record.

## Constitution Check

- **Bounded structure**: The feature root has four children: `spec.md`, `plan.md`, `tasks.md`, and `design/`. The `design/` directory has four children. No new source package is needed.
- **Existing structure debt**: The repository has existing direct-child debt in `changelog.d/`. This feature adds only `issue-3726-upgrade-lock-retention.md`. Separate remediation remains outside this issue.
- **Function limits**: Keep each touched function within the repository limits of five parameters, five logical blocks, five operations per block, and 25 lines. Check touched functions during implementation.
- **Safety**: Treat server errors, invalid status values, and malformed success responses as uncertain. Do not release their locks or enable retry. Keep known 4xx refusals and known non-submissions distinct.
- **No live action**: Use only mocked responses and intercepted lock callbacks. Do not send Mist requests or change a production lock.
- **Scope**: Do not change retry, timeout, lease, or status-read behavior. Do not expand issue #3329.
- **Pull request control**: Keep `needs-human-review`. Hold publication until PR #4679 releases the serial merge slot.
- **Feature pointer**: `.specify/feature.json` names another feature. Leave it unchanged and use the explicit routed paths in this record.
- **Route tooling**: PowerShell is unavailable in this environment. The route was calculated as eight base-5 segments and its parent capacities were checked directly.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/0/4/4/0/1/3726-upgrade-lock-retention/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── checklists/
        └── requirements.md
```

### Source Code

```text
src/operations/execution/firmware/aggregate_upgrade_service.py
src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py
src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py
tests/unit/firmware/test_aggregate_upgrade_service.py
tests/unit/upgrade_portal/test_org_upgrade_lock_release.py
tests/unit/upgrade_portal/test_org_cancel_outcomes.py
changelog.d/issue-3726-upgrade-lock-retention.md
```

**Structure Decision**: Update the existing firmware submission classifier and portal release rules. Reuse their current test modules. Do not add a package, API, or storage field.

## Complexity Tracking

No new constitution violation is planned. The issue adds one unique release-note fragment to an established process folder. Track the existing `changelog.d/` direct-child debt as a separate incremental process-folder remediation.
