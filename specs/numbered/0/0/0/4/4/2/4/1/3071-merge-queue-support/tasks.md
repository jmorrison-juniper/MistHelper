# Tasks: Merge queue rollout and acceptance

**Input**: `spec.md`, `plan.md`, and the artifacts under `design/` in this folder. Requirement IDs refer to `spec.md`.

**Status values**: `open`, `verified-present`, `partial`, or `absent`. Each status reflects `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on 2026-11-26. The row IDs in brackets refer to the tables in `design/research.md`.

**Owner steps**: The owner steps O-1 to O-7 in `plan.md` are not tasks. They run after T-MERGE.

## Phase 1: Baseline (read-only)

- [ ] T001 [FR-009] Record the baseline of branch protection, rulesets, the merge queue, and the `main` commit.
  - Files: none.
  - Acceptance: `strict` is true. Protection lists 15 required contexts. Rulesets count is zero. The merge queue value is null. The `main` commit is recorded in `analysis.md`.
  - Verify: the read-only commands in section 1 of `design/quickstart.md`. No row of the local gates table applies to this task.
  - Status: verified-present (R-52, R-54, R-55, R-60).

- [ ] T002 [FR-014] Read the review rule with the three API reads and record each value.
  - Files: `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/analysis.md`.
  - Acceptance: the three values are recorded. The owner confirms the rule before owner step O-3.
  - Verify: the review rule reads in section 1 of `design/quickstart.md`. No row of the local gates table applies to this task.
  - Status: partial (R-53). The reads disagree.

## Phase 2: Guard and documentation

- [ ] T003 [FR-008] Add one method named `test_queue_docs_name_each_queue_workflow` to the class `TestPullRequestTrigger` in `tests/guardrails/test_ci_gate_triggers.py`, after line 146.
  - Files: `tests/guardrails/test_ci_gate_triggers.py`.
  - Acceptance: the method reads the `ci.yml` row and the `codeql.yml` row of `.github/copilot-instructions.md`. It asserts that each row contains the text `merge queue candidate`. It reads `documentation/quality-gates.md` and asserts that the heading `## Merge queue preparation and activation` exists. The method prints the count of rows and headings that it examined. Each new line has an inline comment. The method fails before T004 and passes after T004.
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py -k queue_docs -q`
  - Status: absent. Main has no such method. The existing methods are at R-30 to R-33.

- [ ] T004 [P] [FR-006] Correct the `ci.yml` row at line 467 and the `codeql.yml` row at line 468 in the workflow table of `.github/copilot-instructions.md`.
  - Files: `.github/copilot-instructions.md`.
  - Acceptance: row 467 contains `each merge queue candidate`. Row 468 contains `each merge queue candidate`. No other row changes. The STE gate passes for the file.
  - Verify: `python -m pytest tests/guardrails/test_ci_gate_triggers.py -k queue_docs -q` and the STE command in T-LOCAL-GATES.
  - Status: stale (R-27, R-28). Both rows omit merge queue candidates on `main`.

- [ ] T005 [P] [FR-007, FR-013, FR-014] Revise the procedure under the heading `## Merge queue preparation and activation` in `documentation/quality-gates.md`.
  - Files: `documentation/quality-gates.md`.
  - Acceptance: the heading text does not change, because `.github/copilot-instructions.md` line 499 links to its anchor. The `### Preparation` subsection states the completed preparation: PR #4362, merge commit `00633cad3a544190a1fbf4fd1999308e91b90c4a`, merged on 2026-10-20. The `### Owner activation and verification` subsection adds the review rule step (O-1) and the batch size step (O-3). A new `### Constraints` subsection states three rules: pull requests that edit `.github/workflows/` need a manual merge, `ste-lint.yml` needs a `merge_group` trigger before its check becomes required, and `skipped` results are unresolved. Each new sentence passes the STE gate.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md` and `markdown-link-check documentation/quality-gates.md`.
  - Status: partial (R-23, R-24, R-25). The headings exist. The preparation text is in the future tense. No constraints subsection exists.

- [ ] T006 [P] [Constitution release-note rule, R-65] Add one fragment named `changelog.d/issue-3071-merge-queue-rollout.md`.
  - Files: `changelog.d/issue-3071-merge-queue-rollout.md`.
  - Acceptance: the file has one `###` heading that names the change. The file has one bullet that starts with `- **Changed**:` and ends with `Issue #3071.` The file name is unique. `CHANGELOG.md` stays unchanged.
  - Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
  - Status: absent.

- [ ] T007 [FR-010] Confirm that the change set has no workflow file.
  - Files: none.
  - Acceptance: the command prints no path.
  - Verify: `git diff --name-only origin/main -- .github/workflows`. No row of the local gates table applies. The command is a read-only Git check.
  - Status: open. Run after T003 to T006 are committed.

- [ ] T008 [All] Land the revised record files in `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/`.
  - Files: the nine files in the record folder listed in `plan.md`.
  - Acceptance: each file keeps its legacy path. The folder holds five children or fewer. The stale legacy claims listed in `analysis.md` are corrected.
  - Verify: `python -m pytest tests/guardrails/test_process_folder_structure.py tests/guardrails/test_spec_route_contract.py -q`
  - Status: open.

## Phase 3: Final tasks

- [ ] T-LOCAL-GATES [All] Run each gate in this list. Record the exact command and the result in the pull request body. Run the test quality ratchet only after the intended tests are committed.
  - Files: the changed files listed in `plan.md`.
  - Acceptance: each command exits 0, and each output matches the expected result below. A gate that does not apply names its reason in the pull request body.
  - Verify, applies:
    1. `python -m pytest tests/guardrails/test_ci_gate_triggers.py -q`. Expected: all tests pass.
    2. `python -m pytest tests/guardrails -q`. The CI shard for guardrails includes this path (`.github/workflows/ci.yml` line 255). Expected: all tests pass.
    3. `python -m ruff check .`. Expected: `All checks passed`.
    4. `python -m black --check .`. Expected: no file needs a change.
    5. `radon cc tests/guardrails/test_ci_gate_triggers.py -j | complexity-gate --max 10`. Expected: no block above complexity 10.
    6. `bandit -c pyproject.toml -r . -q`. The CI job runs the same command on the repository root (`.github/workflows/ci.yml` line 451). Expected: no finding.
    7. `symbol-diff --base origin/main tests/guardrails/test_ci_gate_triggers.py`. Expected: `no module-level name changed`, exit code 0.
    8. `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`. Expected: the preflight passes.
    9. `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. Expected: `gate: 0 new findings vs baseline`. The baseline file stays unchanged.
    10. `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`. Expected: each file scores 80 or above. This is the CI command.
    11. `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md` and the nine record files listed in `plan.md`. Expected: each file scores 80 or above. The `AGENTS.md` rule applies, and the CI command does not cover these files.
    12. `markdown-link-check .github/copilot-instructions.md documentation/quality-gates.md`. Expected: no broken link and no missing anchor.
    13. `git diff --check`. Expected: no output.
  - Verify, does not apply: `python -m py_compile MistHelper.py` (no change to `MistHelper.py`). `python -m mypy $MYPY_PATHS --config-file pyproject.toml` (`MYPY_PATHS` excludes tests, `.github/workflows/ci.yml` line 93). `vulture $VULTURE_PATHS --min-confidence 70` (product paths only, line 101). `pydocstyle $PYDOCSTYLE_PATHS` (line 104) and `interrogate $INTERROGATE_PATHS` (line 107) (product paths only). `pylint src/` (product paths only). `pip-audit -r requirements.txt` (no dependency change). The coverage gate (no `src/` change). The menu reference gate (no menu change). The safe sweep (no runtime change). The ops portal and ops platform gates (no change in those trees).
  - Status: open.

- [ ] T-PR [All] Commit the explicit paths, push the branch `docs/3071-merge-queue-rollout`, and open the pull request against `main`.
  - Files: the explicit paths listed in `plan.md`. Do not use `git add -A` or `git add .`.
  - Acceptance:
    - The commit subject is `docs(ci): record merge queue rollout gate for #3071`.
    - The pull request title is the same subject.
    - The pull request body uses `.github/PULL_REQUEST_TEMPLATE.md` (blob `ed03e8f36f20962d9c7bbd74cde192d5adfdcc77`).
    - The body contains `Refs #3071` and does not contain `Closes #3071`. The body gives the reason from decision D-5.
    - The body gives the local gate results from T-LOCAL-GATES, the changed-file summary, the rollback steps from `plan.md`, and the statement that no repository setting changed.
    - The commit message ends with the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
    - The pull request carries the labels `chore` and `ci`.
  - Verify: `gh pr view $pullNumber -R jmorrison-juniper/MistHelper --json number,title,state,body,headRefName` with `$pullNumber` set to the number that `gh pr create` returns. No row of the local gates table applies to this task.
  - Status: open.

- [ ] T-REMOTE-CI [All] Wait for the required contexts on the pull request head.
  - Files: none.
  - Acceptance: each of the 15 required contexts reports `SUCCESS` on the head commit. No required context reports canceled, timed out, stale, or skipped. Any failed non-required job is named with its cause in the pull request.
  - Verify: `gh pr checks $pullNumber -R jmorrison-juniper/MistHelper --watch`. The remote required contexts replace the local gates for this task.
  - Status: open.

- [ ] T-MERGE [All] Enable auto-merge or squash-merge the pull request only after T-REMOTE-CI passes and the orchestrator authorizes the merge.
  - Files: none.
  - Acceptance:
    - The coordinator review is recorded on the pull request.
    - No other pull request holds the serial merge slot.
    - The pull request still has no workflow file change (T007).
    - The squash commit lands on `main`. The `main` run starts.
    - Issue #3071 stays open after the merge.
  - Verify: `gh pr view $pullNumber -R jmorrison-juniper/MistHelper --json state,mergedAt,mergeCommit` and `gh issue view 3071 -R jmorrison-juniper/MistHelper --json state`. No row of the local gates table applies to this task.
  - Status: open.

## Dependencies & Execution Order

- T001 and T002 run first. They read `main` and do not change files.
- T003 runs before T004. T003 must fail before T004 is applied, to prove that the test can fail.
- T004, T005, and T006 run in parallel after the red run of T003. Each one changes a different file.
- T007 and T008 run after T003 to T006.
- T-LOCAL-GATES runs after T003 to T008.
- T-PR runs after T-LOCAL-GATES. T-REMOTE-CI runs after T-PR. T-MERGE runs after T-REMOTE-CI.

## Parallel Examples

- T004 changes `.github/copilot-instructions.md`. T005 changes `documentation/quality-gates.md`. T006 adds a fragment. The three files do not overlap.
- T003 changes `tests/guardrails/test_ci_gate_triggers.py` alone, so it runs in its own lane.

## Implementation Strategy

Deliver one documentation pull request. Keep it free of workflow file changes, so the shared auto-merge workflow can merge it. Keep the serial merge slot until the owner records the evidence from O-4 and O-5.
