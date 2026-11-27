# Test Isolation Checklist: Dash module isolation for map callback tests

**Purpose**: Verify the fixture change in each slice file before publication.
**Created**: 2026-11-26
**Feature**: spec.md, plan.md, and design/quickstart.md

## State Restoration

- [ ] ISO01 The fixture records whether the dash entry exists before it installs the stub (FR-002). Check by reading the edited fixture against the target in plan.md.
- [ ] ISO02 The restore reuses the saved object, including the None entry (FR-003). Check with QS-02 and QS-03.
- [ ] ISO03 An absent entry is removed with pop (FR-003). Check with QS-03.
- [ ] ISO04 The restore sits in a finally block (FR-004). Check by reading the edited fixture.

## Module Scope and Symbols

- [ ] ISO05 No module-level assignment to sys.modules['dash'] remains (FR-001). Check with QS-02.
- [ ] ISO06 No module-level name is added or removed (FR-012). Check with QS-12.
- [ ] ISO07 The launcher import keeps its noqa comment (FR-006). Check with QS-08, which applies rule RUF100.
- [ ] ISO08 The `_build_dash_stub` function is unchanged (FR-005). Check with QS-12 and the diff of the slice file.

## Assertions and Baseline

- [ ] ISO09 The wave A checks at lines 134 and 181 match FR-007 and FR-008. Check with QS-04.
- [ ] ISO10 The wave E2 checks at lines 174 and 178 match FR-010. Check with QS-04.
- [ ] ISO11 The baseline file has no diff (FR-017). Check with QS-16.
- [ ] ISO12 The test-quality gate reports zero new findings (FR-019). Check with QS-11.

## Logging and Comments

- [ ] ISO13 The fixture logs info before and debug after each state change, with %s arguments (FR-014). Check by reading the edited fixture.
- [ ] ISO14 Each changed line has an inline comment and fits 120 characters (FR-015). Check with QS-08 and a read of the diff.
- [ ] ISO15 The logging import sits inside the fixture (FR-013). Check with QS-12.

## Notes

- Each item stays open until the slice worktree passes its local gates in quickstart.md.
