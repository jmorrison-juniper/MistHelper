# Tasks: Bounded numeric inputs

**Input**: Design documents from `specs/3395-bounded-numeric-inputs/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), and [input-readers.md](contracts/input-readers.md).

**Tests**: The issue requires real reader regression tests and property tests.

## Phase 1: Setup

- [x] T001 Reserve the exact issue file set before edits. (delivered: specs/3395-bounded-numeric-inputs/plan.md)
- [x] T002 Complete the current specification and design templates. (delivered: specs/3395-bounded-numeric-inputs/spec.md)

## Phase 2: Foundational

- [x] T003 Add the real reader failure corpus. (delivered: tests/contract/upgrade_portal/test_bounded_numeric_routes.py)
- [x] T004 Add the page limit failure corpus. (delivered: tests/unit/upgrade_portal/test_bounded_numeric_inputs.py)
- [x] T005 Record the original failures for all three readers. (delivered: specs/3395-bounded-numeric-inputs/analysis.md)
- [x] T006 Add the semantic reader. (delivered: src/interfaces/portals/upgrade_portal/api/numeric_input.py)

## Phase 3: User Story 1 - Open a damaged picker link

- [x] T007 [US1] Repair the offset reader. (delivered: src/interfaces/portals/upgrade_portal/app/routes/select.py)
- [x] T008 [US1] Prove the first page and valid page rules. (delivered: tests/contract/upgrade_portal/test_bounded_numeric_routes.py)

## Phase 4: User Story 2 - Refuse a damaged capture tier

- [x] T009 [US2] Repair the tier reader. (delivered: src/interfaces/portals/upgrade_portal/app/routes/capture.py)
- [x] T010 [US2] Prove exact refusals with no launch. (delivered: tests/contract/upgrade_portal/test_bounded_numeric_routes.py)

## Phase 5: User Story 3 - Use the page limit fallback

- [x] T011 [US3] Repair the setting reader. (delivered: src/interfaces/portals/upgrade_portal/capture/clients.py)
- [x] T012 [US3] Prove the fallback, clamps, and properties. (delivered: tests/unit/upgrade_portal/test_bounded_numeric_inputs.py)

## Phase 6: Cross-Cutting Proof

- [x] T013 Prove zero oversized conversions and complete reader coverage. (delivered: tests/unit/upgrade_portal/test_bounded_numeric_inputs.py)
- [x] T014 Record the current local quality results. (delivered: specs/3395-bounded-numeric-inputs/analysis.md)
- [x] T015 Add the issue release note. (delivered: changelog.d/issue-3395-bounded-numeric-inputs.md)
- [x] T016 Analyze requirement coverage. (delivered: specs/3395-bounded-numeric-inputs/analysis.md)

## Dependencies & Execution Order

T003 and T004 depend on T002.
T005 depends on both failure corpora.
T006 depends on T005.
Each caller repair depends on T006.
Each story proof depends on its caller repair.
The final coverage and quality evidence depend on all three story proofs.

## Parallel Opportunities

The two failure corpus files can be prepared independently.
After T006, the three caller repairs do not share a file.
One agent performs this bounded repair without child agents.

## Implementation Strategy

Record failures first.
Implement one shared reader and preserve each caller's contract.
Run the same proof again before the wider local quality gates.
Keep publication outside these local implementation tasks until the parent authorizes it.
