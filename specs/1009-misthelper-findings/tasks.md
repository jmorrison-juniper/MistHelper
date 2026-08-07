# Tasks: Clear the Length Findings in MistHelper.py

**Spec**: `specs/1009-misthelper-findings/spec.md`
**Issue**: #1009

## Phase 1: Baseline

- [X] T001 Record the score, grade, and the ten findings before the change.

## Phase 2: Argument-parser helpers

- [X] T002 Split `_add_safety_arguments` into destructive-safety and external-call flags.
- [X] T003 Split `_add_interface_arguments` into interface-mode and auth/backend flags.
- [X] T004 Split the systematic-test flags out of `_add_output_format_arguments`.

## Phase 3: Flag validation

- [X] T005 Extract the report-and-exit body of `_reject_unsupported_flag_variants`.

## Phase 4: Verification

- [X] T006 Confirm the four targeted functions left the report.
- [X] T007 Confirm the score rose above 77.0.
- [X] T008 Run ruff, black, and mypy.
- [X] T009 Confirm `MistHelper.py --help` still prints usage.
- [X] T010 Run the full unit and tools suites.
