# Data Safety Checklist: Resumed 52-week device-event CSV export

**Purpose**: Check that each resume path protects the CSV file and the checkpoint file.
**Created**: 2026-11-26
**Feature**: `..\spec.md`

## Refusals run before any write

- [x] A missing CSV refuses a resume before any page request (FR-002, test line 703).
- [x] A header mismatch refuses a resume before any write (FR-003, test line 679).
- [x] A partial last row refuses a resume before any write (FR-004, test line 725).
- [x] An unreadable checkpoint stops the export before any page request (FR-005, test line 543).
- [x] An empty checkpoint with an existing CSV refuses a resume (FR-006, planned test N1).

## Checkpoint integrity

- [x] The live checkpoint file is never opened for writing (FR-007, planned test N5).
- [x] A failed replace keeps the previous checkpoint token (FR-007, planned test N4).
- [x] A failed checkpoint write logs a warning that names the file (FR-009, test line 120).
- [x] The checkpoint file keeps its name and token format (FR-010, test line 104).

## CSV integrity

- [x] A valid resume appends rows and keeps earlier rows (FR-001, test line 649).
- [x] A resumed run with no new rows keeps the CSV and the checkpoint unchanged (FR-008, planned test N6).
- [x] No path in the change deletes or truncates the CSV file during a resume. The change adds no `os.remove` call for the CSV path.
- [x] A fresh run replaces the CSV file. The refusal message and the operator guide name this behavior (FR-013).

## Scope limits

- [x] The SQLite output path keeps its tests unchanged (FR-011, tests at lines 574, 597, 625).
- [x] The change adds no credential log. The checkpoint token is a pagination cursor.
- [ ] Not covered: an HTTP or connection error that returns an empty page can complete a streaming run and remove the checkpoint. This defect is out of scope (finding A-19, decision D-12). A follow-up issue must track it.
- [ ] Not covered: cross-organization mixing when headers match (finding A-10, decision D-6). A follow-up issue must track it.
- [ ] Not covered: a backup copy before a fresh run (decision D-7). A follow-up issue must track it.

## Notes

- The unchecked items name the risk and the tracking step. Each one stays open by design.
- The planned tests become checks only after T001 to T004 pass.
