# Implementation Plan: Site Lock Safety for Uncertain Submissions

**Branch**: `jmorrison-juniper-upgrade-portal-submission-replies` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/spec.md`.

## Summary

Classify only explicitly allowlisted client refusals as `rejected`. Record every other non-accepted response as `submission_unknown`, and keep site locks and retry controls blocked until the operation proves that no firmware write can follow. Use a shared refusal predicate and settlement helper for submission classification, lock release, retry eligibility, and cancellation reporting.

## Technical Context

**Language/Version**: Python 3.13 or newer
**Primary Dependencies**: Existing `mistapi` firmware clients; no dependency changes
**Storage**: Existing aggregate operation records and site locks
**Testing**: `pytest`, `ruff`, and `black`
**Target Platform**: Upgrade portal on Windows, macOS, and Linux
**Project Type**: Python web service
**Performance Goals**: No new network calls, retries, or polling
**Constraints**: Fail closed on uncertain outcomes. Use offline tests only. Preserve existing lock lease and recovery behavior. Do not send a live firmware request or alter a production lock.
**Human-review boundary**: Prepare one pull request and keep `needs-human-review`. Do not approve, merge, enable auto-merge, or deploy this change.
**Scale/Scope**: Submission normalizers, aggregate execution, shared certainty checks, portal readers, offline regression modules, and one changelog fragment.

## Constitution Check

- **Bounded structure**: Use the existing routed feature directory. Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at its root, with supporting files under `design/`.
- **Five-item rule**: Add no module to the firmware package, which already has 12 direct children. Add one module under `src/foundation/support/`, which has three direct children. Keep its class to one status set, a refusal predicate, and a settlement helper.
- **Process-folder debt**: `changelog.d/` has 287 direct children. Add only the required unique issue fragment. Track a separate maintenance action to reduce this existing count. Do not restructure the changelog directory in this issue.
- **Active feature pointer**: `.specify/feature.json` points to issue #4653. Leave it unchanged. The Spec Kit PowerShell wrapper cannot run because `pwsh` is unavailable. The route was verified from `Resolve-SpecFeaturePath` and an eight-digit base-5 calculation.
- **Mist Cloud transport**: Keep existing SDK calls and authentication. Add no transport, retry, or timeout behavior. Mock all responses in tests.
- **Destructive-path safety**: Retain locks on unknown outcomes. Do not run any destructive menu or live firmware action.

## Design Decisions

1. Use HTTP 400, 401, 403, and 404 as refusal candidates because `documentation/mist-api-openapi31json.json` lists them for upgrade endpoints. Keep 429 and undocumented statuses uncertain.
2. Keep any response with a retained job identity or accepted target uncertain, even when its status is a documented refusal candidate.
3. Put the shared refusal predicate in `src/foundation/support/submission_certainty.py`. The common foundation layer can serve both firmware execution and portal code without a reverse dependency or duplicated rules. This folder has three direct children, so one new module keeps it within the five-child limit.
4. Keep `rejected` only when a response proves refusal. Convert ambiguous returned responses to `submission_unknown`.
5. Treat an accepted-looking device response without an upgrade identity as `submission_unknown`. Keep its lock because the portal cannot reconcile the job.
6. Apply the refusal evidence check to legacy `rejected` records. A missing, malformed, undocumented, or conflicting response does not prove that no job exists.
7. Preserve current lock lease, recovery controls, error-handling breadth, and retry policy. The existing settled-operation gate blocks retry while an unknown child remains.
8. Store separate organization progress proof. Share its reader between summary counts and device rows, including legacy records and valid later reads.

## Phase 0: Research

See [research.md](design/research.md). It records the source evidence, refusal allowlist, shared contract location, and alternatives considered.

## Phase 1: Design and Contracts

- Use the shared certainty module as the contract for submission, settlement, retry eligibility, and cancellation reporting.
- [Data model](design/data-model.md): document outcome fields, transitions, and lock-release proof.
- [Submission certainty contract](design/contracts/submission-certainty.md): define shared response classification and downstream behavior.
- [Quickstart](design/quickstart.md): list offline validation commands and expected results.
- No Mist Cloud API schema changes or new external endpoints are introduced.

## Constitution Check After Design

- One production module is added under `src/foundation/support/`, which remains within the five-child limit.
- The new helper contains one class, one status set, and one predicate. The touched existing functions stay within their method limits.
- Unit and route-contract tests use only offline fixtures.
- The feature adds one required changelog record to an existing process folder. The separate folder-debt action remains out of scope.
- No change is made to `.specify/feature.json`, live locks, retries, or lock expiration.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      submission-certainty.md
    checklists/
      requirements.md
```

### Source Code

```text
src/foundation/support/submission_certainty.py
src/operations/execution/firmware/aggregate_upgrade_service.py
src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py
src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py
src/interfaces/portals/upgrade_portal/upgrade/org_devices.py
tests/unit/firmware/test_aggregate_upgrade_service.py
tests/unit/upgrade_portal/test_org_upgrade_lock_release.py
tests/unit/upgrade_portal/test_org_cancel_outcomes.py
tests/contract/upgrade_portal/test_org_upgrade_routes.py
changelog.d/issue-3726-site-lock-safety.md
```

**Structure Decision**: Add one shared certainty module under `src/foundation/support/`, then update existing firmware-service and portal modules. Keep all test changes in existing focused test files.

## Complexity Tracking

| Existing condition | Required action | Scope |
|---|---|---|
| `changelog.d/` has 287 direct children. | Add a separate maintenance issue to reduce this count through incremental cleanup. | Not part of issue #3726. |
| The firmware package has 12 direct children. | Add no module there. Put the shared refusal predicate in `src/foundation/support/submission_certainty.py`. | This feature. |
