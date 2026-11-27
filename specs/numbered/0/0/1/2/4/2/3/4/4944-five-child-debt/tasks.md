# Tasks: Remediate the five-child debt of three folders

**Input**: `plan.md` (change map and PR sequence), `spec.md` (FR and SC identifiers), `design/research.md` (decisions D-1 to D-14 and remote rows).

**Order**: The tasks follow the PR sequence in `plan.md`. Each group task starts after the previous PR merges on `main`. Only T001 runs in parallel, because it reads and writes no file.

**Format**: `- [ ] ID [P?] [FR or SC IDs] Title`. Each task names its paths, its acceptance statement, its verification command, and its status (open, verified-present, partial, or absent).

## Phase 1: Baseline

- [x] T001 [P] [FR-004] Confirm the baseline on main.
  - Paths: none.
  - Acceptance: At commit f03c6c9b, `scripts/` holds 53 tracked children, `tests/unit/scripts/` holds 10, and `documentation/noc-runbooks/` holds 17.
  - Verify: `quickstart.md` Scenario 1 and Scenario 2.
  - Status: verified-present. This record ran both counts on 2026-11-26. The remote and local counts match.

## Phase 2: Guard (PR-1)

- [ ] T002 [FR-001, FR-002, FR-003, FR-004] Add the child-count guard.
  - Paths: `tests/guardrails/test_process_folder_structure.py`.
  - Acceptance: The guard prints one ASCII line for each debt folder. The growth case fails. `DEBT_FOLDER_BASELINE` holds 53, 10, and 17. Counts come from `git ls-files`, as decision D-4 states.
  - Verify: `python -m pytest tests/guardrails/test_process_folder_structure.py -q -s`
  - Status: open.

## Phase 3: Runbooks by platform (PR-2)

- [ ] T003 [FR-007, FR-008, FR-010, FR-012] Group the runbooks by platform.
  - Paths: the 16 moves in `plan.md` PR-2, `documentation/noc-runbooks/SSR_ALARM_INDEX.md`, `scripts/netcool_runbook_smoke/__main__.py` line 230, `scripts/verify_ssr_commands.py` line 67, `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py` line 27.
  - Acceptance: The top level of `documentation/noc-runbooks/` holds five children. Every relative link resolves. Baseline for `documentation/noc-runbooks/` is 5.
  - Verify: `python -m pytest tests/guardrails/test_markdown_links.py tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py -q`
  - Status: open.

## Phase 4: `verification_tools/` (PR-3)

- [ ] T004 [FR-005, FR-006, FR-008, FR-009, FR-010] Move the verification group.
  - Paths: the nine moves in `plan.md` PR-3, the edits in its table, and `tests/unit/scripts/test_script_imports.py` (create the path-depth test with 6 cases).
  - Acceptance: `scripts/` baseline is 47. `tests/unit/scripts/` baseline is 9. Each moved verification module passes its root-depth case.
  - Verify: `python -m pytest tests/unit/scripts tests/guardrails/test_wave1_gate_runner.py tests/unit/config/foundation/support/benchmarks tests/test_performance_memory.py tests/unit/utils/test_tls_policy.py -q`
  - Status: open.

## Phase 5: `repository_tools/` (PR-4)

- [ ] T005 [FR-005, FR-006, FR-008, FR-009, FR-010] Move the repository group.
  - Paths: the 14 moves in `plan.md` PR-4, the edits in its table, and `tests/unit/scripts/test_script_imports.py` (add 2 cases).
  - Acceptance: `scripts/` baseline is 40. `tests/unit/scripts/` baseline is 4. The `bootstrap_worktree.py` import and every patch target name the new module path.
  - Verify: `python -m pytest tests/unit/scripts tests/guardrails/test_pr_title_workflow.py tests/guardrails/test_rrm_dry_run_read_sites.py tests/contract/test_release_body_workflow.py tests/contract/packaging/test_bootstrap_compose_provider.py tests/unit/config/standalone/foundation/runtime/release/test_release_body.py tests/unit/config/foundation/runtime/startup/bootstrap -q`
  - Status: open.

## Phase 6: `reference_tools/` (PR-5)

- [ ] T006 [FR-005, FR-006, FR-008, FR-009, FR-010, FR-011] Move the reference group and regenerate its pages.
  - Paths: the five moves in `plan.md` PR-5, the edits in its table, the regenerated pages in `plan.md` "Regenerated outputs", and `tests/unit/scripts/test_script_imports.py` (add 4 cases).
  - Acceptance: `scripts/` baseline is 37. `tests/unit/scripts/` baseline is 4. Running the generator twice changes no file. The `--check` command exits 0.
  - Verify: `python scripts/reference_tools/generate_menu_wiki.py`, then `python -m scripts.reference_tools.menu_api_map --check`, then `python -m pytest tests/unit/scripts tests/guardrails/test_move_module_guidance.py tests/guardrails/test_portal_operation_coverage.py tests/guardrails/test_markdown_links.py -q`
  - Status: open.

## Phase 7: `one_time_scans/` (PR-6)

- [ ] T007 [FR-005, FR-008, FR-009, FR-010, FR-012] Move the one-time scans and set the final baselines.
  - Paths: the 33 moves in `plan.md` PR-6, the edits in its table, `tests/unit/scripts/test_script_imports.py` (add 12 cases), `tests/guardrails/test_process_folder_structure.py` (baselines 5, 4, and 5).
  - Acceptance: `scripts/` holds 5 tracked children. The path-depth test holds 24 cases. The MYPY paths in `ci.yml` name the new paths and pass the mypy gate.
  - Verify: `python -m pytest tests/unit/scripts tests/guardrails/test_mypy_paths_openai_scripts.py tests/guardrails/test_issue_2753_csv_device_id_scan.py tests/test_pdf_to_markdown.py tests/unit/utils/test_tls_policy.py -q`, then `python -m mypy $MYPY_PATHS --config-file pyproject.toml` with `$MYPY_PATHS` read from `.github/workflows/ci.yml`.
  - Status: open.

## Phase 8: Final state

- [ ] T008 [FR-001, FR-012, SC-001, SC-002] Verify the final state on main after PR-6 merges.
  - Paths: none changed.
  - Acceptance: `scripts/` holds 5 tracked children, `tests/unit/scripts/` holds 4, and `documentation/noc-runbooks/` holds 5. The old-path sweep prints no line. The guard passes on main.
  - Verify: `quickstart.md` Scenario 2, Scenario 3, and Scenario 5.
  - Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run the applicable local gates for each pull request.
  - Paths: the changed files of the pull request. Stage them by explicit path.
  - Acceptance: Every applicable gate exits 0. The pull request body lists each gate with its result. Each gate that does not apply names its reason.
  - Verify, per pull request:
    - Compile: `python -m py_compile <each changed .py file>`
    - Lint: `python -m ruff check .` prints `All checks passed`
    - Format: `python -m black --check .`
    - Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`
    - Tests: the command in the group task
    - Test quality: the ratchet procedure in `.github/copilot-instructions.md`
    - Complexity: `radon cc scripts -j | complexity-gate --max 10`
    - Security lint: `bandit -c pyproject.toml -r scripts -q`
    - Guardrails: `python -m pytest tests/guardrails -q`
    - Old paths: the sweep in `quickstart.md` Scenario 5 for the paths the pull request moves
    - Symbols: `symbol-diff --base origin/main <file>` for each moved Python file. Research unverified item U-5 applies.
    - STE: `ste-linter --config .ste-linter.toml --min-score 80 .github/copilot-instructions.md README.md AGENTS.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`, in PR-4, PR-5, and PR-6
    - Menu reference: `python -m scripts.reference_tools.menu_api_map --check`, in PR-5
    - Pylint, vulture, pydocstyle, and interrogate, in PR-6 only, because PR-6 edits `src/` docstrings
    - Full shards: the two `pytest-chunks` commands in `.github/copilot-instructions.md`, once for each pull request that changes test files
    - Not applicable: safe sweep (no `MistHelper.py` or operation change), dependency audit (no requirements change), and ops portal and ops platform (no change there). CI runs the coverage shards.
  - Status: open.

- [ ] T-PR Open the pull request for each group.
  - Paths: the changed files of the group, and `changelog.d/pr-<number>.md` after the pull request exists.
  - Acceptance: The branch uses the name `chore/4944-<slug>` and starts from `main`. The commit uses a Conventional Commit subject and the `Co-authored-by` trailer. The title passes `pull-request-title.yml`. The body uses `Refs #4944` in PR-1 to PR-5 and `Closes #4944` in PR-6. The fragment has one `### Changed` heading and one bullet that names issue 4944.
  - Titles: PR-1 `chore(tests): add a child-count guard for five-child debt folders`. PR-2 `refactor(docs): group noc runbooks by platform`. PR-3 `refactor(scripts): move verification tools into verification_tools`. PR-4 `refactor(scripts): move repository tools into repository_tools`. PR-5 `refactor(scripts): move reference tools into reference_tools`. PR-6 `refactor(scripts): move one-time scans into one_time_scans`.
  - Verify: `gh pr view <number> --json title,body` and `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks for each pull request.
  - Paths: none.
  - Acceptance: Each required check reports success. For a failed check, the cause is repaired in the same branch, and the branch is pushed once more.
  - Verify: `gh pr checks <number> --watch`, then `gh pr checks <number>`.
  - Status: open.

- [ ] T-MERGE Merge each pull request after its checks pass.
  - Paths: none.
  - Acceptance: The `auto-merge` label is added only after every check shows green and the orchestrator authorizes the merge. The pull request merges as one squash commit, and its branch and worktree are removed. After PR-6, the `container-build.yml` run on main reports the merged commit SHA in its revision label.
  - Verify: `gh pr view <number> --json state,mergedAt`
  - Status: open.
