# Tasks: Main workflow recovery

**Input**: Numeric record at `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, `design/contracts/`.

**Format**: `- [ ] T### [US#] [FR-###] Description`. Tick `[x]` only after the named verification passes.

**Status values**: open, verified-present, partial, absent.

**Verification rule**: A configuration task names a command from the local gates table. A hosted task uses a query in `design/quickstart.md`, section 3. The local gates table has no hosted gate. Analysis item E-2 records this exception.

## Phase 1: Verified state (authoring run)

- [x] T001 [US1] [FR-001] Verify the consumer pin on line 61 of `.github/workflows/auto-merge.yml`.
  - Acceptance: line 61 pins `d63a120487cecf750184cb178387cdc25c0a7635`.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`.
  - Evidence: RC-01. Status: verified-present.
  - (delivered: .github/workflows/auto-merge.yml)

- [x] T002 [US1] [FR-002] Verify the four-workflow list on line 65 of `.github/workflows/auto-merge.yml`.
  - Acceptance: line 65 names `ci.yml`, `codeql.yml`, `container-build.yml`, and `ste-lint.yml`.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`.
  - Evidence: RC-02. Status: verified-present.
  - (delivered: .github/workflows/auto-merge.yml)

- [x] T003 [US1] [FR-003] Verify the triggers, permissions, and close job in `.github/workflows/auto-merge.yml`.
  - Acceptance: lines 25, 35, 44, 46, 50, 79, and 85 match RC-03 to RC-07.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`.
  - Status: verified-present.
  - (delivered: .github/workflows/auto-merge.yml)

- [x] T004 [US2] [FR-004, FR-005, FR-006] Verify the shared gates at `d63a120` in `misthelper-devtools`.
  - Files: remote `jmorrison-juniper/misthelper-devtools:.github/workflows/reusable-auto-merge.yml`. No local file.
  - Acceptance: lines 116, 234, 238, 258, 265, 274, 284, 301, 311, and 365 match RC-25 to RC-34.
  - Verification: `design/quickstart.md`, section 2 (decode command).
  - Status: verified-present.

- [x] T005 [US1] [FR-007, FR-008] Verify the guard test pins and the four-workflow set.
  - Files: `tests/guardrails/test_auto_merge_issue_close.py`.
  - Acceptance: lines 46, 159, and 166 match RC-08 to RC-10.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`.
  - Status: verified-present.

- [x] T006 [US1] [FR-001, FR-002] Verify the consumer release-note fragment.
  - Files: `changelog.d/issue-4763-post-merge-consumer.md`.
  - Acceptance: the file exists on `main` (RC-14).
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`.
  - Status: verified-present.
  - (delivered: changelog.d/issue-4763-post-merge-consumer.md)

- [x] T007 [US1] [FR-009] Verify the eight immediate-path merges.
  - Files: none. Hosted runs and pull requests.
  - Acceptance: RC-56 to RC-63 each show one `Verified pull request N: merged.` line and four `Started` lines.
  - Verification: `design/quickstart.md`, query H-03 for each run.
  - Status: verified-present.

- [x] T008 [US3] [FR-004] Verify the merged-close path.
  - Files: none. Hosted runs.
  - Acceptance: run 43793516716 (RC-49) and closed run 44952654909 (RC-64) show a dispatch job that completed with success.
  - Verification: `design/quickstart.md`, query H-02.
  - Status: verified-present.

- [ ] T009 [US3] [FR-006] Verify scheduled coverage and check for scheduled starts.
  - Files: none. Hosted runs.
  - Acceptance: run 45786075135 logs coverage for four workflows (RC-65). No scheduled run started a workflow in the window (RC-67).
  - Verification: `design/quickstart.md`, query H-04.
  - Status: partial. Evidence verifies coverage. A scheduled start has no evidence.

- [x] T010 [US4] [FR-011] Verify the workflow-file block.
  - Files: remote shared workflow `reusable-auto-merge.yml` at `d63a120`, lines 116 to 122.
  - Acceptance: run 43800244711 logs `Pull request 4816 edits a workflow file.` (RC-54).
  - Verification: `design/quickstart.md`, query H-06.
  - Status: verified-present.

- [ ] T011 [US2] [FR-004, FR-005, FR-009] Observe one delayed-path merge.
  - Files: none. Hosted runs and pull requests.
  - Acceptance: a labeled run logs `Verified pull request N: enabled.` with a skipped dispatch job. A closed run or a scheduled run covers a later merge within six hours.
  - Verification: `design/quickstart.md`, query H-01 and section 4.
  - Status: open. RC-68 shows no pending request in the survey.

- [ ] T012 [FR-010] Gate the closure of issue #4763.
  - Files: none. The issue on GitHub.
  - Acceptance: T011 passes. The orchestrator approves the closure (acceptance item AC-05).
  - Verification: `design/quickstart.md`, section 6.
  - Status: open.

- [ ] T013 [FR-012] Record the exclusion of `wiki-publish.yml` in `design/research.md` (decision D-4).
  - Files: `design/research.md`.
  - Acceptance: D-4 cites RC-40 to RC-42 and RC-75. The guard test enforces the four-name set (RC-09).
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`.
  - Status: open. The record commits with T-PR.

## Final tasks

- [ ] T-LOCAL-GATES [SC-004] Run the gates that apply to the changed record files.
  - Files: the eleven record files under `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/`.
  - Command: `python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_auto_merge_issue_close.py`.
  - Not applicable: compile (MistHelper.py only), lint, format, types, full tests, coverage, test quality, and complexity.
  - Not applicable: bandit, dependency audit, dead code, docstrings, menu reference, symbols, ops portal, ops platform, and safe sweep.
  - Not applicable: STE (the table names five other files). No Python file changes.
  - Acceptance: each command exits with status 0. The orchestrator records each summary line.
  - Status: open. This agent ran no test.

- [ ] T-PR [FR-009, FR-010, FR-012] Commit the record, push the branch, and open the pull request.
  - Files: the eleven record files. Replace the legacy files at the same route (D-9).
  - Commit title: `docs(specs): record main workflow recovery acceptance`.
  - Branch: `docs/4763-post-merge-consumer`.
  - Pull request body: contains `Refs #4763`, not `Closes #4763` (D-7). Lists the evidence rows and the open items.
  - Pre-check: `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName,files` shows no overlap with the record route.
  - Acceptance: the pull request targets `main`, its title follows Conventional Commits, and it changes no file under `.github/workflows/`.
  - Status: open.

- [ ] T-REMOTE-CI [FR-008] Watch the required checks on the record pull request.
  - Command: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`.
  - Acceptance: each required check passes on the latest commit. The SpecKit task audit is advisory (RC-86).
  - Status: open.

- [ ] T-MERGE [FR-011] Merge the record pull request after the orchestrator authorizes the merge.
  - Command: add the `auto-merge` label after every check passes (AGENTS.md, RC-72). The workflow allows a token merge because the pull request changes no workflow file.
  - Acceptance: the labeled run logs one confirmed merge and four start lines for the merge commit. The record pull request adds one more immediate-path observation.
  - Note: The merge does not close #4763 (D-7). T012 controls the closure.
  - Status: open.
