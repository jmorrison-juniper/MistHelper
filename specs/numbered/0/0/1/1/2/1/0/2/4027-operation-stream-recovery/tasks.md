---

description: "Dependency-ordered implementation tasks for operation stream recovery"

---

# Tasks: Operation Stream Recovery

**Input**: Design documents in `specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/browser-operation-run-state.md`, and `quickstart.md`

**Tests**: The specification requires test-first Playwright proof for #4027 and #4032.

**Organization**: The tasks preserve separate red-proof and repair commits for each issue.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it changes a different file.
- **[Story]**: The task maps to a user story in `spec.md`.
- Tick a task only after its required evidence exists.

## Required File Boundary

Product edits are permitted only in `web_portal/static/js/operations.js`.

The implementation can also change these required files:

```text
tests/e2e/web_portal/test_operation_stream_recovery.py
changelog.d/issue-4027-operation-stream-recovery.md
changelog.d/issue-4032-output-replay-deduplication.md
specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/
```

Do not change these excluded files:

```text
web_portal/services/operation.py
web_portal/services/output_scan.py
MistHelper.py
tests/e2e/web_portal/test_operations_panel_workflow.py
```

## Phase 1: Setup and Environment Refresh

**Purpose**: Create a clean, current, and reproducible worktree before test changes.

- [ ] T001 Record `git status --short` and `git diff --name-only` from repository root `.` without changing existing work.
- [ ] T002 Confirm no open pull request owns the required files through `gh pr list --state open --json number,headRefName,files` from `.`.
- [ ] T003 Refresh the worktree environment with `python scripts\bootstrap_worktree.py` from repository root `.`.
- [ ] T004 Verify `.venv\Scripts\python.exe`, Playwright 1.63.0, pytest-playwright 0.9.0, and Chromium from `.venv\` without dependency edits.
- [ ] T005 Commit only `specs/numbered/0/0/1/1/2/1/0/2/4027-operation-stream-recovery/` as `docs(spec): plan operation stream recovery`.

**Checkpoint**: The planning records are committed, and both changelog fragments remain outside the planning commit.

---

## Phase 2: Foundational Browser Proof Design

**Purpose**: Identify the existing browser seams before the first red proof.

**Critical**: Complete this phase before either issue sequence.

- [ ] T006 Map stream ownership, status recovery, terminal rendering, and output rendering in `web_portal/static/js/operations.js`.
- [ ] T007 Map reusable Flask and Playwright fixtures under `tests/e2e/conftest.py` and `tests/e2e/web_portal/`.
- [ ] T008 Define controlled `EventSource`, timeout, status route, and preview route evidence in `tests/e2e/web_portal/test_operation_stream_recovery.py`.
- [ ] T009 Record the allowed and excluded file baseline from `origin/main` for the final scope check in `.`.

**Checkpoint**: The browser proof design can reproduce each defect without a Mist credential.

---

## Phase 3: User Story 1 - Recover a Lost Terminal Event (Priority: P1) MVP

**Goal**: Recover `completed` and `failed` states while the event stream remains open.

**Independent Test**: Status changes from `running` to terminal without an event error, reconnect, or terminal event.

### Red Proof for #4027

- [ ] T010 [US1] Add only #4027 Playwright cases and controlled browser doubles in `tests/e2e/web_portal/test_operation_stream_recovery.py`.
- [ ] T011 [US1] Print examined status checks, terminal transitions, stream errors, and 5,000-millisecond delays from `tests/e2e/web_portal/test_operation_stream_recovery.py`.
- [ ] T012 [US1] Run the #4027 selectors in `tests/e2e/web_portal/test_operation_stream_recovery.py` and confirm the current page remains `Running`.
- [ ] T013 [US1] Stage only `tests/e2e/web_portal/test_operation_stream_recovery.py` and verify the staged file list from `.`.
- [ ] T014 [US1] Commit the failing proof as `test(web-portal): reproduce operation stream recovery failure` with the required co-author trailer.

### Repair for #4027

- [ ] T015 [US1] Replace `currentSSE` with one run-state record in `web_portal/static/js/operations.js` without adding a top-level declaration.
- [ ] T016 [US1] Add one recursive 5,000-millisecond status check with request and run guards in `web_portal/static/js/operations.js`.
- [ ] T017 [US1] Add terminal cleanup for timers, requests, and matching streams in `web_portal/static/js/operations.js`.
- [ ] T018 [P] [US1] Finalize the #4027 release note in `changelog.d/issue-4027-operation-stream-recovery.md`.
- [ ] T019 [US1] Run the #4027 selectors in `tests/e2e/web_portal/test_operation_stream_recovery.py` and confirm all #4027 cases pass.
- [ ] T020 [US1] Stage only `web_portal/static/js/operations.js` and `changelog.d/issue-4027-operation-stream-recovery.md`, then verify the staged list.
- [ ] T021 [US1] Commit the repair as `fix(web-portal): recover terminal operation status` with the required co-author trailer.

**Checkpoint**: #4027 has one red commit and one later repair commit.

---

## Phase 4: User Story 2 - Render Each Output Once (Priority: P1)

**Goal**: Render each run-scoped exact output identity once and clear terminal empty output.

**Independent Test**: Status replay and terminal replay produce one link and one preview load for one exact path.

### Red Proof for #4032

- [ ] T022 [US2] Add only #4032 replay cases to `tests/e2e/web_portal/test_operation_stream_recovery.py` after the #4027 repair commit.
- [ ] T023 [US2] Cover duplicate replay, same-name paths, cross-run paths, and terminal empty output in `tests/e2e/web_portal/test_operation_stream_recovery.py`.
- [ ] T024 [US2] Print examined replay sources, exact paths, rendered links, and preview loads from `tests/e2e/web_portal/test_operation_stream_recovery.py`.
- [ ] T025 [US2] Run the #4032 selectors in `tests/e2e/web_portal/test_operation_stream_recovery.py` and confirm the current duplicate behavior fails.
- [ ] T026 [US2] Stage only `tests/e2e/web_portal/test_operation_stream_recovery.py` and verify the staged file list from `.`.
- [ ] T027 [US2] Commit the failing proof as `test(web-portal): reproduce output replay duplication` with the required co-author trailer.

### Repair for #4032

- [ ] T028 [US2] Deduplicate each exact path delivery and preserve first order in `web_portal/static/js/operations.js`.
- [ ] T029 [US2] Compare canonical `run_id` and exact-path sets before rendering in `web_portal/static/js/operations.js`.
- [ ] T030 [US2] Replace changed links and skip identical preview loads in `web_portal/static/js/operations.js`.
- [ ] T031 [US2] Clear terminal empty output with `OperationResults.reset()` in `web_portal/static/js/operations.js` without resetting the terminal message.
- [ ] T032 [P] [US2] Finalize the #4032 release note in `changelog.d/issue-4032-output-replay-deduplication.md`.
- [ ] T033 [US2] Run all tests in `tests/e2e/web_portal/test_operation_stream_recovery.py` and confirm both issue contracts pass.
- [ ] T034 [US2] Stage only `web_portal/static/js/operations.js` and `changelog.d/issue-4032-output-replay-deduplication.md`, then verify the staged list.
- [ ] T035 [US2] Commit the repair as `fix(web-portal): make output replay idempotent` with the required co-author trailer.

**Checkpoint**: #4032 has one red commit and one later repair commit.

---

## Phase 5: User Story 3 - Keep the Repair Within the Browser Boundary (Priority: P2)

**Goal**: Preserve all server contracts and restrict product changes to the browser controller.

**Independent Test**: The final diff contains one product file, one dedicated test module, two fragments, and feature records.

- [ ] T036 [US3] Verify `git diff --name-only origin/main...HEAD` contains only the approved paths from the Required File Boundary.
- [ ] T037 [US3] Verify `web_portal/services/operation.py` and `web_portal/services/output_scan.py` match `origin/main`.
- [ ] T038 [US3] Verify `MistHelper.py` and `tests/e2e/web_portal/test_operations_panel_workflow.py` match `origin/main`.
- [ ] T039 [US3] Verify `tests/e2e/web_portal/test_operation_stream_recovery.py` is the only new browser test module.
- [ ] T040 [US3] Verify the four issue commits remain ordered and separate through `git log --oneline origin/main..HEAD`.

**Checkpoint**: The implementation changes no server contract and no excluded file.

---

## Phase 6: Required Focused and Full-Tree Gates

**Purpose**: Run every required local gate before rebase and repeat affected gates after rebase.

- [ ] T041 Run Ruff, Black, the dedicated Playwright module, and the changelog guard for `tests/e2e/web_portal/test_operation_stream_recovery.py`.
- [ ] T042 Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`.
- [ ] T043 Run the changed-test analyzer against `origin/main` and the full analyzer using `.github/test-quality-config.toml`.
- [ ] T044 Run compile, `ruff check .`, `black --check --diff .`, and mypy with `MYPY_PATHS` from `.github/workflows/ci.yml`.
- [ ] T045 Run Radon, Vulture, Pylint, pydocstyle, and Interrogate with their full paths from `.github/workflows/ci.yml`.
- [ ] T046 Run `bandit -c pyproject.toml -r . -q` and `pip-audit -r requirements.txt` from repository root `.`.
- [ ] T047 Run both documented `pytest-chunks` commands for `tests\unit`, `tests\contract`, `tests\guardrails`, and `tests\integration`.
- [ ] T048 Run `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` and confirm coverage remains at least 80 percent.
- [ ] T049 Run `python MistHelper.py --test` from repository root `.` and record each credential-based skip.
- [ ] T050 Record each command and result for the pull request body based on `.github/PULL_REQUEST_TEMPLATE.md`.

**Checkpoint**: Every required focused and full-tree gate passes before rebase.

---

## Phase 7: Rebase, One Push, and Draft Pull Request

**Purpose**: Deliver the verified commit sequence through one remote update.

- [ ] T051 Fetch `origin/main` and rebase the committed branch onto it from repository root `.` without a merge commit.
- [ ] T052 Repeat tasks T041 through T049 after the rebase and update gate evidence for `.github/PULL_REQUEST_TEMPLATE.md`.
- [ ] T053 Verify `git status --short` is clean and the five planned commits remain ordered in `origin/main..HEAD`.
- [ ] T054 Push exactly once with `git push --force-with-lease -u origin HEAD` from repository root `.`.
- [ ] T055 Create one draft pull request to `main` with title `fix(web-portal): recover operation stream state` and both issue closures.
- [ ] T056 Populate every section and checklist item from `.github/PULL_REQUEST_TEMPLATE.md` with actual gate results or `N/A`.
- [ ] T057 Verify the pull request reports `isDraft: true`, base `main`, the current head branch, and the expected title through `gh pr view`.
- [ ] T058 Verify the draft pull request changed-file list matches the Required File Boundary through `gh pr view --json files`.

**Checkpoint**: The branch has one push, and the pull request remains a verified draft.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** starts immediately.
- **Phase 2** depends on Phase 1.
- **Phase 3** depends on Phase 2.
- **Phase 4** depends on the #4027 repair commit in Phase 3.
- **Phase 5** depends on both issue repair commits.
- **Phase 6** depends on the final four issue commits.
- **Phase 7** depends on all local gates.

### Commit Dependencies

```text
docs(spec): plan operation stream recovery
  -> test(web-portal): reproduce operation stream recovery failure
  -> fix(web-portal): recover terminal operation status
  -> test(web-portal): reproduce output replay duplication
  -> fix(web-portal): make output replay idempotent
```

Do not combine a red proof with its repair.
Do not combine the two repairs.
Do not push before the rebase and post-rebase gates.

### User Story Dependencies

- **User Story 1** is the MVP and has no user story dependency.
- **User Story 2** follows User Story 1 because both stories edit the same test and product files.
- **User Story 3** verifies the completed User Story 1 and User Story 2 diff.

### Parallel Opportunities

- T018 can run with T015 through T017 because it changes a separate fragment.
- T032 can run with T028 through T031 because it changes a separate fragment.
- No red proof can run in parallel with its repair.
- User Story 1 and User Story 2 cannot run in parallel because they share two files.

---

## Parallel Example: User Story 1

```text
Task T015-T017: Repair terminal status recovery in web_portal/static/js/operations.js.
Task T018: Finalize changelog.d/issue-4027-operation-stream-recovery.md.
```

## Parallel Example: User Story 2

```text
Task T028-T031: Repair output replay in web_portal/static/js/operations.js.
Task T032: Finalize changelog.d/issue-4032-output-replay-deduplication.md.
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete the #4027 red proof.
3. Complete the #4027 repair.
4. Run the #4027 selectors.
5. Stop and verify User Story 1 independently.

### Incremental Delivery

1. Commit the feature planning records.
2. Deliver #4027 through separate red and repair commits.
3. Deliver #4032 through separate red and repair commits.
4. Run browser boundary verification.
5. Run focused and full-tree gates.
6. Rebase and repeat affected gates.
7. Push once and create a draft pull request.

## Notes

- Use `.venv\Scripts\python.exe` when shell activation is not persistent.
- Add inline purpose comments to each changed executable JavaScript line.
- Add before and after logs for each browser request.
- Keep the existing status and output discovery contracts unchanged.
- Do not add a compatibility path or a second product file.
- Keep test evidence free of credentials and production Mist requests.
