# Tasks: Retry stale reads without repeating writes

**Input**: Design documents from `/specs/3732-stale-read-connection-retry/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`

**Tests**: The specification requires unit and integration tests with zero live Mist API calls.

**Organization**: Tasks are grouped by user story for independent implementation and validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it uses a different file and has no incomplete dependency.
- **[Story]**: The label maps the task to one user story.
- Tick a task only after the task has verified evidence.

## Reserved File Manifest

Production changes are limited to:

- `src/foundation/support/refactors/initialize_mist_session.py`
- `web_portal/routes/operations.py`

Test changes are limited to:

- `tests/unit/refactors/test_issue_3732_read_retry.py`
- `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`

Process records are limited to:

- `specs/3732-stale-read-connection-retry/`
- `changelog.d/issue-3732-stale-read-connection-retry.md`

Do not change upgrade portal production code, dependency files, shared documentation, or another test file.

## Phase 1: Setup and Scope Control

**Purpose**: Prepare the worktree and protect the reserved file scope.

- [X] T001 Confirm the reserved manifest and excluded work in `specs/3732-stale-read-connection-retry/plan.md`.
- [X] T002 Confirm that no open pull request owns a reserved path from `specs/3732-stale-read-connection-retry/plan.md`.
- [X] T003 Verify the existing Python environment before edits, as required by `specs/3732-stale-read-connection-retry/quickstart.md`.
- [X] T004 Record the pre-edit status for each reserved path in `specs/3732-stale-read-connection-retry/tasks.md`.

---

## Phase 2: Foundational Contracts

**Purpose**: Fix the shared policy boundaries before user story implementation.

**Critical**: Complete this phase before production changes.

- [X] T005 Review the transport constraints in `specs/3732-stale-read-connection-retry/contracts/transport-retry.md`.
- [X] T006 [P] Review the response rules in `specs/3732-stale-read-connection-retry/contracts/pick-list-read.md`.
- [X] T007 Define the exact allowed methods and retry counters in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T008 [P] Define fake SDK response builders with no credentials in `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`.

**Checkpoint**: The tests can express the retry, response, and zero-live-call contracts.

---

## Phase 3: User Story 1 - Recover a Stale Read Connection (Priority: P1) - MVP

**Goal**: Recover one stale GET or HEAD connection within a strict transport bound.

**Independent Test**: A local reset occurs first, then a successful GET returns rows after exactly two attempts.

### Tests for User Story 1

- [X] T009 [US1] Add a local reset-then-success GET test with exactly two attempts in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T010 [US1] Add a local reset-then-success HEAD test with exactly two attempts in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T011 [US1] Add an exhausted stale-read test that stops after two attempts in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T012 [US1] Add a connection-failure test that stops after three total attempts in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T013 [US1] Add an HTTP error test that proves status responses cause one attempt in `tests/unit/refactors/test_issue_3732_read_retry.py`.

### Implementation for User Story 1

- [X] T014 [US1] Add a guarded retry type for GET and HEAD in `src/foundation/support/refactors/initialize_mist_session.py`.
- [X] T015 [US1] Set `total=2`, `connect=2`, `read=1`, and all other retry categories to zero in `src/foundation/support/refactors/initialize_mist_session.py`.
- [X] T016 [US1] Mount the same bounded adapter policy for HTTP and HTTPS in `src/foundation/support/refactors/initialize_mist_session.py`.
- [X] T017 [US1] Preserve caller timeouts and existing mistapi authentication in `src/foundation/support/refactors/initialize_mist_session.py`.

**Checkpoint**: GET and HEAD recover once from a stale reset and never exceed the total bound.

---

## Phase 4: User Story 2 - Prevent a Repeated Write (Priority: P1)

**Goal**: Keep one transport attempt for POST and every other method outside GET and HEAD.

**Independent Test**: A local POST reset records one attempt and no retry.

### Tests for User Story 2

- [X] T018 [US2] Add a local POST reset test with exactly one attempt in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T019 [US2] Add PUT, PATCH, DELETE, and other-method one-attempt cases in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T020 [US2] Prove the shared read adapter fails the upgrade write-session validator in `tests/unit/refactors/test_issue_3732_read_retry.py`.
- [X] T021 [US2] Prove the existing upgrade adapter keeps zero total retries in `tests/unit/refactors/test_issue_3732_read_retry.py`.

### Implementation for User Story 2

- [X] T022 [US2] Re-raise the original transport error before retry classification for unsafe methods in `src/foundation/support/refactors/initialize_mist_session.py`.
- [X] T023 [US2] Keep HTTP status retries, redirects, retry headers, and unclassified retries disabled in `src/foundation/support/refactors/initialize_mist_session.py`.
- [X] T024 [US2] Verify no upgrade portal production file changed by inspecting the reserved manifest in `specs/3732-stale-read-connection-retry/plan.md`.

**Checkpoint**: No write method can receive a second transport attempt.

---

## Phase 5: User Story 3 - Report a Failed Pick-List Read (Priority: P2)

**Goal**: Distinguish a failed Mist API read from a valid empty HTTP 2xx result.

**Independent Test**: Local fake responses classify missing status, HTTP errors, and valid empty 2xx responses correctly.

### Tests for User Story 3

- [X] T025 [US3] Add `status_code is None` failure cases for each reserved picker in `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`.
- [X] T026 [US3] Add HTTP 400 and HTTP 500 failure cases for each reserved picker in `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`.
- [X] T027 [US3] Add valid empty HTTP 2xx cases with the existing no-rows reason in `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`.
- [X] T028 [US3] Assert the exact retry message for each failed route result in `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`.
- [X] T029 [US3] Add mixed wireless and wired source outcomes in `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`.
- [X] T030 [US3] Assert that all feature tests make zero live Mist API calls in `tests/integration/web_portal/test_issue_3732_pick_list_failures.py`.

### Implementation for User Story 3

- [X] T031 [US3] Add shared status classification to the existing `PickList` class in `web_portal/routes/operations.py`.
- [X] T032 [US3] Reject missing, unusable, 3xx, and HTTP 400-or-higher statuses in `web_portal/routes/operations.py`.
- [X] T033 [US3] Preserve valid empty HTTP 2xx results and the existing no-rows reason in `web_portal/routes/operations.py`.
- [X] T034 [US3] Apply the status rule before data access for site and device pickers in `web_portal/routes/operations.py`.
- [X] T035 [US3] Apply the status rule before data access for wireless and wired client pickers in `web_portal/routes/operations.py`.
- [X] T036 [US3] Preserve valid rows from one client source and record the failed source in `web_portal/routes/operations.py`.
- [X] T037 [US3] Return `The portal could not reach the Mist API. Try again.` for failed reads in `web_portal/routes/operations.py`.
- [X] T038 [US3] Log the operation, non-secret target, and status for each failed read in `web_portal/routes/operations.py`.

**Checkpoint**: Failed reads use the retry message, and valid empty 2xx results keep the no-rows message.

---

## Phase 6: Focused Validation and Release Record

**Purpose**: Validate the reserved implementation and record the operator-visible repair.

- [X] T039 Create one `Fixed` entry for #3732 in `changelog.d/issue-3732-stale-read-connection-retry.md`.
- [X] T040 Run the focused unit and integration tests from `specs/3732-stale-read-connection-retry/quickstart.md`.
- [X] T041 Run the related session, picker, SDK, and upgrade-session regression tests from `specs/3732-stale-read-connection-retry/quickstart.md`.
- [X] T042 Run Ruff on the two production files and two reserved test files from `specs/3732-stale-read-connection-retry/quickstart.md`.
- [X] T043 Run Black check on the two production files and two reserved test files from `specs/3732-stale-read-connection-retry/quickstart.md`.
- [X] T044 Run mypy on the two production files with `pyproject.toml`, as listed in `specs/3732-stale-read-connection-retry/quickstart.md`.
- [X] T045 Run Bandit on the two production files with `pyproject.toml`, as listed in `specs/3732-stale-read-connection-retry/quickstart.md`.
- [X] T046 Run `symbol-diff` against `origin/main` for each production file in `specs/3732-stale-read-connection-retry/plan.md`.
- [X] T047 Run STE on all feature artifacts and `changelog.d/issue-3732-stale-read-connection-retry.md`.
- [X] T048 Run `git diff --check` for the complete reserved manifest in `specs/3732-stale-read-connection-retry/plan.md`.

### Implementation evidence

- The reserved production and test paths were clean before the implementation.
- The feature directory was untracked, and `.specify/feature.json` had an existing unrelated change.
- No open pull request owned a reserved path.
- The existing `.venv` used Python 3.13.13, so no bootstrap was necessary.
- The focused feature run passed 43 tests.
- The related regression run passed 274 tests.
- Ruff, Black, Bandit, symbol checks, STE, and the diff check passed.
- The exact mypy command reported 40 existing errors in `web_portal/routes/operations.py`.
- The unchanged baseline reported the same 40 errors.
- `initialize_mist_session.py` passed mypy with no issue.
- The parent session reserved T049 through T058 for delivery.

---

## Phase 7: Commit, Quality Gate, and Pull Request

**Purpose**: Commit the verified change and complete the repository delivery workflow.

- [X] T049 Stage only the reserved manifest from `specs/3732-stale-read-connection-retry/plan.md`.
- [ ] T050 Create a local Conventional Commit for #3732 with the required co-author trailer, and include `specs/3732-stale-read-connection-retry/tasks.md`.
- [ ] T051 After the commit, run the test-quality preflight named in `specs/3732-stale-read-connection-retry/quickstart.md`.
- [ ] T052 After the commit, run the changed-test quality gate against `origin/main` for the two reserved test files.
- [ ] T053 Fetch `origin/main` and rebase the committed feature branch, as required by `specs/3732-stale-read-connection-retry/plan.md`.
- [ ] T054 Rerun focused tests and affected static gates after the rebase, using `specs/3732-stale-read-connection-retry/quickstart.md`.
- [ ] T055 Push the rebased branch with `--force-with-lease` and no direct push to `main`.
- [ ] T056 Complete every applicable heading and checklist item from `.github/PULL_REQUEST_TEMPLATE.md`.
- [ ] T057 Create the pull request to `main` with `Closes #3732`, the reserved file summary, and exact validation results.
- [ ] T058 Add the #3732 pull request link, commit SHA, gate results, and merge state to #3959, as required by `specs/3732-stale-read-connection-retry/tasks.md`.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no dependencies.
- **Phase 2** depends on Phase 1 and blocks all user story work.
- **Phase 3** and **Phase 4** depend on Phase 2.
- **Phase 5** depends on Phase 2 and can proceed in parallel with the transport stories.
- **Phase 6** depends on the selected user stories.
- **Phase 7** depends on all implementation and validation tasks.

### User Story Dependencies

- **User Story 1** has no dependency on another story.
- **User Story 2** has no behavior dependency on User Story 1, but both stories edit the same transport files.
- **User Story 3** has no behavior dependency on the transport stories and can run in parallel in separate files.

### Within Each User Story

- Write each test first and confirm that it fails for the intended reason.
- Implement the smallest reserved production change that makes the test pass.
- Preserve the existing mistapi endpoint and authentication contracts.
- Keep secrets and live Mist calls out of all tests and logs.

## Parallel Opportunities

- T006 and T008 can run in parallel with the matching foundational tasks.
- User Story 3 can run in parallel with User Stories 1 and 2.
- T039 can run in parallel with implementation after the operator-visible behavior is final.
- Ruff, Black, mypy, Bandit, symbol checks, and STE can run in parallel after focused tests pass.
- User Stories 1 and 2 require coordination because they share one production file and one test file.

## Parallel Example: Transport and Portal Work

```text
Worker A: Complete T009 through T024 in the transport production and unit test files.
Worker B: Complete T025 through T038 in the portal production and integration test files.
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1.
3. Run the focused GET and HEAD transport tests.
4. Confirm exactly two attempts for reset-then-success reads.

### Incremental Delivery

1. Add User Story 1 for stale read recovery.
2. Add User Story 2 for the write safety boundary.
3. Add User Story 3 for correct operator failure messages.
4. Run all reserved tests and regression tests.
5. Complete the commit, quality, rebase, push, and pull request tasks.

## Notes

- Do not implement a direct Mist REST request.
- Do not change an upgrade portal production file.
- Do not add a dependency or change a dependency version.
- Do not use a broad exception catch or a silent fallback.
- Keep every task unchecked until its evidence exists.
