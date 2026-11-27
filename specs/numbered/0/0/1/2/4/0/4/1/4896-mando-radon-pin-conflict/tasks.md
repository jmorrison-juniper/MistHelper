# Tasks: Mando pin conflict in the pip-audit gate

**Input**: Design documents in `specs/numbered/0/0/1/2/4/0/4/1/4896-mando-radon-pin-conflict/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/dependency-pin-rule.md`, and `design/quickstart.md`.

**Tests**: Run T003 before T002. TC-4 must then fail, because the rule is absent. After T002, TC-4 passes. The negative tests, TC-2 and TC-5, pass when they detect the defect they expect.

**Execution rules**:

- Before each edit, run `git status`. Leave a file that changed without your edit.
- Add files by explicit path. Do not run `git add -A` or `git add .`.
- Do not switch to another branch in this worktree.

## Format

- **[P]**: The task edits a file that no other open task edits.
- **Status**: `open`, `verified-present`, `partial`, or `absent`. The status shows the state of `main` at the time of this record.

## Phase 1: Verify the Current State

### T001 [P] [FR-002] Confirm the mando and radon pins on main

- **Status**: verified-present (R-13, R-14, R-15)
- **Files**: `requirements-dev.txt` (read only)
- **Acceptance**: Line 179 reads `mando==0.7.1`. Line 365 reads `radon==6.0.1`. Line 356 reads `pyyaml==6.0.4`.
- **Verify**: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T006 [P] [FR-007, FR-008] Keep the pip_audit job unchanged

- **Status**: verified-present (R-09, R-10, R-11, R-29)
- **Files**: `.github/workflows/ci.yml` (read only), `tests/guardrails/test_ci_gate_triggers.py` (read only)
- **Acceptance**: Line 454 names the check `pip-audit (CVE scan)`. Line 483 installs `requirements-dev.txt`. Line 498 runs `pip-audit -r requirements.txt`. The guard at line 189 maps `pip_audit` to that name.
- **Verify**: `python -m pytest tests/guardrails/test_ci_gate_triggers.py`

## Phase 2: Implement the Fix

### T002 [P] [FR-003] Add the mando ignore rule to the pip entry

- **Status**: absent (R-22, R-23)
- **Files**: `.github/dependabot.yml` (modify). The pip entry starts at line 3 (R-22).
- **Change**: Add an `ignore:` key to the pip entry. Add one rule with `dependency-name: "mando"`. Set `update-types` to `version-update:semver-minor` and `version-update:semver-major` (R-24, R-50).
- **Acceptance**: The pip entry holds one `ignore` key. The rule names mando and both update types. The rule holds no `versions` key, because the docs show no pip example (U-8). The comment names issue #4896 and the review trigger.
- **Verify**: `python -m pytest tests/guardrails/test_dependency_lock_file.py`, run after T003.

### T003 [FR-002, FR-004, FR-005, FR-006] Add the guard cases to the lock guard module

- **Status**: absent (R-27, R-28)
- **Depends on**: T001, T002
- **Files**: `tests/guardrails/test_dependency_lock_file.py` (modify). Add no file under `tests/guardrails/`.
- **Change**: Add a constant that maps radon `6.0.1` to the range `<0.8,>=0.6` (R-46, R-51). Add two methods to `DependencyLock`. The range method reports defects. The Dependabot method reads the YAML file. Add five test functions, TC-1 to TC-5.
- **Test functions**:
  - TC-1 `test_pinned_mando_satisfies_radon_range`: the pinned mando satisfies the range. No defect.
  - TC-2 `test_mando_above_radon_range_is_a_defect`: mando 0.8.2 gives one defect that names both versions.
  - TC-3 `test_unknown_radon_version_fails_closed`: a radon version without a range raises `AssertionError`.
  - TC-4 `test_dependabot_ignores_mando_minor_and_major`: the real configuration holds the rule.
  - TC-5 `test_dependabot_without_mando_rule_is_a_defect`: a fixture without the rule gives one defect.
- **Acceptance**: Each new executable line has an inline comment. Each file read logs `info` before and `debug` after. Each new function holds five parameters or fewer and 25 lines or fewer. Negative cases use `tmp_path` fixtures. The range check prints the number of pins that it examined, as AGENTS.md requires for a guard.
- **Verify**: `python -m pytest tests/guardrails/test_dependency_lock_file.py`

### T004 [P] [FR-009] Document the mando hold

- **Status**: absent (R-37 shows the `pip_audit` row only)
- **Files**: `documentation/quality-gates.md` (modify). Add one paragraph below the job table.
- **Acceptance**: The paragraph names the hold, mando 0.7.1, and radon 6.0.1. It names the range source, which is the radon 6.0.1 `Requires-Dist` line. It names the review trigger, which is a radon release that accepts mando 0.8. Each sentence follows the STE rules.
- **Verify**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`

### T005 [P] [FR-010] Add the release-note fragment

- **Status**: absent (R-31 counts 335 entries, none for this change)
- **Files**: `changelog.d/issue-4896-mando-radon-pin-conflict.md` (add)
- **Acceptance**: The file holds one `###` heading. The file holds one `- **Fixed**:` bullet that names issue #4896. The file name follows the naming rule in `changelog.d/README.md` for an issue without a pull request.
- **Verify**: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4896-mando-radon-pin-conflict.md`

## Phase 3: Gates and Delivery

### T-LOCAL-GATES [FR-001 to FR-010] Run the applicable local gates

- **Status**: open
- **Depends on**: T002, T003, T004, T005, T006
- **Files**: the four changed files and the record. Commit the test file first, because the test-quality gate reads committed files (R-57).
- **Acceptance**: Each command below reports its expected result.
  1. `python -m py_compile MistHelper.py` reports no output (R-58).
  2. `python -m ruff check .` reports `All checks passed` (R-58).
  3. `python -m black --check .` reports that no file needs a change (R-58).
  4. `python -m pytest tests/guardrails/test_dependency_lock_file.py` reports all tests passed (R-35).
  5. `python -m pytest tests/guardrails` reports all guard tests passed.
  6. `bandit -c pyproject.toml -r tests/guardrails/test_dependency_lock_file.py -q` reports no finding (R-60).
  7. `symbol-diff --base origin/main tests/guardrails/test_dependency_lock_file.py` reports no removed or changed module-level name (R-59). Record each added name in the pull request.
  8. `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` reports zero new findings.
  9. `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md documentation/quality-gates.md changelog.d/issue-4896-mando-radon-pin-conflict.md` reports a score of 80 or above for each file (line 74, R-36).
- **Not applicable**: The dependency audit (`pip-audit -r requirements.txt`) needs no run, because `requirements.txt` does not change. The CI job runs it (R-11). Mypy, Pylint, Vulture, pydocstyle, interrogate, and radon read path variables that name no `tests/guardrails` path (R-56). The coverage, safe sweep, menu reference, ops portal, and ops platform gates cover other code.
- **Verify**: Each command above, with its expected result.

### T-PR [FR-001, FR-007, FR-010] Commit, push, and open the replacement pull request

- **Status**: open
- **Depends on**: T-LOCAL-GATES
- **Steps**:
  1. Add the label `in-progress` to issue #4896 before you create the branch.
  2. Create the branch `fix/4896-mando-radon-pin-conflict` from `main` in a worktree.
  3. Add the changed files and the record by explicit path.
  4. Commit with the subject `fix(ci): hold mando below 0.8 for radon 6.0.1`. The body holds `Closes #4896` and the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
  5. Rebase onto `origin/main`. Rerun the affected local gates.
  6. Push the branch without force.
  7. Open the pull request to `main`. Use the commit subject as the title. The body holds `Closes #4896`, the changed-file list, the local gate results, the deployment note, and `Supersedes #4888`.
- **Acceptance**: The pull request title passes the Conventional Commits check. The body names the issue. The changed-file list matches the plan change map.
- **Verify**: `python -m pytest tests/guardrails/test_dependency_lock_file.py`, on the pushed commit.

### T-REMOTE-CI [SC-001, SC-004] Watch the remote checks

- **Status**: open
- **Depends on**: T-PR
- **Steps**:
  1. Run `gh pr checks <number> --watch` on the replacement pull request.
  2. Confirm that the check `pip-audit (CVE scan)` reports success.
  3. Confirm that every other required check reports success on the latest commit.
  4. If a check fails, stop. Open an issue for that failure with its full output. Do not merge.
- **Acceptance**: `pip-audit (CVE scan)` reports success. No required check reports a failure. The job `Run pip install -r requirements-dev.txt` exits with code 0.
- **Verify**: `pip-audit -r requirements.txt`, run on the rebased worktree before the push in T-PR step 6.

### T-MERGE [FR-011, SC-004] Merge, verify main, and close pull request #4888

- **Status**: open
- **Depends on**: T-REMOTE-CI and the owner's authorization
- **Steps**:
  1. Confirm the owner authorizes the merge. Without that authorization, stop and report.
  2. Add the label `auto-merge` only after each required check shows success (AGENTS.md, Pull request section).
  3. Squash-merge the replacement pull request.
  4. Wait for the dispatch that `.github/workflows/auto-merge.yml` starts for `container-build.yml` (R-52, R-68). Confirm that the run reports success (constitution Principle IV, step 10).
  5. Confirm that the image revision label equals the merge commit SHA (constitution Principle IV, step 11). The owner host runs `podman image inspect` on the built image (U-9).
  6. Close pull request #4888 with a comment. The comment carries the preservation proof. The proof names the merged replacement pull request and line 179 of `requirements-dev.txt` on main, which pins mando 0.7.1.
  7. Delete the branch and the worktree after the merge.
  8. Hand constitution Principle IV, step 12, to the owner (decision D-8).
- **Acceptance**: The latest Quality Gates run on main reports success for `pip-audit (CVE scan)`. The image revision label equals the merge SHA. Pull request #4888 is closed with the proof comment.
- **Verify**: `python -m pytest tests/guardrails/test_dependency_lock_file.py`, on the updated `main`.

Caution: Closing pull request #4888 is reversible. The owner can reopen it at any time.

Warning: A commit that you push after the squash merge becomes an orphan that no one merges. File a new issue, and branch again from `main`.
