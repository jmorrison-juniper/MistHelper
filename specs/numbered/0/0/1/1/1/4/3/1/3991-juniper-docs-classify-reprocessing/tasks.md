---

description: "Implementation tasks for the Juniper Docs classification reprocessing package"
---

# Tasks: Juniper Docs Classification Reprocessing Package

**Input**: Routed design documents from
`specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/`

**Prerequisites**: `spec.md`, `plan.md`

**Authorized file boundary**:

- `src/mist/intelligence/juniper_docs/classify/reprocessing/__init__.py`
- `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py`
- `src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py`
- Removal of `src/mist/intelligence/juniper_docs/classify/manual_sorter.py`
- Removal of `src/mist/intelligence/juniper_docs/classify/reclassifier.py`
- `tests/unit/juniper_docs/test_reclassifier.py`
- `tests/guardrails/test_juniper_docs_classify_structure.py`
- `tests/guardrails/test_src_domain_structure.py`
- `tests/guardrails/test_src_public_symbol_preservation.py`
- `changelog.d/issue-3991-juniper-docs-classify-reprocessing.md`
- `specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/spec.md`
- `specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/plan.md`
- `specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/tasks.md`

Do not edit a shared registry, a generated reference, a historical specification,
`AGENTS.md`, or `CLAUDE.md`. Do not move another source module.

## Phase 1: Setup

**Purpose**: Confirm the file boundary before implementation work.

- [X] T001 Record and verify the authorized manifest with `git status --short --untracked-files=all` and `git diff --name-status origin/main...HEAD` against the file list in `specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/tasks.md`.

## Phase 2: Foundational

**Purpose**: Create the package and guard contracts that block all user stories.

- [X] T002 [P] Create `src/mist/intelligence/juniper_docs/classify/reprocessing/__init__.py` with the package documentation required by the project.
- [X] T003 [P] Create `tests/guardrails/test_juniper_docs_classify_structure.py` with reusable checks for visible children, the five-child maximum, and the required reprocessing modules.

**Checkpoint**: The canonical package exists, and the focused guard can measure its structure.

## Phase 3: User Story 1 - Keep classification structure within the project limit (Priority: P1)

**Goal**: Move both reprocessing modules into one package and prove the required package shape.

**Independent Test**: Run
`python -m pytest tests/guardrails/test_juniper_docs_classify_structure.py`.
The guard must report five direct structural children and both moved modules.

### Tests for User Story 1

- [X] T004 [P] [US1] Add the valid-layout assertion and measured child count in `tests/guardrails/test_juniper_docs_classify_structure.py`.
- [X] T005 [P] [US1] Add a direct failure test for a sixth structural child in `tests/guardrails/test_juniper_docs_classify_structure.py`.
- [X] T006 [P] [US1] Add direct failure tests for a missing classification root and a missing reprocessing module in `tests/guardrails/test_juniper_docs_classify_structure.py`.

### Implementation for User Story 1

- [X] T007 [US1] Move `src/mist/intelligence/juniper_docs/classify/manual_sorter.py` to `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py` without source changes.
- [X] T008 [US1] Move `src/mist/intelligence/juniper_docs/classify/reclassifier.py` to `src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py` without source changes.
- [X] T009 [US1] Verify the old `src/mist/intelligence/juniper_docs/classify/manual_sorter.py` and `src/mist/intelligence/juniper_docs/classify/reclassifier.py` paths are absent, with no wrappers, aliases, or fallback imports.

**Checkpoint**: The classification package has five direct structural children and one location for each moved module.

## Phase 4: User Story 2 - Preserve classification behavior through canonical imports (Priority: P1)

**Goal**: Preserve behavior and public symbols through canonical reprocessing paths.

**Independent Test**: Run the focused unit test and both shared source guards.
All tests must pass with no old import or duplicate module path.

### Tests for User Story 2

- [X] T010 [P] [US2] Update the `CorpusReclassifier` import in `tests/unit/juniper_docs/test_reclassifier.py` to use `classify.reprocessing.reclassifier`.
- [X] T011 [P] [US2] Map both old module paths to their canonical reprocessing paths in `tests/guardrails/test_src_public_symbol_preservation.py`.
- [X] T012 [P] [US2] Make the tracked-text scan ignore removed filesystem paths while retaining fail-closed Git input handling in `tests/guardrails/test_src_domain_structure.py`.

### Implementation for User Story 2

- [X] T013 [US2] Preserve every module-level symbol and all executable source text in `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py`.
- [X] T014 [US2] Preserve every module-level symbol and all executable source text in `src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py`.
- [X] T015 [US2] Search `src/` and `tests/` for `classify.manual_sorter` and `classify.reclassifier`, then update only matches inside the authorized file boundary.

**Checkpoint**: The focused behavior tests and symbol guard resolve only the canonical reprocessing paths.

## Phase 5: User Story 3 - Record the bounded refactor for maintainers (Priority: P2)

**Goal**: Record the package move and prove that the implementation stays within the approved boundary.

**Independent Test**: Run the changelog guard and compare the final manifest with the authorized file list.

### Implementation for User Story 3

- [X] T016 [US3] Create `changelog.d/issue-3991-juniper-docs-classify-reprocessing.md` with one `### Changed` heading and one bullet that names #3991.
- [X] T017 [US3] Verify the only routed records for this feature are `spec.md`, `plan.md`, and `tasks.md` under `specs/numbered/0/0/1/1/1/4/3/1/3991-juniper-docs-classify-reprocessing/`.
- [X] T018 [US3] Reject any file outside the authorized list through `git status --short --untracked-files=all` and `git diff --name-status origin/main...HEAD`.

**Checkpoint**: The release note and file manifest describe only the bounded refactor.

## Phase 6: Focused Validation

**Purpose**: Prove the requested behavior before repository-wide gates.

- [X] T019 [P] Run `python -m pytest tests/unit/juniper_docs/test_reclassifier.py` and record the result.
- [X] T020 [P] Run `python -m pytest tests/guardrails/test_juniper_docs_classify_structure.py` and record the examined child count.
- [X] T021 [P] Run `python -m pytest tests/guardrails/test_src_domain_structure.py tests/guardrails/test_src_public_symbol_preservation.py` and record the results.
- [X] T022 [P] Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` and record the result.
- [X] T023 [P] Run `python -m py_compile src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py` and record the result.
- [X] T024 Run `git diff --check` and verify the authorized files contain no whitespace errors.

## Phase 7: Applicable Repository Quality Gates

**Purpose**: Run each local gate that reads the changed Python, test, specification, or release-note files.

- [X] T025 Run `python -m ruff check .`; result: `All checks passed!`.
- [X] T026 Run `python -m black --check --diff .`; result: 2,297 files unchanged.
- [X] T027 Run `MYPY_PATHS='src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py'; python -m mypy $MYPY_PATHS --config-file pyproject.toml`; result: no issues in 808 files.
- [X] T028 Run `bandit -c pyproject.toml -r src/mist/intelligence/juniper_docs/classify tests/guardrails/test_juniper_docs_classify_structure.py -q`; result: no findings.
- [X] T029 Run `pylint src/ --fail-under=9.5`; result: 9.93 out of 10.
- [X] T030 Run `RADON_PATHS='src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py'; radon cc $RADON_PATHS -j | complexity-gate --max 10`; result: all functions within threshold.
- [X] T031 Run `VULTURE_PATHS='src/ MistHelper.py wsgi.py web_portal'; vulture $VULTURE_PATHS --min-confidence 70`; result: no findings.
- [X] T032 Run `PYDOCSTYLE_PATHS='src/ wsgi.py web_portal'; pydocstyle $PYDOCSTYLE_PATHS`; result: no violations.
- [X] T033 Run `INTERROGATE_PATHS='src/ MistHelper.py wsgi.py wsgi_capture.py web_portal'; interrogate $INTERROGATE_PATHS --fail-under 90 -v`; result: 99.7 percent.
- [X] T034 Run `python -m pytest -q tests/unit/juniper_docs`; result: 187 passed and 3 skipped.
- [X] T035 Run `ste-linter --config .ste-linter.toml --min-score 80` on the three routed records and release note; result: all four files passed.
- [X] T036 Run `speckit-task-audit --root . --verbose`; result: no issue #3991 finding, with exit 1 from unrelated historical missing citations.
- [X] T037 Verify `origin/main` and the implementation parent resolve to `efd082892584f54099973449a5953cd1b8d9a181`.
- [X] T038 Re-run `git diff --check` and the authorized manifest check before commit.

## Phase 8: Required Post-Commit Test-Quality Checks

**Purpose**: Run the required ratchet against committed test changes before push.

- [X] T039 Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`; result: 1 passed.
- [X] T040 Verify `origin/main^{commit}` resolves to `efd082892584f54099973449a5953cd1b8d9a181`.
- [X] T041 Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`; result: 4 files checked and 0 new findings.
- [X] T042 Run `git status --short --untracked-files=all` after all gates; result: clean after the evidence commit.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 starts first.
- **Foundational**: T002 and T003 depend on T001.
- **User Story 1**: T004 through T006 depend on T003. T007 and T008 depend on T002. T009 depends on T007 and T008.
- **User Story 2**: T010 through T012 depend on T007 through T009. T013 through T015 depend on T010 through T012.
- **User Story 3**: T016 can run after T001. T017 and T018 depend on all selected implementation tasks.
- **Focused Validation**: T019 through T024 depend on T018.
- **Repository Gates**: T025 through T038 depend on focused validation.
- **Post-Commit Checks**: T039 through T042 run in order after the final implementation commit.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after the Foundational phase.
- **User Story 2 (P1)**: Depends on the completed module moves from User Story 1.
- **User Story 3 (P2)**: The release note can start independently, but its final boundary check depends on User Stories 1 and 2.

### Parallel Opportunities

- T002 and T003 can run in parallel.
- T004 through T006 can run in parallel.
- T007 and T008 can run in parallel.
- T010 through T012 can run in parallel after the moves.
- T019 through T023 can run in parallel.
- T025 through T036 can run in parallel when they do not write generated files.

## Parallel Example: User Story 1

```text
Task: "Add the valid-layout assertion in tests/guardrails/test_juniper_docs_classify_structure.py."
Task: "Move manual_sorter.py into src/mist/intelligence/juniper_docs/classify/reprocessing/."
Task: "Move reclassifier.py into src/mist/intelligence/juniper_docs/classify/reprocessing/."
```

## Parallel Example: User Story 2

```text
Task: "Update the canonical import in tests/unit/juniper_docs/test_reclassifier.py."
Task: "Update the move map in tests/guardrails/test_src_public_symbol_preservation.py."
Task: "Harden removed-path handling in tests/guardrails/test_src_domain_structure.py."
```

## Implementation Strategy

### MVP First

1. Complete T001 through T009.
2. Run T020 and verify the five-child package shape.
3. Stop if an old module path or wrapper remains.

### Incremental Delivery

1. Deliver the package move and focused structure guard for User Story 1.
2. Deliver canonical imports and symbol preservation for User Story 2.
3. Deliver the release note and boundary proof for User Story 3.
4. Run focused validation, repository gates, and post-commit test-quality checks in sequence.

## Notes

- Each task uses a checkbox, a sequential task ID, an optional `[P]` marker, a required story label, and an exact file path or command scope.
- A `[P]` task changes a different file or runs an independent read-only gate.
- A gate does not authorize a file outside the authorized boundary.
- Stop at the first failed required command. Repair the cause before the next command.
