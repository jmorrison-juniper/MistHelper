# Tasks: typed operation outcomes

**Specification**: [spec.md](spec.md)  
**Plan**: [plan.md](plan.md)

## Phase 1: Preconditions

- [ ] Confirm pull request #4001 merged into `main`.
- [ ] Rebase the implementation worktree on the merged `main`.
- [ ] Record the changed file set before each implementation issue.
- [ ] Confirm that no implementation branch stacks on an unmerged branch.

## Phase 2: Contract

- [ ] Add `OperationOutcome` in `src/foundation/models/operation_outcome.py`.
- [ ] Define the four allowed states.
- [ ] Define message and detail behavior.
- [ ] Add mock-first tests for all four states.
- [ ] Confirm that the 1021 telemetry model is not implemented twice.

## Phase 3: Named handler migration

- [ ] Migrate the six named handlers that already return values.
- [ ] Add a typed return annotation to each migrated handler.
- [ ] Add tests for the six migrated handlers.
- [ ] Group the remaining 163 resolved named handlers by operation family.
- [ ] Migrate one operation family per serial issue.
- [ ] Add normal, empty, missing-input, and failed outcome tests for each family.
- [ ] Keep portal classification unchanged until all producers are ready.

## Phase 4: Lambda migration

- [ ] File a separate issue for the 112 lambda rows.
- [ ] Convert each lambda to a named function in `MistHelper.py`.
- [ ] Add an explicit return annotation to each new function.
- [ ] Return `OperationOutcome` from each converted function.
- [ ] Add focused tests for converted lambda behavior.
- [ ] Keep unrelated menu edits out of the hot-file batch.

## Phase 5: Portal cutover

- [ ] Change `_capture_and_run` to consume `OperationOutcome`.
- [ ] Preserve the typed state in REST status responses.
- [ ] Preserve the typed state in SSE events.
- [ ] Preserve the operator-facing completion message.
- [ ] Remove `NO_OUTPUT_REASON_MARKERS`.
- [ ] Remove `MISSING_INPUT_MARKERS`.
- [ ] Remove `HANDLED_ERROR_MARKERS`.
- [ ] Remove the private prose readers.
- [ ] Replace prose-dependent tests with typed contract tests.
- [ ] Prove that no fallback classification path remains.

## Phase 6: Defect-asserting tests

- [ ] Update `tests/unit/export/test_endpoint_family_exporter.py:592` to
  assert an explicit typed outcome.
- [ ] Update `tests/unit/marvis/actions/test_alarms.py:30,328` to remove
  the marker dependency and assert typed behavior.
- [ ] Update `tests/unit/marvis/actions/test_portal_contract.py:109,113` to
  test the typed portal contract.
- [ ] Add exception and missing-input edge cases.
- [ ] Verify that all tests use mocked or stubbed clients.

## Phase 7: Quality gates

- [ ] Run focused pytest commands for each changed test module.
- [ ] Run Ruff on changed Python files.
- [ ] Run Black in check mode on changed Python files.
- [ ] Run mypy on changed Python files.
- [ ] Run `python -m py_compile MistHelper.py`.
- [ ] Run `symbol-diff` for changed Python modules.
- [ ] Run the applicable repository quality gates before the final PR.
- [ ] Inspect `data/` for escaped artifacts.
- [ ] Confirm that no source or test file changes belong to the specification
  pull request.
