# Tasks: Runtime Dependency Exports

**Input**: Design documents in `specs/numbered/0/0/1/2/2/4/0/2/4727-runtime-dependency-exports/`.

**Prerequisites**: `plan.md`, `spec.md`, and the available files under `design/`.

**Tests**: Run the existing dependency guardrails, lock check, and audits for both exports.

**Organization**: Tasks follow the two user stories in `spec.md`.

## Phase 1: Setup

**Purpose**: Start from current `main` and confirm the dependency update set.

- [X] T001 Rebase the feature branch onto `origin/main`, then review the refreshed package preview for `uv.lock` with `uv lock --upgrade --dry-run --upgrade-package 'openai==3.48.0'`. (Verified: branch is based on `origin/main`, and the preview resolved the requested versions.)

---

## Phase 2: Foundational

**Purpose**: Prepare shared prerequisites for the user stories.

No new foundational infrastructure is required. The existing lock and dependency guardrails provide the shared prerequisites.

---

## Phase 3: User Story 1 - Install with aligned dependencies (Priority: P1)

**Goal**: Align package versions in the lock and both installation exports while preserving all 11 runtime platform markers.

**Independent Test**: Confirm the three requested package versions match across the lock and exports. Run the existing guardrails and verify all 11 runtime markers remain unchanged.

### Implementation for User Story 1

- [X] T002 [US1] Update `uv.lock` with only the package changes approved in the refreshed preview. Keep existing constraints and set `importlib-metadata` to 10.2.0, `openai` to 3.48.0, and `pypdfium2` to 5.15.2. (Verified: `uv lock --check` passes.)
- [X] T003 [P] [US1] Generate the runtime export in `requirements.txt` from the updated lock with `uv export --locked --no-hashes --no-emit-project`. (Verified: all requested versions match the lock.)
- [X] T004 [P] [US1] Generate the development export in `requirements-dev.txt` from the updated lock with `uv export --locked --no-hashes --no-emit-project --extra dev`. (Verified: all requested versions match the lock.)
- [X] T005 [US1] Run the dependency guardrails in `tests/guardrails/test_dependency_declaration_parity.py`, `tests/guardrails/test_dependency_lock_file.py`, and `tests/guardrails/test_dependency_export.py`. Confirm all 11 baseline runtime markers remain unchanged and report new markers. (Verified: 20 tests passed. All 11 baseline markers remain. One new `lazy-importer` marker applies below Python 3.15.)

**Checkpoint**: The lock and both exports use aligned package versions, and all runtime markers remain present.

---

## Phase 4: User Story 2 - Verify dependency integrity (Priority: P2)

**Goal**: Verify the dependency records, report audit limits, and add the release note.

**Independent Test**: Run `uv lock --check` and audits for both exports. Report every dependency source the audits cannot inspect. Confirm the issue release note exists.

### Implementation for User Story 2

- [X] T006 [P] [US2] Add `changelog.d/issue-4727-runtime-dependency-exports.md` with a `### Changed` heading and a bullet that names issue #4727.
- [X] T007 [P] [US2] Run `uv lock --check` against `uv.lock`. (Verified: passed.)
- [X] T008 [P] [US2] Run `pip-audit -r requirements.txt` and `pip-audit -r requirements-dev.txt`. Report current-platform scope and name every source the audits cannot inspect. (Verified: no known vulnerabilities in inspected packages. The development audit could not inspect `misthelper-devtools==0.6.3` because PyPI does not host it. Both audits cover the current platform only.)

**Checkpoint**: The lock check passes, the audit reports its coverage limits, and the release note names issue #4727.

---

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Validate, publish, and deploy the reviewed dependency change.

- [X] T009 Review `uv.lock`, `requirements.txt`, `requirements-dev.txt`, and `changelog.d/issue-4727-runtime-dependency-exports.md`. Confirm `pyproject.toml` remains unchanged. (Verified: all four files match the requested update. `pyproject.toml` is unchanged.)
- [X] T010 Run `git diff --check` for `uv.lock`, both exports, and `changelog.d/issue-4727-runtime-dependency-exports.md`. (Verified: `git diff --cached --check` passed for all staged files.)
- [X] T011 Run the dependency guardrails, lock check, both audits, and STE gate before staging. Record each result for the pull request. (Verified: 20 guardrails passed. The lock check passed. Audits found no known vulnerabilities in inspected packages. Nine Markdown files scored 93 to 100.)
- [X] T012 Build the explicit feature manifest from `uv.lock`, `requirements.txt`, `requirements-dev.txt`, `changelog.d/issue-4727-runtime-dependency-exports.md`, and the feature directory under `specs/numbered/0/0/1/2/2/4/0/2/4727-runtime-dependency-exports/`. Exclude `.specify/feature.json`. (Verified: the manifest includes 12 files. It excludes `.specify/feature.json`.)
- [X] T013 Stage only the files in the feature manifest from T012. (Verified: eight explicit manifest paths are staged.)
- [X] T014 Commit the staged files with a Conventional Commit subject and the required Co-authored-by trailer. (Verified: commit `6e195afcf` uses the required subject and trailer.)
- [X] T015 Rebase the committed feature branch onto current `origin/main`. Re-run all affected local checks after the rebase. (Verified: the branch was current. Twenty guardrails passed. The lock check passed. Audits found no known vulnerabilities in inspected packages. Nine Markdown files passed STE.)
- [X] T016 Push the rebased feature branch to its matching remote branch. (Verified: branch is published as `origin/chore/4727-runtime-dependency-exports`.)
- [X] T017 Prepare the body from `.github/PULL_REQUEST_TEMPLATE.md`. Include `Closes #4727`, the file list, check results, and audit limits. (Verified: template read. Body prepared.)
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
