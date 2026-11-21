# Tasks: Refresh And Pin Project Dependencies

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/4/3/2/4867-refresh-dependencies/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`

**Tests**: Existing dependency guards and package gates are the verification for this change.

**Organization**: Tasks are grouped by package surface so each story can be validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks in the same phase.
- **[Story]**: Which user story this task supports.
- Include exact file paths.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create the Python 3.15.2 worktree environment from the repository bootstrap.
- [x] T002 Complete PR 4806 rebase, checks, merge, and synchronization to origin/main.
- [x] T003 Confirm the 4867 worktree is clean and rebased onto the synchronized origin/main.
- [x] T004 Record the current direct package versions and outdated package inventory for root Python, Mist Ops Platform, and Ops Portal.

**Checkpoint**: The branch set is serial and no dependency file has an overlapping open PR.

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T005 [P] Read the package constraints in `pyproject.toml`.
- [x] T006 [P] Read the package constraints in `mist-ops-platform/pyproject.toml` and `mist-ops-platform/requirements-dev.txt`.
- [x] T007 [P] Read the package constraints in `ops-portal/package.json` and `ops-portal/package-lock.json`.
- [x] T008 Decide which package major releases are compatible with Python 3.15 and preserve existing behavior.

**Checkpoint**: Package constraints and compatibility exceptions are known before lock updates start.

## Phase 3: User Story 1 - Refresh Root Python Packages (Priority: P1)

**Goal**: Refresh and pin the root Python runtime and development package set.

**Independent Test**: UV lock check passes, exports match the lock, and dependency parity guards pass.

- [x] T009 [US1] Refresh compatible direct package constraints in `pyproject.toml`.
- [x] T010 [US1] Regenerate `uv.lock` with UV using Python 3.15.
- [x] T011 [US1] Export exact runtime packages to `requirements.txt`.
- [x] T012 [US1] Export exact development packages to `requirements-dev.txt`.
- [x] T013 [US1] Run dependency lock, export, parity, and runtime audit guards.
- [x] T014 [US1] Run root compile, Ruff, Black, mypy, pytest, Bandit, and pip-audit gates that apply.

**Checkpoint**: The root Python package set resolves and passes its verification gates.

## Phase 4: User Story 2 - Refresh Ops Platform Packages (Priority: P2)

**Goal**: Refresh and pin Mist Ops Platform runtime and test packages.

**Independent Test**: The platform environment installs and passes its pytest and Ruff gates.

- [x] T015 [P] [US2] Update runtime package constraints in `mist-ops-platform/pyproject.toml`.
- [x] T016 [P] [US2] Update test package constraints in `mist-ops-platform/pyproject.toml` and `mist-ops-platform/requirements-dev.txt`.
- [x] T017 [US2] Add or refresh exact runtime pins in `mist-ops-platform/requirements.txt`.
- [x] T018 [US2] Add or refresh exact test pins in `mist-ops-platform/requirements-dev.txt`.
- [x] T019 [US2] Update `.github/workflows/ci.yml` if the platform package install must use exact exports.
- [x] T020 [US2] Run Mist Ops Platform pytest, coverage, and Ruff gates.

**Checkpoint**: The platform package set installs reproducibly and passes 56 percent coverage.

## Phase 5: User Story 3 - Refresh Ops Portal Packages (Priority: P3)

**Goal**: Refresh and synchronize the Ops Portal npm dependency set.

**Independent Test**: npm ci succeeds and npm audit, typecheck, lint, and tests pass.

- [x] T021 [P] [US3] Refresh direct runtime and development packages in `ops-portal/package.json`.
- [x] T022 [US3] Regenerate `ops-portal/package-lock.json` with npm.
- [x] T023 [US3] Run `npm ci --legacy-peer-deps` in `ops-portal/`.
- [x] T024 [US3] Run npm audit, typecheck, lint, and test gates in `ops-portal/`.

**Checkpoint**: The portal manifest and lock describe one tested dependency graph.

## Phase 6: User Story 4 - Verify Complete Package Refresh (Priority: P4)

**Goal**: Verify all package surfaces and prepare the merge evidence.

**Independent Test**: All applicable local gates pass and the final report names package exceptions.

- [x] T025 [US4] Compare direct and transitive package versions with the package inventory in issue #4867.
- [x] T026 [US4] Record every package that remains out of date with its compatibility blocker.
- [x] T027 [US4] Run the test-quality ratchet and relevant guardrail tests.
- [x] T028 [US4] Run the package build and container-image input checks that apply.
- [x] T029 [US4] No release-note fragment is needed because this change adds no user-facing behavior.
- [ ] T030 [US4] Commit, rebase, push, open the pull request, pass CI, merge, and synchronize origin/main.

**Checkpoint**: The complete package refresh is reproducible and merged.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: PR 4806 must complete before the 4867 root lock can change.
- **Foundational (Phase 2)**: Depends on Setup completion.
- **User Story 1 (Phase 3)**: Depends on Foundational and PR 4806 synchronization.
- **User Story 2 (Phase 4)**: Can start after Foundational and does not require User Story 1.
- **User Story 3 (Phase 5)**: Can start after Foundational and does not require the Python stories.
- **User Story 4 (Phase 6)**: Depends on all three package stories.

### User Story Dependencies

- **User Story 1**: Independent.
- **User Story 2**: Independent.
- **User Story 3**: Independent.
- **User Story 4**: Depends on Users Stories 1, 2, and 3.

### Parallel Opportunities

- T005, T006, and T007 can run in parallel.
- T015 and T016 can run in parallel after T008.
- T021 and T022 can run in sequence because package-lock.json follows package.json.
- T023 and T024 can run in sequence because npm ci creates the install for the tests.

## Parallel Example: Package Surfaces

```text
T005 Root Python package constraints
T006 Mist Ops Platform package constraints
T007 Ops Portal package constraints
T015 Mist Ops Platform runtime constraints
T016 Mist Ops Platform test constraints
T021 Ops Portal package.json refresh
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational.
2. Complete User Story 1.
3. Validate the root lock and pip exports independently.
4. Continue to the platform and portal stories.

### Incremental Delivery

1. Refresh root Python packages.
2. Refresh Mist Ops Platform packages.
3. Refresh Ops Portal packages.
4. Run final verification and merge.

## Notes

- Keep one dependency edit in one serial merge slot.
- Do not close PR 4806 or disable its dependency update stream.
- Use the exact package constraints instead of manual lock edits.
- A package major update requires a passing compatibility gate before it is accepted.
