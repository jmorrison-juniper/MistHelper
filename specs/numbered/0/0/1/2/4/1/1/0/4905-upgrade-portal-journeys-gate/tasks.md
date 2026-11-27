# Tasks: Upgrade Portal Journeys Gate on PR 4888

**Input**: Numeric record `specs/numbered/0/0/1/2/4/1/1/0/4905-upgrade-portal-journeys-gate/`. Use `plan.md`, `spec.md`, and the files under `design/`.

**Format**: `[ID] [P?] [Requirements] Description`. Each task names its files, its acceptance statement, its verification command, and its status. The status is `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Evidence

- [ ] T001 [verified-present] [FR-001, FR-002] Confirm the failed check, job, run, step, and rule. Files: `design/research.md`, `design/quickstart.md`. Acceptance: the quickstart outputs in sections 2 to 6 match research section E-1, row R-62, and rows R-01 and R-02. Verification: `python -m pytest tests/guardrails/test_upgrade_portal_journey_ci.py` (local gates Tests row, R-43). Status: verified-present. The evidence is in the record, and the remote rows confirm it.

## Phase 2: Implementation

- [ ] T002 [absent] [FR-004, FR-005] Add the mando ignore entry to the pip update stream. File: `.github/dependabot.yml`. Acceptance: `updates[0]` holds an `ignore` list with `dependency-name: "mando"` and `versions: [">=0.8"]`. The rationale comment names issue 4905 and PR 4888. The github-actions and npm streams show no change in the diff. Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py` after T003 (local gates Tests row, R-43). Status: absent. Caution: T002 and T003 land together. Run the guard after T003 only.

- [ ] T003 [absent] [FR-004, FR-005, FR-006] Extend the policy snapshot and add three test cases. File: `tests/guardrails/test_pr_title_workflow.py`. Acceptance: `POLICY_SNAPSHOTS["dependabot"]["updates"][0]` holds the same ignore entry as T002. The parameter list of `test_unrelated_changes_fail` holds `("updates", 0, "ignore")` with `[]`, and `("updates", 0, "ignore", 0, "versions")` with `[">=0.9"]`. The class `TestDependabotPolicy` holds the new method `test_mando_ignore_blocks_the_failed_release`. The module imports `SpecifierSet` from `packaging.specifiers`. Before T002, the new method fails with the missing entry. Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py` (local gates Tests row, R-43). Status: absent. Depends on T002.

- [ ] T004 [P] [absent] [FR-007] Add the changelog fragment. File: `changelog.d/issue-4905-upgrade-portal-journeys-gate.md`. Acceptance: the file has one `###` heading and one `Changed` bullet. The bullet names issue 4905. The file name passes the fragment guard. Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (local gates Tests row, R-43). Status: absent. Runs in parallel with T002 and T003, because it changes a different file.

Draft text for the fragment, in Simplified Technical English:

```markdown
### Dependabot stops the mando 0.8 update

- **Changed**: Dependabot no longer proposes mando 0.8 or later releases. Radon 6.0.1 requires mando below 0.8, and the journeys gate failed on pull request #4888. Issue #4905.
```

## Phase 3: Final Tasks

- [ ] T-LOCAL-GATES [open] [FR-009] Run every local gate that applies to the changed files. Files: `tests/guardrails/test_pr_title_workflow.py`, `.github/dependabot.yml`, `changelog.d/issue-4905-upgrade-portal-journeys-gate.md`, and the record files. Acceptance: each applicable command in the list below gives the expected result. Verification: the list below. Status: open. Depends on T002, T003, and T004.

  Applicable gates and their commands:
  1. Lint (R-77): `python -m ruff check .` gives `All checks passed`.
  2. Format (R-78): `python -m black --check .` reports no file that needs a change.
  3. Tests (R-43): run `python -m pytest tests/guardrails/test_pr_title_workflow.py`, `python -m pytest tests/guardrails/test_upgrade_portal_journey_ci.py`, `python -m pytest tests/guardrails/test_dependency_export.py`, `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`, and `python -m pytest tests/guardrails/test_spec_route_contract.py`. Each command exits with code 0.
  4. Full tests (R-44, R-45): run the guardrail shard command from the quickstart, section 10. Each shard prints one summary line.
  5. Test quality (R-80): run the `test-quality-analyzer` command from the quickstart, section 10, after the local commit. It gives `gate: 0 new findings vs baseline`.
  6. Security lint (R-81, R-82): run `bandit -c pyproject.toml -r tests/guardrails -q`. It reports no finding.
  7. Symbols (R-84): run `symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py`. It gives `no module-level name changed`.
  8. STE (R-46, R-50): run `ste-linter` on each Markdown file of the record and on the fragment. Each file scores 80 or above.

  Not applicable, with reasons: the Compile, Safe sweep, Coverage, and Menu reference rows of the local gates table name scopes that exclude this change. The Types gate reads the mypy path list, which names no test folder (R-79). The Complexity gate reads the radon path list, which names no guardrail test (R-85). The dead code and docstring gates name no guardrail test (R-86, R-87, R-88). Dependency audit covers `requirements.txt` only, and this change edits no requirement file (R-06, R-83).

- [ ] T-PR [open] [FR-008, FR-009] Commit, push, and open the pull request. Files: `.github/dependabot.yml`, `tests/guardrails/test_pr_title_workflow.py`, `changelog.d/issue-4905-upgrade-portal-journeys-gate.md`, and the folder `specs/numbered/0/0/1/2/4/1/1/0/4905-upgrade-portal-journeys-gate/`. Acceptance: the pull request targets `main`. Its title is `fix(ci): stop Dependabot from proposing mando 0.8`. Its body contains `Closes #4905`, the changed-file summary, the local gate results, and each item of `.github/PULL_REQUEST_TEMPLATE.md` with its evidence (R-54). The commit uses the Conventional Commits form and adds the Co-authored-by trailer required by the repository harness. The branch is `fix/4905-upgrade-portal-journeys-gate`. Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py` (local gates Tests row, R-43). Status: open. Steps:
  1. Add the `in-progress` label to issue 4905 before the branch exists. AGENTS.md section `Issue first` requires this claim.
  2. Create the branch from `main` in a worktree. Do not use `git checkout` in a shared checkout.
  3. Stage explicit paths only. Do not stage `git add -A` or `git add .`.
  4. Commit the change. The message body contains `Closes #4905`.
  5. Push the branch. Use `--force-with-lease` only if a push needs a rewrite.
  6. Open the pull request with the title and body above.

- [ ] T-REMOTE-CI [open] [FR-001, FR-006] Watch the CI run of the pull request. Files: `.github/workflows/ci.yml` and `tests/guardrails/test_upgrade_portal_journey_ci.py`, both read only. Acceptance: each required check passes. The check `Upgrade portal journeys` concludes `success`. The check `Dependency lock and exports` concludes `success`. The check `Conventional Commits PR title` concludes `success`. Verification: `python -m pytest tests/guardrails/test_upgrade_portal_journey_ci.py` (local gates Tests row, R-43), and the remote read in quickstart section 9 for the new run. Status: open. Steps: watch the pull request checks with `gh pr checks` and the `--watch` option. Wait for CodeQL before the next step. Add the `auto-merge` label only after each check shows green.

- [ ] T-MERGE [open] [FR-010, FR-011] Merge the fix and close the blocked pull request, after the orchestrator authorizes the merge. Files: `.github/dependabot.yml` and `tests/guardrails/test_pr_title_workflow.py`, both merged by the fix. Acceptance: the fix merges as one squash commit. The journeys gate on the merge commit concludes `success` (TST-011). After the closure authorization, PR 4888 reads `CLOSED`, and its comment names the surviving branch `dependabot/pip/mando-0.8.2` and commit `e86098cdc2b189d217805b3b4060ef609cbc37af` (TST-009). Gate issues 4891 to 4904 close with a comment that names PR 4888 (TST-010). Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py` (local gates Tests row, R-43), then the read commands of quickstart section 12. Status: open. Steps:
  1. Add the `auto-merge` label only after T-REMOTE-CI passes. The change touches no destructive operation.
  2. Squash the merge. Delete the branch `fix/4905-upgrade-portal-journeys-gate` after the merge.
  3. Read the journeys gate on the merge commit (quickstart section 9, with the run ID of the merge).
  4. Close PR 4888 only after the orchestrator authorizes the closure (U-2). Add one comment. Do not replace an earlier comment.
  5. Close gate issues 4891 to 4904 after PR 4888 closes. Add a comment that names the fix pull request.

  Warning: deleting the branch `dependabot/pip/mando-0.8.2` removes the only branch reference to the bump commit. Do not delete it.

  Caution: a commit pushed after the squash merge becomes an orphan. Open a new issue for any later fix, and branch again from `main`.

## Dependencies and Execution Order

- T001 has no prerequisite. Its evidence exists in the record.
- T002 depends on T001.
- T003 depends on T002.
- T004 has no prerequisite and runs in parallel with T002 and T003.
- T-LOCAL-GATES depends on T002, T003, and T004.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on the orchestrator authorization.

## Requirement Coverage

| Requirement | Task | Test or check |
| - | - | - |
| FR-001 | T001, T-REMOTE-CI | TST-005, TST-011 |
| FR-002 | T001 | TST-005 |
| FR-003 | T001 | TST-006 |
| FR-004 | T002, T003 | TST-001, TST-004 |
| FR-005 | T002, T003 | TST-001 |
| FR-006 | T003, T-REMOTE-CI | TST-002, TST-003 |
| FR-007 | T004 | TST-007 |
| FR-008 | T-PR | TST-008 |
| FR-009 | T-LOCAL-GATES | TST-001 to TST-008 |
| FR-010 | T-MERGE | TST-009 |
| FR-011 | T-MERGE | TST-010 |

## Test Plan

Tests planned: 11. Three tests are new, one is updated, and four run unchanged. Three command checks read the GitHub state.

| ID | Test or check | Status | Command | Requirements |
| - | - | - | - | - |
| TST-001 | `TestDependabotPolicy::test_complete_policy`. The live file equals the snapshot. | Updated | `python -m pytest tests/guardrails/test_pr_title_workflow.py` | FR-004, FR-005 |
| TST-002 | `test_unrelated_changes_fail`, case with the pip ignore list set to `[]`. | New | `python -m pytest tests/guardrails/test_pr_title_workflow.py` | FR-006 |
| TST-003 | `test_unrelated_changes_fail`, case with the mando range set to `>=0.9`. | New | `python -m pytest tests/guardrails/test_pr_title_workflow.py` | FR-006 |
| TST-004 | `TestDependabotPolicy::test_mando_ignore_blocks_the_failed_release`. The range blocks 0.8.2 and allows 0.7.1. | New | `python -m pytest tests/guardrails/test_pr_title_workflow.py` | FR-004 |
| TST-005 | `TestUpgradePortalJourneyCi::test_ci_runs_bounded_journeys_and_uploads_evidence`. The job contract holds 15 rules. | Existing | `python -m pytest tests/guardrails/test_upgrade_portal_journey_ci.py` | FR-001, FR-002 |
| TST-006 | `TestDependencyExport::test_requirements_exports_match_the_lock`. The exports equal the lock output. | Existing | `python -m pytest tests/guardrails/test_dependency_export.py` | FR-003 |
| TST-007 | The changelog fragment guard accepts the issue form of the file name. | Existing | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | FR-007 |
| TST-008 | The route contract test keeps the numeric route stable. | Existing | `python -m pytest tests/guardrails/test_spec_route_contract.py` | FR-008 |
| TST-009 | PR 4888 reads `CLOSED`, its head is `e86098c`, and a comment names the surviving branch. | Command check | `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,headRefOid,comments` | FR-010 |
| TST-010 | Gate issues 4891 to 4904 are closed, and no open pull request changes mando or radon. | Command check | `gh issue list -R jmorrison-juniper/MistHelper --label quality-gate --state open --json number,title` and `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName` | FR-011, SC-002 |
| TST-011 | The journeys gate on the merge commit concludes `success`. | Command check | Quickstart section 9, with the run ID of the merge commit | FR-001, SC-001 |
