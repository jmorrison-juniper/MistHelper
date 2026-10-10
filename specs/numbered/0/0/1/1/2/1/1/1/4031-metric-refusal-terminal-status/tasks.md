---
description: "Implementation and verification tasks for Metric Refusal Terminal Status"
---

# Tasks: Metric Refusal Terminal Status

**Input**: `plan.md`, `spec.md`, `data-model.md`, `research.md`, and
`quickstart.md` in this feature directory.

**Scope boundary**: Product and test work is limited to the two metric
operation modules, the two named focused test modules, and exactly one issue
#4031 changelog fragment. `metric_refusals.py` is read-only context and may be
inspected to verify the existing refusal contract, but MUST NOT be edited.
`web_portal/services/operation.py` MUST NOT be edited or included in the
implementation manifest.

**Tests**: Required by FR-011, FR-012, and the quickstart validation guide.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the existing implementation and validation boundary
without changing product behavior.

- [ ] T001 Read `specs/numbered/0/0/1/1/2/1/1/1/4031-metric-refusal-terminal-status/plan.md`, `specs/numbered/0/0/1/1/2/1/1/1/4031-metric-refusal-terminal-status/spec.md`, `specs/numbered/0/0/1/1/2/1/1/1/4031-metric-refusal-terminal-status/data-model.md`, `specs/numbered/0/0/1/1/2/1/1/1/4031-metric-refusal-terminal-status/research.md`, and `specs/numbered/0/0/1/1/2/1/1/1/4031-metric-refusal-terminal-status/quickstart.md` to confirm the marker, ordering, refusal semantics, and validation commands.
- [ ] T002 [P] Inventory the current `_run_export`, `_collect_metrics`, and refusal-report call sites in `src/operations/exporting/export/site_insights/site_metric_operation.py` and `src/operations/exporting/export/site_insights/device_metric_operation.py`; record that successful rows are finalized before terminal status logging.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm shared contracts and protect the user-approved file
boundary before story work begins.

- [ ] T003 [P] Verify the existing refusal-recording and reporting contract in `src/operations/exporting/export/site_insights/metric_refusals.py` without modifying that file; confirm that `MetricRefusalLog.refusals` is the post-batch condition and that refusal details remain available.
- [ ] T004 Establish the changed-file manifest in `specs/numbered/0/0/1/1/2/1/1/1/4031-metric-refusal-terminal-status/quickstart.md` terms: the two operation modules, the two focused test modules, and exactly one `changelog.d/issue-4031-metric-refusal-terminal-status.md` fragment; explicitly exclude `web_portal/services/operation.py`, `metric_refusals.py`, and unrelated files.

**Checkpoint**: The existing helper and portal classifier are understood, and
the implementation boundary is fixed before user-story changes begin.

## Phase 3: User Story 1 - Report refused metrics as a failed operation (Priority: P1) 🎯 MVP

**Goal**: Menus 74 and 76 continue the batch, preserve valid rows, report each
refusal, and emit exactly one existing `Failed to` handled-error marker after
finalization whenever at least one refusal occurred.

**Independent Test**: In each focused module, replay successful responses mixed
with repeated HTTP 400 responses. Assert that every successful row is written,
every refused metric is absent from writer rows, later requests execute, every
refusal is reported, and exactly one `Failed to` marker is logged after the
batch.

### Tests for User Story 1

- [ ] T005 [P] [US1] Add Menu 74 mixed-batch tests in `tests/unit/export/site_insights/test_site_insight_path.py` using fresh successful and refused responses to assert preserved annotated rows, excluded refusal bodies, repeated refusal details, continued later requests, retrieved-row counts, and one `Failed to` marker.
- [ ] T006 [P] [US1] Add Menu 76 mixed-batch tests in `tests/unit/export/site_insights/test_device_metric_refusals.py` using device-scoped responses to assert preserved annotated rows, excluded refusal bodies, repeated refusal details, continued later requests, device labels, retrieved-row counts, and one `Failed to` marker.

### Implementation for User Story 1

- [ ] T007 [US1] Update `src/operations/exporting/export/site_insights/site_metric_operation.py` in `_run_export` so `_finalize()` and the existing `MetricRefusalLog.report(context.site_name)` run unchanged first, then emit one ASCII `ERROR` log containing the existing `Failed to` marker only when `self._refusal_log.refusals` is non-empty; do not alter request, row, count, export, or exception behavior.
- [ ] T008 [P] [US1] Update `src/operations/exporting/export/site_insights/device_metric_operation.py` in `_run_export` so `_finalize()` and the existing `MetricRefusalLog.report(context.device_name)` run unchanged first, then emit one ASCII `ERROR` log containing the existing `Failed to` marker only when `self._refusal_log.refusals` is non-empty; do not alter device filtering, request, row, count, export, or exception behavior.
- [ ] T009 [P] [US1] Add exactly one release-note fragment at `changelog.d/issue-4031-metric-refusal-terminal-status.md` stating that Menus 74 and 76 now report failed terminal status after refused metric requests while retaining successful partial rows.

**Checkpoint**: User Story 1 is complete when both menu paths independently
produce a non-Complete handled-error signal for refusals without losing valid
partial output.

## Phase 4: User Story 2 - Preserve successful and non-refused behavior (Priority: P2)

**Goal**: The terminal-status repair changes only refusal outcomes; fully
successful, empty, transport-exception, cancelled, and empty-metric behavior
remains unchanged.

**Independent Test**: Run both focused modules with fully successful, mixed
successful/empty/refused, transport-exception, empty-metric, and cancelled
fixtures. Compare writer payloads, counts, scope labels, and log markers;
no-refusal runs must not emit the refusal failure marker.

### Tests for User Story 2

- [ ] T010 [US2] Extend `tests/unit/export/site_insights/test_site_insight_path.py` with no-refusal success assertions, mixed empty/refused response assertions, transport-exception regression coverage, empty-metric/cancel behavior checks, and an ordering assertion that the terminal `Failed to` marker follows finalization and refusal reporting.
- [ ] T011 [US2] Extend `tests/unit/export/site_insights/test_device_metric_refusals.py` with no-refusal success assertions, mixed empty/refused response assertions, transport-exception regression coverage, empty-metric/cancel behavior checks, device scope-label checks, and an ordering assertion that the terminal `Failed to` marker follows finalization and refusal reporting.

## Phase 5: Polish & Cross-Cutting Verification

**Purpose**: Prove focused behavior, static quality, and the exact file
boundary without changing the portal or shared refusal helper.

- [ ] T012 [P] Run `python -m pytest tests/unit/export/site_insights/test_site_insight_path.py -q` and verify all Menu 74 refusal, preservation, and no-refusal assertions pass.
- [ ] T013 [P] Run `python -m pytest tests/unit/export/site_insights/test_device_metric_refusals.py -q` and verify all Menu 76 refusal, preservation, and no-refusal assertions pass.
- [ ] T014 [P] Run `python -m py_compile src/operations/exporting/export/site_insights/site_metric_operation.py src/operations/exporting/export/site_insights/device_metric_operation.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/export/site_insights/test_device_metric_refusals.py` and record a successful compile.
- [ ] T015 [P] Run `python -m black --check src/operations/exporting/export/site_insights/site_metric_operation.py src/operations/exporting/export/site_insights/device_metric_operation.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/export/site_insights/test_device_metric_refusals.py` and `python -m ruff check src/operations/exporting/export/site_insights/site_metric_operation.py src/operations/exporting/export/site_insights/device_metric_operation.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/export/site_insights/test_device_metric_refusals.py`; resolve only findings in the approved files.
- [ ] T016 Verify `git diff --name-only` and `git status --short` contain only the two metric operation modules, the two focused test modules, exactly one `changelog.d/issue-4031-metric-refusal-terminal-status.md` fragment, and this feature directory's design artifacts; confirm `web_portal/services/operation.py` and `src/operations/exporting/export/site_insights/metric_refusals.py` are absent.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No implementation dependency; T001 and T002 may run in parallel.
- **Foundational (Phase 2)**: Depends on T001 and T002; T003 and T004 may run in parallel once the design documents are loaded.
- **User Story 1 (Phase 3)**: Depends on Phase 2. T005 and T006 are independent test-file tasks and may run in parallel; T007 and T008 are independent implementation-file tasks and may run in parallel after the tests are prepared. T009 is independent of the Python edits and may run in parallel.
- **User Story 2 (Phase 4)**: Depends on the User Story 1 implementation and uses the same two focused test files, so T010 and T011 are sequential file extensions rather than parallel tasks.
- **Polish (Phase 5)**: Depends on User Stories 1 and 2. T012, T013, T014, and T015 may run in parallel; T016 runs after all edits and checks.

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational phase completion; no dependency on User Story 2.
- **User Story 2 (P2)**: Depends on the User Story 1 terminal-marker implementation because its regression assertions verify the repaired paths while preserving all prior behavior.

### Dependency Graph

```text
T001 + T002 -> T003 + T004
T003 + T004 -> T005 + T006
T005 + T006 -> T007 + T008
T004 -> T009
T007 + T008 -> T010 + T011
T007 + T008 + T009 + T010 + T011 -> T012 + T013 + T014 + T015
T012 + T013 + T014 + T015 -> T016
```

The graph expresses the critical ordering: understand the refusal contract,
write the P1 behavior tests, implement both operation markers, add P2
regressions, then run the complete focused verification and scope check.

## Parallel Execution Examples

### User Story 1

```text
Parallel batch A:
  T005 -> tests/unit/export/site_insights/test_site_insight_path.py
  T006 -> tests/unit/export/site_insights/test_device_metric_refusals.py
  T009 -> changelog.d/issue-4031-metric-refusal-terminal-status.md

Parallel batch B after the P1 tests are prepared:
  T007 -> src/operations/exporting/export/site_insights/site_metric_operation.py
  T008 -> src/operations/exporting/export/site_insights/device_metric_operation.py
```

### User Story 2

```text
The two regression-test tasks share the P1-modified focused test modules and
should be completed sequentially to avoid edit conflicts:
  T010 -> tests/unit/export/site_insights/test_site_insight_path.py
  T011 -> tests/unit/export/site_insights/test_device_metric_refusals.py
```

### Verification

```text
After T010 and T011:
  T012, T013, T014, and T015 can run in parallel.
  T016 runs last and verifies the final manifest and prohibited-file boundary.
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phases 1 and 2 to lock the refusal contract and file boundary.
2. Add the two focused mixed/refusal test cases in Phase 3.
3. Add the conditional post-report marker to both operation modules.
4. Add the single changelog fragment.
5. Run the two focused tests and stop for MVP validation: successful partial
   rows remain exported and refused requests produce the existing failed
   terminal signal.

### Incremental Delivery

1. Deliver User Story 1 as the smallest operator-visible fix.
2. Add User Story 2 regression coverage for all no-refusal and legacy edge
   paths.
3. Run static checks and the exact diff-scope verification.
4. Keep `web_portal/services/operation.py` and
   `metric_refusals.py` unchanged throughout.

## Independent Test Criteria

- **US1**: Menu 74 and Menu 76 mixed batches preserve all valid rows, exclude
  all refusal bodies, execute later metrics, report all refusal details, and
  emit exactly one `Failed to` marker after finalization.
- **US2**: Fully successful batches preserve rows, counts, labels, and success
  behavior; empty payloads and transport exceptions retain their prior
  semantics; no-refusal batches emit no refusal failure marker; cancel and
  empty-metric paths remain unchanged.

## Notes

- Every task uses the required `- [ ] T###` checklist form.
- `[P]` appears only on tasks that touch different files or are independently
  executable without incomplete task dependencies.
- `[US1]` and `[US2]` labels appear on every task in a user-story phase.
- Every implementation or verification task names an explicit file path or
  command path.
- No task authorizes editing `web_portal/services/operation.py` or
  `metric_refusals.py`.
