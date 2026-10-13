# Tasks: Prevent Unsafe Stale Builds

**Input**: Design documents from this feature directory.

**Prerequisites**: `plan.md`, `spec.md`, and the design records under `design/`.

**Tests**: Add contract tests before implementation. Use a temporary Git remote to verify the behind-count direction. Do not build or publish an image during local tests.

## Phase 1: Setup

**Purpose**: Confirm the existing repository structure and avoid unrelated changes.

- The Python environment is ready, so no setup task applies.

## Phase 2: Foundational

**Purpose**: No shared source component blocks the user stories.

- The feature needs no shared source component.

## Phase 3: User Story 1 - Stop a stale build (Priority: P1)

**Goal**: Stop builds from stale checkouts and stop when the remote check fails.

**Independent Test**: Use a temporary Git remote with the checkout behind by one commit. Confirm the contract rejects a default build before the provider call.

### Tests for User Story 1

- [x] T001 [US1] Add a temporary Git remote test for `HEAD..origin/main` count direction in `tests/contract/packaging/test_compose_rebuild_warning.py`.
- [x] T002 [US1] Add contract checks for fetch failure, behind-count reporting, default refusal, and refusal before the provider call in `tests/contract/packaging/test_compose_rebuild_warning.py`.

### Implementation for User Story 1

- [x] T003 [US1] Update the build block in `scripts/compose.ps1` to fetch `origin/main`, count missing commits, report the count, and stop before the provider on a stale checkout.

**Checkpoint**: A current checkout can build, while a stale checkout or failed fetch cannot start a build by default.

## Phase 4: User Story 2 - Allow a local stale build (Priority: P2)

**Goal**: Permit an explicit stale build without changing the published image name.

**Independent Test**: Use a stale checkout and the explicit override. Confirm that the local image name is selected and the provider receives no unsupported override argument.

### Tests for User Story 2

- [x] T004 [US2] Add contract checks for the explicit override, local image selection, environment restoration, and unchanged current-build naming in `tests/contract/packaging/test_compose_rebuild_warning.py`.

### Implementation for User Story 2

- [x] T005 [US2] Add the published image default and `MISTHELPER_BUILD_IMAGE` override to `compose.build.yml`.
- [x] T006 [US2] Update `scripts/compose.ps1` to consume `--allow-stale`, select `misthelper:local` only for an allowed stale build, and restore the previous environment value.

**Checkpoint**: An explicit stale build uses a local-only image name. Current builds keep their existing image name.

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Keep operator guidance and release records consistent with the new guard.

- [x] T007 [P] Update the build instructions in `documentation/container-deployment.md` and `documentation/wiki/Container-Setup.md` to use the guarded helper.
- [x] T008 [P] Add the issue release note in `changelog.d/issue-4164-compose-stale-build.md`.
- [ ] T009 Run the focused contract tests, Ruff, Black, markdown checks, and the applicable test-quality gate. Record each result in the pull request body.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: No code changes are required.
- **Foundational**: No shared source component blocks implementation.
- **User Story 1**: The tests in T001 and T002 precede the stale-build guard in T003.
- **User Story 2**: T004 depends on the command contract from T001 and T002. T005 and T006 depend on the stale-build decision in T003.
- **Polish**: T007 and T008 can proceed after the command contract is stable. T009 depends on all implementation and documentation tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Independent. It establishes the fail-closed stale-build check.
- **User Story 2 (P2)**: Depends on User Story 1 because the override changes the stale-build refusal.

### Parallel Opportunities

- T007 and T008 change different files and can run in parallel after the command contract is stable.
- T005 and T007 change different files, but the documentation must use the final image name.

## Implementation Strategy

### MVP First

Complete T001 through T003. Validate current, stale, and fetch-failure paths before implementing the override.

### Incremental Delivery

Complete T004 through T006 after the stale guard passes. Finish documentation and the release note, then run T009.

## Notes

- Each task names its file path and follows the required checkbox format.
- Track existing process-folder baseline cleanup as a separate maintenance action. Do not alter unrelated baseline entries in this change.
- The host has no `pwsh` command. The plan uses the checked-in template and the resolved feature path.
