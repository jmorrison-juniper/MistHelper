# Tasks: Webhook config test isolation

**Input**: Numeric record `specs\numbered\0\0\1\2\2\4\1\0\4730-webhook-env-isolation`. Prerequisites: `plan.md`, `spec.md`, `design/research.md`, and `design/quickstart.md`.

## Format: `[ID] [P?] Description`

`[P]` marks a task that is safe in parallel. Each task names its requirements, exact paths, acceptance statement, one verification command from the local gates table, and status. Status is one of: open, verified-present, partial, or absent.

**Naming**: `NEW-ISSUE` is the number that GitHub assigns to the follow-up issue created in T008. The branch and commit names use that number.

## Path Conventions

Single project. Paths start at the repository root. The changed file is `tests/unit/web_portal/test_webhook_signature.py`. The record folder is the route folder that `spec.md` names.

## Phase 1: Verify the merged repair (no code change)

- [x] T001 [P] Verify the main blob of the test file. Requirements: FR-001, FR-002. Paths: `tests/unit/web_portal/test_webhook_signature.py`. Acceptance: the tree entry on `main` is blob `bcf0ad12319281ea484e98bba65ff2d544f6b8d3` (R-01). Verification command (Tests gate): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Remote read: quickstart Q-1. Status: verified-present. (delivered: tests/unit/web_portal/test_webhook_signature.py)

- [x] T002 [P] Verify the precondition and the default assertion on `main`. Requirements: FR-001, FR-006. Paths: `tests/unit/web_portal/test_webhook_signature.py`. Acceptance: line 234 removes `WEBHOOK_ENABLED`, and line 240 asserts `is True` (R-02, R-03). Verification command (Tests gate): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Remote read: quickstart Q-2. Status: verified-present. (delivered: tests/unit/web_portal/test_webhook_signature.py)

- [x] T003 [P] Verify the production default on `main`. Requirements: FR-001. Paths: `web_portal/app.py`, `web_portal/routes/webhooks.py`. Acceptance: `web_portal/app.py` line 129 reads `WEBHOOK_ENABLED` with the default `"true"` (R-11). Verification command (Tests gate): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Status: verified-present. (delivered: web_portal/app.py)

- [x] T004 [P] Verify that no sibling test depends on the default. Requirements: FR-005. Paths: `tests/unit/config/standalone/foundation/persistence/redis/test_webhook_ingestion.py`, `tests/e2e/web_portal/test_map_site_selection_race_journey.py`, `tests/support/wip_target_controls/native.py`, `tests/conftest.py`. Acceptance: each sibling sets the variable itself or has no handling (R-13, R-14, R-15, R-16). Verification command (Tests gate): `python -m pytest tests/unit/config/standalone/foundation/persistence/redis/test_webhook_ingestion.py`. Remote read: quickstart Q-3. Status: verified-present. (delivered: tests/unit/config/standalone/foundation/persistence/redis/test_webhook_ingestion.py)

- [x] T005 [P] Verify the CI evidence on `main`. Requirements: SC-001. Paths: `.github/workflows/ci.yml`. Acceptance: Quality Gates run 45774119357 on `f03c6c9` concluded success, and the root unit shard passed (R-20, R-21). Verification command (Full tests gate): `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`. Remote read: quickstart Q-4. Status: verified-present. (delivered: .github/workflows/ci.yml)

- [x] T006 [P] Verify the merged scope and the ancestry of the merge commit. Requirements: FR-005, SC-002. Paths: `tests/unit/web_portal/test_webhook_signature.py`. Acceptance: PR #4843 changed one file with `+1 -0`, and merge commit `15da34506` is an ancestor of `main` (R-08, R-09). Verification command (Tests gate): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Remote read: quickstart Q-5. Status: verified-present. (delivered: tests/unit/web_portal/test_webhook_signature.py)

- [ ] T007 Record that the issue link is partial. Requirements: FR-011. Paths: `tests/unit/web_portal/test_webhook_signature.py` (the merged file that PR 4843 changed). Acceptance: PR #4843 links issue #4730 with `Refs #4730` and no closing keyword (R-10). Verification command (Tests gate): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Status: partial.

## Phase 2: Issue hygiene

- [ ] T008 File the follow-up issue before the branch. Requirements: FR-008. Paths: `tests/unit/web_portal/test_webhook_signature.py`. Acceptance: a new issue titled `Chore: missing inline comments in the webhook config test` exists with labels `chore`, `tests`, and `in-progress`. Verification command (Tests gate, step A worktree): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Status: open.

- [ ] T009 Close issue #4730 after step A passes. Requirements: FR-011. Paths: `tests/unit/web_portal/test_webhook_signature.py` (the closure evidence names this merged file). Acceptance: the issue state is CLOSED. A closing comment names PR #4843 and merge commit `15da34506`. The `in-progress` label is removed (quickstart Q-6). Owner: the orchestrator (D-2). Verification command (Tests gate, step A worktree): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Status: open.

## Phase 3: Comment-only follow-up

- [ ] T010 Add inline comments to the touched test function. Requirements: FR-008, FR-009. Paths: `tests/unit/web_portal/test_webhook_signature.py` lines 229, 230, 233, 234, 235, 237, 239, and 240. Acceptance: each listed code line has one inline comment on the same line that gives its purpose. No code token changes. Each line fits in 120 characters (R-31). Depends on T008. Verification command (Lint gate): `python -m ruff check .`. Status: open.

- [ ] T011 Confirm that the follow-up changes comments only. Requirements: FR-009. Paths: `tests/unit/web_portal/test_webhook_signature.py`. Acceptance: the diff names one file, and the symbol gate reports no module-level name change. Depends on T010. Verification command (Symbols gate): `symbol-diff --base origin/main tests/unit/web_portal/test_webhook_signature.py`. Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run the local gates in two worktrees. Requirements: FR-003, FR-004, FR-007, FR-010, SC-001, SC-004. Paths: `tests/unit/web_portal/test_webhook_signature.py` and the record folder. Acceptance: step A (worktree at `origin/main`) passes checks TC-001, TC-002, TC-003, TC-004, TC-007, and TC-010. Step B (follow-up branch) passes checks TC-003, TC-005, TC-006, TC-008, TC-009, TC-012, TC-013, and TC-014. Step A gates T009. Depends on T004 to T006 (step A) and T010 and T011 (step B). Verification command (Tests gate): `python -m pytest tests/unit/web_portal/test_webhook_signature.py`. Status: open.

- [ ] T-PR Commit, push, and open the follow-up pull request. Requirements: FR-009, FR-012, FR-013. Paths: `tests/unit/web_portal/test_webhook_signature.py`. Acceptance: branch `chore/<NEW-ISSUE>-webhook-test-comments` starts from `main`. The commit subject is `chore(tests): add inline comments to the webhook config test`. The commit body and the pull request body contain `Closes #<NEW-ISSUE>` and `Refs #4730`. The pull request body states the internal-only reason for no fragment. The commit adds the Co-authored-by trailer for this session. Hooks run normally (FR-012). Depends on T-LOCAL-GATES. Verification command (Test quality gate): `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. Status: open.

- [ ] T-REMOTE-CI Watch the remote checks. Requirements: SC-001, SC-004. Paths: `.github/workflows/ci.yml`. Acceptance: every required check on the pull request passes, including the root unit shard and the test quality gate. Depends on T-PR. Verification command (Full tests gate, CI equivalent): `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`. Command for the watch: `gh pr checks <number> --watch`, with the number that `gh pr create` returns. Status: open.

- [ ] T-MERGE Merge after authorization. Requirements: SC-001, FR-011. Paths: `tests/unit/web_portal/test_webhook_signature.py` (the follow-up changes this file). Acceptance: the orchestrator authorizes the merge. The executor adds `auto-merge` only after every check passes. The squash merge lands on `main`. The branch is deleted. The main Quality Gates run on the merge commit passes. Depends on T-REMOTE-CI. Verification command (Full tests gate): `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`. Status: open.

## Dependencies & Execution Order

- Tasks T001 to T006 are read-only and safe in parallel. T007 has no prerequisite.
- T008 has no prerequisite. T009 needs step A of T-LOCAL-GATES.
- T010 needs T008. T011 needs T010.
- T-LOCAL-GATES step B needs T010 and T011. T-PR needs T-LOCAL-GATES. T-REMOTE-CI needs T-PR. T-MERGE needs T-REMOTE-CI.

### User Story Mapping

- US1 (run the test in any environment): T001, T002, T003, and T-LOCAL-GATES.
- US2 (confirm that the merged repair changed one line): T004, T005, T006, and T007.
- US3 (read each code line of the touched function): T010, T011, T-PR, T-REMOTE-CI, and T-MERGE.
- US4 (close the issue with the correct evidence): T008 and T009.

## Notes

- Tick a task only after its delivered file or its evidence is verified.
- A task with status `open` or `partial` keeps its box empty until its acceptance statement holds.
