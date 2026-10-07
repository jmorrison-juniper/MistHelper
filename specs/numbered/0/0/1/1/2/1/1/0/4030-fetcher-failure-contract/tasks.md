---

description: "Dependency-ordered tasks for issue #4030"

---

# Tasks: Fetcher Failure Contract

**Input**: Design documents in `specs/numbered/0/0/1/1/2/1/1/0/4030-fetcher-failure-contract/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/fetcher-failure-contract.md`, and `quickstart.md`

**Production scope**: Only `src/foundation/support/refactors/device_data_fetcher.py`

**Test scope**: Only `tests/unit/refactors/test_device_data_fetcher.py` and `tests/unit/web_portal/test_portal_silent_completion.py`

**Release note**: Keep `changelog.d/issue-4030-fetcher-failure-contract.md` unchanged.

**Evidence scope**: Store uncommitted command evidence under `test-artifacts/issue-4030/`.

## Phase 1: Setup and Scope Lock

**Purpose**: Confirm the worktree, dependencies, issue state, and authorized file set before any implementation edit.

- [ ] T001 Confirm `.venv\Scripts\python.exe` exists; if it does not exist, run `rtk python scripts\bootstrap_worktree.py` from the repository root.
- [ ] T002 Run `rtk git status --short --branch` and record the existing feature-owned specification files and `changelog.d/issue-4030-fetcher-failure-contract.md` without changing unrelated work.
- [ ] T003 Run `rtk gh pr list --repo jmorrison-juniper/MistHelper --state open --json number,headRefName,isDraft,files --limit 100` and stop if an open pull request owns `src/foundation/support/refactors/device_data_fetcher.py`, `tests/unit/refactors/test_device_data_fetcher.py`, or `tests/unit/web_portal/test_portal_silent_completion.py`.
- [ ] T004 Create the ignored evidence directory `test-artifacts/issue-4030/` and save the initial output of `rtk git diff --name-only` in `test-artifacts/issue-4030/initial-scope.txt`.

**Checkpoint**: The worktree is ready, and no other pull request owns an authorized implementation file.

---

## Phase 2: Foundational Contract Review

**Purpose**: Confirm the current return, display, and portal contracts without widening the implementation scope.

- [ ] T005 Read the unresolved-site branch in `src/foundation/support/refactors/device_data_fetcher.py` and the existing unresolved-site coverage in `tests/unit/refactors/test_device_data_fetcher.py`; record the current implicit return and current side effects in `test-artifacts/issue-4030/baseline-notes.txt`.
- [ ] T006 Read the real Menu 95 display and portal verdict path used by `tests/unit/web_portal/test_portal_silent_completion.py`; keep `src/interfaces/visualization/ui/interactive_display_utils.py`, `web_portal/services/operation.py`, and `PARAMETER_REGISTRY` read-only.
- [ ] T007 Record the SHA-256 hash of `changelog.d/issue-4030-fetcher-failure-contract.md` in `test-artifacts/issue-4030/changelog-hash-before.txt` so the final scope check can prove the fragment stayed unchanged.

**Checkpoint**: The implementation boundary and the existing cross-component contract are explicit.

---

## Phase 3: Red-First Tests for User Stories 1 and 2

**Goal**: Add both required regressions before the production repair.

**Independent Test for User Story 1**: An unresolved site returns explicit `False`, emits the exact error, and stops before downstream work.

**Independent Test for User Story 2**: Menu 95 reports `failed` through the real fetcher, display, executor, and scanner path when unrelated output appears.

### Tests

- [ ] T008 [P] [US1] Extend the unresolved-site contract in `tests/unit/refactors/test_device_data_fetcher.py` to assert explicit `False`, the exact `! Error fetching device data: site ID could not be resolved.` text, and no device selection, Mist request, transform, export, render, or requested result creation.
- [ ] T009 [P] [US2] Add the issue #4030 regression in `tests/unit/web_portal/test_portal_silent_completion.py` with the real `InteractiveDisplayUtils.device_tests`, `DeviceDataFetcher`, `OperationExecutor`, and `OutputFileScanner`; create unrelated output during site selection and do not fake the fetcher result or portal log entries.
- [ ] T010 [US2] Before any production edit, run `rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py -q 2>&1 | Tee-Object -FilePath test-artifacts\issue-4030\focused-red.txt`; keep the complete verbatim output and require a failing issue #4030 assertion that observes portal status `completed` instead of expected `failed`.
- [ ] T011 [US2] Inspect `test-artifacts/issue-4030/focused-red.txt` and confirm the failure comes from the pre-repair contract, not test setup, import, fixture, or environment failure.

**Checkpoint**: Both focused tests exist, and the saved red output proves the current false completion.

---

## Phase 4: User Story 1 - Report the Missing Site as a Failure

**Goal**: Make the fetcher emit the required operator error and return explicit failure before downstream work.

**Independent Test**: Run the fetcher with no resolvable site and verify the exact error, explicit `False`, and zero downstream calls.

### Implementation

- [ ] T012 [US1] Change only the unresolved-site branch in `src/foundation/support/refactors/device_data_fetcher.py` to log `! Error fetching device data: site ID could not be resolved.` and return explicit `False`; add the required inline comment and do not change adjacent failure contracts.
- [ ] T013 [US1] Run `rtk .venv\Scripts\python.exe -m pytest tests\unit\refactors\test_device_data_fetcher.py -q` and require all focused fetcher tests to pass.

**Checkpoint**: User Story 1 passes independently without a Mist credential.

---

## Phase 5: User Story 2 - Keep the Portal Verdict Correct

**Goal**: Prove that unrelated output cannot override the fetcher failure.

**Independent Test**: Execute Menu 95 through the real path and verify `failed`, the exact failure reason, retained unrelated output, no completion log, and no Mist request.

### Validation

- [ ] T014 [US2] Run `rtk .venv\Scripts\python.exe -m pytest tests\unit\web_portal\test_portal_silent_completion.py -k 4030 -q` and require the issue #4030 regression to pass.
- [ ] T015 [US2] Run `rtk .venv\Scripts\python.exe -m pytest tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py -q` and require both complete focused modules to pass.
- [ ] T016 [US2] Save the green focused output with `rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py -q 2>&1 | Tee-Object -FilePath test-artifacts\issue-4030\focused-green.txt` and confirm the artifact contains no credential or secret.

**Checkpoint**: Both user stories pass together, and the red-green evidence uses the same focused test set.

---

## Phase 6: Required Local Gates

**Purpose**: Run the exact focused and repository gates required for the authorized Python files.

- [ ] T017 Run `rtk .venv\Scripts\python.exe -m ruff check src\foundation\support\refactors\device_data_fetcher.py tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py` and require `All checks passed`.
- [ ] T018 Run `rtk .venv\Scripts\python.exe -m black --check src\foundation\support\refactors\device_data_fetcher.py tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py` and require no file to need a change.
- [ ] T019 Run `rtk .venv\Scripts\python.exe -m mypy src\foundation\support\refactors\device_data_fetcher.py --config-file pyproject.toml` and require success.
- [ ] T020 Run `rtk bandit -c pyproject.toml -r src\foundation\support\refactors\device_data_fetcher.py -q` and require no finding.
- [ ] T021 Run `rtk proxy .venv\Scripts\python.exe -m radon cc src\foundation\support\refactors\device_data_fetcher.py -j | rtk complexity-gate --max 10` and require no block above cyclomatic complexity 10.
- [ ] T022 Run `rtk .venv\Scripts\python.exe -m py_compile src\foundation\support\refactors\device_data_fetcher.py` and require no output.
- [ ] T023 Run `rtk symbol-diff --base origin/main src\foundation\support\refactors\device_data_fetcher.py` and require `no module-level name changed`.
- [ ] T024 Run `rtk git diff --check` and `rtk git diff --name-only`; require no whitespace error and no implementation change outside the one production file and two test files.
- [ ] T025 Compare the SHA-256 hash of `changelog.d/issue-4030-fetcher-failure-contract.md` with `test-artifacts/issue-4030/changelog-hash-before.txt` and require an exact match.

**Checkpoint**: The focused behavior, syntax, style, types, security, complexity, symbols, and strict scope all pass.

---

## Phase 7: Commit, Rebase, and Post-Rebase Verification

**Purpose**: Create a committed implementation, rebase it once onto current `origin/main`, and verify the rebased tree before analysis.

- [ ] T026 Stage only the feature specification records, `changelog.d/issue-4030-fetcher-failure-contract.md`, `src/foundation/support/refactors/device_data_fetcher.py`, `tests/unit/refactors/test_device_data_fetcher.py`, and `tests/unit/web_portal/test_portal_silent_completion.py`; commit with a valid `fix` Conventional Commit subject, `Closes #4030`, and the required `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>` trailer.
- [ ] T027 Run `rtk git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"` and then `rtk git rebase origin/main`; resolve no conflict by dropping another change.
- [ ] T028 Rerun tasks T015 and T017 through T025 against the rebased tree and require the same passing results.
- [ ] T029 If post-rebase repair changed an authorized file, stage each changed path explicitly and commit it before continuing; otherwise run `rtk git status --short --untracked-files=all` and require no relevant staged, unstaged, or untracked implementation change.

**Checkpoint**: The final implementation tree is rebased, committed, clean, and ready for the committed-tree analyzer.

---

## Phase 8: Required Post-Commit Test-Quality Checks

**Purpose**: Run the test-quality preflight and changed-from analyzer only after the final test changes are committed.

- [ ] T030 Run `rtk .venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides` and require the live guidance preflight to pass.
- [ ] T031 Run `rtk git rev-parse --verify "origin/main^{commit}"` and record the resolved base commit in `test-artifacts/issue-4030/origin-main-commit.txt`.
- [ ] T032 Run `rtk test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` and require `gate: 0 new findings vs baseline`.
- [ ] T033 Run `rtk git status --short --untracked-files=all` and require no relevant staged, unstaged, or untracked implementation change after the analyzer.

**Checkpoint**: The analyzer reads the final committed test tree and reports zero new findings.

---

## Phase 9: One Push and Immediate Draft Pull Request Checks

**Purpose**: Publish one final branch revision and confirm the pull request state immediately.

- [ ] T034 Push exactly once with `rtk git push --force-with-lease origin HEAD:jmorrison-juniper-fix-4030-fetcher-failure-contract`; do not make an intermediate push and do not push directly to `main`.
- [ ] T035 Read `.github/PULL_REQUEST_TEMPLATE.md` and create one draft pull request to `main` with a valid `fix` title, `Closes #4030`, the exact changed-file list, the red and green evidence, every gate result, the rebase result, the one-push statement, and deployment and rollback notes.
- [ ] T036 Immediately run `rtk gh pr view --repo jmorrison-juniper/MistHelper --json number,state,isDraft,headRefName,baseRefName,url`; require `state` to be `OPEN`, `isDraft` to be `true`, the head to be `jmorrison-juniper-fix-4030-fetcher-failure-contract`, and the base to be `main`.
- [ ] T037 Immediately run `rtk gh pr checks --repo jmorrison-juniper/MistHelper` and record the initial check state without changing the draft state or adding `auto-merge`.

**Checkpoint**: One draft pull request is open against `main`, and its initial state is recorded.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no dependency.
- **Phase 2** depends on Phase 1.
- **Phase 3** depends on Phase 2. T010 depends on T008 and T009.
- **Phase 4** depends on the saved red proof in T010 and the diagnosis in T011.
- **Phase 5** depends on the production repair in T012.
- **Phase 6** depends on both user story validations.
- **Phase 7** depends on every local gate.
- **Phase 8** depends on the final committed and rebased tree.
- **Phase 9** depends on the zero-finding analyzer and a clean relevant tree.

### User Story Dependencies

- **User Story 1 (P1)** provides the explicit fetcher failure contract.
- **User Story 2 (P2)** depends on User Story 1 for the repaired portal verdict.
- Both test changes must exist before the production repair so T010 captures one valid integrated red proof.

### Parallel Opportunities

- T008 and T009 can run in parallel because they edit different authorized test files.
- All later tasks run serially because they depend on the integrated red proof, one production edit, one commit sequence, one rebase, one analyzer order, and one push.

---

## Parallel Example: Red-First Test Authoring

```text
Task T008: Extend tests/unit/refactors/test_device_data_fetcher.py.
Task T009: Extend tests/unit/web_portal/test_portal_silent_completion.py.
Join at T010: Run both focused modules before the production repair.
```

---

## Implementation Strategy

### MVP First

1. Complete Phases 1 through 4.
2. Validate User Story 1 independently with T013.
3. Stop if the exact error, explicit `False`, or zero-side-effect contract fails.

### Incremental Delivery

1. Add both regressions and save the integrated red proof.
2. Repair only the unresolved-site branch.
3. Prove the fetcher contract.
4. Prove the portal verdict with unrelated output.
5. Run all required gates.
6. Commit before the changed-from analyzer.
7. Rebase, verify, push once, and open one draft pull request.

### Scope Guard

- Do not edit `src/interfaces/visualization/ui/interactive_display_utils.py`.
- Do not edit `web_portal/services/operation.py`.
- Do not edit `PARAMETER_REGISTRY`.
- Do not edit any production file except `src/foundation/support/refactors/device_data_fetcher.py`.
- Do not edit any test file except the two named test modules.
- Do not modify the existing changelog fragment.
