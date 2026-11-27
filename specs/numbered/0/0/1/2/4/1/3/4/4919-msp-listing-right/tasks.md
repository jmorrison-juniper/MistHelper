# Tasks: MSP organization list skipped without the listing right

**Input**: `specs/numbered/0/0/1/2/4/1/3/4/4919-msp-listing-right/` with `spec.md`, `plan.md`, and `design/`.

**Format**: `ID [P?] [Story] Description`. `[P]` marks a task that touches different files and has no open dependency.

**Status meanings**:

- `open`: a process step that has not started.
- `absent`: the change is not on `main`. Remote check R-rows show the gap.
- `partial`: `main` holds some of the required behavior.
- `verified-present`: `main` already holds the required behavior.

**Start condition**: HUMAN-DECISION-REQUIRED. Start only after decision D8 approves scheduling. Follow tasks in phase order.

## Phase 1: Preconditions

- [ ] T-000 Create the implementation worktree from `origin/main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` or a later commit. Do not include the pending working-copy change. Requirements: FR-010. Files: `src/mist/intelligence/reports/subscription_expiry/client.py`, `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. Acceptance: the worktree diff against `origin/main` is empty before the first edit. Verification: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. Status: open.

## Phase 2: Listing right and skipped rows (User Stories 1 and 2)

- [ ] T001 Add the class attribute `MSP_GRANT_SCOPE` with value `msp`, and add the static method `_has_msp_listing_right` to `SubscriptionExpiryClient` in `src/mist/intelligence/reports/subscription_expiry/client.py`. Requirements: FR-001, FR-002. Acceptance: the method returns True for scope `msp` and for a missing scope key. It returns False for `org`, `orggroup`, `site`, `sitegroup`, and None. Verification: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. Status: absent (remote rows R04 to R06 show no related helper on `main`). Depends on T-000.

- [ ] T002 Change the MSP branch in `discover_organizations` in `src/mist/intelligence/reports/subscription_expiry/client.py` so that `_discover_msp` runs only when `_has_msp_listing_right` returns True. Requirements: FR-003, FR-009. Acceptance: no listing call occurs for scope `org`. Scope `msp` keeps the existing listing behavior. Verification: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. Status: absent (remote row R02 shows the unconditional branch at main line 99). Depends on T001.

- [ ] T003 Add the methods `_skipped_msp_rows` and `_skipped_msp_row` to `src/mist/intelligence/reports/subscription_expiry/client.py`. Append their rows to the return value of `discover_organizations`. Requirements: FR-004, FR-005, FR-006, FR-011. Acceptance: each MSP id without the listing right gets one row. The row fields and reason text follow `design/contracts/status-rows.md`. The method logs an info line before and a debug line after. Verification: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. Status: absent. Depends on T002.

## Phase 3: Console summary (User Story 1)

- [ ] T004 Update `_print_summary` in `src/mist/intelligence/reports/subscription_expiry/operation.py`. Exclude skipped rows from the "Organizations discovered" count. Print the skipped source count and one line for each skipped row. Add the static methods `_skipped_rows` and `_print_skipped_sources`. Requirements: FR-007, FR-008. Acceptance: the output matches `design/contracts/console-summary.md`. The method adds at most two lines to `_print_summary`. Verification: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. Status: absent (remote row R11 shows the current count line at main line 505). Depends on T003.

## Phase 4: Unit tests (User Stories 1 and 2)

- [ ] T005 [P] Add six test functions to `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. The functions are:
  - `test_msp_scope_grant_lists_msp_organizations`: calls `listMspOrgs` once.
  - `test_org_scope_grant_skips_msp_listing_and_writes_one_row`: makes no call, writes one skipped row, logs one info line and one debug line, and checks the return shape and the six status columns.
  - `test_non_msp_scopes_with_msp_id_skip_listing`: is parametrized over `orggroup`, `site`, and `sitegroup`. Each value behaves like scope `org`.
  - `test_missing_scope_key_keeps_msp_listing`: calls `listMspOrgs`.
  - `test_msp_scope_wins_over_org_scope_for_same_msp`: makes one call and writes no skipped row.
  - `test_repeated_org_scope_grants_write_one_skipped_row`: writes one skipped row for one MSP id.

  Requirements: FR-001 to FR-004, FR-009, FR-014. Acceptance: test (2) fails on the unchanged `main` code. Verification: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`. Status: partial (remote row R20 shows the direct and MSP discovery test at main line 104. No skipped-row test exists, as remote row R21 shows). Depends on T002 and T003.

- [ ] T006 [P] Add two test functions to `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. The functions are:
  - `test_skipped_msp_source_prints_reason_and_excludes_count`: checks the skipped count, its reason, and the organization count that excludes it.
  - `test_skipped_only_profile_writes_no_no_access_row`: checks that a profile with only skipped MSP grants writes the skipped row and no "No accessible organization" row.

  Requirements: FR-007, FR-008, FR-014. Verification: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py`. Status: absent (remote row R23 shows no skipped-source test on `main`). Depends on T004.

## Phase 5: Documentation and release note (User Story 3)

- [ ] T007 [P] Update `documentation/cross-org-subscription-stock.md`. Add the listing right rule after the sentence at main line 22. Add a `skipped` row to the status table after main line 30. Add a bullet to "Failure behavior" after main line 79. Add a Caution about omitted organizations. Requirements: FR-012. Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/cross-org-subscription-stock.md`. Status: absent (remote row R17 shows no `skipped` text on `main`). Depends on T003.

- [ ] T008 [P] Add `changelog.d/issue-4919-msp-listing-right.md`. The file holds one `###` heading and one `Fixed` bullet that names issue 4919. Requirements: FR-013. Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4919-msp-listing-right.md`. Status: absent. Depends on T003.

- [ ] T009 Run the symbol gate on each changed Python file. Verification: `symbol-diff --base origin/main src/mist/intelligence/reports/subscription_expiry/client.py` and `symbol-diff --base origin/main src/mist/intelligence/reports/subscription_expiry/operation.py`. Each command must print `no module-level name changed`. Requirements: SC-004. Status: open. Depends on T004, T005, and T006.

## Phase 6: Delivery

- [ ] T-LOCAL-GATES Paths: the files in the `plan.md` change map. Run each applicable gate from the local gates table on the changed files. Applicable gates: compile, lint, format, types, tests, full tests, coverage, safe sweep, test quality, complexity, security lint, code quality, dead code, docstrings, symbols, and STE. Menu 308 is in the `safe` category, so the safe sweep applies. Not applicable gates: menu reference, dependency audit, ops portal, and ops platform. Reasons appear in `plan.md`. Requirements: SC-004. Verification: `python -m ruff check .`, which must print `All checks passed`. Status: open. Depends on T005, T006, T007, T008, and T009.

- [ ] T-PR Paths: the files in the `plan.md` change map. Commit with the message `fix(subscription-report): skip MSP organization list without listing right` and the body line `Closes #4919`. Push branch `fix/4919-msp-listing-right`. Open the pull request with the same title and `Closes #4919` in the body. List each local gate result from T-LOCAL-GATES in the body. Verification: `python -m py_compile MistHelper.py`, which must print no output. Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI Paths: the files in the `plan.md` change map. Watch the required checks with `gh pr checks <number> --watch`. This remote check is not in the local gates table. The local gate `python -m ruff check .` already passed in T-LOCAL-GATES. Requirements: SC-005. Verification: `gh pr checks <number> --watch`, which must report every required check as passed. Status: open. Depends on T-PR.

- [ ] T-MERGE Paths: the files in the `plan.md` change map. After every required check passes, and after the orchestrator authorizes the merge, add the `auto-merge` label. Verification: `gh pr view <number> --json state,mergedAt`. Status: open. Depends on T-REMOTE-CI.

## Dependencies

- T-000 starts first. T001 depends on T-000. T002 depends on T001. T003 depends on T002.
- T004 depends on T003.
- T005 depends on T002 and T003. T006 depends on T004. T005 and T006 run in parallel.
- T007 and T008 depend on T003. They run in parallel with T005 and T006.
- T009 depends on T004, T005, and T006.
- T-LOCAL-GATES depends on every implementation and documentation task.
- T-PR, T-REMOTE-CI, and T-MERGE run in order.
