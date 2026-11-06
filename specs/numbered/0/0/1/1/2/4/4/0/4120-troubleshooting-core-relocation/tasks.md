# Tasks: Cohesive troubleshooting modules

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Confirm current base, prerequisites, and file ownership for `src/mist/intelligence/troubleshooting/core/`.
- [x] T002 Resolve the managed specification route and prepare the isolated environment with `scripts/bootstrap_worktree.py`.

## Phase 2: Foundation

- [x] T003 Record the destination and identity contracts in `spec.md` and `design/data-model.md`.

## Phase 3: Subject-specific modules

**Goal**: Complete US1 without losing declarations.
**Independent test**: Canonical imports succeed and all obsolete imports fail.

- [x] T004 [US1] Move the runner to `src/foundation/support/menu_testing/interactive_test_runner.py`.
- [x] T005 [P] [US1] Move both Marvis modules to `src/mist/intelligence/marvis/troubleshooting/`.
- [x] T006 [US1] Update imports in `MistHelper.py`, affected tests, and `tests/fixtures/next5_parity_baseline.py`.
- [x] T007 [US1] Update `tests/guardrails/test_src_public_symbol_preservation.py` and the active `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv`.

## Phase 4: Preserved operator behavior

**Goal**: Complete US2 with canonical dependency resolution.
**Independent test**: Existing behavior tests and unmocked resolver identity tests pass.

- [x] T008 [US2] Update moved dependency entries in `src/foundation/runtime/config/source_dependency_resolver.py`.
- [x] T009 [US2] Add import, identity, resolver, and obsolete-path tests under `tests/unit/troubleshooting/`.
- [x] T010 [US2] Run affected tests, package checks, and all `tests/guardrails/` checks.

## Phase 5: Completion

- [x] T011 Generate references with `scripts/generate_menu_wiki.py` and `scripts/menu_api_map/`.
- [x] T012 Add `changelog.d/issue-4120-troubleshooting-core-relocation.md` and record verification in `analysis.md`.
- [ ] T013 Run applicable local gates, commit explicit paths, and run the test-quality ratchet before the PR.

## Dependencies

T001 through T003 precede implementation.
T004 and T005 are independent file moves.
T006 through T009 require the moves.
T010 through T013 require the completed consumers.
The source moves and consumer updates ship atomically.

## Parallel execution

US1 permits independent runner and Marvis moves.
US2 permits independent behavior tests and static checks after consumer updates.

## Implementation strategy

Preserve source bytes, then update consumers and verify canonical identities.
Do not restructure unrelated behavior or edit files owned by another PR.
