# Tasks: Windows guardrail test failures

**Input**: Numeric record `specs/numbered/0/0/1/2/4/1/3/2/4917-windows-guardrail-tests/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/data-model.md`. This record has no contracts folder, because no contract applies (`plan.md`, Contracts).

**Tests**: The specification requires tests. Each implementation task names the test case that proves it. Each verification command is one command from the local gates table, or a pytest command for the changed file.

**Process tasks**: T001, T012, T-PR, T-REMOTE-CI, and T-MERGE cover Git and GitHub steps. The local gates table covers code only, so these tasks name a `gh` or `git` command instead.

## Format

`ID [P?] [Requirements] Description. Files: exact paths. Acceptance: the result that proves the task. Verify: one command. Status: open.`

- **[P]**: The task edits a file that no other parallel task edits.
- **Requirements**: The `FR-###` or `SC-###` IDs from `spec.md`.

## Dependencies

- T001 runs first.
- T002 to T007 run in parallel after T001.
- T008 and T009 run in parallel after T001.
- T010 and T011 run after T002 to T009.
- T-LOCAL-GATES runs after T010 and T011.
- T-PR runs after T-LOCAL-GATES.
- T-REMOTE-CI runs after T-PR.
- T-MERGE runs after T-REMOTE-CI and the orchestrator authorizes the merge.
- T012 runs at any time after T001.

## Phase 1: Setup

- T001 [FR-014] Claim issue #4917 with the `in-progress` label. Create the branch `fix/4917-windows-guardrail-tests` from `main` in the worktree `..\MistHelper-4917-windows-guardrails`. Files: none, because the change is Git metadata. Acceptance: the issue shows `in-progress`, and the worktree holds the new branch. Verify: `git -C ..\MistHelper-4917-windows-guardrails rev-parse --abbrev-ref HEAD`. Status: open.

## Phase 2: Test changes

- T002 [P] [FR-002, FR-003, FR-004, FR-011] Skip the five browser execution tests on Windows. Files: `tests/guardrails/e2e_timeout_budget/test_browser_installation.py`, at lines 71, 92, 111, 140, and 156. Acceptance: Windows skips the 11 cases with the reason, and each reason names Ubuntu CI. The YAML-only tests at lines 66, 169, and 179 still run. Each new line has an inline comment. Verify: `python -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py -q -rs`. Status: open.

- T003 [P] [FR-002, FR-003, FR-011] Skip the shell-override cases on Windows. Files: `tests/guardrails/test_snmp_base_oid_defaults.py`, above the `parametrize` of `test_shell_overrides` at line 85. Acceptance: Windows skips the 9 cases. `test_defaults_match` and `test_mismatches_fail` still run. Each new line has an inline comment. Verify: `python -m pytest tests/guardrails/test_snmp_base_oid_defaults.py -q -rs`. Status: open.

- T004 [P] [FR-005, FR-011] Add the environment-folder lookup to `DependencyExport.find_uv`, and add its test. Files: `tests/guardrails/test_dependency_export.py`, at lines 38 to 46, at line 135, and after the test at line 137. Acceptance: with PATH lacking `uv` and the environment folder holding `uv.exe`, the lookup returns that file. With neither lookup finding `uv`, the existing failure message remains. The lookup logs `info` before and `debug` after. Verify: `python -m pytest tests/guardrails/test_dependency_export.py -q`. Status: open.

- T005 [P] [FR-006, FR-011] Skip the symlink case only for WinError 1314. Files: `tests/guardrails/test_spec_route_contract.py`, at line 296, plus the new `logging` import and module logger. Acceptance: a workstation without the privilege skips the symlink case, and the skip reason names the privilege. Any other `OSError` re-raises. The link creation logs `info` before and `debug` after. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs`. Status: open.

- T006 [P] [FR-007, FR-011] Compare the Git root as a `Path` object. Files: `tests/guardrails/local_test_quality_loop/test_scope.py`, at lines 643 to 645. Acceptance: `test_git_ignores_poisoned_locations` passes on Windows. The assertion still fails for a different root. Verify: `python -m pytest tests/guardrails/local_test_quality_loop/test_scope.py -q`. Status: open.

- T007 [P] [FR-008, FR-011] Print POSIX paths in the missing-root message, and match the same paths in the test. Files: `tests/guardrails/test_analytics_package_structure.py`, at lines 75 and 177. Acceptance: `test_missing_root_fails_with_path_and_cause` passes on Windows. The message shows forward-slash paths. Verify: `python -m pytest tests/guardrails/test_analytics_package_structure.py -q`. Status: open.

## Phase 3: Documentation and changelog

- T008 [P] [FR-010] Add the Windows note to the setup guide. Files: `documentation/development-setup.md`, as the subsection `### Guardrail tests on Windows` after line 175 and before `## Work on a change`. Acceptance: the subsection names the Windows skip behavior, the uv lookup, the symlink privilege, and the Ubuntu CI proof. It has one `Caution:` statement. Each instruction has 20 words or fewer. The file holds no semicolon. Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md`. Status: open.

- T009 [P] [FR-012] Add the changelog fragment. Files: `changelog.d/issue-4917-windows-guardrail-tests.md`, a new file. Acceptance: the file holds one `###` heading and one `Fixed` bullet that names issue #4917. The file name matches the issue pattern. Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`. Status: open.

## Phase 4: Verification

- T010 [FR-001, FR-009, SC-001, SC-003] Run the guardrail suite on the Windows workstation. Files: none. Acceptance: the summary reports zero failed tests. Record the passed and skipped counts. `git diff --name-status main -- tests/guardrails` lists only `M` rows. Verify: `python -m pytest -q tests/guardrails`. Depends on T002 to T007. Status: open.

- T011 [FR-011, FR-013] Audit the diff for inline comments and suppressions. Files: the seven changed files and the new fragment. Acceptance: each changed executable line has an inline comment. The diff adds no `# nosec`, `# noqa`, or `# type: ignore`. No line exceeds 120 characters. Verify: `python -m ruff check .`. Depends on T002 to T009. Status: open.

## Phase 5: Follow-up

- T012 [FR-014] File two follow-up issues, one concern for each. Files: none. Acceptance: issue A names the weak `None` assertion in `test_invalid_mirror_configuration_fails_without_a_write`, which passes on Windows because Bash fails and leaves no file. Issue B names the 79-child folder debt of `tests\guardrails` and the Windows CI gap (D-6). Each issue links to #4917. Verify: `gh issue list -R jmorrison-juniper/MistHelper --search "4917 in:body" --json number,title`. Status: open.

## Final tasks

- T-LOCAL-GATES [FR-001, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, SC-004] Run each applicable local gate on the changed files. Files: the seven changed files and the new fragment. Acceptance: each gate below exits with its expected result. The outputs go into the pull request body. Depends on T010 and T011. Verify: `python -m ruff check .`. Status: open.
  - Gate 1: `python -m ruff check .` expects `All checks passed`.
  - Gate 2: `python -m black --check .` expects no file that needs a change.
  - Gate 3: `python -m pytest -q tests/guardrails` expects zero failures.
  - Gate 4: The second `pytest-chunks` command at `.github/copilot-instructions.md` line 88 expects one summary line for each shard and no failure. Run it on the Windows workstation.
  - Gate 5: The test quality procedure at `.github/copilot-instructions.md` line 95 expects `gate: 0 new findings vs baseline`.
  - Gate 6: `bandit -c pyproject.toml -r . -q` expects no finding.
  - Gate 7: `symbol-diff --base origin/main` for each changed Python file expects `no module-level name changed`. One example file is `tests/guardrails/test_dependency_export.py`.
  - Gate 8: `python -m pytest -q tests/guardrails/test_markdown_links.py tests/guardrails/test_container_policy_docs.py` expects no failure.
  - Not applicable: compile, mypy, pylint, vulture, pydocstyle, interrogate, radon, coverage, pip-audit, and the menu reference. Each one reads a path that this change does not touch (`ci.yml` path variables, RC-16, RC-47).

- T-PR [FR-014, SC-005] Commit, push, and open the pull request. Files: the seven changed files and the new fragment. Acceptance: the commit subject is `fix(tests): repair Windows guardrail test failures`. The commit body holds `Closes #4917` and the Co-authored-by trailer. The pull request title matches the commit subject, and its body holds `Closes #4917` and the gate outputs. Warning: a force-push replaces the shared branch history. Push without `--force`, and use `--force-with-lease` only on a branch that no other agent uses. Verify: `gh pr view -R jmorrison-juniper/MistHelper --json title,body --jq "(.body | contains(\"Closes #4917\"))"`. Depends on T-LOCAL-GATES. Status: open.

- T-REMOTE-CI [FR-013, SC-002, SC-005] Watch the checks of the pull request from T-PR. Files: none. Acceptance: each required check reports success. The Ubuntu pytest shard that runs `tests/guardrails` reports one more collected test than `main`, and no Ubuntu test gains a skip. Verify: `gh pr checks -R jmorrison-juniper/MistHelper --watch`. Depends on T-PR. Status: open.


- T-MERGE [FR-014, SC-005] Merge the pull request after the orchestrator authorizes it. Files: none. Acceptance: the squash commit appears on `main`, and the worktree and the branch are removed. Warning: auto-merge squashes the pull request into `main`. Add the `auto-merge` label only after the orchestrator authorizes the merge and every required check reports success. Verify: `gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha`. Depends on T-REMOTE-CI. Status: open.
