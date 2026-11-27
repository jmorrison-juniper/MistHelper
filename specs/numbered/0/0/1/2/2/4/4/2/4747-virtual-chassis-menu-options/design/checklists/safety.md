# Safety Checklist: Virtual Chassis Menu Guidance

**Purpose**: Confirm that the change keeps every safety control of the virtual chassis conversion path.
**Created**: 2026-11-26
**Feature**: `plan.md` and `design/contracts/vc-menu-guidance.md`

## Confirmations and calls

- [x] CHK001 The bulk confirmation still accepts only the literal `CONVERT` (virtual_chassis.py line 380, RC-16).
- [x] CHK002 The single confirmation still accepts only the literal `CONVERT` (line 868, RC-17).
- [x] CHK003 The single conversion call and the bulk conversion call keep their arguments (lines 477 and 588, RC-14 and RC-15).
- [x] CHK004 The new tests call only the usage-note helper and the response handler. Neither helper takes an API session (RC-10 and RC-103).

## Destructive categories

- [x] CHK005 Menus 161 and 162 keep the `destructive` category (RC-34 and RC-35).
- [x] CHK006 Menu 14 keeps the `resource_intensive` category (RC-36).
- [x] CHK007 The safe sweep excludes the three menus (RC-98).

## Output and logs

- [x] CHK008 Every new string uses ASCII characters only (Principle V, RC-69).
- [x] CHK009 The change adds no log line that could carry a secret. It adds no logger call.
- [x] CHK010 The typed prompts keep their context strings. The change edits no prompt text.

## Warnings and cautions

- [x] CHK011 Each statement about irreversible harm starts with `Warning:` (spec Safety Statements).
- [x] CHK012 Each statement about recoverable harm starts with `Caution:` (spec Safety Statements).

## Merge controls

- [x] CHK013 The `needs-human-review` label stays on the issue (issue 4747 labels).
- [x] CHK014 The `auto-merge` label stays off (D-11, T-MERGE).
- [x] CHK015 The orchestrator authorizes publication and merge before each step (T-PR, T-MERGE).
