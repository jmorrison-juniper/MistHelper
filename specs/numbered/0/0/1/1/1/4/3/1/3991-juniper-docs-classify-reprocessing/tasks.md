---

description: "Implementation tasks for the Juniper Docs classification reprocessing package"
---

# Tasks: Juniper Docs Classification Reprocessing Package

**Input**: Routed design documents from
`specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/`

**Prerequisites**: `spec.md`, `plan.md`

**Authorized implementation boundary**: Move the two classification modules,
update affected imports and tests, add the focused structure guard, add the
issue release note, and validate the routed feature records. Do not edit
shared registries, generated references, historical specifications,
`AGENTS.md`, or `CLAUDE.md`.

## Phase 1: Setup

**Purpose**: Establish the planned package path and the implementation boundary.

- [ ] T001 Record the authorized file manifest in the implementation workspace, including `src/mist/intelligence/juniper_docs/classify/`, `tests/unit/juniper_docs/test_reclassifier.py`, `tests/guardrails/test_juniper_docs_classify_structure.py`, `changelog.d/issue-3991-juniper-docs-classify-reprocessing.md`, and the three routed feature records.

## Phase 2: Foundational

**Purpose**: Create the package boundary before moving modules or updating imports.

- [ ] T002 [P] Create `src/mist/intelligence/juniper_docs/classify/reprocessing/__init__.py` with the package metadata required by the project.
- [ ] T003 [P] Add the focused structure guard test file at `tests/guardrails/test_juniper_docs_classify_structure.py` with valid-layout fixtures and examined-child reporting.

## Phase 3: User Story 1 - Keep classification structure within the project limit (Priority: P1) 🎯 MVP

**Goal**: Place both reprocessing modules in one package, remove the old paths, and prove the five-child structure rule.

**Independent Test**: Run `python -m pytest tests/guardrails/test_juniper_docs_classify_structure.py` and verify that the classification package has five direct structural children, both reprocessing modules exist, and both old paths are absent.

### Tests for User Story 1

- [ ] T004 [US1] Add a focused guard case in `tests/guardrails/test_juniper_docs_classify_structure.py` that fails when `src/mist/intelligence/juniper_docs/classify/` contains a sixth direct structural child.
- [ ] T005 [US1] Add a focused guard case in `tests/guardrails/test_juniper_docs_classify_structure.py` that fails when either `reprocessing/manual_sorter.py` or `reprocessing/reclassifier.py` is missing or misplaced.

### Implementation for User Story 1

- [ ] T006 [US1] Move `src/mist/intelligence/juniper_docs/classify/manual_sorter.py` to `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py` without changing its source symbols, behavior, logging, or path handling.
- [ ] T007 [US1] Move `src/mist/intelligence/juniper_docs/classify/reclassifier.py` to `src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py` without changing its source symbols, behavior, logging, or processing defaults.
- [ ] T008 [US1] Remove the old `src/mist/intelligence/juniper_docs/classify/manual_sorter.py` and `src/mist/intelligence/juniper_docs/classify/reclassifier.py` paths as part of the moves, with no wrappers, aliases, or fallback imports.

**Checkpoint**: The classification package satisfies the direct-child limit and has one canonical location for each reprocessing module.

## Phase 4: User Story 2 - Preserve classification behavior through canonical imports (Priority: P1)

**Goal**: Update every affected caller and focused test to use canonical `classify.reprocessing` imports while preserving public symbols.

**Independent Test**: Run the focused Juniper Docs tests and the symbol and source-structure guards. The tests pass with no old import path or duplicate module entry point.

### Tests for User Story 2

- [ ] T009 [P] [US2] Update `tests/unit/juniper_docs/test_reclassifier.py` to import `CorpusReclassifier` from `src.mist.intelligence.juniper_docs.classify.reprocessing.reclassifier` and retain its behavior assertions.
- [ ] T010 [P] [US2] Add canonical import and module-symbol checks in `tests/guardrails/test_juniper_docs_classify_structure.py` for `ManualDocumentSorter`, `CorpusReclassifier`, and the existing module-level public symbols.

### Implementation for User Story 2

- [ ] T011 [US2] Update every affected runtime import under `src/mist/intelligence/juniper_docs/` from the old module paths to `classify.reprocessing.manual_sorter` or `classify.reprocessing.reclassifier`.
- [ ] T012 [US2] Update every affected test import under `tests/` from the old module paths to the matching canonical `classify.reprocessing` path, without adding compatibility aliases.
- [ ] T013 [US2] Verify that `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py` and `src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py` retain their public module-level symbols and no tracked source or test file imports the old locations.

**Checkpoint**: Focused classification behavior and canonical symbol checks pass without duplicate entry points.

## Phase 5: User Story 3 - Record the bounded refactor for maintainers (Priority: P2)

**Goal**: Record the package move and its exclusions in one issue-specific release note.

**Independent Test**: Review the release note and the final file manifest. The record names issue #3991 and the manifest contains no excluded shared or historical files.

### Implementation for User Story 3

- [ ] T014 [US3] Create `changelog.d/issue-3991-juniper-docs-classify-reprocessing.md` with one `###` heading and one `Changed` bullet that names issue #3991, the reprocessing package move, canonical imports, and the focused structure guard.
- [ ] T015 [US3] Verify `git status --short --untracked-files=all` contains only the moved modules, affected imports and tests, focused guard files, `changelog.d/issue-3991-juniper-docs-classify-reprocessing.md`, and the three routed feature records.

**Checkpoint**: The release record and implementation manifest show the bounded refactor without unauthorized file changes.

## Phase 6: Polish and Validation

**Purpose**: Validate the complete implementation and preserve the authorized boundary.

- [ ] T016 [P] Run `python -m pytest tests/unit/juniper_docs/test_reclassifier.py` and record the result in the implementation handoff.
- [ ] T017 [P] Run `python -m pytest tests/guardrails/test_juniper_docs_classify_structure.py` and record the result in the implementation handoff.
- [ ] T018 [P] Run `python -m pytest tests/guardrails/test_src_domain_structure.py tests/guardrails/test_src_public_symbol_preservation.py` and record the result in the implementation handoff.
- [ ] T019 [P] Run `python -m py_compile src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py` and record the result in the implementation handoff.
- [ ] T020 [P] Run `python -m ruff check src/mist/intelligence/juniper_docs tests/unit/juniper_docs tests/guardrails` and record the result in the implementation handoff.
- [ ] T021 [P] Run `python -m black --check src/mist/intelligence/juniper_docs tests/unit/juniper_docs tests/guardrails` and record the result in the implementation handoff.
- [ ] T022 Verify `git diff --check`, `git status --short --untracked-files=all`, and `git diff --name-only` show no unauthorized file changes.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 starts immediately and defines the authorized manifest.
- **Foundational**: T002 and T003 depend on T001 and must finish before story implementation.
- **User Story 1**: T004 and T005 depend on T003. T006 through T008 depend on T002 and T003. T008 completes the move before import updates.
- **User Story 2**: T009 and T010 depend on T006 through T008. T011 and T012 depend on the moved files. T013 depends on T009 through T012.
- **User Story 3**: T014 depends on the completed implementation from User Stories 1 and 2. T015 depends on T014 and all implementation files.
- **Polish**: T016 through T022 depend on T015 and the complete implementation.

### User Story Dependencies

- **User Story 1 (P1)**: Depends on the Foundational phase and has no dependency on another user story.
- **User Story 2 (P1)**: Depends on User Story 1 because imports target the moved modules.
- **User Story 3 (P2)**: Depends on User Stories 1 and 2 because the release record describes the complete bounded change.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T004 and T005 can run in parallel after T003.
- T009 and T010 can run in parallel after the module moves.
- T016 through T021 can run in parallel after implementation is complete.

## Implementation Strategy

### MVP First

1. Complete T001 through T008.
2. Complete T009 through T013 to preserve canonical imports and symbols.
3. Run the User Story 1 and User Story 2 independent tests.

### Incremental Delivery

1. Deliver the package move and focused structure guard as User Story 1.
2. Deliver canonical imports and symbol preservation as User Story 2.
3. Deliver the release note and boundary review as User Story 3.
4. Complete the focused validation commands in the Polish phase.

## Notes

- Each task uses the required checkbox, sequential ID, optional `[P]` marker, story label where required, and an exact file path.
- The task list does not authorize changes to shared registries, generated references, historical specifications, `AGENTS.md`, or `CLAUDE.md`.
