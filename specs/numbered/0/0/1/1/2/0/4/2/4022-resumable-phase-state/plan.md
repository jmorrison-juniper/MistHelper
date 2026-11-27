# Implementation Plan: Persist resumable firmware phase state

**Branch**: `feat/4022-resumable-phase-state` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at route `specs/numbered/0/0/1/1/2/0/4/2/4022-resumable-phase-state/`. The eight-level base-5 route is `00112042` (RC-089).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

A stop leaves the operator without a safe next step. Phase entries exist, but no recovery point, no submission state, and no resume action exist. The plan adds a durable recovery point, a per-phase submission state, an in-place resume, and a site hold for unknown outcomes. Single-site work comes first. Multi-site resume waits for issue #4021.

## Technical Context

**Language and version**: Python 3.15 or newer, as `.github/copilot-instructions.md` states (RC-131).

**Primary dependencies**: The `mistapi` SDK is the only Mist interface (RC-131, RC-132). The installed SDK functions cited in the spec are RC-098 to RC-105. No new package is added.

**Storage**: The run document store, collection `upgrade_runs` (RC-064). Writes use the existing `write_run` read-back (RC-066, RC-065). The Redis site lock store uses the key template in `lock.py` (RC-041).

**Testing**: pytest. Changed test files are listed in tasks.md. The gate table in `.github/copilot-instructions.md` lists the commands (RC-131).

**Target platform**: Windows 11, macOS, and Linux. The upgrade capture portal runs on port 8056 (RC-131).

**Project type**: Single Python project with a Flask portal under `src/interfaces/portals/upgrade_portal/`.

**Performance goals**: A resume reads each device of one phase once, plus one job listing. The settle gate keeps its existing poll interval.

**Constraints**: Destructive operations need typed confirmation (RC-131, `constitution.md` Principle III). No firmware write runs without a verified write of the attempt record.

**Scale and scope**: About 20 source and template files, 11 test files, and 2 document files. The change touches one destructive path in two flows.

## Constitution Check

Each rule has a result and a reason. "Fail on main" marks a current defect that the change repairs.

| # | Rule | Result | Reason and evidence |
| - | - | - | - |
| I | Five-item rule | Pass | The plan adds no folder and no module file. It edits existing modules only. Existing violations stay as recorded debt (RC-114 to RC-127). See Complexity Tracking. |
| II | Class-based architecture | Pass | New behavior sits in named classes: `SubmissionOutcomeClassifier`, `RecoveryPointRecorder`, `ResumeReconciler`, and `SiteHoldGuard`. No wrapper function is added. |
| III | Safety first and typed confirmation | Fail on main, pass after T002 and T003 | Main maps a transport fault and a 5xx reply to a refusal (RC-022, RC-023, RC-024). Main releases the site lock at `failed` and `stopped` (RC-014, RC-015, RC-016). The resume uses typed `RESUME` (FR-007). Secrets are not logged (FR-029). |
| IV | Full deployment pipeline | Pass | `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` cover each step. `T-MERGE` waits for the container build and checks the revision label. |
| V | Observability and logging | Pass | New log lines use the module logger with `%s` values (D-10). New strings are ASCII only. |
| VI | Inline comments | Pass | Each executable line of new code carries an inline comment, as the constitution requires. The review gate checks this. |
| VII | Action logging | Pass | FR-029 and TC-11 check an info line before and a debug line after each resume action. |
| Tech | mistapi as the only Mist interface | Pass | Each Mist call uses a named SDK function (Mist Cloud Transport Requirements in spec.md). FR-028 forbids direct HTTP. `test_mistapi_sdk_compatibility.py` runs in `T-LOCAL-GATES` (RC-086). |
| Tech | Owned WebSocket transport | Not applicable | The change owns no WebSocket transport. |
| Tech | Test containers | Not applicable | No container starts for this change. |
| Tech | File paths | Pass | New code uses `pathlib` or the existing helpers. No path string is joined by hand. |
| Tech | Output backends | Not applicable | The change does not alter an export. |
| Tech | Operational store | Pass | See the operational store plan below. |
| Tech | Database keys | Pass | Each new record keys on the existing run key and on the natural Mist keys `org_id` and `site_id`. No endpoint export is added. |
| Tech | Data directory | Pass | The change writes no file under `data/`. The takeover audit file is unchanged. |
| Tech | Container security and Zscaler | Not applicable | The change alters no container. Builds run in GitHub Actions (RC-131). |
| Workflow | Menu operations | Not applicable | FR-030 forbids a new menu. |
| Workflow | Testing | Pass | TC-01 to TC-29 cover each functional requirement. See analysis.md. |
| Workflow | Security findings | Not applicable | No security tool reports a finding for this change. |
| Workflow | Documentation | Pass | `documentation/upgrade_capture_portal.md` and `README.md` change (RC-087, RC-128). The change adds a changelog fragment (RC-091). |
| Workflow | Audience standard | Pass | D-12 requires plain operator text with a next step. |
| Workflow | SpecKit escalation | Pass | The change touches a destructive operation. This record is the required specification. |
| Workflow | Multi-agent git | Pass | The branch starts from `main`. Labels follow the repository rules. The open-PR overlap check in analysis.md finds no overlap. |
| Governance | Compliance review | Pass | Principles VI and VII appear in the review checklist. The complexity table separates debt from new design. |

### Operational store plan

- **Fail-closed behavior**: A stop or a resume that cannot verify its write keeps the site hold and blocks new writes (FR-003, FR-004).
- **Verified persistence**: The portal reports success only after `verify_write` reads the document back (RC-065). The store write call is `write_run` (RC-066).
- **Backup and recovery**: The run document already persists in the document store. The recovery point is a field of that document. Each page load and each resume reads it again.
- **Retention**: Run retention does not change. The new fields follow the existing retention rule.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/2/0/4/2/4022-resumable-phase-state/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      resume-route.md
      stop-recovery-record.md
    checklists/
      requirements.md
      safety.md
```

### Source change map

The map lists each existing path that changes. Paths marked "read only" stay unchanged. No new source file or folder is created.

| Path | Action | Purpose | Evidence |
| - | - | - | - |
| `src/interfaces/portals/upgrade_portal/runtime/runs.py` | Modify | Add `RunState.RESUMING`, the resume transition, the `submission` phase key, and the stopped next-step text. | RC-001 to RC-009 |
| `src/interfaces/portals/upgrade_portal/upgrade/driver.py` | Modify | Write the recovery point at stop and failure. Keep the lock under a hold. Add the resume method and a start index for the cascade. | RC-014 to RC-019 |
| `src/interfaces/portals/upgrade_portal/app/wiring.py` | Modify | Classify each firmware reply. Write refusal and unknown outcomes. Verify each write. | RC-021 to RC-027 |
| `src/foundation/support/submission_certainty.py` | Modify | Add a settlement predicate that the org path, the lease, and the single-site path share. | RC-033, RC-034 |
| `src/interfaces/portals/upgrade_portal/api/run_controls/services/reconciliation.py` | Modify | Add `ResumeReconciler`. Refuse a complete outcome while a phase is unresolved. | RC-058 to RC-061 |
| `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py` | Modify | Add `RESUME_TEXT`, the resume route, and the hold guard on start and retry. | RC-050 to RC-055 |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/progress.html` | Modify | Add the recovery card, the resume control, and the retry suppression under a hold. | RC-069, RC-070 |
| `src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js` | Modify | Wire the resume control with the existing typed-control pattern of `initRunReconciliation`. | RC-129 |
| `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/record.py` | Modify | Add the `submission` key to the multi-site phase shape. Keep the observation rule. | RC-010 |
| `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py` | Modify | Use the shared settlement predicate before a lease release. Reset the recovery phase for observation. | RC-011, RC-012 |
| `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/locks.py` | Modify | Release a lock only after the shared settlement predicate allows it. | RC-013 |
| `src/operations/execution/firmware/aggregate_upgrade_service.py` | Modify after #4021 | Checkpoint each child job by phase. Resume only unresolved children. | RC-044 to RC-046 |
| `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | Modify after #4021 | Add the multi-site resume route and the hold guard. Use the shared settlement predicate. | RC-047 to RC-049 |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html` | Modify after #4021 | Show the stopped phase, the reason, and the next step. | RC-067, RC-068 |
| `documentation/upgrade_capture_portal.md` | Modify | Add `RESUME` to the phrase table. Add a resume section. Correct the lock life value. | RC-087, RC-088 |
| `README.md` | Modify | Update the upgrade capture portal section for the resume behavior. | RC-128 |
| `specs/1823-upgrade-capture-portal/contracts/site-lock.md` | Modify | Add the hold to the release rule at lines 105 and 106. | RC-039 |
| `changelog.d/issue-4022-resumable-phase-state.md` | Add | One release-note fragment for the change. | RC-091 |
| `src/operations/execution/firmware/upgrade_service.py` | Read only | Supplies `invoke_upgrade` and the accepted statuses. | RC-029 to RC-032 |
| `src/interfaces/portals/upgrade_portal/capture/store.py` | Read only | Supplies `write_run` and `verify_write`. | RC-064 to RC-066 |
| `src/interfaces/portals/upgrade_portal/runtime/lock.py` | Read only | Keeps the lock constants. The change keeps `LOCK_TTL_SECONDS` at 3600. | RC-041 to RC-043 |
| `src/interfaces/portals/upgrade_portal/runtime/signals.py` | Read only | Supplies `RunDispatchGate`. | RC-028 |

### Test change map

Each test file below already exists. No test file is added. Test names and cases appear in tasks.md.

| Path | Action | Cases | Evidence |
| - | - | - | - |
| `tests/unit/upgrade_portal/test_wiring_submitter.py` | Modify | TC-01 to TC-04 | RC-075 |
| `tests/unit/upgrade_portal/test_upgrade_driver.py` | Modify | TC-05 to TC-16 (TC-07 and TC-08 change) | RC-071, RC-072 |
| `tests/unit/upgrade_portal/test_org_cascade_walk.py` | Modify | TC-17, TC-18, TC-28 (TC-17 changes) | RC-073, RC-074 |
| `tests/unit/upgrade_portal/test_runs/test_reconciliation.py` | Modify | TC-19 | RC-083 |
| `tests/contract/upgrade_portal/test_retry_failed_run.py` | Modify | TC-20 to TC-22 | RC-082 |
| `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | Modify | TC-23, TC-24 | RC-081 |
| `tests/unit/upgrade_portal/test_org_phase_list_parity.py` | Modify | TC-25 (changes) | RC-077 |
| `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` | Modify | TC-26 (changes) | RC-078 |
| `tests/unit/firmware/test_aggregate_upgrade_service.py` | Modify after #4021 | TC-27 | RC-076 |
| `tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py` | Modify after #4021 | TC-29 | RC-080 |

## Architecture

```text
Stop request -> driver stops at the gate -> recovery point verified -> site hold set
  -> operator reads the run page -> operator repairs the cause -> operator types RESUME
  -> route checks the hold, the lock, and the typed word
  -> ResumeReconciler reads the live devices and the job list
  -> resume attempt verified -> run moves to resuming
  -> recovery phase: one firmware call or observation only
  -> cascade continues in phase order -> post-check -> final state
```

The driver keeps one thread for each run (RC-014, RC-015). The resume reuses the same dispatch gate for each firmware call (RC-026, RC-028). The resume does not start a new run.

## Dependencies

- Issue #4020 is closed. Pull request #4109 merged its single-site prerequisite as commit `acaae1ad` (RC-095).
- Issue #4021 is open. The multi-site resume depends on it.
- Issue #3726 is closed. Pull request #4701 merged its org-path fix as commit `53ad73cc` (RC-097).
- The pinned `mistapi` package is unchanged.
- The Redis site lock store and the document store are unchanged.

## Implementation Outline

1. Confirm that no site hold or resume state exists on `main`. Confirm each cited line (RC-001 to RC-020).
2. Fix the single-site classification and the lock rule. This fix repairs a current defect (T002, T003).
3. Add the state, the recovery point, and the verified writes (T004 to T007).
4. Add the reconciliation and the resume path (T008, T009).
5. Add the route, the hold guards, and the operator surfaces (T010 to T013).
6. Add the multi-site path after issue #4021 (T014, T015).
7. Update the documentation and the changelog (T016, T017).
8. Run the gates, open the pull request, wait for CI, and wait for owner approval (T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).

## Complexity Tracking

Grandfathered debt is listed first. New design is listed second.

| Type | Violation | Why needed | Simpler alternative rejected because |
| - | - | - | - |
| Grandfathered debt | `upgrade/` has 22 children, `runtime/` has 10, `upgrade/org_cascade/` has 7, `app/routes/` has 13, `operations/execution/firmware/` has 12 (RC-117 to RC-123) | The change edits existing modules in these folders. | A new package adds a child to a noncompliant parent, which the constitution forbids. |
| Grandfathered debt | `api/run_controls/` and `api/run_controls/services/` hold five children each (RC-115, RC-116) | The resume reconciler joins `reconciliation.py`. | A new file adds a sixth child, which the constitution forbids. |
| Grandfathered debt | `tests/unit/upgrade_portal/` has 168 children, `tests/contract/upgrade_portal/` has 66, `tests/e2e/upgrade_portal/` has 68 (RC-124 to RC-126) | The change adds cases to existing test files. | A new test file adds a child to a noncompliant folder. |
| Grandfathered debt | The `specs/1823-upgrade-capture-portal/` folder sits as a direct child of `specs/` (RC-039) | The site lock contract lives there. | Moving the contract changes a cited path and breaks the code comments. |
| New design | `RunState.RESUMING` and a new transition | The resume runs in place. | A child run needs a second lock owner and a second tracker row. The retry flow creates a new run after a fresh capture. |
| New design | A durable site hold in the run record | The Redis lock expires, and the quiet period allows a takeover (RC-038, RC-040, RC-041). | Relying on the Redis lock lets a takeover start a second write. |

## Risks and Mitigations

- **R-1: The cloud job list misses a job that a 5xx reply created.** Mitigation: FR-014 requires the operator to read the evidence. The hold stays when the list is empty and the versions are not proven. Unverified item U-02 records this risk.
- **R-2: The change keeps a site blocked after a stop.** Mitigation: the run page shows the phase, the reason, and the proof. The operator resolves the phase through RESUME.
- **R-3: A test pins the old wrong behavior.** Mitigation: TC-07, TC-08, and TC-17 get an audit before the change. Each assertion that pins the old behavior is replaced in the same change.
- **R-4: A changed string breaks a parity test.** Mitigation: FR-026 and TC-25 and TC-26 require the same change to update the test.
- **R-5: The state machine rejects a stored `resuming` run after a rollback.** Mitigation: see the rollback warning below.
- **R-6: The multi-site resume starts before issue #4021 defines the gate.** Mitigation: T014 depends on #4021. The task status stays absent until the owner approves D-11.
- **R-7: A stop lands during the resume.** Mitigation: the dispatch gate (RC-026, RC-028) makes the stop and the write one action for each run.

## Rollback

1. Revert the squash commit on `main` with a new pull request. Do not force-push.
2. Confirm that no run holds the `resuming` state before the revert.
3. Restore the release rule at `stopped` and `failed` only after the owner approves the rollback.

Warning: A rollback while a run holds the `resuming` state can strand that run. The older state machine rejects the unknown state name. Finish or stop each resuming run before the revert.

Warning: A rollback that restores the release at `failed` returns the unknown-outcome defect (RC-014, RC-016, RC-022 to RC-024).
