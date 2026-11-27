# Tasks: Isolate Marvis Alarm Handling Modules

**Input**: Design documents in `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/quickstart.md`, and `design/checklists/`

**Tests**: The focused selection holds 223 test functions. Each change runs the guard or the focused test that covers it. Each task names one verification command from the local gates table in `design/quickstart.md`.

**Ownership**: The shared checkout holds five unrelated modified files. Do not stage, reset, or clean those files. Work in a new worktree.

Warning: `git clean` and `git reset --hard` discard the five unrelated edits in the shared checkout. Run neither command there.

**Environment**: Create the worktree environment with the steps in `design/quickstart.md`.

## Format

- `[P]` means the task edits a file that no other task of its phase edits.
- Each task lists its requirement IDs, its exact repository paths, and its acceptance statement.
- Status values: `open` means no work exists. `partial` means the content exists on an archive branch and not on main. `absent` means no content exists on main or on an archive branch.
- Final tasks verify with GitHub checks, because they run after the local gates.

## Phase 1: Preflight

- [ ] T001 Create a worktree and branch from current main. Requirement: FR-011. Files: new worktree `..\MistHelper-4008` on branch `chore/4008-marvis-alarm-handling`. Acceptance: `origin/main` is an ancestor of `HEAD`, and the worktree holds no staged change. Verify: `python -m pytest tests/guardrails`. Status: open.
- [ ] T002 Confirm the held symbol guard file is free. Requirement: FR-011. Files: `tests/guardrails/test_src_public_symbol_preservation.py`. Acceptance: no open pull request changes this file, or the coordinator posts a file-scoped handoff on issue #4008. Verify: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`. Status: open.

## Phase 2: Move

- [ ] T003 [P] Add the package marker. Requirements: FR-001, FR-002. Files: `src/mist/intelligence/marvis/actions/alarm_handling/__init__.py`. Acceptance: the file holds one docstring line and re-exports no name. Verify: `python -c "import src.mist.intelligence.marvis.actions.alarm_handling"`. Status: partial.
- [ ] T004 Move the two modules with `git mv`. Requirements: FR-001, FR-004. Files: `src/mist/intelligence/marvis/actions/acknowledgement.py` to `src/mist/intelligence/marvis/actions/alarm_handling/acknowledgement.py`, and `src/mist/intelligence/marvis/actions/alarms.py` to `src/mist/intelligence/marvis/actions/alarm_handling/alarms.py`. Acceptance: the blob SHA of `acknowledgement.py` stays `765c01070ebdf0d79580af464441f9f44e3c34fb`, the blob SHA of `alarms.py` stays `c61405c839212c6c64c5cbd8c07cd2e582cd4287`, and both old paths no longer exist. Verify: `python -c "import src.mist.intelligence.marvis.actions.alarm_handling.alarms"`, and then `python -c "import src.mist.intelligence.marvis.actions.alarms"` fails with `ModuleNotFoundError`. Status: partial.

## Phase 3: Canonical references

- [ ] T005 [P] Update the operation imports. Requirement: FR-003. Files: `src/mist/intelligence/marvis/actions/operation.py` (lines 51 and 57). Acceptance: both import statements name `alarm_handling`, and no name changes. Verify: `symbol-diff --base origin/main src/mist/intelligence/marvis/actions/operation.py`. Status: partial.
- [ ] T006 [P] Update the actions package docstring. Requirement: FR-003. Files: `src/mist/intelligence/marvis/actions/__init__.py` (lines 4 to 7). Acceptance: the docstring names `alarm_handling` for the alarm join and the acknowledgement. Verify: `symbol-diff --base origin/main src/mist/intelligence/marvis/actions/__init__.py`. Status: partial.
- [ ] T007 [P] Update the test imports and patch targets. Requirements: FR-003, FR-005. Files: `tests/unit/marvis/actions/test_acknowledgement.py` (lines 7, 30, 43, and 58), `tests/unit/marvis/actions/test_alarms.py` (lines 18 and 19), `tests/unit/marvis/actions/test_operation.py` (line 20), `tests/unit/marvis/actions/test_model.py` (line 15), and `tests/unit/marvis/actions/test_properties.py` (line 25). Acceptance: no test names an old path, and the logger check reads `alarms_module.__name__`. Verify: `python -m pytest tests/unit/marvis/actions`. Status: partial.
- [ ] T008 [P] Update the active code location row. Requirement: FR-006. Files: `documentation/marvis-actions-api-endpoints.md` (line 1329). Acceptance: the row names `src/mist/intelligence/marvis/actions/alarm_handling/alarms.py`. Verify: `git grep -n "marvis[./]actions[./]\(alarms\|acknowledgement\)" -- . ":(exclude)specs" ":(exclude)CHANGELOG.md"` returns no line. Status: partial.

## Phase 4: Guards

- [ ] T009 [P] Add the structure test. Requirements: FR-002, FR-010. Files: `tests/guardrails/test_src_domain_structure.py` (insert before `test_tracked_text_uses_only_canonical_source_paths`, line 120). Acceptance: `test_marvis_actions_has_alarm_handling_package` passes and checks the exact child sets of both packages. Verify: `python -m pytest tests/guardrails/test_src_domain_structure.py`. Status: partial.
- [ ] T010 Add the two symbol mappings after T002 passes. Requirements: FR-004, FR-010, FR-011. Files: `tests/guardrails/test_src_public_symbol_preservation.py` (`MODULE_PATHS`, line 36). Acceptance: `mist/intelligence/marvis/actions/acknowledgement.py` and `mist/intelligence/marvis/actions/alarms.py` map to their `alarm_handling` paths, and no other entry changes. Verify: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`. Status: partial.
- [ ] T011 [P] Update the nested baseline and the expected message. Requirements: FR-002, FR-008, FR-010. Files: `tests/guardrails/nested_package_baseline.json` (delete lines 91 to 95), and `tests/guardrails/test_nested_package_structure.py` (line 177). Acceptance: the expected message reads `32 violations, 235 total excess`, and no baseline entry is stale. Stage the moved files by explicit path before the run, because the ratchet reads tracked files. Verify: `python -m pytest tests/guardrails/test_nested_package_structure.py`. Status: partial.

## Phase 5: Generated and release text

- [ ] T012 [P] Check the menu references. Requirement: FR-007. Files: `documentation/menu-api/interactive-safe.md`, `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md`, and the output of `scripts/menu_api_map`. Acceptance: the generator changes no file, or each changed generated file holds only the regenerated lines. Verify: `python -m scripts.menu_api_map --check`. Status: open.
- [ ] T013 [P] Add the changelog fragment. Requirement: FR-009. Files: `changelog.d/issue-4008-marvis-alarm-handling.md`. Acceptance: one `###` heading names the refactor, and one `- **Changed**:` bullet names issue #4008. The archive copy uses a bare heading and fails this shape, so it is not reused. Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Status: partial.

## Final tasks

- [ ] T-LOCAL-GATES Run every applicable local gate. Requirement: FR-012. Files: the changed files of `plan.md`, by explicit path. Acceptance: each applicable row of the local gates table reports its expected result, and each non-applicable row names its reason. Verify: the gate commands in `design/quickstart.md`. Status: open.
- [ ] T-PR Commit, rebase, push, and open the pull request. Requirements: FR-005, FR-011, FR-012, FR-013. Files: the changed files, by explicit path. Acceptance: the commit subject is `refactor(marvis): isolate alarm handling modules`. The body holds `Closes #4008`, the gate results, the logger change, the touched-debt table, and the hold status. The remediation child issue under #3824 exists, and the body names it. Verify: `python -m pytest tests/guardrails`. Status: open.
- [ ] T-REMOTE-CI Watch CI and CodeQL. Requirement: FR-012. Files: none. Acceptance: every required check reports success on the pull request head. Verify: `gh pr checks --watch`, a GitHub check, because CI runs after the local gates. Status: open.
- [ ] T-MERGE Merge after the orchestrator authorizes it. Requirements: FR-011, FR-012. Files: none. Acceptance: the orchestrator authorizes the merge, the `auto-merge` label is added, and the squash merge completes. The `container-build.yml` run succeeds on the merged revision, its image revision label equals the merged commit, and the orchestrator deploys the approved image and records the health check. Verify: `gh run list --workflow container-build.yml --branch main --limit 1`, a GitHub check. Status: open.

Warning: a commit pushed after the squash merge leaves its pull request orphaned. File a new issue and branch again from main.

## Dependencies

- T001 runs first. T002 runs before T010.
- T003 and T004 follow T001. T004 follows T003.
- T005, T006, T007, T008, T009, and T011 follow T004.
- T010 follows T002 and T004.
- T012 follows T005 and T006. T013 has no prerequisite.
- T-LOCAL-GATES follows T001 through T013. T-PR follows T-LOCAL-GATES. T-REMOTE-CI follows T-PR. T-MERGE follows T-REMOTE-CI.
