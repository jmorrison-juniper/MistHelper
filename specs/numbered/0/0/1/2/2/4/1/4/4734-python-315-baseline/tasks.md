# Tasks: Python 3.15 Baseline

**Input**: `spec.md`, `plan.md`, `design/research.md`, and `design/quickstart.md`.

**Prerequisites**: The implementation plan and the feature specification are complete. The user authorized narrow Python-version edits in files held by open pull requests.

**Tests**: Tests are required by the specification and the project constitution.

**Organization**: Tasks follow the three user stories in priority order. The shared support guard blocks all implementation tasks.

## Phase 1: Setup

**Purpose**: Confirm file ownership and clean project environments before implementation.

- [x] T001 Refresh pull request ownership and remove each pre-existing `.venv` directory in registered MistHelper worktrees after an active-process check.

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
- [x] T004 [P] [US1] Set Python 3.15 in `.github/copilot-instructions.md` and `documentation/development-setup.md`.
- [x] T005 [US1] Create a fresh `.venv` in the current worktree and verify startup with `specs/numbered/0/0/1/2/2/4/1/4/4734-python-315-baseline/design/quickstart.md`.

**Checkpoint**: The feature worktree uses Python 3.15.2 and MistHelper starts. Every other registered `.venv` remains absent.

---

## Phase 4: User Story 2 - Install Supported Packages (Priority: P2)

**Goal**: Require Python 3.15 or newer for both Python projects.

**Independent Test**: Confirm both projects reject Python 3.14 and install dependencies with Python 3.15.2.

### Tests for User Story 2

- [x] T006 [US2] Add package-floor tests for both project metadata files in `tests/guardrails/test_dependency_declaration_parity.py`.

### Implementation for User Story 2

- [x] T007 [US2] Set Python minimums and tool targets in both project metadata files.
- [x] T008 [US2] Regenerate the lock and exports with `importlib-metadata` 10.2.0, `openai` 3.48.0, and `pypdfium2` 5.15.2. Preserve all 11 runtime markers.
- [x] T009 [US2] Verify both project floors, the Python 3.15.2 lock, and both generated exports.

**Checkpoint**: Both projects enforce the same Python minimum and resolve their dependencies.

---

## Phase 5: User Story 3 - Build and Release on Python 3.15 (Priority: P3)

**Goal**: Use Python 3.15 for CI, release builds, and product containers.

**Independent Test**: Run the relevant workflow and container checks with Python 3.15.

### Tests for User Story 3

- [x] T010 [US3] Guard Python 3.15 in CI, release, and container workflows and in all product images.

### Implementation for User Story 3

- [x] T011 [US3] Set Python 3.15 in `.github/workflows/ci.yml`.
- [x] T012 [US3] Set Python 3.15 in the release and container workflows.
- [x] T013 [P] [US3] Update Python base images in `Containerfile`, `Dockerfile`, `mist-ops-platform/deploy/Containerfile.api`, and `mist-ops-platform/deploy/Containerfile.worker`.
- [x] T014 [US3] Update active support references in `documentation/release-notes.md` and `mist-ops-platform/docs/operations.md`. Keep the 3.13 comparison in `documentation/python-parallelism-matrix.md`.
- [x] T015 [US3] Add the release note in `changelog.d/issue-4734-python-315.md`.
- [x] T016 [US3] Run focused baseline, workflow, container, and bootstrap tests. The Python 3.15.2 run passed 312 tests.

**Checkpoint**: CI, release artifacts, and product containers use Python 3.15 or newer.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Complete the end-to-end validation and confirm the change preserves existing behavior.

- [x] T017 Verify Python 3.15 in the CI, release, and container workflows.
- [x] T018 Verify Python 3.15 in all four product container files.
- [x] T019 Run the quickstart and applicable quality gates. The 314 focused tests and 734 title-guard tests passed. CI passed all 37 checks, including coverage and the Ops Platform suite. The test-quality ratchet found zero new findings. Ruff, Black, dependency resolution, and the local image build passed.
- [x] T020 Run `speckit.analyze` against `spec.md`, `plan.md`, and `tasks.md`.

---

## Phase 7: Commit, Review, and Merge

**Purpose**: Deliver the tested feature through the protected pull request flow.

- [x] T021 Build the explicit feature manifest and stage only its files after all local gates pass.
- [x] T022 Commit the staged feature files with an accepted Conventional Commit subject and the required co-author trailer.
- [x] T023 Rebase the committed branch onto current `origin/main` and rerun available local gates. The local image build and Linux CI Ops Platform suite passed. Windows still cannot link `lupa`.
- [x] T024 Push the branch and open a pull request from the repository template with the issue closure, file summary, gate results, and deployment notes.
- [x] T025 Wait for all required checks to pass, then squash-merge the pull request.

---

## Phase 8: Post-Merge Deployment

**Purpose**: Verify the merged image and deploy it only after explicit approval.

- [ ] T026 After merge, wait for the main image build and verify that the image revision matches the merge commit.
- [ ] T027 After explicit approval, deploy the image and verify container and portal health.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 must refresh ownership and verify the registered worktree environments before shared-file edits.
- **Foundational**: T001 must complete before shared-file edits.
- **User stories**: Complete their tests before implementation. Complete US2 dependency work before T005 creates the environment.
- **Polish**: T017 through T020 depend on all implementation tasks.
- **Delivery**: T021 follows local validation. T022 follows T021. T023 follows T022. T024 follows T023. T025 follows T024 and all required checks.
- **Post-merge**: T026 follows T025 and the main image build. T027 follows T026 and explicit deployment approval.

### User Story Dependencies

- **US1 (P1)**: T002 precedes T003. T005 depends on T003 because its environment and startup check use the existing Python 3.15-compatible lock. T004 and T008 remain separate follow-up work.
- **US2 (P2)**: T006 precedes T007. T008 depends on T007. T009 depends on both metadata and dependency updates. Respect the open pull request ownership conditions in T007 and T008.
- **US3 (P3)**: T010 precedes T011 through T013. Respect the open pull request ownership conditions in T011 and T012. T016 depends on all US3 implementation tasks.
- **Delivery**: T021 through T025 follow the order defined in Phase Dependencies.
- **Deployment**: T026 follows merge and image publication. T027 requires T026 and explicit approval.

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
5. Stage the feature manifest, commit, rebase, open the pull request, pass required checks, and squash-merge.
6. Verify the merged image revision. Deploy only after explicit approval.

## Notes

- `[P]` marks tasks that change separate files and have no incomplete prerequisite.
- Keep each task unchecked until its file and required test pass.
- Remove only pre-existing registered worktree `.venv` directories with no active process. Create one fresh environment in the feature worktree. Preserve environments outside registered worktrees.
