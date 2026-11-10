# Tasks: Python 3.15 Baseline

**Input**: `spec.md`, `plan.md`, `design/research.md`, and `design/quickstart.md`.

**Prerequisites**: The implementation plan and the feature specification are complete. Recheck open pull request ownership before each shared-file edit.

**Tests**: Tests are required by the specification and the project constitution.

**Organization**: Tasks follow the three user stories in priority order. The shared support guard blocks all implementation tasks.

## Phase 1: Setup

**Purpose**: Confirm file ownership before implementation.

- [x] T001 Refresh open pull request ownership in `specs/numbered/0/0/1/2/2/4/1/4/4734-python-315-baseline/plan.md` before editing shared files.

---

## Phase 2: Foundational

**Purpose**: No shared code infrastructure is required. Complete the ownership review before shared-file edits.

---

## Phase 3: User Story 1 - Create a Supported Local Environment (Priority: P1)

**Goal**: Create a clean local environment with stable Python 3.15 and start MistHelper.

**Independent Test**: Follow `specs/numbered/0/0/1/2/2/4/1/4/4734-python-315-baseline/design/quickstart.md` and confirm Python 3.15.2 and a zero exit status.

### Tests for User Story 1

- [x] T002 [US1] Add bootstrap version tests in `tests/unit/scripts/test_browser_driver_bootstrap.py`, update the Windows entry point, and correct the bootstrap guidance in the test support files.

### Implementation for User Story 1

- [x] T003 [US1] Select and enforce Python 3.15 in `scripts/bootstrap_worktree.py` and `scripts/bootstrap_worktree.ps1`.
- [ ] T004 [P] [US1] Update `.github/copilot-instructions.md` and update `documentation/development-setup.md` after pull request #4322 releases it.
- [ ] T005 [US1] Create a fresh `.venv` in the current worktree and verify startup with `specs/numbered/0/0/1/2/2/4/1/4/4734-python-315-baseline/design/quickstart.md`.

**Checkpoint**: The current worktree uses Python 3.15.2 and MistHelper starts. Preserve environments in other worktrees.

---

## Phase 4: User Story 2 - Install Supported Packages (Priority: P2)

**Goal**: Require Python 3.15 or newer for both Python projects.

**Independent Test**: Confirm both projects reject Python 3.14 and install dependencies with Python 3.15.2.

### Tests for User Story 2

- [ ] T006 [US2] Add package-floor tests for both project metadata files in `tests/guardrails/test_dependency_declaration_parity.py`.

### Implementation for User Story 2

- [ ] T007 [US2] Set the Python minimum and tool targets in `pyproject.toml` and `mist-ops-platform/pyproject.toml` after pull request #4358 releases `pyproject.toml`.
- [ ] T008 [US2] Rebase onto current `main`, then regenerate `uv.lock`, `requirements.txt`, and `requirements-dev.txt` with Python 3.15. Preserve platform markers and the dependency intent from issue #4727.
- [ ] T009 [US2] Verify Python 3.14 rejection and Python 3.15.2 dependency resolution for `pyproject.toml`, `mist-ops-platform/pyproject.toml`, `uv.lock`, `requirements.txt`, and `requirements-dev.txt`.

**Checkpoint**: Both projects enforce the same Python minimum and resolve their dependencies.

---

## Phase 5: User Story 3 - Build and Release on Python 3.15 (Priority: P3)

**Goal**: Use Python 3.15 for CI, release builds, and product containers.

**Independent Test**: Run the relevant workflow and container checks with Python 3.15.

### Tests for User Story 3

- [x] T010 [US3] Update workflow version expectations in `tests/guardrails/test_pr_title_workflow.py` and add a Python image baseline test in `tests/unit/container/test_build_files_match.py`.

### Implementation for User Story 3

- [ ] T011 [US3] Set CI Python versions in `.github/workflows/ci.yml` after pull requests #4617 and #4208 release that workflow.
- [ ] T012 [US3] Set release and container workflow Python versions in `.github/workflows/release.yml` and `.github/workflows/container-build.yml` after pull request #4668 releases `release.yml`.
- [x] T013 [P] [US3] Update Python base images in `Containerfile`, `Dockerfile`, `mist-ops-platform/deploy/Containerfile.api`, and `mist-ops-platform/deploy/Containerfile.worker`.
- [x] T014 [US3] Update active support references in `documentation/release-notes.md` and `mist-ops-platform/docs/operations.md`. Keep the 3.13 comparison in `documentation/python-parallelism-matrix.md`.
- [x] T015 [US3] Add the release note in `changelog.d/issue-4734-python-315.md`.
- [ ] T016 [US3] Run focused tests in `tests/guardrails/test_pr_title_workflow.py`, `tests/guardrails/test_dependency_declaration_parity.py`, and `tests/unit/container/test_build_files_match.py`.

**Checkpoint**: CI, release artifacts, and product containers use Python 3.15 or newer.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Complete the end-to-end validation and confirm the change preserves existing behavior.

- [ ] T017 Verify Python 3.15 in `.github/workflows/ci.yml`, `.github/workflows/release.yml`, and `.github/workflows/container-build.yml`.
- [ ] T018 Verify Python 3.15 in `Containerfile`, `Dockerfile`, `mist-ops-platform/deploy/Containerfile.api`, and `mist-ops-platform/deploy/Containerfile.worker`.
- [ ] T019 Run the quickstart and applicable quality gates from `.github/copilot-instructions.md`.
- [ ] T020 Run `speckit.analyze` against `spec.md`, `plan.md`, and `tasks.md`.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 must refresh ownership before shared-file edits.
- **Foundational**: T001 must complete before shared-file edits.
- **User stories**: Complete their tests before implementation. Complete US2 dependency work before T005 creates the environment.
- **Polish**: T018 through T021 depend on all implementation tasks.

### User Story Dependencies

- **US1 (P1)**: T002 precedes T003. T005 depends on T003, T004, and T008 because the environment needs the bootstrap changes and updated exports.
- **US2 (P2)**: T006 precedes T007 and T008. T009 depends on both metadata and dependency updates. Respect the open pull request ownership conditions in T007 and T008.
- **US3 (P3)**: T010 precedes T011 through T013. Respect the open pull request ownership conditions in T011 and T012. T016 depends on all US3 implementation tasks.

### Parallel Opportunities

- T002 and T004 can proceed in parallel after T001.
- T007 and T011 through T015 can proceed in parallel when their file ownership conditions clear.
- T013 can proceed in parallel with T011 and T012 because it changes separate files.
- Run independent package and container checks in parallel after their implementation tasks.

## Parallel Example: User Story 3

```text
Task: Update workflow version expectations in tests/guardrails/test_pr_title_workflow.py.
Task: Update Python base images in the product container files.
```

## Implementation Strategy

### MVP First

1. Complete T001 and T002.
2. Complete US1 bootstrap tests and setup changes.
3. Complete US2 metadata and dependency updates required by the fresh environment.
4. Create the environment and verify MistHelper startup through T005.

### Incremental Delivery

1. Complete US1 and verify the local environment.
2. Complete US2 and verify both package floors.
3. Complete US3 and verify CI, release, and container declarations.
4. Run all applicable quality gates and analyze the artifacts.

## Notes

- `[P]` marks tasks that change separate files and have no incomplete prerequisite.
- Keep each task unchecked until its file and required test pass.
- Do not remove `.venv` directories from other worktrees.
