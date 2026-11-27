# Tasks: History Site Column Failure Evidence

**Input**: Numeric record `specs/numbered/0/0/1/1/3/4/4/4/4249-history-site-column-evidence/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, and `design/contracts/diagnostics-artifact.md`.

## Format

- `[P]`: The task can run in parallel because it changes different files.
- Requirements: Each `FR-###` or `SC-###` identifier comes from `spec.md`.
- Status: `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Verify the Baseline

### T001 Confirm the diagnostics step and the shard command on main

- **Requirements**: FR-001, FR-002, FR-003
- **Paths**: `.github/workflows/ci.yml`
- **Acceptance**: `main` holds the shard command (line 909), the diagnostics condition (line 939), and the diagnostics paths (lines 945 and 946). Research rows RC-19 to RC-27 record each line. The guard passes on the unchanged workflow before any edit.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py`
- **Status**: verified-present

## Phase 2: Guard and Documentation

### T002 Add the diagnostics audit class

- **Requirements**: FR-001, FR-002, FR-004
- **Paths**: `tests/guardrails/test_e2e_shard_partition.py`
- **Acceptance**: Class `EvidenceUploadAudit` has the static method `check_upload(workflow)`. The method asserts five rules and returns five. Each executable line has an inline comment. The method logs before the read and after the count.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py`
- **Status**: open

### T003 Add the guard test cases

- **Requirements**: FR-004
- **Paths**: `tests/guardrails/test_e2e_shard_partition.py`
- **Acceptance**: Test `test_the_diagnostics_upload_keeps_the_evidence_after_a_failure_or_cancel` expects five. Test `test_a_missing_diagnostic_fails` runs five cases and expects `AssertionError` in each. The cases are `condition`, `trace`, `log`, `tee`, and `duplicate`. They remove the condition, the browser output path, the shard log path, and the `tee` target, and they add a second upload step.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py`
- **Status**: open

### T004 Update the module docstring

- **Requirements**: FR-004
- **Paths**: `tests/guardrails/test_e2e_shard_partition.py`
- **Acceptance**: The module docstring names the diagnostics rule and issue 4249 in one sentence.
- **Verification**: `python -m ruff check tests/guardrails/test_e2e_shard_partition.py`
- **Status**: open

### T005 Update the gate page [P]

- **Requirements**: FR-006, FR-007
- **Paths**: `documentation/quality-gates.md`
- **Acceptance**: The `playwright` row names the diagnostics artifact. One new paragraph after line 86 names its files, the failure screenshot, the trace, and the cancel limit.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`
- **Status**: open

### T006 Add the changelog fragment [P]

- **Requirements**: FR-008
- **Paths**: `changelog.d/issue-4249-history-site-column-evidence.md`
- **Acceptance**: The fragment has one `###` heading and one `Changed` bullet. The bullet ends with "Issue #4249."
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

### T007 Confirm the change scope

- **Requirements**: FR-005, FR-009
- **Paths**: `tests/guardrails/test_e2e_shard_partition.py`, `documentation/quality-gates.md`, `changelog.d/issue-4249-history-site-column-evidence.md`, and the record folder
- **Acceptance**: The diff holds only the paths above. No path under `src/` or `tests/e2e/` changes. The diff check is test TP-04.
- **Verification**: `python -m pytest tests/guardrails/test_e2e_shard_partition.py`
- **Status**: open

### T008 Place the record in the repository [P]

- **Requirements**: FR-011
- **Paths**: `specs/numbered/0/0/1/1/3/4/4/4/4249-history-site-column-evidence/`
- **Acceptance**: The folder holds the files that `plan.md` lists. The STE gate scores each Markdown file at 80 or above.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/3/4/4/4/4249-history-site-column-evidence/spec.md`
- **Status**: open

## Phase 3: Gates and Delivery

### T-LOCAL-GATES Run each applicable local gate

- **Requirements**: FR-002 to FR-011, SC-002
- **Paths**: The changed paths from T002 to T008.
- **Acceptance**: Each applicable gate exits with its expected result. The pull request body names each gate that does not apply, with its reason.
- **Verification commands**, run in this order:
  1. `python -m py_compile tests/guardrails/test_e2e_shard_partition.py` prints no output.
  2. `python -m ruff check tests/guardrails/test_e2e_shard_partition.py` prints `All checks passed`.
  3. `python -m black --check tests/guardrails/test_e2e_shard_partition.py` reports no file that needs a change.
  4. `python -m pytest tests/guardrails/test_e2e_shard_partition.py` reports all tests passed.
  5. `bandit -c pyproject.toml -r tests/guardrails/test_e2e_shard_partition.py -q` reports no finding.
  6. `symbol-diff --base origin/main tests/guardrails/test_e2e_shard_partition.py` reports `no module-level name changed` with exit code 0.
  7. `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` passes the preflight.
  8. `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` reports `gate: 0 new findings vs baseline`.
  9. `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md changelog.d/issue-4249-history-site-column-evidence.md specs/numbered/0/0/1/1/3/4/4/4/4249-history-site-column-evidence/spec.md` scores each file at 80 or above.
  10. `check-citations src tests` reports that every citation resolves.
- **Not applicable**: `python -m mypy` (`MYPY_PATHS` excludes tests, `ci.yml` line 93). `radon` (`RADON_PATHS` excludes the guard file, line 99). `vulture`, `pydocstyle`, and `interrogate` (their paths exclude tests, `ci.yml` lines 101 to 107). Coverage, the menu reference, the ops portal, and the ops platform (no related change).
- **Status**: open

### T-FOLLOW Open the follow-up issue before the merge

- **Requirements**: FR-010
- **Paths**: None. The follow-up issue lives on GitHub.
- **Acceptance**: An open issue names the unverified root cause and the checks of FR-011. It carries the labels `bug`, `needs-investigation`, and `tests`. The pull request body names its number.
- **Verification**: `gh issue list -R jmorrison-juniper/MistHelper --state open --label needs-investigation --json number,title`
- **Status**: open

### T-PR Commit, push, and open the pull request

- **Requirements**: FR-008, FR-010
- **Paths**: The files from T002 to T008.
- **Acceptance**: One commit uses the subject `test(e2e): keep the shard diagnostics after a cancel`. The commit body holds `Closes #4249` and the Co-authored-by trailer. The branch is `fix/4249-history-site-column-evidence`. The pull request title equals the commit subject. The pull request body holds the file summary, the local gate results, the deployment note, the rollback note, and the follow-up issue number. The labels are `bug`, `tests`, and `in-progress`.
- **Verification**: `gh pr view --json body --jq .body` contains `Closes #4249`.
- **Status**: open

### T-REMOTE-CI Watch the required checks

- **Requirements**: SC-003
- **Paths**: None.
- **Acceptance**: Each required check passes on the pull request. The `E2E smoke tests` check passes after all three shard rows finish.
- **Verification**: `gh pr checks --watch`
- **Status**: open

### T-MERGE Enable auto-merge after the owner authorizes the merge

- **Requirements**: FR-010, SC-003
- **Paths**: None.
- **Acceptance**: The orchestrator authorizes the merge. The `auto-merge` label is then added. The squash merge closes issue 4249, and the follow-up issue stays open. The checks on `main` pass after the merge.
- **Verification**: `gh pr view --json autoMergeRequest --jq .autoMergeRequest`
- **Status**: open

## Test Plan

| ID | Test or check | Requirements | Expected result | Status |
|---|---|---|---|---|
| TP-01 | `test_the_diagnostics_upload_keeps_the_evidence_after_a_failure_or_cancel` | FR-001, FR-002 | Passes and reports five rules | open |
| TP-02 | `test_a_missing_diagnostic_fails` with cases `condition`, `trace`, `log`, `tee`, and `duplicate` | FR-002, FR-004 | Each case raises `AssertionError` | open |
| TP-03 | `test_each_shard_keeps_the_options_of_the_single_job` (existing) | FR-003 | Passes | verified-present |
| TP-04 | `git diff --name-only origin/main` | FR-005 | No path under `src/` or `tests/e2e/` | open |
| TP-05 | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | FR-008 | Passes with the new fragment | open |
| TP-06 | STE gate on `documentation/quality-gates.md` | FR-006, FR-007 | Score of 80 or above | open |
| TP-07 | `git ls-tree --name-only origin/main tests/guardrails/` | FR-009 | 79 entries, none added | open |
| TP-08 | `gh pr view --json body --jq .body` | FR-010 | Body holds `Closes #4249` and the follow-up number | open |
| TP-09 | Heading `## Unverified` in `design/research.md` | FR-011 | The list holds each candidate cause and its check | open |

## Dependencies and Execution Order

- T001 runs first.
- T002, T003, and T004 run in this order. They change one file.
- T005 and T006 run in parallel with each other. T008 runs in parallel with them.
- T007 runs after T002 to T006.
- T-LOCAL-GATES runs after T007 and T008.
- T-FOLLOW runs before T-MERGE. It can run in parallel with T-PR.
- T-PR runs after T-LOCAL-GATES.
- T-REMOTE-CI runs after T-PR.
- T-MERGE runs after T-REMOTE-CI and T-FOLLOW, when the owner authorizes the merge.

## Notes

- Caution: each push starts a full CI run. Group the edits, and push one time.
- Use the prose term "canceled". Keep the identifier `cancelled()` and the conclusion value `cancelled` unchanged.
