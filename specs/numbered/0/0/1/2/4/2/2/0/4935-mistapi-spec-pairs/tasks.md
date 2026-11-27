# Tasks: Check Every Operation Pair in the mistapi Spec Guard

**Input**: Design documents in `specs/numbered/0/0/1/2/4/2/2/0/4935-mistapi-spec-pairs/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/guard-interface.md`, and `design/quickstart.md`.

**Tests**: The specification requires tests (FR-010 and User Stories 1 to 4). Task T007 proves that the wrong-first-pair fixture fails on the pre-change logic.

**Organization**: Tasks are grouped by phase. The `[US]` label maps a task to a user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel, because it edits a different file.
- **[Story]**: The user story that the task serves.
- Each task lists its requirements, exact paths, acceptance statement, verification command, and status.
- Status values are `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Verify and Claim

- [ ] T001 [US1] Confirm the defect on `main`. Status: verified-present.
  - Requirements: FR-001, FR-002.
  - Paths: `tests/guardrails/test_mistapi_spec_modules.py` (lines 67 to 77 and lines 52 to 54).
  - Acceptance: The helper returns one pair for each file. The spec file of issue #4934 holds 25 operation lines from line 461 to line 557.
  - Verification: `python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q`

- [ ] T002 Claim issue #4935 and create the worktree. Status: open.
  - Requirements: None. This task follows the claim rule in `AGENTS.md`. No local gate applies to this process step.
  - Paths: Branch `fix/4935-mistapi-spec-pairs` in worktree `..\MistHelper-fix-4935`.
  - Acceptance: Issue #4935 carries the `in-progress` label. The worktree branches from `main`.
  - Verification: `gh issue view 4935 -R jmorrison-juniper/MistHelper --json labels` and `git worktree list`
  - Caution: OneDrive file locks can block a worktree operation. Pause sync for the worktree folder when a lock error appears.

## Phase 2: Repair Spec File 511 and the Guard

- [ ] T003 [P] [US1] Correct lines 14 to 16 of `specs/511-mist-count-org-client-fingerprints/spec.md`. Status: absent.
  - Requirements: FR-008.
  - Paths: `specs/511-mist-count-org-client-fingerprints/spec.md`.
  - Acceptance: Line 14 begins with the text `- **mistapi SDK module**: ` and then the path `mistapi.api.v1.orgs.insights` in backticks. Line 15 states that the installed SDK defines `countOrgClientFingerprints` in that module. Line 16 is deleted.
  - Verification: `python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -s -k declared_sdk` after T006 reports zero defects for spec file 511.

- [ ] T004 [US1] Rewrite `_source_fields` as a pair parser. Status: absent.
  - Requirements: FR-002, FR-003, FR-013, FR-014.
  - Paths: `tests/guardrails/test_mistapi_spec_modules.py` (lines 67 to 77).
  - Acceptance: The helper returns `list[tuple[str, str | None]]` in file order. A pair without a module carries `None`. A module line without a pending operation line is ignored. The helper logs an `info` line before the read and a `debug` line after it.
  - Verification: `python -m py_compile tests/guardrails/test_mistapi_spec_modules.py`

- [ ] T005 [US1] Update `spec_declarations` to append every pair. Status: absent.
  - Requirements: FR-001, FR-009, FR-013.
  - Paths: `tests/guardrails/test_mistapi_spec_modules.py` (lines 41 to 56).
  - Acceptance: The method appends each pair from `_source_fields`. The `frozen_spec_files` set is unchanged. The debug line reports the pair count after the scan.
  - Verification: `python -m py_compile tests/guardrails/test_mistapi_spec_modules.py`

- [ ] T006 [US1] Add the declared absences, the failure helper, and the summary line. Status: absent.
  - Requirements: FR-004, FR-005, FR-006, FR-007, FR-014, FR-016.
  - Paths: `tests/guardrails/test_mistapi_spec_modules.py` (class `MistapiSpecModuleIndex` and class `TestMistapiSpecModules`).
  - Acceptance: The class attribute `ABSENT_SDK_OPERATIONS` holds the two entries in the contract. The static method `failure_messages` returns the four message templates in the contract. The real test prints the summary line and asserts that the failure list is empty. The guard file gains no module-level name.
  - Verification: `python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -s -k declared_sdk` prints `mistapi spec module guard: examined 489 operation pairs, 0 defects.`

- [ ] T007 [US1] Add the fixture test for the wrong first pair. Status: absent.
  - Requirements: FR-010.
  - Paths: `tests/guardrails/test_mistapi_spec_modules.py`, new test `test_wrong_first_pair_fails_the_guard`.
  - Acceptance: The fixture holds two pairs. The first pair names `mistapi.api.v1.orgs.wrong` for `listWebhookTopics`. The second pair names the correct module for `countOrgClientFingerprints`. The test asserts that the first pair is reported and that the summary line reports two examined pairs. The test uses monkeypatched roots and the fixed SDK map.
  - Proof: Temporarily change `_source_fields` so that it returns only its last pair, as the old helper does. The test must fail. Revert the temporary change before the commit.
  - Verification: `python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -k wrong_first_pair`

- [ ] T008 [US2] Add three edge-case fixture tests. Status: absent.
  - Requirements: FR-003, FR-005, FR-006.
  - Paths: `tests/guardrails/test_mistapi_spec_modules.py`, new tests `test_operation_without_module_line_fails_the_guard`, `test_empty_spec_tree_fails_the_guard`, and `test_declared_absence_fails_when_sdk_defines_operation`.
  - Acceptance: The orphan test names the operation that lacks a module line. The empty-tree test fails with the zero-pair message. The absence test passes when the fixed SDK map lacks the operation and reports one defect when the map defines it.
  - Verification: `python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -k "without_module or empty_spec or declared_absence"`

- [ ] T009 [P] [US3] Add the changelog fragment. Status: absent.
  - Requirements: FR-015.
  - Paths: `changelog.d/issue-4935-mistapi-spec-pairs.md`.
  - Acceptance: The fragment holds one `###` heading and one `Fixed` bullet that names issue #4935. The heading names the change.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`

- [ ] T010 [P] [US3] Check the record `spec.md` for guard prefixes. Status: absent.
  - Requirements: FR-012.
  - Paths: `specs/numbered/0/0/1/2/4/2/2/0/4935-mistapi-spec-pairs/spec.md`.
  - Acceptance: No line of the record `spec.md` begins with the operation prefix or the module prefix.
  - Verification: `Select-String -LiteralPath "specs\numbered\0\0\1\2\4\2\2\0\4935-mistapi-spec-pairs\spec.md" -Pattern '^- \*\*(operationId|mistapi SDK module)\*\*: `'` returns no output. After the record moves, `python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -s -k declared_sdk` still prints 489 examined operation pairs.

## Phase 3: Final Tasks

- [ ] T-LOCAL-GATES Run each applicable local gate. Status: open.
  - Requirements: SC-004.
  - Paths: The changed files listed in the File Change Map of `plan.md`.
  - Acceptance: Each applicable gate reports its expected result. Record each command and its result in the pull request body.
  - Commands and expected results:
    1. Compile: `python -m py_compile tests/guardrails/test_mistapi_spec_modules.py` prints no output.
    2. Lint: `python -m ruff check .` prints `All checks passed`.
    3. Format: `python -m black --check .` reports that no file needs a change.
    4. Tests: `python -m pytest tests/guardrails/test_mistapi_spec_modules.py -q -s` passes and prints `mistapi spec module guard: examined 489 operation pairs, 0 defects.`
    5. Guardrails shard: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` prints one summary line for each shard with zero failures. This shard includes the record placement guards and the markdown link guard.
    6. Test quality preflight: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` passes.
    7. Test quality gate: after the local commit, run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. The output reports `gate: 0 new findings vs baseline`.
    8. Symbols: `symbol-diff --base origin/main tests/guardrails/test_mistapi_spec_modules.py` reports `no module-level name changed` and exits with code 0.
    9. Citations: `check-citations src tests` reports that each citation resolves.
    10. STE: `ste-linter --config .ste-linter.toml --min-score 80` followed by each record Markdown file reports a score of 80 or above for each file.
  - Not applicable, with the reason:
    - Types: `ci.yml` line 93 sets `MYPY_PATHS` without `tests`.
    - Complexity: `ci.yml` line 99 sets `RADON_PATHS` without `tests/guardrails`.
    - Security lint: `pyproject.toml` line 503 lists `tests` in `exclude_dirs`.
    - Code quality, dead code, and docstrings: `ci.yml` lines 78, 101, 104, and 107 exclude `tests`.
    - Coverage and safe sweep: no `src/` file and no product path changes.
    - Menu reference, ops portal, ops platform, and dependency audit: no affected file.

- [ ] T-PR Commit, push, and open the pull request. Status: open.
  - Requirements: FR-011, SC-005.
  - Paths: The four file groups in the File Change Map of `plan.md`.
  - Acceptance: The pull request holds only the four file groups. Its body contains `Closes #4935`, the local gate results, the declared absences, and the changelog decision. Its labels are `bug` and `tests`.
  - Steps:
    1. Run `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName,files` and confirm that no open pull request changes the same files.
    2. Stage each path by name. Do not stage with `git add -A` or `git add .`.
    3. Confirm the staged list with `git diff --cached --name-only`.
    4. Commit with the title `fix(tests): check every mistapi spec operation pair`. The body holds `Closes #4935` and the Co-authored-by trailer that the session policy requires.
    5. Push the branch with `git push -u origin fix/4935-mistapi-spec-pairs`.
  - Warning: a force-push to a shared branch removes commits that other agents need. Do not force-push this branch.

- [ ] T-REMOTE-CI Watch the remote checks. Status: open.
  - Requirements: SC-005.
  - Paths: Not applicable. The checks run on the pull request.
  - Acceptance: Each required check reports success. The guardrails shard, the test quality gate, CodeQL, and the pull request title check pass.
  - Verification: `gh pr checks --watch` run in the worktree, with the pull request number that `gh pr create` prints.

- [ ] T-MERGE Enable auto-merge after authorization. Status: open.
  - Requirements: SC-005.
  - Paths: Not applicable. The label is set on the pull request.
  - Acceptance: The `auto-merge` label is added only after T-REMOTE-CI passes and the orchestrator authorizes the merge.
  - Verification: `gh pr view -R jmorrison-juniper/MistHelper --json labels` run in the worktree, for the pull request number that `gh pr create` prints.

## Dependencies & Execution Order

- T001 and T002 come first. T002 claims the issue before any file change.
- T003 and T009 and T010 are parallel with each other after T002.
- T004 follows T002. T005 follows T004. T006 follows T003 and T005.
- T007 and T008 follow T006.
- T-LOCAL-GATES follows T003, T007, T008, T009, and T010.
- T-PR follows T-LOCAL-GATES. T-REMOTE-CI follows T-PR. T-MERGE follows T-REMOTE-CI.

## Notes

- Each test case must fail on the pre-change logic. Task T007 gives the proof for the wrong-first-pair case.
- The record `spec.md` must never begin a line with a guard prefix, because the guard reads every `spec.md` file.
- The Out of Scope items in `spec.md` need separate issues. Do not add them to this change.
