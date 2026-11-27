# Tasks: Stop VPN Creation When the VPN Inventory Is Unverified

**Input**: Record in `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`.

**Tests**: Required by FR-018 and SC-005. Task T001 writes the test cases first. The failure-class cases must fail on the unchanged code.

**Environment**: Run commands from the root of the worktree with its `.venv`. Do not run `tests/integration/test_wan_vpn_builder_live.py`.

## Format

Each task names its requirement IDs, its exact paths, an acceptance statement, one verification command, and a status. The status is `open`, `verified-present`, `partial`, or `absent`. The status `absent` means that the deliverable is not on `main`. The status `open` means that the task has not started.

## Phase 1: Tests First

- [ ] T001 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-017] Replace the class `TestFetchExistingVpns` in `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` (lines 319 to 333). Write 15 test functions with 25 cases. Use native responses that wrap `requests.Response` in mistapi `APIResponse`, as `TestFetchProfilesHttpRefusal` does. Acceptance: each failure class has a case. Each failure-class case fails on the unchanged code. The verified empty case passes on the unchanged code. Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`. Status: absent.

## Phase 2: Reader and Builder

- [ ] T002 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-016, FR-017] Create `src/operations/wan/vpn_inventory.py`. Write the class `VpnInventoryReader` with the five methods in `plan.md`. Acceptance: each executable line has an inline comment. Each function has 25 lines or fewer. The module uses no `assert`. Each log line uses ASCII and `%s` values. The class has no field that stores a token. Depends on T001. Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`. Status: absent.

- [ ] T003 [FR-012, FR-013, FR-014, FR-015, FR-016] Modify `src/operations/wan/wan_vpn_builder.py`. Add the import of `VpnInventoryReader` after line 22. Change `_prompt_name_after_display` (lines 132 to 140) to stop on None and to strip names. Change `_fetch_existing_vpns` (lines 390 to 406) to return None when the reader returns None. Acceptance: the message text at line 404 stays unchanged. `CONFIRM_TOKEN` at line 41 stays unchanged. The method count of `WanVpnBuilder` stays unchanged. Depends on T002. Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`. Status: absent.

## Phase 3: Release Note and Record

- [ ] T004 [P] [FR-018] Add `changelog.d/issue-4792-wan-vpn-list-failure.md`. Write one `###` heading and one `- **Fixed**:` bullet that names issue #4792. Acceptance: the file names no PR number. Verify: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4792-wan-vpn-list-failure.md`. Status: absent.

- [ ] T005 [FR-018] Regenerate the menu API pages after T003. Acceptance: the first generator run changes only the pages that name the reader. The second run changes no file. Verify: `python -m scripts.menu_api_map --check`. Depends on T003. Status: absent.

- [ ] T006 [P] [FR-018] Copy the record from the draft folder to `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/`. Acceptance: the record holds the spec, the plan, the tasks, the analysis, the design folder, the contracts, and the checklists. Verify: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/spec.md`. Repeat the command for each Markdown file of the record. Status: absent.

## Phase 4: Local Gates and Delivery

- [ ] T-LOCAL-GATES [FR-001 to FR-018] Run each local gate that applies to the changed files. Acceptance: each gate reports its expected result. Record each result in the pull request body. Depends on T001 to T006. The gates are listed below. Status: open.

  1. Compile: `python -m py_compile src/operations/wan/vpn_inventory.py src/operations/wan/wan_vpn_builder.py`. Expected: no output.
  2. Lint: `python -m ruff check src/operations/wan/vpn_inventory.py src/operations/wan/wan_vpn_builder.py tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`. Expected: `All checks passed`.
  3. Format: `python -m black --check src/operations/wan/vpn_inventory.py src/operations/wan/wan_vpn_builder.py tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`. Expected: no file needs a change.
  4. Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. The scope comes from `MYPY_PATHS` in `.github/workflows/ci.yml` line 93. Expected: `Success`.
  5. Tests: `python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py`. Expected: all 25 cases pass.
  6. Guardrails for the record and the note: `python -m pytest tests/guardrails/test_process_folder_structure.py tests/guardrails/test_changelog_fragment_policy.py`. Expected: all tests pass.
  7. Test quality preflight: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`. Expected: all tests pass.
  8. Test quality gate: fetch with `git fetch --no-tags origin +refs/heads/main:refs/remotes/origin/main`, then run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. Expected: `gate: 0 new findings vs baseline`.
  9. Complexity: `radon cc src/operations/wan -j | complexity-gate --max 10`. Expected: no block above cyclomatic complexity 10.
  10. Security lint: `bandit -c pyproject.toml -r src/operations/wan -q`. Expected: no finding at any severity.
  11. Code quality: `pylint src/ --fail-under=9.5`. Expected: score 9.5 or above.
  12. Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`. The scope comes from `VULTURE_PATHS` in `.github/workflows/ci.yml` line 101. Expected: no finding.
  13. Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`. Expected: no violation, and coverage at 90 percent or above.
  14. Menu reference: `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`, then `python -m scripts.menu_api_map --check`. Expected: the second run changes no file.
  15. Symbols: `symbol-diff --base origin/main src/operations/wan/wan_vpn_builder.py`. Expected: no module-level name removed. The added import appears in the output. The pull request explains that reason.
  16. STE: `ste-linter --config .ste-linter.toml --min-score 80` followed by each changed Markdown file. Expected: each file scores 80 or above.
  17. Safe sweep: `python MistHelper.py --test`, with `MIST_APITOKEN` and `MIST_API_TOKEN` unset. Expected: each safe operation completes. The Mist API checks skip with a credential reason.
  18. Inline comment audit: read each executable line of the new module and each changed line of the builder. Expected: each line has an inline comment that gives its purpose.
  19. Not applicable: `pip-audit -r requirements.txt`, because no dependency changes. Not applicable: the ops portal and the ops platform gates, because those folders do not change.
  20. Deferred to CI: the two `pytest-chunks` shards and the coverage run, because `tests/integration` holds the live test (see decision D-18). Expected: CI reports each shard as passing.

- [ ] T-PR [FR-018] Commit the change with the subject `fix(wan-vpn): stop VPN creation when inventory is unverified`. Push the branch `fix/4792-wan-vpn-list-failure` from a worktree that starts from `main`. Open a pull request. Acceptance: the body contains `Closes #4792`. The pull request carries the `needs-human-review` label. The pull request does not carry the `auto-merge` label. The body lists each gate result and states that the change supersedes the diverged branch of commit `8d8f1a63c`. Depends on T-LOCAL-GATES. Verify: `gh pr view <number> --json title,labels,body`. Status: open.

- [ ] T-HEADER-CHECK [FR-005, FR-006] Before T-MERGE, the owner runs one read-only `listOrgVpns` request on one organization and records the result. The owner records only the names of the three pagination headers and whether each header is present. The owner does not record a token. Acceptance: the pull request body holds the header result. If a header is absent on a complete page, the owner stops the merge and reverts the change. Depends on T-PR. This task requires the owner. The agent cannot run it. Status: open.

- [ ] T-REMOTE-CI [FR-018] After T-PR, watch the checks on the pull request. Acceptance: each required check reports success on the head commit of the pull request. Depends on T-PR. Verify: `gh pr checks <number> --watch`. Status: open.

- [ ] T-MERGE [FR-018] Merge the pull request only after T-REMOTE-CI passes, T-HEADER-CHECK completes, and the orchestrator authorizes the merge. A human owner reviews the change before the merge. This change does not enable auto-merge, as decision D-13 records. Acceptance: the labels show `needs-human-review` and no `auto-merge`. Depends on T-REMOTE-CI and T-HEADER-CHECK. Verify: `gh pr view <number> --json labels --jq ".labels[].name"`. Status: open.

## Dependencies and Execution Order

- T001 comes first. T002 depends on T001. T003 depends on T002.
- T004 and T006 can run in parallel with each other and with T002 and T003, because they edit different files.
- T005 depends on T003, because the menu call path changes in T003.
- T-LOCAL-GATES depends on T001 to T006.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI and T-HEADER-CHECK depend on T-PR.
- T-MERGE depends on T-REMOTE-CI and T-HEADER-CHECK.
