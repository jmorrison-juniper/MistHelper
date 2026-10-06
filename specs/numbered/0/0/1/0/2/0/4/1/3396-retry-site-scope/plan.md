# Implementation Plan: Retry Site Scope

**Branch**: `jmorrison-juniper-assess-3396-stale-site-retry`  
**Date**: 2026-10-06  
**Spec**: [spec.md](spec.md)  
**Issue**: #3396

## Summary

Narrow a retry operation after device-family filtering without changing the
operator selection. The save route will keep the selected rows for validation,
then filter those rows by the site identifiers in the planned aggregate
targets. The aggregate builder will store only those effective rows.

The confirmation page and submission context will read the durable operation
scope for aggregate plans. The existing precheck, exact-context, lock, audit,
idempotency, and compare-and-set paths will then use the same durable scope.
Plain saves and legacy access point saves will keep their current behavior.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Flask and the existing upgrade portal services. No
new dependency.

**Storage**: The existing durable run store and compare-and-set interface. No
schema change.

**Testing**: pytest with the Flask test client, in-memory run storage, fake
Mist reads, fake prechecks, fake lock storage, and a socket block.

**Target Platform**: Windows 11, macOS, Linux, and the Podman deployment.

**Project Type**: Server-rendered web portal with JSON route controls.

**Performance Goals**: Use one set membership check across the selected rows.
Add no Mist request and no durable write.

**Constraints**: Keep authentication, typed confirmation, lock tokens, audit
timing, idempotency, and compare-and-set behavior unchanged. Stop if another
production file becomes necessary.

**Scale/Scope**: One existing route module, one existing contract test file,
one release-note fragment, and the feature specification records.

## Constitution Check

*GATE: Passed before research. Passed again after design.*

| Rule | Result |
| - | - |
| Destructive-path safety | Pass. Typed confirmation and every existing write gate remain in place. |
| Authentication and authorization | Pass. The design changes no identity or ownership rule. |
| Durable coordination | Pass. The existing write and compare-and-set paths remain authoritative. |
| Mist transport | Pass. The design adds no Mist request and no direct HTTP request. |
| External validation | Pass. The focused contract file will block socket access and use only fakes. |
| Five-item rule | Pass for new structure. The design adds no production module or top-level production symbol. |
| Class architecture | Pass. The edit reuses existing private helpers and adds no module-level symbol. |
| Inline comments and action logging | Pass. Each changed executable line will use the existing comment and logging style. |
| Simplified Technical English | Pass. The planning records use short active sentences. |
| Product output location | Not applicable. The change writes no product output. |
| Process-folder rule | Pass. The numeric specification uses the managed eight-level base-5 route. |
| Conventional Commit form | Future implementation work must use an accepted Conventional Commit subject. |

### Existing Debt and Incremental Remediation

`org_upgrade.py` already exceeds the module child limit. The approved boundary
requires a narrow edit to existing functions and forbids a new production
module. The implementation must add no top-level production symbol.

The existing route module exceeds the module child limit. This change adds no
module-level symbol. It reduces `confirm_page` below 25 lines by reusing the
existing `_confirmation_targets` helper for prepared template values.

The existing operational store keeps verified ArangoDB records or CSV backup
records. Compare-and-set coordination fails closed and does not use the
in-memory mirror or backup file. Existing recovery, unlimited retention,
retry lineage, and idempotency behavior remain unchanged.

## Project Structure

### Documentation for This Feature

```text
specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/
├── spec.md
├── plan.md
└── tasks.md
```

### Implementation Boundary

```text
src/interfaces/portals/upgrade_portal/app/routes/
└── org_upgrade.py

tests/contract/upgrade_portal/
└── test_org_child_controls_routes.py

changelog.d/
└── issue-3396-retry-site-scope.md
```

**Structure Decision**: Keep the correction at the portal orchestration
boundary. That boundary already owns target aggregation, durable plan creation,
confirmation scope, submission scope, prechecks, and lock checks. If the
implementation needs another production file, stop and report the blocker.

## Design

### 1. Derive the Effective Retry Rows

`_aggregate_saved_options` will continue to validate all selected site rows.
For a retry only, it will collect the unique site identifiers from
`aggregate["targets"]`. It will retain selected rows whose identifiers occur in
that target set.

This order is required:

1. Build filtered aggregate targets.
2. Read and validate all selected rows.
3. Detect the active retry.
4. Filter rows by target site identifier.
5. Pass the filtered rows to `AggregateBuildInput`.

The row filter preserves selected-site order. It also keeps each site name
aligned with its identifier. The operator session retains the original
selected-site tuple.

### 2. Make the Durable Scope Authoritative

For an aggregate plan, `confirm_page` will read the durable operation before it
selects rows. It will use the durable `site_ids` for site validation, the site
count, and confirmation prechecks. Legacy access point confirmation will still
use the active selected sites.

`_load_submission_context` will keep the active organization, mode, signed
options, cloud session, and owner checks. For an aggregate plan, it will read
the owned durable operation and use its ordered `site_ids` for the submission
context and the initial lock refusal check. A missing or foreign durable
operation will fail closed before any precheck, lock write, or firmware write.
The durable scope must be a nonempty ordered subset of the active authorized
selection.

### 3. Keep Existing Destructive Safeguards

No design change applies to these controls:

- The exact `CONFIRM` word remains required.
- The write-enable gate remains first.
- Operator accountability remains required.
- Precheck capture records still use compare-and-set.
- Lock acquisition still creates or binds the same lock token.
- Each stored lock still uses compare-and-set on the operation record.
- Child submission still uses the existing idempotent aggregate service.
- Audit fields and retry lineage stay on the durable operation.

The exact-context check will compare the operation identity, organization,
durable ordered site scope, and nonce. It will not compare a filtered retry
against the wider operator selection.

### 4. Add Focused Contract Evidence

Extend `test_org_child_controls_routes.py`. Do not create another test file.
Add a socket-block fixture in this file. It must block direct TCP, error-code
TCP, UDP transmission, alternate socket transmission, and connection helpers.

The filtered retry scenario will start with a failed switch at site A and a
failed access point at site B. It will clear the switch family and then prove:

- The operator selection still contains sites A and B.
- The parent `site_ids` list contains site B only.
- The parent `site_names` mapping contains site B only.
- Each child scope refers to site B only.
- The confirmation shows one site and one device.
- Confirmation prechecks read site B only.
- Submission prechecks read site B only.
- The initial lock refusal check reads site B only.
- The durable lock map contains site B only.
- A lock for site A does not block the filtered retry.
- A stale nonce or durable record still fails before a firmware write.

Keep existing plain-save and fully targeted retry tests as regression evidence.
Use the existing in-memory run store to preserve compare-and-set behavior.

## Validation Plan

1. Implement the focused contract assertions and route correction.
2. Run the focused contract file with the socket block active.
3. Run Ruff and Black checks on the two changed Python files.
4. Run MyPy with the repository paths.
5. Run Bandit and Radon on `org_upgrade.py`.
6. Run the test-quality preflight and changed-test gate after the commits.
7. Run the STE linter on the three specification records and release note.

## Complexity Tracking

The implementation adds no module-level symbol. It reduces the touched
confirmation route and its value helper to 25 lines or fewer. The existing
save function also stays below 25 lines by reusing the existing durable write
helper. Three focused tests divide saved, confirmation, and submission evidence.
The existing module child debt remains recorded for separate remediation.
