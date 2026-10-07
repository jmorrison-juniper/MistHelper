---

description: "Dependency-ordered tasks for issue 4033 delay history integrity"
---

# Tasks: Menu 56 Delay Metrics Integrity

**Input**: Design documents from `specs/numbered/0/0/1/1/2/1/1/3/4033-menu-56-jsi-failure/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/delay-history-persistence.md`, and `quickstart.md`

**Tests**: The specification requires deterministic red-first tests and complete regression tests.

**Scope**: Modify only `src/foundation/support/utils/rate_limiting.py`, `tests/unit/test_rate_limiting.py`, and `changelog.d/issue-4033-menu-56-jsi-failure.md` during implementation.

**Excluded file**: Do not modify `web_portal/services/operation.py`.

## Phase 1: User Story 1 - Prove Concurrent Corruption (Priority: P1)

**Goal**: Prove the current concurrent-writer defect before any source repair.

**Independent Test**: Coordinate concurrent writers and capture `File I/O: Failed to read data/delay_metrics.json`.

### Red Tests for User Story 1

- [ ] T001 [US1] Add a deterministic concurrent-writer test with bounded thread events and a controlled write handle in `tests/unit/test_rate_limiting.py`
- [ ] T002 [US1] Run `python -m pytest tests\unit\test_rate_limiting.py -k concurrent_writer -vv` and confirm the unchanged source fails in `tests/unit/test_rate_limiting.py`
- [ ] T003 [US1] Confirm the T002 captured log contains the exact warning `File I/O: Failed to read data/delay_metrics.json` from `src/foundation/support/utils/rate_limiting.py`
- [ ] T004 [US1] Preserve the red test final assertions without weakening them in `tests/unit/test_rate_limiting.py`

**Checkpoint**: The current source has a deterministic red proof and the exact warning is captured.

---

## Phase 2: User Story 1 - Repair Concurrent Persistence (Priority: P1)

**Goal**: Serialize the complete read-modify-write cycle and preserve every complete row.

**Independent Test**: Run the concurrent-writer test and confirm each expected row exists exactly once as valid JSONL.

### Implementation for User Story 1

- [ ] T005 [US1] Add one module-level `threading.Lock` for delay history persistence in `src/foundation/support/utils/rate_limiting.py`
- [ ] T006 [US1] Hold the same lock from the destination read through replacement or failure cleanup in `src/foundation/support/utils/rate_limiting.py`
- [ ] T007 [US1] Create a named temporary file beside the destination and write every retained JSONL row completely in `src/foundation/support/utils/rate_limiting.py`
- [ ] T008 [US1] Close the temporary file before `os.replace` changes the destination in `src/foundation/support/utils/rate_limiting.py`
- [ ] T009 [US1] Add narrow filesystem and JSON exception handling with ASCII context logs in `src/foundation/support/utils/rate_limiting.py`
- [ ] T010 [US1] Run `python -m pytest tests\unit\test_rate_limiting.py -k concurrent_writer -vv` and confirm the concurrent proof passes with complete rows

**Checkpoint**: Concurrent writers preserve all expected complete rows within the retention cap.

---

## Phase 3: User Story 2 - Preserve the Previous File (Priority: P2)

**Goal**: Keep the prior destination intact and remove temporary files after a failed cycle.

**Independent Test**: Force `os.replace` to fail and compare the destination bytes before and after the call.

### Tests and Implementation for User Story 2

- [ ] T011 [US2] Add a replacement-failure test that proves byte-for-byte destination integrity in `tests/unit/test_rate_limiting.py`
- [ ] T012 [US2] Add failed-write and failed-replacement cleanup tests for same-directory temporary files in `tests/unit/test_rate_limiting.py`
- [ ] T013 [US2] Remove the temporary file after each failed write or replacement in `src/foundation/support/utils/rate_limiting.py`
- [ ] T014 [US2] Log a cleanup failure with the temporary path and bound exception in `src/foundation/support/utils/rate_limiting.py`
- [ ] T015 [US2] Add a successful-write test that proves no temporary file remains in `tests/unit/test_rate_limiting.py`

**Checkpoint**: Each failed replacement preserves the prior bytes, and each completed cycle leaves no temporary file.

---

## Phase 4: User Story 3 - Recover from Empty History (Priority: P3)

**Goal**: Treat a zero-byte destination as empty history and preserve existing retention behavior.

**Independent Test**: Start with a zero-byte file and confirm the next update creates one valid row without a warning.

### Tests and Implementation for User Story 3

- [ ] T016 [US3] Add a zero-byte destination test with warning assertions in `tests/unit/test_rate_limiting.py`
- [ ] T017 [US3] Treat a missing or zero-byte destination as empty history in `src/foundation/support/utils/rate_limiting.py`
- [ ] T018 [US3] Complete retention-cap and custom-filename regression coverage in `tests/unit/test_rate_limiting.py`

**Checkpoint**: Empty history recovers with one valid row, and existing retention behavior remains unchanged.

---

## Phase 5: Changelog and Pre-Commit Gates

**Purpose**: Complete the user-visible record and verify the explicit implementation manifest.

- [ ] T019 Add an issue 4033 fixed-entry fragment in `changelog.d/issue-4033-menu-56-jsi-failure.md`
- [ ] T020 Run `python -m pytest tests\unit\test_rate_limiting.py` for the complete target test module
- [ ] T021 Run `python -m py_compile src\foundation\support\utils\rate_limiting.py` and `python -m mypy src\foundation\support\utils\rate_limiting.py --config-file pyproject.toml`
- [ ] T022 Run the full-tree gate `python -m ruff check .` from the repository root
- [ ] T023 Run the full-tree gate `python -m black --check .` from the repository root
- [ ] T024 Confirm the implementation manifest contains only `src/foundation/support/utils/rate_limiting.py`, `tests/unit/test_rate_limiting.py`, and `changelog.d/issue-4033-menu-56-jsi-failure.md`

**Checkpoint**: The target tests and each applicable pre-commit gate pass.

---

## Phase 6: Commit and Test-Quality Gate

**Purpose**: Commit the verified implementation before the required test-quality comparison.

- [ ] T025 Stage only `src/foundation/support/utils/rate_limiting.py`, `tests/unit/test_rate_limiting.py`, and `changelog.d/issue-4033-menu-56-jsi-failure.md`
- [ ] T026 Commit the staged manifest with a Conventional Commit subject and `Closes #4033`
- [ ] T027 Fetch `origin/main` and verify `origin/main^{commit}` for the test-quality base without rebasing
- [ ] T028 Run `python -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides`
- [ ] T029 Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` and require zero new findings

**Checkpoint**: The committed tests pass the required changed-from test-quality gate.

---

## Phase 7: Rebase and Post-Rebase Verification

**Purpose**: Rebase the committed branch before its only push.

- [ ] T030 Rebase the current issue 4033 branch onto `origin/main`
- [ ] T031 Run `python -m pytest tests\unit\test_rate_limiting.py` after the rebase
- [ ] T032 Run `python -m ruff check .` after the rebase
- [ ] T033 Run `python -m black --check .` after the rebase
- [ ] T034 Confirm the rebased branch still excludes `.specify/feature.json` and `web_portal/services/operation.py`

**Checkpoint**: The rebased commit passes the required repeated gates and preserves the approved scope.

---

## Phase 8: Single Push, Draft Pull Request, and State Verification

**Purpose**: Push once, create a draft pull request, and verify its exact state.

- [ ] T035 Push exactly once with `git push --force-with-lease origin HEAD`
- [ ] T036 Read `.github/PULL_REQUEST_TEMPLATE.md` and create a draft pull request that targets `main`, closes issue 4033, and records the gate results
- [ ] T037 Confirm the pull request has no `auto-merge` label and do not enable auto-merge
- [ ] T038 Run `gh pr view --json isDraft,state,headRefName,headRefOid,labels,url` and `git rev-parse HEAD`
- [ ] T039 Confirm the pull request is draft and open, its remote head equals local `HEAD`, and its labels exclude `auto-merge`

**Checkpoint**: The open pull request remains draft, matches the local commit, and cannot auto-merge.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1**: Starts first and blocks every source edit.
- **Phase 2**: Depends on the failed red proof and exact warning capture in Phase 1.
- **Phase 3**: Depends on the concurrent persistence repair in Phase 2.
- **Phase 4**: Depends on the persistence and cleanup behavior from Phases 2 and 3.
- **Phase 5**: Depends on complete tests and implementation for all user stories.
- **Phase 6**: Depends on every pre-commit gate and the explicit manifest check.
- **Phase 7**: Depends on the commit and successful test-quality gate.
- **Phase 8**: Depends on the rebase and repeated post-rebase gates.

### User Story Dependencies

- **User Story 1 (P1)**: The red proof must precede all source work. The source repair must make the unchanged proof pass.
- **User Story 2 (P2)**: Depends on the atomic temporary-file replacement design from User Story 1.
- **User Story 3 (P3)**: Depends on the locked read path from User Story 1 and the cleanup behavior from User Story 2.

### Parallel Opportunities

No implementation task is parallel.
The approved workflow edits one shared test file and one shared source file in a strict sequence.
The delivery tasks also require one ordered commit, rebase, push, and pull request.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 without a source edit.
2. Complete Phase 2 and rerun the unchanged concurrent proof.
3. Stop and verify that every expected concurrent row is complete and present.

### Incremental Delivery

1. Add the deterministic red proof and capture the exact warning.
2. Repair the locked atomic persistence cycle.
3. Add replacement-failure and cleanup guarantees.
4. Add empty-history and retention regression guarantees.
5. Add the changelog fragment and run all required gates.
6. Commit, run the test-quality gate, and rebase.
7. Repeat the required gates after the rebase.
8. Push once and create the draft pull request without auto-merge.

## Notes

- Do not modify `.specify/feature.json`.
- Do not modify `web_portal/services/operation.py`.
- Do not weaken the red test after the source repair.
- Do not push before the rebase.
- Do not push more than once.
- Do not merge the pull request.
