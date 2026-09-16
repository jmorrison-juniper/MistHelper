# Implementation Plan: False Failure Reconciliation

**Branch**: `fix/2614-false-failure` | **Date**: 2026-09-15 |
**Spec**: [spec.md](./spec.md)

## Summary

Issue #2614 shows a data-quality defect in a terminal upgrade run. The stored
run says a gateway failed. Current cloud evidence proves that the gateway runs
the target firmware and that `fwupdate` succeeded.

The design extends the existing durable reconciliation path. It adds a narrow
failed-timeout path that can repair only the false-failure shape. It does not
open all terminal states.

## Technical Context

**Language**: Python 3.13.

**Dependencies**: Existing `mistapi>=0.64.0,<0.65`, Flask, ArangoDB action
repository, pytest, ruff, black, and mypy.

**Storage**: Existing ArangoDB run and action collections. No schema migration.

**Testing**: Unit tests under `tests/unit/upgrade_portal` and contract tests
under `tests/contract/upgrade_portal`.

**Target Platform**: Windows development and Linux container runtime.

**Project Type**: Flask backend and operator-facing web portal.

**Performance Goals**: One reconciliation reads one site statistics page and
writes one transaction.

**Constraints**:

- Do not use `listSiteDevices` for firmware decisions.
- Keep failed, complete, stopped, and cancelled distinct.
- Do not invent reboot or settle times.
- Do not edit vendor API documentation.

## Constitution Check

| Principle | Design result |
| - | - |
| I. Five-Item Rule | The work edits existing files only and adds one compliant spec directory. |
| II. Class-Based Architecture | `StoppingRunReconciler` owns the terminal repair. `SiteStatsFirmwareEvidenceReader` owns the cloud evidence read. |
| III. Safety-First | The existing typed `RECONCILE <run_id>` phrase and site guard stay in place. |
| IV. Full Deployment Pipeline | The plan includes local gates, a branch, a pull request, and CI checks. |
| V. Observability | New decisions log before reads and after results without secrets. |
| VI. Inline Comments | New executable lines include inline comments. |
| VII. Action Logging | New meaningful actions include before and after log messages. |

## Project Structure

### Documentation

```text
specs/2614-false-failure/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
src/upgrade_portal/api/run_controls/
├── routes.py
└── services/reconciliation.py

src/upgrade_portal/app/routes/
└── upgrade.py

src/upgrade_portal/persistence/actions/
└── models.py

tests/unit/upgrade_portal/test_runs/
└── test_reconciliation.py
```

**Structure Decision**: The fix stays in the existing reconciliation package,
because that package already owns durable run repair.

## Design

1. Add safe firmware proof fields to `TargetEvidence`.
2. Add a failed-timeout branch to `StoppingRunReconciler`.
3. Require every failed target to have matching running version evidence and
   `fwupdate` status `success`.
4. Write `complete`, repaired target rows, repaired phase rows, and a
   reconciliation record in the same transaction.
5. Keep `reboot_seen_at` and `settled_at` null when the gate did not measure
   them.
6. Let the run page show the reconciliation control for this narrow failed
   timeout shape.

## Files Changed

- `src/upgrade_portal/api/run_controls/services/reconciliation.py`
- `src/upgrade_portal/api/run_controls/routes.py`
- `src/upgrade_portal/app/routes/upgrade.py`
- `src/upgrade_portal/persistence/actions/models.py`
- `tests/unit/upgrade_portal/test_runs/test_reconciliation.py`
- `changelog.d/issue-2614-false-failure.md`

## Complexity Tracking

No new violation is introduced. Existing large modules receive surgical edits.

## Risk Controls

- The failed-run path accepts only an upgrade timeout error.
- The success path requires current positive firmware evidence.
- The transaction checks `_rev` and prior state before the run changes.
- The action row stores the evidence digest with the outcome.
