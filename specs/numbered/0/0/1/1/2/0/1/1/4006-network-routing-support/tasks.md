# Tasks: Isolate Network Routing Support Modules

**Input**: `spec.md` and `plan.md` in this record. Supporting files are in `design/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/contracts/module-path-map.md`.

**Verification rule**: Each task names one verification command. The command comes from the local gates table when a gate applies. Otherwise it uses a quickstart check (TC-xx). Process tasks use TC-13 or TC-16.

**Format**: `- [ ] ID [P?] [FR IDs] Description`. `[P]` marks a task that can run in parallel. Status values are open, verified-present, partial, or absent.

## Phase 1: Preparation

- [ ] T001 [FR-021] Create the worktree for `chore/4006-network-routing-support` from `main`. Files: none. Acceptance: the worktree exists, and `main` has no new commit. Verification: TC-16. Status: absent.
- [ ] T002 [FR-021] Add the `in-progress` label to issue #4006 before the branch receives a commit. Files: none. Acceptance: the issue lists `in-progress`, and the existing labels stay. Verification: TC-16. Status: absent.
- [ ] T003 [FR-021] Confirm each publication condition in `design/checklists/publication.md`. Files: none. Acceptance: each of the five conditions records a result. Verification: TC-13. Status: open.

## Phase 2: Move

- [ ] T004 [FR-001, FR-002, FR-005, FR-018] Move the three support modules and add the support initializer. Files: `src/mist/networking/network/support/__init__.py` (add), `src/mist/networking/network/support/_routing_utils_display.py` (move from `_routing_utils_display.py`), `src/mist/networking/network/support/_routing_utils_parsing.py` (move from `_routing_utils_parsing.py`), and `src/mist/networking/network/support/_routing_utils_payload.py` (move from current `main`). Acceptance: old paths do not exist, and the initializer holds a docstring only. Verification: `symbol-diff --base origin/main src\mist\networking\network\support\_routing_utils_display.py` (Symbols gate). Status: partial.

## Phase 3: Active References

- [ ] T005 [P] [FR-006, FR-007] Update imports at `routing_utils.py` lines 22, 26, and 27. Files: `src/mist/networking/network/routing_utils.py`. Acceptance: each import names a support path, and Ruff passes. Verification: `python -m pytest tests/unit/test_routing_utils.py` (Tests gate). Status: partial.
- [ ] T006 [P] [FR-007] Update the payload import at `_routing_utils_routing.py` line 25. Files: `src/mist/networking/network/_routing_utils_routing.py`. Acceptance: the import names the support payload path. Verification: `python -m pytest tests/unit/test_routing_utils.py` (Tests gate). Status: partial.
- [ ] T007 [P] [FR-010] Update the docstring reference at `_utility_commands_selection.py` line 15. Files: `src/mist/resources/device/_utility_commands_selection.py`. Acceptance: the module-level names stay unchanged. Verification: `symbol-diff --base origin/main src\mist\resources\device\_utility_commands_selection.py` (Symbols gate). Status: partial.
- [ ] T008 [P] [FR-008] Update 23 mock and logger targets in the routing unit tests. Files: `tests/unit/test_routing_utils.py`. Acceptance: no target names an old path. Verification: `python -m pytest tests/unit/test_routing_utils.py` (Tests gate). Status: partial.
- [ ] T009 [P] [FR-008] Update the import at line 16 and the logger string at line 82. Files: `tests/unit/test_unparseable_response_guards.py`. Acceptance: both lines name canonical paths. Verification: `python -m pytest tests/unit/test_unparseable_response_guards.py` (Tests gate). Status: partial.
- [ ] T010 [P] [FR-006, FR-011] Add three `MODULE_PATHS` entries after line 43 of the symbol guard. Each added line has an inline comment. Files: `tests/guardrails/test_src_public_symbol_preservation.py`. Acceptance: each moved module maps from its old path to its new path. Verification: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py` (Tests gate). Status: partial.
- [ ] T011 [P] [FR-013, FR-014] Add three `_HISTORICAL_PATH_MOVES` entries after line 37 of the catalog guard. Each added line has an inline comment. Files: `tests/guardrails/test_performance_hook_catalog.py`. Acceptance: hook rows 0281, 0283, and 0284 resolve, and no CSV file changes. Verification: `python -m pytest tests/guardrails/test_performance_hook_catalog.py` (Tests gate). Status: absent.
- [ ] T012 [P] [FR-015] Remove the network object at lines 106 to 110 of the baseline. Change line 177 of the nested-package test to `32 violations, 234 total excess`. Files: `tests/guardrails/nested_package_baseline.json`, `tests/guardrails/test_nested_package_structure.py`. Acceptance: the ratchet test passes and prints the new report. Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py` (Tests gate). Status: absent.

## Phase 4: Guard and Generated Pages

- [ ] T013 [FR-003, FR-004, FR-006, FR-016] Add the structure guard from the candidate, refreshed from current `main`. Split `active_old_path_violations` into helpers of 25 lines or fewer. Exclude the catalog move map from the scan. Add an inline comment to each line. Print examined counts on success. Files: `tests/guardrails/test_network_routing_support_structure.py` (add). Acceptance: the guard passes on the moved tree and fails on a sixth child. Verification: `python -m pytest tests/guardrails/test_network_routing_support_structure.py` (Tests gate). Status: partial.
- [ ] T014 [FR-012] Regenerate the two WebSocket menu pages with the generator. Files: `documentation/menu-api/websocket.md` and `documentation/wiki/Menu-API-Endpoints-Websocket.md`. Acceptance: both pages show canonical links, and a second run changes no file. Verification: `python scripts/generate_menu_wiki.py` (Menu reference gate). Status: partial.
- [ ] T015 [P] [FR-017] Add the changelog fragment. Files: `changelog.d/issue-4006-network-routing-support.md`. Acceptance: one `###` heading and one `Changed` bullet that names issue #4006. Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d\issue-4006-network-routing-support.md` (STE gate). Status: partial.
- [ ] T016 [FR-013] Confirm that no file under `specs/` changes, except the record folder. Files: `specs/` (read only). Acceptance: the diff names no path under `specs/` except the record folder. Verification: TC-09. Status: verified-present.
- [ ] T017 [FR-009] Confirm that each module logger uses `logging.getLogger(__name__)`. Files: `src/mist/networking/network/_routing_utils_display.py`, `src/mist/networking/network/_routing_utils_forwarding.py`, `src/mist/networking/network/_routing_utils_payload.py`, `src/mist/networking/network/_routing_utils_routing.py`, `src/mist/networking/network/_routing_utils_ssr.py`, `src/mist/networking/network/routing_utils.py`, and `src/mist/resources/device/_utility_commands_selection.py`. Acceptance: TC-09 finds no hard-coded logger name in `src`. Verification: TC-09. Status: verified-present.
- [ ] T018 [FR-001, FR-011, FR-018] Confirm that the moved files keep their content and module-level names. Files: `src/mist/networking/network/support/_routing_utils_display.py`, `src/mist/networking/network/support/_routing_utils_parsing.py`, and `src/mist/networking/network/support/_routing_utils_payload.py`. Acceptance: `git hash-object` returns blobs `81619905f517792de24025d65b267bc540c158b8`, `50cd37ff14e40e0b8f1ddda896ac3a9c1ab82f86`, and `38c2458ff14370be660d956ca30c252dc4fd291c`. Verification: `symbol-diff --base origin/main src\mist\networking\network\support\_routing_utils_payload.py` (Symbols gate). Status: partial.

## Phase 5: Final Tasks

- [ ] T-LOCAL-GATES [FR-019, FR-020] Run each applicable gate in the local gates table, the test-quality ratchet, and the STE check. Files: every changed file, including each changed Markdown file. Acceptance: each gate reports success, or the record states why the gate does not apply. Ops portal and ops platform gates do not apply, because this change touches neither. Verification: `python -m ruff check .` (Lint gate). Status: absent.
- [ ] T-PR [FR-021, FR-022] Commit with `refactor(network): isolate network routing support modules`, push `chore/4006-network-routing-support`, and open a pull request. The body contains `Closes #4006`. Files: every changed file and the record folder. Acceptance: the commit subject and the pull request title follow Conventional Commits. Verification: TC-12. Status: absent. Gate: publication conditions met (T003).
- [ ] T-REMOTE-CI [FR-020] Watch the required checks until each one reports a result. Files: none. Acceptance: each required check passes. Verification: `gh pr checks --watch` (copilot-instructions pull request rule). Status: absent.
- [ ] T-MERGE [FR-021] Add the `auto-merge` label after each check passes and the orchestrator authorizes the merge. Files: none. Acceptance: the squash merge lands on `main`, the container build passes on `main`, and its revision label equals the merge commit. Verification: TC-12. Status: absent.

Caution: a squash merge is recoverable through a revert commit. The revert restores the previous paths.
