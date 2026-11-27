# Tasks: Ops Platform Deepdiff Pin

**Input**: Design documents in `specs/numbered/0/0/1/2/4/1/1/2/4907-ops-platform-deepdiff-pin/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/contracts/pin-guard-output.md`

**Tests**: The guard test is the test task. It proves two behaviors: main passes, and a synthetic conflict fails. No other test is required.

## Format

- **[P]**: The task can run in parallel with other [P] tasks of its phase. It edits a different file.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.
- Each task names its requirement IDs, its exact paths, its acceptance statement, and its verification command.
- Verification rule: local tasks name one command from the local gates table. Evidence, delivery, and remote tasks use read-only `gh` or `git` commands, because that table covers local checks only.

## Phase 1: Evidence

- [X] **T001** [verified-present] Confirm the failing check and the failing step. Requirements: FR-002. Paths: `.github/workflows/ci.yml` lines 1122 to 1162. Acceptance: The log of run 45064277976 holds `ResolutionImpossible` and no pytest marker. Verification: `gh run view 45064277976 -R jmorrison-juniper/MistHelper --log-failed`. Evidence: research rows 1 to 4 and quickstart.

- [X] **T002** [verified-present] Confirm that main keeps the pin and the declared constraint in agreement, and that main passes the ops gate. Requirements: FR-005. Paths: `mist-ops-platform/pyproject.toml` line 31, `mist-ops-platform/requirements.txt` line 56. Acceptance: Main pins `deepdiff==8.6.2`, the constraint is `>=8.6.2,<9.0`, and run 45774119357 reports job `pytest (ops platform)` as success. Verification: `gh run view 45774119357 -R jmorrison-juniper/MistHelper --json jobs`. Evidence: research rows 10 and 12, and spec clarifications.

## Phase 2: Implementation

- [ ] **T003** [open] Add the test method `test_ops_platform_pins_obey_declared_constraints` to class `TestDependencyExport`. Update the module docstring at line 1 to name issue 4907. Requirements: FR-001, FR-002, FR-003, FR-004. Paths: `tests/guardrails/test_dependency_export.py`. Acceptance: On main pins the method prints `ops platform pins: examined 22 pins, 0 defects` and passes. On the synthetic `deepdiff==9.2.1` copy it reports exactly `deepdiff`. The class holds five methods, and the module holds five top-level names. Verification: `python -m pytest tests/guardrails/test_dependency_export.py -q -s`.

- [ ] **T004** [P] [open] Add the changelog fragment `changelog.d/issue-4907-ops-platform-deepdiff-pin.md`. Requirements: FR-006. Paths: `changelog.d/issue-4907-ops-platform-deepdiff-pin.md`. Acceptance: The fragment holds one `###` heading and one `Fixed` bullet. The bullet ends with `Issue #4907.` Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`.

## Phase 3: Final Gates and Delivery

- [ ] **T-LOCAL-GATES** [open] Run each local gate that applies to the changed files. Run it after T003 and T004. Requirements: FR-001 to FR-006. Paths: `tests/guardrails/test_dependency_export.py`, `changelog.d/issue-4907-ops-platform-deepdiff-pin.md`, and the record Markdown files. Acceptance: Each applicable gate passes. Each gate that does not apply states its reason in the PR body. Verification and expected results:
  - `python -m ruff check .` prints `All checks passed`.
  - `python -m black --check .` reports that no file needs a change.
  - `python -m pytest tests/guardrails/test_dependency_export.py -q` passes.
  - `symbol-diff --base origin/main tests/guardrails/test_dependency_export.py` prints `no module-level name changed`.
  - `bandit -c pyproject.toml -r tests/guardrails/test_dependency_export.py -q` reports no finding.
  - `python -m pytest tests/guardrails/test_ci_gate_triggers.py tests/guardrails/test_pr_title_workflow.py -q` passes. These existing guards hold the workflow and Dependabot values that FR-005 protects.
  - `ste-linter --config .ste-linter.toml --min-score 80` on each record Markdown file scores 80 or above.
  - The Test quality ratchet procedure in `.github/copilot-instructions.md` (lines 95 to 141) prints `gate: 0 new findings vs baseline`.
  - Not applicable: compile, because `MistHelper.py` is unchanged.
  - Not applicable: mypy, because tests are outside `MYPY_PATHS` (`ci.yml` line 93).
  - Not applicable: pydocstyle and interrogate, because tests are outside `PYDOCSTYLE_PATHS` (line 104).
  - Not applicable: vulture (line 101) and radon (line 99), because tests are outside their paths.
  - Not applicable: coverage, because no `src/` file changes. Menu reference and ops portal also do not apply.

- [ ] **T-PR** [open] Create the pull request. Requirements: FR-005, FR-006. Paths: `tests/guardrails/test_dependency_export.py`, `changelog.d/issue-4907-ops-platform-deepdiff-pin.md`, and `specs/numbered/0/0/1/2/4/1/1/2/4907-ops-platform-deepdiff-pin/`. Acceptance: Issue 4907 holds the label `in-progress` before the branch exists (`AGENTS.md` line 187). The branch is `fix/4907-ops-platform-deepdiff-pin` from `main`. The commit subject is `fix(ci): guard ops platform pins against declared constraints`, and its body holds `Closes #4907` and the Co-authored-by trailer. The PR title equals the commit subject. The PR body answers each checkbox of `.github/PULL_REQUEST_TEMPLATE.md`. The diff against `origin/main` lists only the paths above. Verification: `git diff --name-only origin/main HEAD`. Push with a normal push. Do not force-push.

- [ ] **T-REMOTE-CI** [open] Watch the CI checks of the change pull request. Requirements: FR-001 to FR-003, SC-001, SC-002. Acceptance: `Dependency lock and exports`, `pytest (ops platform)`, and `pytest coverage shard (root-and-contracts)` report success. The job log of `Dependency lock and exports` shows `ops platform pins: examined 22 pins, 0 defects`. Verification: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch` (`AGENTS.md` line 229), then `gh run view <run-id> -R jmorrison-juniper/MistHelper --log`.

- [ ] **T-MERGE** [open] Merge the change and close PR #4889. Requirements: FR-007, SC-003, SC-004. Acceptance: The orchestrator authorizes the merge. The squash merge happens only after every check passes (`AGENTS.md` lines 229 and 233). Issue #4907 closes after the merge. Check the `container-build.yml` run list for the merge commit. Expected result: no run, because the push paths match no changed file (`.github/workflows/container-build.yml` lines 6 to 19). Record that result in the PR. Then close PR #4889 with a closing comment. The comment names the declared constraint (`mist-ops-platform/pyproject.toml` line 31) and the decision to keep deepdiff on 8.x. The comment also names the preservation proof: branch `dependabot/pip/deepdiff-9.2.1` at commit `9d4640661fa40b1e0a7809f46a0007eff7add517`. Verification: `gh pr view 4889 -R jmorrison-juniper/MistHelper --json state,mergedAt` reports `CLOSED` and `null`.
  - Caution: closing PR #4889 hides its failing check from the default pull request list. Reopen it if the owner reverses decision D-1.
  - Warning: do not delete branch `dependabot/pip/deepdiff-9.2.1`. It is the only remote copy of the proposed bump.
