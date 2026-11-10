# Tasks: Runtime Dependency Exports

**Input**: Design documents in `specs/numbered/0/0/1/2/2/4/0/2/4727-runtime-dependency-exports/`.

**Prerequisites**: `plan.md`, `spec.md`, and the available files under `design/`.

**Tests**: Run the existing dependency guardrails, lock check, and audits for both exports.

**Organization**: Tasks follow the two user stories in `spec.md`.

## Phase 1: Setup

**Purpose**: Start from current `main` and confirm the dependency update set.

- [ ] T001 Rebase the feature branch onto `origin/main`, then review the refreshed package preview for `uv.lock` with `uv lock --upgrade --dry-run`.

---

## Phase 2: Foundational

**Purpose**: Prepare shared prerequisites for the user stories.

No new foundational infrastructure is required. The existing lock and dependency guardrails provide the shared prerequisites.

---

## Phase 3: User Story 1 - Install with aligned dependencies (Priority: P1)

**Goal**: Align package versions in the lock and both installation exports while preserving all 11 runtime platform markers.

**Independent Test**: Confirm the three requested package versions match across the lock and exports. Run the existing guardrails and verify all 11 runtime markers remain unchanged.

### Implementation for User Story 1

- [ ] T002 [US1] Update `uv.lock` with only the package changes approved in the refreshed preview. Keep existing constraints and set `importlib-metadata` to 10.2.0, `openai` to 3.48.0, and `pypdfium2` to 5.15.2.
- [ ] T003 [P] [US1] Generate the runtime export in `requirements.txt` from the updated lock with `uv export --locked --no-hashes --no-emit-project`.
- [ ] T004 [P] [US1] Generate the development export in `requirements-dev.txt` from the updated lock with `uv export --locked --no-hashes --no-emit-project --extra dev`.
- [ ] T005 [US1] Run the dependency guardrails in `tests/guardrails/test_dependency_declaration_parity.py`, `tests/guardrails/test_dependency_lock_file.py`, and `tests/guardrails/test_dependency_export.py`. Confirm all 11 runtime markers remain unchanged.

**Checkpoint**: The lock and both exports use aligned package versions, and all runtime markers remain present.

---

## Phase 4: User Story 2 - Verify dependency integrity (Priority: P2)

**Goal**: Verify the dependency records, report audit limits, and add the release note.

**Independent Test**: Run `uv lock --check` and audits for both exports. Report every dependency source the audits cannot inspect. Confirm the issue release note exists.

### Implementation for User Story 2

- [ ] T006 [P] [US2] Add `changelog.d/issue-4727-runtime-dependency-exports.md` with a `### Changed` heading and a bullet that names issue #4727.
- [ ] T007 [P] [US2] Run `uv lock --check` against `uv.lock`.
- [ ] T008 [P] [US2] Run `pip-audit -r requirements.txt` and `pip-audit -r requirements-dev.txt`. Report current-platform scope and name every source the audits cannot inspect.

**Checkpoint**: The lock check passes, the audit reports its coverage limits, and the release note names issue #4727.

---

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Validate, publish, and deploy the reviewed dependency change.

- [ ] T009 Review `uv.lock`, `requirements.txt`, `requirements-dev.txt`, and `changelog.d/issue-4727-runtime-dependency-exports.md`. Confirm `pyproject.toml` remains unchanged.
- [ ] T010 Run `git diff --check` for `uv.lock`, both exports, and `changelog.d/issue-4727-runtime-dependency-exports.md`.
- [ ] T011 Run the dependency guardrails, lock check, both audits, and STE gate before staging. Record each result for the pull request.
- [ ] T012 Build the explicit feature manifest from `uv.lock`, `requirements.txt`, `requirements-dev.txt`, `changelog.d/issue-4727-runtime-dependency-exports.md`, and the feature directory under `specs/numbered/0/0/1/2/2/4/0/2/4727-runtime-dependency-exports/`. Exclude `.specify/feature.json`.
- [ ] T013 Stage only the files in the feature manifest from T012.
- [ ] T014 Commit the staged files with a Conventional Commit subject and the required Co-authored-by trailer.
- [ ] T015 Rebase the committed feature branch onto current `origin/main`. Re-run all affected local checks after the rebase.
- [ ] T016 Push the rebased feature branch to its matching remote branch.
- [ ] T017 Prepare the pull request body from `.github/PULL_REQUEST_TEMPLATE.md`. Include `Closes #4727`, changed files, local check results, and audit limits.
- [ ] T018 Wait for all required pull request checks and CodeQL to pass on the current pull request commit.
- [ ] T019 Squash merge the approved pull request to `main` after all required checks pass.
- [ ] T020 Wait for `.github/workflows/container-build.yml` on the merged commit. Verify the image revision label equals the merged commit SHA.
- [ ] T021 After explicit production approval, deploy the approved image and confirm container and portal health using `documentation/container-deployment.md`.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 must finish before the lock update.
- **Foundational**: No tasks are required because the project already has the needed lock and guardrails.
- **User Story 1**: T002 follows T001. T003 and T004 follow T002. T005 follows T003 and T004.
- **User Story 2**: T006 can start after T001. T007 follows T002. T008 follows T003 and T004.
- **Polish and release**: T009 and T010 follow T005 through T008. T011 follows T009 and T010. T012 follows T011. T013 follows T012. T014 follows T013. T015 follows T014. T016 follows T015. T017 follows T016. T018 follows T017. T019 follows T018. T020 follows T019. T021 requires T020 and explicit production approval.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T001 and delivers the aligned lock and exports.
- **User Story 2 (P2)**: Its lock and audit checks require the updated records from User Story 1. Its release note can be drafted after T001.

### Parallel Opportunities

- Run T003 and T004 in parallel after T002 because they write separate export files.
- Run T006 while the lock update proceeds because the release note uses the approved package targets.
- Run T006 with the dependency validation because it writes a separate release-note file.
- Run T005, T007, and T008 in parallel after the lock and both exports are ready.
- Run T009 and T010 after validation. Run T011 after both complete.

---

## Parallel Examples

### User Story 1

```text
After T002:
Task: Generate requirements.txt from uv.lock.
Task: Generate requirements-dev.txt from uv.lock.
```

### User Story 2

```text
After T001:
Task: Add changelog.d/issue-4727-runtime-dependency-exports.md.

After T003:
Task: Run uv lock --check.
Task: Run pip-audit -r requirements.txt and pip-audit -r requirements-dev.txt.
```

## Implementation Strategy

### MVP First

1. Complete T001 and T002.
2. Complete T003 and T004.
3. Complete T005 and validate User Story 1 independently.
4. Add the release note in T006 before the pull request.
5. Complete T007 and T008 before the pull request.

### Incremental Delivery

1. Align `uv.lock` with the reviewed compatible package set.
2. Generate both exports and validate User Story 1.
3. Complete the lock check, security audit, and release note for User Story 2.
4. Review the final file set and prepare the pull request.
