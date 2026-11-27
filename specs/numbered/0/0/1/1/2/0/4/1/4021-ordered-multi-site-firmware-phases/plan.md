# Implementation Plan: Ordered Multi-Site Firmware Families

**Branch**: `feat/4021-ordered-multi-site-firmware-phases` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/1/2/0/4/1/4021-ordered-multi-site-firmware-phases/spec.md`

**Input**: Numeric specification route `0/0/1/1/2/0/4/1` (base-5 value 4021). Route check: 4021 equals 112041 in base 5, which the eight-level route `00112041` encodes.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The multi-site aggregate service sends every child in one loop. It places access point children first, and it continues after a refusal. This plan changes the aggregate service so that it sends one family at a time. A family gate separates each family from the next. A refusal, an unknown outcome, a failed gate, a lock loss, or a cancellation stops the run and writes a stop record. The change reuses the single-site order, the phase limit, and the existing mistapi calls. It adds no module and no endpoint.

## Technical Context

**Language/Version**: Python 3.15 or newer (constitution Technology constraints, remote row 59).

**Primary Dependencies**: `mistapi==0.64.1` (requirements pin, row 68). The installed package has the functions listed in remote rows 75-80.

**Storage**: The durable run store uses compare-and-set through `RunStore.read_run` and `RunStore.compare_and_set_run`. The aggregate service calls it in `submit` (row 1). The route passes the store (row 27).

**Testing**: `pytest` with doubles only. The targeted files are `tests/unit/firmware/test_aggregate_upgrade_service.py`, `tests/unit/upgrade_portal/test_org_cascade_walk.py`, and `tests/contract/upgrade_portal/test_org_upgrade_routes.py`.

**Target Platform**: Windows 11, macOS, and Linux. The upgrade capture portal runs one Gunicorn worker process (row 16 docstring context).

**Project Type**: Python backend library with a Flask route. No browser change.

**Performance Goals**: One family gate waits at most 1800 seconds (row 20). The gate polls every 20 seconds (row 22).

**Constraints**: No live Mist request during implementation tests. No new endpoint. No new module under a noncompliant folder (Complexity Tracking).

**Scale/Scope**: Three families. Each family covers every selected site. The change touches three production modules and about 17 test files.

## Constitution Check

The table records each rule with its result and reason. Remote rows give the evidence.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (row 55) | Pass with recorded debt | The change adds no direct child to a noncompliant folder. It edits existing modules only. Existing violations are listed in Complexity Tracking. |
| II. Class-based architecture (row 55 section II) | Pass | The gate adapter and the run registry are classes. No standalone wrapper function delegates to a method. |
| III. Safety-first (row 56) | Pass | The destructive confirmation stays unchanged. Menu 239 remains in the destructive set (row 54). Stop sentences hold no host, token, or cloud body. |
| IV. Full deployment pipeline (row 55 section IV) | Pass as planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run the pipeline. The change adds no auto-merge label. |
| V. Observability (row 58) | Pass as planned | Each log line uses ASCII text. Each log line names the family and the run. |
| VI. Inline comments (row 57) | Pass as planned | Each changed executable line receives an inline comment. Each touched block receives comments. |
| VII. Action logging (row 58) | Pass as planned | Each cloud call and each family gate wait receives an info line before it and a debug line after it. |
| Technology: mistapi only (row 59) | Pass | The change reuses `upgradeOrgDevices`, `upgradeSiteDevices`, `upgradeDevice`, and `upgradeOrgSsrs` (rows 64-67, 75-80). |
| Technology: test containers (row 59) | Pass | No container starts for this change. |
| Technology: file paths (row 59) | Pass | The change adds no path. The changelog fragment uses the existing directory rule. |
| Operational store (row 60) | Pass | The parent record uses compare-and-set (rows 1, 81). A failed write stops the run. The stop record persists before the background run ends. |
| Data directory (row 59) | Pass | The change writes no product output outside the existing run record. |

## Design Summary

The detailed decisions appear in `design/research.md`. The summary follows.

1. **Family order (D-1)**: The order reuses `upgrade_service.PLAN_FAMILY_ORDER` (row 9). An SSR child maps to the gateway family.
2. **Gate seam (D-2, D-15)**: The aggregate module defines a portal-neutral `FamilySettleGate`. The phase watch module supplies `OrgFamilyGate`. The gate wraps the existing `PhaseSettleGate` with the 1800-second phase limit (rows 16, 20, 21).
3. **Stop rule (D-3)**: A refusal, an unknown outcome, a failed gate, a lock loss, or a cancellation stops the family and every later family.
4. **Background run (D-4)**: The route checks the request synchronously. The background run sends the families. The route returns the job page.
5. **Claims (D-5)**: The parent claim covers one family send. No parent claim covers a gate wait. The wait marker refreshes every 20 seconds.
6. **Watch handoff (D-6)**: The phase watch reads the stored family gate result. It does not start a second wait.
7. **Locks (D-7)**: The existing release rule stays unchanged (rows 25, 28). The lease renews the locks during each wait (row 29).
8. **Process loss (D-8)**: A stale wait marker ends in a `process_lost` stop (row 82).
9. **Manifest (D-9, D-10)**: The issue manifest adds `org_upgrade.py` and `walk.py`. No module is added.

## Flow

The flow below describes the intended run.

```text
POST route
  -> synchronous check (no claim, no cloud call)
  -> background run starts (one thread for each operation)
       for family in gateway, switch, ap:
         if family has no child: record skipped, continue
         claim parent for this family send
         for child in family (plan order):
            refresh site locks
            claim child, send once, store the reply
            if refused or unknown or lock lost: write stop record, end run
         release parent claim
         wait for family gate (renew locks, refresh wait marker)
         if gate is not settled: write stop record, end run
  -> phase watch reads stored family gate results (no second wait)
```

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `src/operations/execution/firmware/aggregate_upgrade_service.py` | Modify | Add the family rank, the `FamilySettleGate` protocol, and the `FamilyGateResult` type. Order the children in `_children`. Add the family loop to `submit`. Add the stop rules to `_submit_child`. Add the stop record writer. Add the process-lost branch to `_recover_for_status`. Map `family_waiting` to `running` in `_aggregate_state`. Add the stop sentences. |
| `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py` | Modify | Add `OrgFamilyGate` around `OrgPhaseGates`. Add `AggregateRunRegistry` to start one background run for each operation. Make `OrgCascade._settle` read the stored family gate result. Update the module docstring that says the watch sends no firmware request. |
| `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | Modify | Split `_send_aggregate` into the synchronous check and the background start. Pass the lock lease to the background run. Keep the existing error mapping for the synchronous check. |
| `tests/unit/firmware/test_aggregate_upgrade_service.py` | Modify | Rewrite the two defect-locking tests. Add 12 tests. |
| `tests/unit/upgrade_portal/test_org_cascade_walk.py` | Modify | Add 2 tests for the stored result and the lock renewal. |
| `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | Modify | Add 1 route test. Change any assertion that the change breaks. |
| `tests/integration/test_aggregate_upgrade_flow.py` | Modify | Change the persisted partial-status assertion only if the stored state changes. |
| Files in research rows 36-50 | Verify, modify only broken assertions | Run each file. Change only the assertion that the new rule breaks. |
| `changelog.d/issue-4021-ordered-multi-site-firmware-phases.md` | Add | One release-note fragment with one bullet for the change. |

## Dependencies

No package is added or changed. The change uses `mistapi==0.64.1` as it is (row 68).

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A family gate wait exceeds the claim lease. | The parent claim covers one family send only (D-5). The wait marker refreshes every 20 seconds. |
| The route cannot return a synchronous error after the background start. | The route runs the replay check before the start. A later failure writes the stop record. |
| The phase watch and the background run both wait for one family. | The phase watch reads the stored result and makes no second wait (D-6). A test proves it. |
| A stored result is stale after a process restart. | The process-lost branch writes a stop record. No child receives a resend (D-8). |
| Locks expire during a long wait. | The lease renews the locks during each wait (D-7). A test proves the renewal. |
| Existing tests lock the defect. | Two tests change in the same commit. Each changed test names the replaced behavior (FR-020). |
| The manifest grows beyond the issue. | The owner reviews the expanded manifest before merge (D-9). |

Warning: a wrong family order can remove the upstream path of many devices at once. The change requires a human review before merge.

## Rollback

1. Revert the squash commit of the pull request on `main`.
2. Confirm that no run has a `family_stop` field that the reverted code cannot read. The reverted code ignores unknown fields.
3. If a run stopped under the new rules, read the stop record and the child rows before any new action.
4. Do not resend a child with the status `submission_unknown`. Read the cloud state first.

Warning: a rollback does not undo a firmware write that the cloud accepted. Read each child before a new action.

## Complexity Tracking

The table separates grandfathered debt from the new design.

| Violation | Status | Why it stays | Remediation action |
| - | - | - | - |
| `src/operations/execution/firmware/` holds 13 direct children | Grandfathered debt, touched by no new module | A new module there violates the rule. The change edits an existing module. | R-1: move the aggregate family code into a compliant nested package in a separate issue. |
| `src/operations/execution/` holds 7 direct children | Grandfathered debt | No new child is added. | Covered by R-1. |
| `src/interfaces/portals/upgrade_portal/app/routes/` holds 14 direct children | Grandfathered debt | The change edits `org_upgrade.py` only. | R-2: split the multi-site route handlers in a separate issue. |
| `src/interfaces/portals/upgrade_portal/upgrade/` holds 23 direct children | Grandfathered debt | The change edits `org_cascade/walk.py`, which sits in a nested package. | R-3: group the upgrade modules in a separate issue. |
| `aggregate_upgrade_service.py` holds more than five top-level names | Touched existing violation | The change adds names to the module. | R-1 covers this module. |

The counts come from a local checkout at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, which equals remote `main`. The HEAD check appears in `design/research.md`, section 4.

## Structure Decision

The change adds only the record files and one changelog fragment. Each production change edits an existing module. The record folder `specs/numbered/0/0/1/1/2/0/4/1/4021-ordered-multi-site-firmware-phases/` follows the route rule. Its parent `0/0/1/1/2/0/4/` holds two folders today, `0` for issue 4020 and `4` for another existing record. The new folder `1` makes three children, which meets the five-child limit.
