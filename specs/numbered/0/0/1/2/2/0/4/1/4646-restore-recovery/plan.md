# Implementation Plan: Reviewed Restore and Partial-Operation Recovery

**Branch**: `feat/4646-restore-recovery` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/4/1/4646-restore-recovery/`. Decimal 4646 equals `122041` in base 5. Padded to eight levels, it gives `0/0/1/2/2/0/4/1`, which matches the route in the task message.

## Summary

Add reviewed restore and partial-operation recovery to the converter state model. A restore reads one verified private backup. It compares each object with the current cloud state and assigns one decision per object. A write needs a fresh approval, the typed word `CONFIRM`, and a verified recovery backup. Each write waits for a read-back. A failed, partial, or indeterminate outcome stops later writes. Recovery reverses only the changes that this operation proves it made.

The record depends on issue 4636 for the state package. It depends on issue 4643 for the backup format. It depends on issues 4644 and 4645 for the gated apply path and the administrative gate. No production write is authorized by this record.

## Technical Context

**Language/Version**: Python 3.15 or newer. Source: `.github/copilot-instructions.md`, section Language and environment.

**Primary Dependencies**: `mistapi` version 0.64.1, pinned in `requirements.txt` line 129 (remote check 27). Standard library only for the new code. No dependency change.

**Storage**: Private JSON records under `data/cisco_config_converter/state/`, written by the store from issue 4636 (decision D-3 of issue 4636). Backup bodies stay in that private store.

**Testing**: pytest with a fake gateway and a fixed clock. The tests make no network call and use synthetic objects.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container that runs as UID 1000.

**Project Type**: Feature package inside the existing web portal interface package.

**Performance Goals**: At most 100 write decisions per operation. A write waits at most 60 seconds (decision D-15).

**Constraints**: No live Mist call. No direct HTTP to Mist. No `/api/` path. No change to shared portal files. No change to existing converter routes.

**Scale/Scope**: The change covers three object families and five commands. It adds one route function, four new modules, and one moved module. It adds one transition edge, one store method, and four test modules with 36 test functions.

## Constitution Check

*GATE: The plan passes this check when each rule passes or names an open gate with a reason.*

| Rule | Result | Reason |
| --- | --- | --- |
| Five-item rule, levels | Pass | Every new directory holds five children or fewer. See the capacity inventory. |
| Five-item rule, new code | Pass after R-4636-1 | Recovery code enters `state/lifecycle/recovery/`. No child is added to a noncompliant parent. Constitution line 42 (remote check 14). |
| Five-item rule, grandfathered debt | Pass | `src/interfaces/portals/` (six children) and `tests/contract/` (17 children) stay untouched. Remote checks 43 and 44. |
| Five-item rule, module names | Pass | `routes.py` reaches five top-level names. `operation.py` reaches four. |
| Five-item rule, functions | Pass with gate | Each function has five parameters or fewer and 25 lines or fewer. Each class holds five methods or fewer, including `__init__`. Record fields follow the schema of issue 4636. T015 runs the complexity gate with maximum 10. |
| Class-based architecture | Pass | Each behavior sits in a named class. The one function, `restore_route`, delegates to a class. |
| Safety-first input | Pass | Each command validates its input and returns at the first failure. |
| Destructive operations | Pass | The typed word `CONFIRM` and two confirmations apply (decision D-7). Constitution line 121 (remote check 15). Writes stay blocked until decision D-14 closes. |
| Secrets in logs | Pass | Logs hold IDs, digests, counts, and phases only (decision D-24). Principle III names this rule (remote check 105). |
| ASCII logs | Pass | Planned messages use ASCII only. |
| Structured logs | Fail until the owner confirms equivalence | Principle V names structlog or an equivalent (remote check 106). Issue 4636 open item U-2 has the same gap. |
| Inline comments | Fail now, pass after T008 to T014 | Each touched line needs a same-line comment. Principle VI requires it (remote check 107). |
| Action logging | Fail now, pass after T012 and T014 | Each write, read-back, and reconciliation step needs an info line and a debug line (FR-028). Principle VII requires it (remote check 108). |
| Technology: mistapi | Pass | Every Mist call uses a mistapi function. Constitution line 280 (remote check 16). |
| Technology: test containers | Pass | This record starts no container. |
| Technology: file paths | Pass | The store uses `pathlib.Path`. |
| Technology: operational store | Pass with open gate | The restore uses the store from issue 4636. It fails closed, reads back each write, and keeps records (decision D-9 of issue 4636). Constitution line 315 (remote check 17). Owner approval of the store policy remains open (issue 4636 U-3). |
| Technology: export boundary | Pass | No export is added. Backup bodies stay private (decisions D-24 and D-27). |
| Technology: database keys | Pass | Mist natural IDs identify each object. `ENDPOINT_PRIMARY_KEY_STRATEGIES` does not apply because the feature adds no export operation. |
| Technology: data directory | Pass | Private state stays under `data/`. |
| Technology: container security | Pass | No ownership change. |
| Development: menu operations | Pass | No menu is added. |
| Development: documentation | Pass with note | Operator documentation belongs to issue 4649 (parity task T033). The change adds a release note fragment. |
| Escalation | Pass | The change touches more than three files and more than two classes. This record exists. |
| Multi-agent: issue first | Pass | Issue 4646 exists and carries the `feature` and `web-portal` labels. |
| Multi-agent: branch | Pass | The branch is `feat/4646-restore-recovery`, from `main`. |
| Multi-agent: overlap | Pass with conditions | Seven open pull requests were scanned. Draft pull request 4208 owns `web_portal/app.py` and `web_portal/templates/base.html`. This plan edits neither file. No open pull request touches a converter path. |
| Multi-agent: pull request title | Pass | The title uses the Conventional Commits form (`.github/copilot-instructions.md` line 501, remote check 9). |
| Deployment pipeline | Pass for this record | Steps 10 to 12 (main build, revision check, and deployment) need separate owner approval. |
| Mist write evidence | Fail until evidence exists | Write-capable paths stay blocked until task T002 and issue 4634 record payload evidence. |

## Capacity and Structure Inventory

Remote child counts come from the recursive tree of `main` (11404 entries, not truncated) and from the contents API for `tests/contract`. Imports are not counted as top-level names. Issue 4636 counts classes and functions only.

| Directory | Children on main | After issue 4636 | After this record | Limit | Status |
| --- | --- | --- | --- | --- | --- |
| `src/interfaces/portals/` | 6 (remote check 43) | 6 | 6 | 5 | Grandfathered. Not touched. |
| `src/interfaces/portals/cisco_config_converter/` | 5 (remote check 39) | 5, with `state/` in place of `models.py` | 5 | 5 | At limit. No child added. |
| `src/interfaces/portals/cisco_config_converter/state/` | Absent (remote check 42) | 5 | 5 | 5 | At limit. No child added here. |
| `state/lifecycle/` | Absent | 5 | 5, with `recovery/` in place of `backup.py` | 5 | At limit. |
| `state/lifecycle/recovery/` | Absent | Absent | 5 | 5 | New package. |
| `tests/contract/` | 17 (remote check 44) | 17 | 17 | 5 | Grandfathered. Not touched. |
| `tests/integration/web_portal/cisco_config_converter/` | 2 (remote check 46) | 3 | 4 | 5 | Compliant. |
| `tests/integration/web_portal/cisco_config_converter/recovery/` | Absent (remote check 48) | Absent | 5 | 5 | New folder. |
| `routes.py` top-level names | 4 (remote check 38) | 4 | 5 | 5 | At limit. |

## Layout Dependency R-4636-1

Issue 4636 holds `state/lifecycle/` at five children. The recovery package needs one more child there. This record therefore needs issue 4636 to make one change before implementation starts:

1. Move `lifecycle/backup.py` to `lifecycle/recovery/backup.py`.
2. Create `lifecycle/recovery/__init__.py` with a module docstring only.

After that change, `lifecycle/` holds `__init__.py`, `approval.py`, `operation.py`, `transitions.py`, and `recovery/`. Issue 4636 needs no other change. Task T003 records the check. Implementation tasks T008 to T014 wait for this change.

## Replacement Layout

```text
src/interfaces/portals/cisco_config_converter/
  __init__.py                       unchanged
  conversion.py                     unchanged
  routes.py                         one import line and one function added
  presentation/                     unchanged, owned by issue 4647
  state/                            from issue 4636
    __init__.py
    intake.py
    proposal.py
    lifecycle/                      five children after R-4636-1
      __init__.py
      approval.py                   unchanged
      operation.py                  DecisionKind and ObjectDecision added
      transitions.py                one edge added
      recovery/                     new package
        __init__.py
        backup.py                   BackupManifest moved, objects mapping added
        planning.py                 RestorePlanner, RecoveryPlanner, RecoveryAction
        execution.py                RestoreExecutor, OutcomeReconciler, RestoreCommandDispatcher
        gateway.py                  MistRestoreGateway and the family mapping
    storage/                        from issue 4636, one method added to store.py

tests/integration/web_portal/cisco_config_converter/
  __init__.py                       unchanged
  test_routes.py                    unchanged
  state/                            from issue 4636
  recovery/                         new folder with five children
    __init__.py
    fakes.py
    test_restore_decisions.py
    test_restore_execution.py
    test_recovery.py
```

## Architecture

The flow runs in this order. Each step writes one record before the next step starts.

1. The command `propose` verifies the backup manifest. It reads each current object by natural ID and list page. It writes an operation record in phase `proposed` with one decision per object.
2. The command `approve` records the scope confirmation. It moves the record through `reviewed` to `approved` and writes one approval record bound to the proposal digest, the scope digest, and the operator. Decision D-14 refuses this step while the operator identity is unverified.
3. The command `execute` checks the approval under the scope lock. It writes a recovery backup of each target object and verifies it. It then moves the record to `executing`. The executor writes each object in family order. Each write is followed by a freshness check and a read-back.
4. A failed, partial, or indeterminate outcome stops the executor. The command `reconcile` reads each uncertain object and records the result.
5. The command `recovery-propose` lists reverse actions only for proven outcomes. The commands `approve` and `execute` then run the recovery with a new approval and a new recovery backup.

## File-by-File Change Map

| Path | Action | Content |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/backup.py` | Move in from `state/lifecycle/backup.py` | `BackupManifest` from issue 4636. Adds the private `objects` mapping (decision D-27). |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/planning.py` | Add | `RestorePlanner`, `RecoveryPlanner`, and `RecoveryAction`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/execution.py` | Add | `RestoreExecutor`, `OutcomeReconciler`, and `RestoreCommandDispatcher`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/gateway.py` | Add | `MistRestoreGateway` and the family mapping constant. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/operation.py` | Modify | Adds `DecisionKind` and `ObjectDecision`. Adds the fields `object_decisions`, `recovery_actions`, and `write_count` to `OperationRecord`. |
| `src/interfaces/portals/cisco_config_converter/state/lifecycle/transitions.py` | Modify | Adds the edge `reconciled` to `verified` (decision D-25). |
| `src/interfaces/portals/cisco_config_converter/state/storage/store.py` | Modify | Adds `acquire_scope_lock` (decision D-26). |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | Adds one import line and one function `restore_route` for the `GET` and `POST` methods under `/cisco-config-converter/admin/restore`. |
| `tests/integration/web_portal/cisco_config_converter/recovery/__init__.py` | Add | Package marker. |
| `tests/integration/web_portal/cisco_config_converter/recovery/fakes.py` | Add | `FakeMistGateway` and `FixedClock`. |
| `tests/integration/web_portal/cisco_config_converter/recovery/test_restore_decisions.py` | Add | 14 test functions for decisions and manifests. |
| `tests/integration/web_portal/cisco_config_converter/recovery/test_restore_execution.py` | Add | 15 test functions for approvals, writes, and outcomes. |
| `tests/integration/web_portal/cisco_config_converter/recovery/test_recovery.py` | Add | 7 test functions for recovery. |
| `changelog.d/issue-4646-restore-recovery.md` | Add | One release note fragment. The route is closed by default, and the fragment names the issue. |

Unchanged paths: `src/interfaces/portals/cisco_config_converter/presentation/`, `web_portal/app.py`, `web_portal/templates/base.html`, `deploy/.env.example`, `requirements.txt`, and `documentation/`.

## Dependencies

- No package is added. The pin stays at `mistapi==0.64.1` (remote check 27).
- Issue 4633 is closed. Its handover gate remains open for the shared portal files (issue 4224 comment of 2026-11-09).
- Issue 4634 must record payload evidence for each write before T011 starts.
- Issue 4635 must record the licensing decision before any reused source expression. This record reuses no source expression.
- Issue 4636 must complete R-4636-1 and the state package before T008 starts.
- Issue 4643 must store the normalized backup bodies in the private store (decision D-27) before T009 starts.
- Issues 4644 and 4645 supply the write path and the delete path before T012 and T013 start.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Issue 4636 does not adopt R-4636-1. | Implementation cannot start. | Task T003 checks the change. Implementation waits until it is merged. |
| Caution: A timed-out write completes after the operation stops. | A change lands outside the reviewed flow. | Reconcile before any next write (decisions D-16 and D-17). Test E11 covers the timeout. |
| Warning: An override replaces a change that another operator made. | A production field changes without the operator knowing. | Each override is recorded per object. The scope digest and the recovery backup cover it (decision D-8). |
| The SDK repeats a write after HTTP 429. | A duplicate create can appear. | A final HTTP 429 is indeterminate. Test E12 proves that reconciliation runs before any next write. |
| The Mist update merges fields instead of replacing them. | The read-back differs and the outcome is partial. | The full normalized body is written. The read-back compares digests (assumption U-2). |
| Reference semantics for `services` are unknown. | A policy can bind to the wrong object. | An unresolved reference blocks execution (decision D-11). |
| Shared `routes.py` causes merge conflicts. | Rebase work for each pull request. | Merge in the order of the parity overlap comment. Rebase before each push. |
| The identity gate never closes. | Restore stays unusable. | Accepted. Decision D-14 is owned by the owner. |
| The parity test path under `tests/contract/` breaks the five-child rule. | The nested package guard fails. | Decision D-3 places the tests in the integration folder. |
| Sibling records 4647 to 4649 are not complete. | The UI or the tests diverge. | Review each sibling record before T005 starts (unverified item U-12). |

## Rollback Steps

1. Revert the squash commit through a pull request on `main`.
2. Confirm that `routes.py` no longer defines `restore_route`.
3. Confirm that the `state/lifecycle/recovery/` package is gone and that `state/lifecycle/backup.py` is back.
4. Run `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py` and confirm that it passes.
5. Check the operation records under `data/cisco_config_converter/state/operation/` for the phase `executing`. Warning: Removing a recovery backup record can remove the only copy of a backup. Check the record type before any removal.

## Complexity Tracking

| Item | Type | Reason | Action |
| --- | --- | --- | --- |
| `routes.py` holds four top-level names (remote check 38). | Grandfathered. The change reaches the limit of five and does not exceed it. | The restore route adds one function. | Remediation R-1 splits the routes in a separate issue. |
| `src/interfaces/portals/` holds six children (remote check 43). | Grandfathered. Not touched. | Predates this record. | Remediation R-2 in `analysis.md`. |
| `tests/contract/` holds 17 children (remote check 44). | Grandfathered. Not touched. | Predates this record. | Remediation R-3 in `analysis.md`. The tests use the integration path (decision D-3). |
| `state/lifecycle/recovery/gateway.py` imports mistapi inside the state tree. | New design. | No compliant place exists in the converter package. A class in `routes.py` would add a sixth name. | The SDK compatibility guard covers the file. The design exception to issue 4636 decision D-13 is recorded in `research.md`. |
| `state/lifecycle/recovery/` package. | New design. | Keeps each level at five children. | None. |
