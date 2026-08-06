# Tasks: CountExporter

**Spec**: `specs/1802-count-exporter/spec.md`
**Issue**: #1802

## Phase 1: Discovery

- [X] T001 Resolve every count operation against the installed SDK, not the spec text.
- [X] T002 Group the operations by the identifier each one takes.
- [X] T003 Confirm no count operation already has a call site in first-party code.

## Phase 2: Implementation

- [X] T004 Add `src/export/count_exporter.py` with the `_CountOp` row type.
- [X] T005 Populate the org, site, and MSP tables from the resolved operation list.
- [X] T006 Add `_resolve`, which reports a missing module or operation instead of raising.
- [X] T007 Add `_choose`, which rejects a non-numeric and an out-of-range answer.
- [X] T008 Add `_persist`, routing the operationId to the primary key strategy.
- [X] T009 Add `_run`, calling the operation with the session and the identifier.
- [X] T010 Add the three scope entry points.

## Phase 3: Wiring

- [X] T011 Import `CountExporter` in `MistHelper.py`.
- [X] T012 Register menus 235, 236, and 237 in `menu_actions`.
- [X] T013 Mark all three `interactive_safe` in the operation registry.
- [X] T014 Add the 38 missing primary key strategies.

## Phase 4: Verification

- [X] T015 Confirm the table covers all 70 SDK count operations with none extra.
- [X] T016 Confirm every row resolves to a real function.
- [X] T017 Confirm every callable accepts a session and an identifier.
- [X] T018 Confirm all 70 strategies are registered and auto-increment.
- [X] T019 Add unit tests covering the table, the resolver, the chooser, and the writer.
- [X] T020 Run ruff, black, mypy, radon, and vulture.
- [X] T021 Run the full unit suite.
- [X] T022 Update the menu reference documentation.
