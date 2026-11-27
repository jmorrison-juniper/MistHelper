# Tasks: Windows Bash Guardrail Skips

**Input**: Record in `specs/numbered/0/0/1/2/4/0/0/2/4877-windows-bash-guardrails/`. The branch name is `fix/4877-windows-bash-guardrails`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/contracts/skip-report.md`.

**Status values**: open, verified-present, partial, or absent.

## Format

- `[P]` marks a task that can run in parallel with other `[P]` tasks.
- `[US1]`, `[US2]`, and `[US3]` map a task to a user story in `spec.md`.
- Tick a task only after you verify its delivered file.

## Phase 1: Baseline Verification

- [x] T001 [P] [US1] Verify the shell-call sites on `main`. Covers FR-001 and FR-007.
  - Paths: `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` and `tests/guardrails/test_snmp_base_oid_defaults.py`.
  - Acceptance: Blob SHAs match `main` and commit `23379f0e0`. Shell calls exist at lines 63 and 95. (delivered: verified in `design/research.md`)
  - Verification: `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object -- tests/guardrails/test_snmp_base_oid_defaults.py` prints `c04297ce81c9c9f005a54fa655354c064138a3b9`. Local gate: `python -m pytest --collect-only -q tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_snmp_base_oid_defaults.py` lists 31 cases.
  - Status: verified-present (checks RC-02, RC-15, RC-55, and RC-56).

## Phase 2: Implementation

- [ ] T002 [P] [US1] Add the POSIX shell mark to the browser module. Covers FR-001, FR-002, FR-003, FR-005, and FR-010.
  - Path: `tests/guardrails/e2e_timeout_budget/test_browser_installation.py`.
  - Acceptance: The constant follows `MIRRORS` (line 14). The mark decorates the functions at lines 71, 92, 111, 140, and 156. A Windows run shows 8 passed and 11 skipped. An Ubuntu run shows 19 passed.
  - Verification: `python -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py -rs -q` on a Windows host.
  - Status: absent (check RC-13).

- [ ] T003 [P] [US1] Add the POSIX shell mark to the SNMP module. Covers FR-001, FR-002, FR-003, FR-005, and FR-010.
  - Path: `tests/guardrails/test_snmp_base_oid_defaults.py`.
  - Acceptance: `import sys` follows line 12. The mark decorates `test_shell_overrides` (line 85). A Windows run shows 3 passed and 9 skipped. An Ubuntu run shows 12 passed.
  - Verification: `python -m pytest tests/guardrails/test_snmp_base_oid_defaults.py -rs -q` on a Windows host.
  - Status: absent (check RC-18).

- [ ] T004 [P] [US3] Document the Windows result. Covers FR-008.
  - Path: `documentation/development-setup.md`.
  - Acceptance: The section from `plan.md` Documentation Text appears before line 339. The file scores 80 or above in `ste-linter`. The container policy guard passes.
  - Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`, then `python -m pytest tests/guardrails/test_container_policy_docs.py -q`.
  - Status: absent (checks RC-35 and RC-36 show the insertion point).

- [ ] T005 [P] [US3] Add the changelog fragment. Covers FR-009.
  - Path: `changelog.d/issue-4877-windows-bash-guardrails.md`.
  - Acceptance: One `###` heading. One bullet that begins `- **Fixed**:` and names issue #4877. The name matches check RC-42.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`.
  - Status: absent.

## Phase 3: Gates and Delivery

- [ ] T-LOCAL-GATES Run each applicable local gate on a Windows host. Covers FR-001 to FR-006 and FR-010.
  - Depends on: T002, T003, T004, and T005.
  - Paths: `tests/guardrails/e2e_timeout_budget/test_browser_installation.py`, `tests/guardrails/test_snmp_base_oid_defaults.py`, `documentation/development-setup.md`, and `changelog.d/issue-4877-windows-bash-guardrails.md`.
  - Acceptance: Each command below passes.
    1. `python -m ruff check .` prints `All checks passed`.
    2. `python -m black --check .` reports that no file needs a change.
    3. The two-module pytest command prints 11 passed and 20 skipped, with each reason shown.
    4. `python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_container_policy_docs.py -q` passes.
    5. `symbol-diff --base origin/main` on each changed Python module prints `no module-level name changed`.
    6. `bandit -c pyproject.toml -r . -q` reports no finding.
    7. The test quality gate prints `gate: 0 new findings vs baseline`, as `.github/copilot-instructions.md` describes.
    8. Mypy, Pydocstyle, Interrogate, and Vulture do not apply to tests (check RC-27).
    9. Every failure in `python -m pytest tests/guardrails` belongs to issue #4878 or to another named open issue.
  - Verification: Run the commands above in order.
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request. Covers FR-007 and FR-011.
  - Depends on: T-LOCAL-GATES.
  - Acceptance:
    1. The commit title is `fix(tests): skip bash-dependent guardrails on Windows`. The body contains `Closes #4877` and the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
    2. The commit adds only these paths: the two modules, `documentation/development-setup.md`, `changelog.d/issue-4877-windows-bash-guardrails.md`, and `specs/numbered/0/0/1/2/4/0/0/2/4877-windows-bash-guardrails/`. Do not use `git add -A`.
    3. The branch is `fix/4877-windows-bash-guardrails`, and it starts from `main`.
    4. The pull request body lists each local gate result and two follow-up items. The follow-ups name the None-case assertion and the repository-wide mark guard.
    5. The pull request carries the `tests` scope label, and it keeps the `bug` and `test` labels.
  - Verification: `gh pr view` on the new pull request shows a body with `Closes #4877` and both follow-up items. Local gate: rerun `python -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_snmp_base_oid_defaults.py -rs -q` after the rebase, as constitution Principle IV step 5 requires.
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote CI run. Covers FR-004 and SC-002.
  - Depends on: T-PR.
  - Paths: `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` and `tests/guardrails/test_snmp_base_oid_defaults.py`.
  - Acceptance:
    1. Every required check reports success.
    2. The `pytest_coverage_shards` job log shows both modules with 31 passed.
    3. The job log has no `SKIPPED` line for either module.
  - Verification: Run `gh pr checks --watch` on the new pull request. Then search the job log for the module names and the word `SKIPPED`. Local gate: before the push, run `python -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_snmp_base_oid_defaults.py -q` on an Ubuntu host to predict the remote result.
  - Status: open.

- [ ] T-MERGE Merge after authorization. Covers FR-007 and constitution Principle IV steps 9 to 12.
  - Depends on: T-REMOTE-CI and the orchestrator authorization.
  - Paths: none change in this task. The record folder `specs/numbered/0/0/1/2/4/0/0/2/4877-windows-bash-guardrails/` merges with the pull request.
  - Acceptance:
    1. The `auto-merge` label is added after each check reports green. This change touches no destructive operation, so the label is allowed.
    2. The squash merge makes one commit on `main`.
    3. `container-build.yml` shows no run for the merge commit, because check RC-28 excludes this change. The closing comment records this evidence.
    4. The branch and the worktree are removed after the merge.
  - Verification: `gh pr view` shows the state MERGED. `gh run list --workflow container-build.yml --branch main --limit 1`   shows no run for the merge commit. Local gate: rerun `python -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_snmp_base_oid_defaults.py -q` on the merge candidate before the authorization request.
  - Status: open.

Warning: A commit pushed after a squash merge becomes an orphan that no pull request holds. Open a new issue, and branch again from `main`.

## Dependencies and Execution Order

- T001 is complete.
- T002, T003, T004, and T005 run in parallel.
- T-LOCAL-GATES waits for T002 to T005.
- T-PR waits for T-LOCAL-GATES.
- T-REMOTE-CI waits for T-PR.
- T-MERGE waits for T-REMOTE-CI and the orchestrator authorization.
