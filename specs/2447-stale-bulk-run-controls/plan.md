# Implementation Plan: Stale and Bulk Run Controls

**Branch**: `fix/2447-stale-bulk-run-controls` | **Date**: 2026-09-11 |
**Spec**: [spec.md](./spec.md)

## Summary

The feature adds one stale policy, safe reconciliation, authoritative bulk
preview, atomic cancel and retry actions, and isolated browser tests.

New behavior enters compliant nested packages. Existing noncompliant modules
receive only necessary surgical edits. The feature does not restructure
unrelated repository debt.

ArangoDB is the declared operational store for run actions. It stores each run
mutation and related outcome in one transaction. The portal fails closed when
it cannot verify persistence.

## Technical Context

**Language**: Python 3.13, existing JavaScript syntax, Jinja, and CSS.

**Dependencies**: Flask, Flask-WTF, mistapi, python-arango, Redis client,
structlog, pytest, pytest-playwright, and Chromium.

**Operational store**: ArangoDB for run records, action records, leases,
idempotency, compare-and-swap, and atomic outcomes.

**Output backends**: API exports and collected API data continue through
`DataExporter.write_with_format_selection()`.

**Test storage**: Process-owned memory with no persistent fallback.

**Performance goals**:

- A fixed 50-row history workload completes in less than 1 second.
- A fixed 50-run local no-cloud action completes in less than 5 seconds.

**Safety constraints**:

- No bulk action submits firmware.
- No pre-cloud cancel calls the cloud.
- A `stopping` run reaches only proven `stopped`.
- Every mutation and successful outcome commit together.
- Every initialized item reaches one durable final outcome.
- Recovery never repeats a claimed or final item.

## Constitution Check

| Principle | Design result |
| - | - |
| I. Five-Item Rule | The feature adds code only under compliant nested packages. Surgical edits do not add children to existing noncompliant modules or directories. |
| II. Class-Based Architecture | Named classes own preview, processing, reconciliation, retry, persistence, and test controls. |
| III. Safety-First | Typed phrases, current guards, durable claims, atomic writes, and fail-closed storage protect mutations. |
| IV. Full Deployment Pipeline | The tasks claim the issue, check file overlap, use the complete manifest, rebase, pass PR CI, squash merge, verify the main build, deploy, and check health. |
| V. Observability | Structured logs use stable safe fields and omit credentials and raw actor identity. |
| VI. Inline Comments | The manifest requires a comment review for each changed executable line. |
| VII. Action Logging | The manifest requires before and after logs for each meaningful action. |

## Storage Governance

The action journal is internal operational coordination data. It is not an API
export or collected API data.

ArangoDB supplies the transaction, lease, idempotency, and compare-and-swap
operations that the action journal needs. CSV, SQLite, Redis, memory, and file
backends cannot join the run mutation transaction.

The portal returns `action_store_unavailable` before mutation when ArangoDB is
unavailable. It reports no success until the transaction commits and the
required record verification passes.

Before schema work or deployment, the operator creates and verifies an
ArangoDB backup. The recovery procedure restores that backup to an isolated
target and verifies both collections.

The first release retains each action record for the lifetime of its referenced
run records. It performs no automatic action cleanup.

## Source Structure

### New API Package

The `src/upgrade_portal/api` directory currently has fewer than five children.
Add this compliant package:

```text
src/upgrade_portal/api/run_controls/
├── __init__.py
├── models.py
├── routes.py
├── services/
└── views.py

services/
├── __init__.py
├── bulk.py
├── preview.py
├── reconciliation.py
└── retry.py
```

`models.py` owns request and response values. `routes.py` owns the blueprint.
`views.py` owns stale assessment for both pages.

The service package owns bulk order, preview, reconciliation, and retry policy.
The `run_controls` package has five children. Its `services` package also has
five children.

### New Persistence Package

The `src/upgrade_portal/persistence` directory currently has fewer than five
children. Add this compliant package:

```text
src/upgrade_portal/persistence/actions/
├── __init__.py
├── models.py
├── replay.py
├── repository.py
└── transactions.py
```

The package owns action records, durable item claims, outcome-only writes,
atomic run writes, lease takeover, and finalization.

The `actions` package has five children.

### Surgical Existing-Child Edits

The feature can edit these existing children without adding a sibling:

- `runtime/signals.py` removes `TERMINAL_RUN_STATES`.
- `app/routes/review.py` removes `FINISHED_RUN_STATES`.
- `app/routes/upgrade.py` adds only the required run-page integration.
- `app/factory.py` registers overrides before route registration.
- `app/wiring.py` wires the new route and operational-store classes.

`runtime/runs.py` remains a reference-only terminal-state authority. The
feature does not edit it.

The feature edits these existing assets:

- `app/assets/templates/review/history.html`
- `app/assets/templates/upgrade/progress.html`
- `app/assets/static/js/portal.js`
- `app/assets/static/css/portal.css`

The edits do not add a direct child to an overfull parent. The implementation
must not add a new top-level helper when an existing class can own the change.

### Test Packages

Replace three existing test files with same-name packages. The replacement
does not increase the child count of their existing parents.

```text
tests/unit/upgrade_portal/test_runs/
├── __init__.py
├── test_actions.py
├── test_isolation.py
├── test_reconciliation.py
└── test_staleness.py

tests/contract/upgrade_portal/test_upgrade_routes/
├── __init__.py
├── test_bulk_actions.py
├── test_isolation.py
├── test_reconciliation.py
└── test_stale_views.py

tests/e2e/upgrade_portal/test_run_controls/
├── __init__.py
├── test_bulk.py
├── test_existing.py
├── test_isolation.py
└── test_stale.py
```

Move each original test into `test_existing.py` or the applicable package file
before adding behavior.

Add the compliant integration and support packages from
[test-isolation.md](contracts/test-isolation.md). The new
`tests/support/upgrade_portal_e2e` child brings its parent to five children.

The integration package has five direct children:

```text
tests/integration/upgrade_portal/run_controls/
├── __init__.py
├── test_actions.py
├── test_performance.py
├── test_reconciliation.py
└── test_recovery.py
```

The support package has five direct children:

```text
tests/support/upgrade_portal_e2e/
├── __init__.py
├── environment.py
├── records/
├── resources.py
└── traps/
```

The records package has five direct children:

```text
records/
├── __init__.py
├── actions.py
├── audit.py
├── cloud.py
└── portal.py
```

The traps package has five direct children:

```text
traps/
├── __init__.py
├── arango.py
├── files.py
├── mist.py
└── redis.py
```

Every new source and test package has five direct children or fewer. Each
same-name test package replaces one existing file and does not add a child to
its grandfathered parent.

## Design

### 1. Canonical Terminal States

`RunStateMachine.TERMINAL` remains the only final-state set.

`runtime/signals.py` coerces the stored state through `RunStateMachine` and
checks `RunStateMachine.TERMINAL`.

`app/routes/review.py` uses the same authority when it selects an end time.
The implementation removes both divergent module-level sets.

### 2. Stale Policy

`RunStalePolicy` receives a run and one UTC clock value. It returns one
`StaleAssessment`.

The history and run-page adapters call the same policy. JavaScript updates only
the displayed age.

### 3. Action Sources

`UpgradeRunAction.source_kind` is `bulk_preview` or
`single_reconciliation`.

A bulk action requires `preview_id`, `preview_digest`, organization scope,
history scope, and server counts.

A reconciliation action sets the preview fields to null. It stores one run
identifier, one site, the confirmation digest, and counts of one.

Both sources use the same durable actor and idempotency key.

### 4. Durable Item Lifecycle

The initialization transaction creates one ordered item for each requested
run. Each item starts with:

```text
processing_state: pending
classification: unknown
reason: not_processed
```

Before work, one compare-and-swap write changes `pending` to `claimed` and
stores the worker lease.

A successful mutation changes the run and finalizes the item in one
transaction.

A refusal, failure, or unknown result that changes no run uses an outcome-only
compare-and-swap write. It changes the item to `final`.

After every item is final, one compare-and-swap write changes the action from
`processing` to `complete`. A complete response reads the verified stored
record.

### 5. Crash Recovery and Safe Resumption

A current lease returns `processing`.

After lease expiry, one worker takes the action lease with compare-and-swap.
The worker finalizes each old `claimed` item as `unknown` with reason
`processing_interrupted`.

The worker resumes only `pending` items. It never repeats a claimed or final
item. It preserves a stored site block and finalizes later blocked site items
as `not_processed_after_site_guard_loss`.

Recovery finishes all items and changes the action to `complete`. Thus every
requested run has one durable final outcome.

### 6. Authoritative Preview

`BulkActionPreviewService` reads the current organization and history scope.
It rejects duplicate identifiers and removes non-visible identifiers.

The service returns exact counts and a signed preview token. The browser
replaces its candidate selection before phrase entry.

Reconciliation does not call this service and does not require a preview.

### 7. Bulk Cancel and Retry

`BulkRunActionService` processes sites in stable order and items in preview
order.

Immediately before each mutation, it checks current write permission and the
exact lock token. Guard loss stores a site block and stops later writes for
that site.

Other sites continue. Every refusal, failure, unknown result, and success
receives a durable final outcome.

`RetryCopyPolicy` applies the exact option allowlist and calls the existing
`build_options` validator.

### 8. Reconciliation

`StoppingRunReconciler` reads stored and cloud evidence. It sends no write
request to the cloud.

A pre-cloud run can become `cancelled`. A `stopping` run can become only
`stopped`, and only with complete proof.

The route creates a single-run action directly. It does not create or require
a bulk preview.

Each `stopping` reconciliation stores the safe serialized evidence summary on
the final outcome. The parent action stores its matching digest.

A success transaction stores the run state, outcome, summary, and digest
together. An outcome-only write stores the summary and digest for a result
that changes no run.

### 9. E2E Factory Isolation

The E2E fixture creates all overrides before application construction. The
factory validates and installs them before blueprint registration.

ArangoDB, Redis, cloud, and file traps fail every unexpected call. Each server
uses unique ports, record stores, identifiers, and artifacts.

Record persistent-store baselines before the full E2E suite. Compare the same
counts immediately after the suite.

### 10. Explicit Feature Manifest

[feature-files.txt](feature-files.txt) is the only staging allowlist.

The 79-path manifest lists every planned source, asset, test, README,
documentation, changelog, specification, constitution, and metadata path
before the first source edit.

The implementation updates this file before it changes an additional path.
The manifest includes all feature-owned tracked changes and untracked files.
It excludes unrelated pre-existing untracked worktree files.

The gate script compares four inputs with the manifest:

1. Changes from the merge base to `HEAD`.
2. Staged changes.
3. Unstaged changes.
4. Untracked files.

The script fails when a changed feature path is absent from the manifest. It
also fails when a changed path outside the manifest is attributed to this
feature.

The staging command uses `git add -A --pathspec-from-file` with this manifest.
A final comparison proves that every changed manifest path is staged.

No workflow file edit is planned. The existing `ci.yml`, `auto-merge.yml`, and
`container-build.yml` workflows already supply the required gates, merge
method, and image build. If implementation needs a workflow edit, update the
manifest before the first edit to that file.

### 11. Performance and Traceability

The history measurement uses 50 fixed records, 10 warm-up calls, and 30
measured calls.

The bulk measurement uses 50 fixed pre-cloud runs, one actor, valid locks, and
no cloud calls. It uses 5 warm-up calls and 20 measured calls.

The traceability review maps FR-001 through FR-076 to named evidence. The final
checklist runs only after this cross-artifact review.

### 12. Deployment

Before implementation, verify that `HEAD` equals current `origin/main`. Claim
issue #2447 and add `in-progress`. Check active worktrees, active branches, and
open pull request files against the complete manifest. Stop when another owner
or open pull request overlaps a feature path.

Update `README.md`, `documentation/upgrade_capture_portal.md`, and
`CHANGELOG.md` before local gates.

Run all local gates. Build and verify the explicit manifest. Stage only
manifest paths and create the feature commit.

Fetch `origin/main`, then rebase the committed feature branch onto it. Rerun
affected local gates. Commit a required conflict repair before the push.

Push `fix/2447-stale-bulk-run-controls`.

Open a pull request to `main` with this title:
`fix(upgrade-portal): add stale and bulk run controls`.

The body must include `Closes #2447`, the specification link, the changed-file
summary, acceptance evidence, local gate results, current CI status, security
results, UI evidence, deployment notes, and rollback notes. Complete every
applicable pull request template item.

Add the `bug`, `web-portal`, and `in-progress` labels.

After required human approval and every required check passes, including
CodeQL, add the `auto-merge` label. The repository workflow uses a squash
merge. Wait for the main container build that uses the merged commit.

Verify that the image revision label equals the merged commit SHA. Then deploy
the image and check the container and portal health endpoints.

## Requirements Traceability

| Requirements | Design owner | Contract | Verification |
| - | - | - | - |
| FR-001 to FR-007 | `RunStalePolicy` and canonical terminal authority | [ui.md](contracts/ui.md) | Unit, contract, and browser stale tests |
| FR-008 to FR-015 | `StoppingRunReconciler` and action transaction manager | [reconciliation.md](contracts/reconciliation.md) | Unit, contract, integration, and browser reconciliation tests |
| FR-016 to FR-023 | `BulkActionPreviewService` | [http-api.md](contracts/http-api.md), [ui.md](contracts/ui.md) | Unit, contract, and browser preview tests |
| FR-024 to FR-033 | Durable item lifecycle and bulk cancel service | [http-api.md](contracts/http-api.md) | Unit, contract, integration, recovery, and browser cancel tests |
| FR-034 to FR-043 | `RetryCopyPolicy` and retry transaction | [http-api.md](contracts/http-api.md) | Unit, contract, integration, recovery, and browser retry tests |
| FR-044 to FR-052 | Actor scope, replay, lease takeover, and safe resumption | [http-api.md](contracts/http-api.md) | Identity, replay, crash, renewal, and cross-actor tests |
| FR-053 to FR-059 | Factory overrides and E2E traps | [test-isolation.md](contracts/test-isolation.md) | Unit, contract, and full E2E suite |
| FR-060 to FR-066 | Operational store, backup, recovery, retention, and verified persistence | [data-model.md](data-model.md) | Store integration, restore drill, and unavailable-store tests |
| FR-067 to FR-073 | Traceability, ownership, explicit manifest, staging, failure ownership, and performance | [quickstart.md](quickstart.md) | Issue claim, overlap audit, manifest audit, gate records, issue links, and measurements |
| FR-074 to FR-076 | Documentation, governed deployment, and live-action exclusion | [quickstart.md](quickstart.md) | Documentation review, PR evidence, image revision, health checks, and optional live record |

## Dependency Rules

1. Verify the current `origin/main` base.
2. Claim issue #2447 and check branch and file overlap.
3. Record the complete feature manifest and debt boundary before implementation.
4. Centralize terminal checks before stale and retry behavior.
5. Complete factory override proof before any browser execution.
6. Add the primary-key strategy before action persistence.
7. Add durable claims and finalization before action mutations.
8. Add preview before bulk confirmation controls.
9. Add stale policy before reconciliation.
10. Record persistent baselines before the full E2E suite.
11. Compare persistent counts immediately after the full E2E suite.
12. Complete traceability and the checklist before final local gates.
13. Commit the verified manifest, then rebase onto `origin/main`.
14. Pass PR CI and required approval before the auto-merge label.
15. Verify the merged revision before deployment.

## Complexity Tracking

| Existing violation | Feature treatment | Separate remediation |
| - | - | - |
| `runtime/runs.py` has more than five symbols. | Use `RunStateMachine.TERMINAL` as a reference. Do not edit this file. | Plan a later runtime model extraction in a separate issue. |
| `runtime/signals.py` has more than five symbols. | Remove its divergent terminal set and use the canonical authority. | Plan a later signal service extraction in a separate issue. |
| `app/routes/review.py` has more than five symbols. | Replace its terminal check without adding a top-level symbol. | Plan a later review-route package in a separate issue. |
| `app/routes/upgrade.py` has more than five symbols. | Add only integration calls to classes in the new package. | Plan a later upgrade-route package in a separate issue. |
| `app/factory.py` and `app/wiring.py` are overfull. | Add only the required registration and injection edits. | Plan later factory and wiring extraction in separate issues. |
| Existing test directories have more than five children. | Replace related test files with same-name compliant packages. | Plan broader test hierarchy cleanup separately. |

No new package exceeds five children. The feature does not increase the child
count of a grandfathered noncompliant parent.
