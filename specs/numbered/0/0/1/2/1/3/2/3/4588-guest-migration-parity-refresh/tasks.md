# Tasks: Refresh guest migration parity planning

**Input**: `specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity-refresh/`.

**Prerequisites**: [spec](spec.md), [plan](plan.md), [research](design/research.md), [data model](design/data-model.md), [SDK contract](design/contracts/api.md), [portal contract](design/contracts/portal.md), [parity inventory](design/contracts/parity.md), and [E2E contract](design/contracts/e2e.md).

**Tests**: Required. Write each failing test before its behavior. Each test uses fictional data and no live Mist request.

## Conventions

- **Status** values: `open` (not started), `partial` (some evidence exists), `verified-present` (the artifact exists and passes its check), `absent` (the artifact does not exist yet).
- **Verify** names one command from the local gates table in the repository instructions (line 50). The table commands apply to each changed file.
- **[P]** marks a task that can run in parallel with its neighbors. Each such task touches different files.
- `G` means the directory `src/interfaces/portals/guest_authorizations/`.
- Test IDs refer to the [E2E contract](design/contracts/e2e.md).

These 40 migration tasks describe future work. Their status is `absent`, `open`, or `partial`. This planning PR does not deliver any of them. Keep issue #4231 as the full-migration tracker. Keep #4278 open as the workflow child. Create no duplicate issue.

## Phase 1: Setup and decision gates

- **T001** Re-pin source and target before implementation. Requirements: FR-030, FR-032. Paths: `design/research.md`, `design/contracts/parity.md`. Depends on: none. Acceptance: TEST-030 and TEST-032 cite the new commit SHAs, the changed files, and the license notices. Verify: `ste-linter --config .ste-linter.toml --min-score 80 design/research.md`. Status: partial (this record pins `0213240c` and `f03c6c9b`).
- **T002** Record D-6 and D-14 approvals. Requirements: FR-002, FR-007, FR-017, FR-020, FR-021. Paths: `design/research.md`, `design/data-model.md`. Depends on: T001. Acceptance: TEST-020 and TEST-021 have approved options, approvers, and negative cases. Block live reads and writes until approval. Verify: `ste-linter --config .ste-linter.toml --min-score 80 design/research.md`. Status: open. Human approval is required for D-6.
- **T003** [P] Verify D-7, D-8, and D-9 against authoritative evidence. Requirements: FR-011, FR-012, FR-013, FR-014, FR-022, FR-034. Paths: `tests/contract/web_portal/guest_authorizations/test_sdk.py`, `design/contracts/api.md`. Depends on: T001, T007. Acceptance: TEST-011, TEST-012, TEST-013, TEST-014, TEST-022, and TEST-034 cover exact signatures, payloads, 4xx, 429, 5xx, and disabled unsupported behavior. Verify: `python -m pytest tests/contract/web_portal/guest_authorizations/test_sdk.py`. Status: partial (signatures and schema verified, cloud behavior open).
- **T004** [P] Record D-11 CSV bounds and duplicate rules. Requirements: FR-018. Paths: `design/research.md`. Depends on: T001. Acceptance: TEST-018 uses the approved limits at limit minus one, limit, and limit plus one. No import code starts before approval. Verify: `ste-linter --config .ste-linter.toml --min-score 80 design/research.md`. Status: partial (decision recorded, approval open).
- **T005** [P] Record D-12 audit and recovery rules. Requirements: FR-010, FR-024. Paths: `design/research.md`, `design/data-model.md`. Depends on: T001, T002. Acceptance: TEST-024 and TEST-025 define intent, outcome, locking, backup shape, and restart. No write dispatch before approval. Verify: `ste-linter --config .ste-linter.toml --min-score 80 design/data-model.md`. Status: partial.
- **T006** [P] Record D-10 and D-13. Requirements: FR-027, FR-028, FR-034. Paths: `design/research.md`, `design/contracts/e2e.md`. Depends on: T001. Acceptance: TEST-027, TEST-028, and TEST-034 state the difference rules and keep notification off. Verify: `ste-linter --config .ste-linter.toml --min-score 80 design/contracts/e2e.md`. Status: partial.
- **T007** Validate ownership and destinations in `plan.md`. Requirements: FR-025, FR-026 (supports). Paths: `plan.md`, `web_portal/app.py`, `web_portal/templates/base.html`. Depends on: T001. Acceptance: TEST-030 reports the child counts and a compliant destination. PR 4208 closes or the owner hands over the files before any shared edit. Verify: `ste-linter --config .ste-linter.toml --min-score 80 plan.md`. Status: open (PR 4208 is open).
- **T008** Reconcile the shared application, store, and dependencies. Requirements: FR-025, FR-026. Paths: `design/data-model.md`, `plan.md`. Depends on: T001, T007. Acceptance: TEST-025, TEST-026, and TEST-035 propose no source database conversion, no second database, no second service, no second token source, and no downgrade. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_deployment.py`. Status: partial (`compose.yml` and `requirements.txt` are current on main).
- **T009** Preserve projection test evidence before a move. Requirements: FR-029. Paths: `tests/unit/web_portal/guest_authorizations/test_read_model.py`, `tests/unit/web_portal/test_guest_authorization_read_model.py`. Depends on: T007. Acceptance: TEST-029 keeps all 22 cases and the exact three-key shape. The move updates every caller without a shim. Verify: `python -m pytest tests/unit/web_portal/test_guest_authorization_read_model.py`. Status: partial (the 22 cases exist on main, and the move is absent).

## Phase 3: User Story 1, review the selected network (P1)

- **T010** [US1] Write route and navigation tests in `tests/integration/web_portal/guest_authorizations/test_review.py`. Requirements: FR-001, FR-026. Depends on: T002, T006, T007, T008. Acceptance: TEST-001 and TEST-026 fail before the wiring exists. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_review.py`. Status: absent.
- **T011** [US1] Add the blueprint and the navigation entry in `G/web/routes/review.py`, `web_portal/app.py`, and `web_portal/templates/base.html`. Requirements: FR-001. Depends on: T010, T013. Acceptance: TEST-001 and TEST-027 keep the shared chrome and the exact scope. No live data appears before D-6 and the read contracts pass. Verify: `python -m ruff check .`. Status: absent.
- **T012** [US1] Implement connection, site and WLAN discovery, filtering, and scope invalidation in `G/services/api_client.py` and `G/web/routes/review.py`. Requirements: FR-002, FR-003, FR-004, FR-033. Depends on: T002, T003, T010, T013, T019. Acceptance: TEST-002, TEST-003, and TEST-004 reject implicit organization selection, unrelated organization WLANs, failed assignments, and stale results. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_review.py`. Status: absent.
- **T013** [US1] Move the offline projection to `G/domain/read_model.py`. Add `G/domain/scope.py` and `G/domain/validation.py`. Remove the old module and update each caller. Requirements: FR-005, FR-006, FR-029. Depends on: T008, T009. Acceptance: TEST-005, TEST-006, and TEST-029 keep the public shape and the unknown-value rules. Run the repository move gates. Verify: `symbol-diff --base origin/main src/interfaces/portals/guest_authorizations.py`. Status: partial (the module exists at the old path).
- **T014** [US1] Implement guest cards, statistics, search, refresh, and empty states in `G/web/templates/page.html` and `G/web/static/review.js`. Requirements: FR-005, FR-006, FR-007, FR-033. Depends on: T002, T006, T011, T012. Acceptance: TEST-005, TEST-006, TEST-007, and TEST-033 cover every approved field, stable order, time boundaries, keyboard access, and the true-empty state. Verify: `python -m pytest tests/unit/web_portal/guest_authorizations/test_read_model.py`. Status: absent.
- **T015** [US1] Complete review integration and browser acceptance in `tests/e2e/web_portal/guest_authorizations/test_review.py`. Requirements: FR-001, FR-005. Depends on: T014, T029. Acceptance: TEST-001 through TEST-007 and TEST-033 use deterministic fixtures, stable selectors, zero writes, and retained failure evidence. Verify: `python -m pytest tests/e2e/web_portal/guest_authorizations/test_review.py`. Status: absent.

## Phase 4: User Story 2, grant, edit, extend, and revoke (P2)

- **T016** [US2] [P] Write validation, creation, and extension tests in `tests/unit/web_portal/guest_authorizations/test_validation.py` and `tests/contract/web_portal/guest_authorizations/test_mutations.py`. Requirements: FR-009, FR-010, FR-011, FR-012, FR-013. Depends on: T002, T003, T007. Acceptance: TEST-009 through TEST-013 and TEST-022 cover every preset, malformed value, read-only field, and the absence of an implicit default. Verify: `python -m pytest tests/contract/web_portal/guest_authorizations/test_mutations.py`. Status: absent.
- **T017** [US2] [P] Implement the add dialog in `G/web/templates/add.html` and `G/web/static/changes.js`. Requirements: FR-009, FR-010, FR-034. Depends on: T006, T010, T016, T020. Acceptance: TEST-009, TEST-010, TEST-011, and TEST-034 keep the device, detail, and client relationships. Unsupported fields are disabled. No dispatch path is enabled until T018 and T024 pass. Verify: `python -m ruff check .`. Status: absent.
- **T018** [US2] Implement reviewed-change access and typed confirmation in `G/domain/scope.py` and `G/services/mutations.py`. Requirements: FR-020, FR-021. Depends on: T002, T003, T005, T013, T016, T030. Acceptance: TEST-020 and TEST-021 bind actor, action, scope, payload, observation, and revision. A wrong, canceled, repeated, stale, or denied confirmation sends zero writes. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_changes.py`. Status: absent.
- **T019** [US2] Write and implement exact-site read and search contracts in `tests/contract/web_portal/guest_authorizations/test_reads.py` and `G/services/api_client.py`. Requirements: FR-003, FR-008, FR-022. Depends on: T002, T003, T007, T013. Acceptance: TEST-003, TEST-008, and TEST-022 verify client statistics, pages, explicit arguments, status checks, bounded read retries, and no organization fallback. Verify: `python -m pytest tests/contract/web_portal/guest_authorizations/test_reads.py`. Status: absent.
- **T020** [US2] Implement connected-client search and selection in `G/web/static/clients.js`. Requirements: FR-008, FR-012. Depends on: T010, T019. Acceptance: TEST-008 and TEST-012 cover MAC, hostname, IP, and SSID matching, two-character guidance, debounce, stale results, selection, and read-only names. Verify: `python -m ruff check .`. Status: absent.
- **T021** [US2] Integrate the confirmed grant and the safe result refresh in `G/web/routes/changes.py`. Requirements: FR-009, FR-033. Depends on: T017, T018, T024, T029. Acceptance: TEST-009, TEST-021, TEST-023, and TEST-033 perform one exact-scope write, validate the observed result, and separate failure from unknown. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_changes.py`. Status: absent.
- **T022** [US2] Implement supported edit and extension in `G/web/templates/edit.html` and `G/web/routes/changes.py`. Requirements: FR-010, FR-011, FR-012, FR-013. Depends on: T016, T018, T024, T029. Acceptance: TEST-010 through TEST-013 keep the MAC fixed, explain the duration origin, and never turn a detail edit into an unreviewed extension. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_changes.py`. Status: absent.
- **T023** [US2] Implement verified revoke in `G/services/mutations.py` and `G/web/routes/changes.py`. Requirements: FR-014. Depends on: T003, T018, T024, T029. Acceptance: TEST-014 and TEST-022 cover cancel, denial, exact-scope delete or an approved alternative, an ineffective 2xx response, timeout, and unknown result. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_changes.py`. Status: absent.
- **T024** [US2] Implement shared dispatch, outcome, and reconciliation in `G/services/mutations.py`. Requirements: FR-014, FR-021, FR-022, FR-023, FR-024. Depends on: T003, T005, T016, T018, T030. Acceptance: TEST-021 through TEST-024 never retry an ambiguous write, never broaden the scope, and never invent a success or an expiry. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_changes.py`. Status: absent.

## Phase 5: User Story 3, CSV review and import (P2)

- **T025** [US3] [P] Write parser and template tests, and implement `G/services/imports.py`. Requirements: FR-011, FR-015, FR-016, FR-018. Depends on: T003, T004, T007, T016. Acceptance: TEST-015, TEST-016, and TEST-018 cover the ten headers, aliases, and two fictional examples. They also cover quoting, newlines, BOM and CRLF, formula text, invalid rows, and the D-11 limits. Every input row is reported. Verify: `python -m pytest tests/unit/web_portal/guest_authorizations/test_imports.py`. Status: absent.
- **T026** [US3] Implement unambiguous scope and duplicate validation in `G/services/imports.py`. Requirements: FR-016, FR-017, FR-018. Depends on: T002, T003, T004, T012, T025. Acceptance: TEST-016 through TEST-018 resolve IDs within scope, reject ambiguous names, follow the approved duplicate rule, and bind the file and map revision. Verify: `python -m pytest tests/contract/web_portal/guest_authorizations/test_imports.py`. Status: absent.
- **T027** [US3] Implement the download, file selection, bounded preview, errors, and batch confirmation in `G/web/templates/import.html` and `G/web/routes/imports.py`. Requirements: FR-015, FR-016, FR-017, FR-019, FR-033. Depends on: T006, T010, T018, T025, T026, T029. Acceptance: TEST-015 through TEST-017, TEST-019, TEST-021, and TEST-033 keep the first-five preview and the full row accounting. Replacing a file invalidates the confirmation. Verify: `python -m pytest tests/e2e/web_portal/guest_authorizations/test_imports.py`. Status: absent.
- **T028** [US3] Implement bounded batch dispatch, progress, outcomes, cancel, and recovery in `G/services/imports.py`. Requirements: FR-018, FR-019, FR-021. Depends on: T004, T005, T024, T026, T027, T030. Acceptance: TEST-018, TEST-019, TEST-021, and TEST-023 separate success, rejection, unknown, invalid, duplicate, and unstarted rows. No blind replay and no hidden partial success. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_imports.py`. Status: absent.

## Phase 6: User Story 5, shared operation and recovery (P3)

- **T029** [US5] Implement safe state and error reporting in `G/web/routes/review.py`, `G/web/static/review.js`, and `tests/integration/web_portal/guest_authorizations/test_errors.py`. Requirements: FR-004, FR-023, FR-033. Depends on: T002, T003, T010, T013. Acceptance: TEST-023 and TEST-033 separate unavailable, invalid, denied, stale, rejected, rate-limited, unknown, and empty results. External values are escaped. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_errors.py`. Status: absent.
- **T030** [US5] Implement approved audit intent, outcome, and recovery in `G/services/audit.py` and `tests/integration/web_portal/guest_authorizations/test_audit.py`. Requirements: FR-010, FR-024, FR-025. Depends on: T005, T007, T008, T013. Acceptance: TEST-024 and TEST-025 cover durable writes, retention, redaction, locking, failures before and after dispatch, and restart. No second store. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_audit.py`. Status: absent.
- **T031** [US5] Integrate health, configuration, dependency, and deployment acceptance in `tests/integration/web_portal/guest_authorizations/test_deployment.py`. Requirements: FR-025, FR-026, FR-035. Depends on: T007, T008, T011, T030. Acceptance: TEST-025, TEST-026, and TEST-035 add zero applications, databases, and Compose groups. The health check, ports, session ownership, and required status names stay intact. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_deployment.py`. Status: absent.

## Phase 7: User Story 4, visual and functional parity (P1)

- **T032** [US4] [P] Write paired scenario fixtures in `tests/e2e/web_portal/guest_authorizations/conftest.py` and update `design/contracts/e2e.md`. Requirements: FR-027, FR-030. Depends on: T001, T006, T007. Acceptance: TEST-027 and TEST-030 freeze the clock, viewport, theme, locale, time zone, fonts, and data digests. Live sessions and unlisted external requests fail. Verify: `python -m pytest tests/e2e/web_portal/guest_authorizations/conftest.py`. Status: absent.
- **T033** [US4] Implement functional browser and accessibility assertions in `tests/e2e/web_portal/guest_authorizations/test_workflows.py`. Requirements: FR-028, FR-034. Depends on: T015, T021, T022, T023, T028, T031, T032. Acceptance: TEST-008 through TEST-028, TEST-033, and TEST-034 cover each control, state, selector, keyboard action, focus, label, and announcement. Verify: `python -m pytest tests/e2e/web_portal/guest_authorizations/test_workflows.py`. Status: absent.
- **T034** [US4] Capture and compare each VIS-001 through VIS-015 pair in `tests/e2e/web_portal/guest_authorizations/test_visual.py`. Requirements: FR-027, FR-028. Depends on: T006, T032, T033. Acceptance: TEST-027 and TEST-028 compare the declared viewports and the approved difference regions. Keep the screenshots, hashes, traces, and comparator results. Do not claim target parity without evidence. Verify: `python -m pytest tests/e2e/web_portal/guest_authorizations/test_visual.py`. Status: absent.

## Phase 8: Cross-cutting release and operator approval

- **T035** Run the applicable gates for the feature file set and record the exact results in `design/quickstart.md`. Requirements: FR-030, FR-035. Depends on: T015, T021, T022, T023, T028, T031, T033, T034. Acceptance: TEST-030 and TEST-035 cover unit, contract, integration, browser, lint, types, format, complexity, security, docstrings, the projection move, routing, hierarchy, and the existing portal regressions. Skipped or stale checks never count as passed. Verify: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`. Status: absent.
- **T036** Write the integrated operator guide in `documentation/guest-authorizations.md`, the README links, and one unique fragment in `changelog.d/`. Requirements: FR-031, FR-032. Depends on: T021, T022, T023, T028, T031, T034. Acceptance: TEST-031 and TEST-032 document the supported contracts, the approved deviations, the source credit, the license notices, and the noncommercial and share-alike terms. Do not invent a relicense. Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/guest-authorizations.md`. Status: absent.
- **T037** Audit traceability in `analysis.md` and `design/contracts/parity.md`. Requirements: FR-030. Depends on: T035, T036. Acceptance: TEST-030 gives measured row, requirement, task, and test counts. It reports zero missing dispositions, zero unmapped requirements, and the actual gate status. Verify: `ste-linter --config .ste-linter.toml --min-score 80 analysis.md`. Status: partial (this record holds the coverage table).
- **T038** Perform the final original-versus-target review in `design/contracts/parity.md` and `design/contracts/e2e.md`. Requirements: FR-027, FR-030. Depends on: T034, T037. Acceptance: TEST-027 and TEST-030 record each row's executed result and each approved difference against exact commits. Missing or unverified evidence blocks approval. Verify: `ste-linter --config .ste-linter.toml --min-score 80 design/contracts/parity.md`. Status: absent.
- **T039** Rehearse cutover, private backup verification, restart, and return to the offline mode in `design/quickstart.md`. Requirements: FR-031, FR-035. Depends on: T005, T031, T035, T036, T038. Acceptance: TEST-024, TEST-025, TEST-031, and TEST-035 prove the approved backup shape and preserve other data. No live cloud change happens without an exact user authorization. Verify: `python -m pytest tests/integration/web_portal/guest_authorizations/test_deployment.py`. Status: absent.
- **T040** Obtain operator release approval in `design/quickstart.md` and in the implementation PR for #4231. Requirements: FR-031, FR-035. Depends on: T002, T003, T004, T005, T006, T037, T038, T039. Acceptance: TEST-031 and TEST-035 record the approvals, the functional and visual evidence, the revision, the recovery result, and the open limits. A planning PR is not release approval. Verify: `ste-linter --config .ste-linter.toml --min-score 80 design/quickstart.md`. Status: absent.

## Planning tasks for this PR

- **T-LOCAL-GATES** Run each gate in [quickstart section 5](design/quickstart.md#5-planning-gates-for-this-record) on the record files and the changelog fragment. Requirements: FR-030. Paths: the record folder and `changelog.d/issue-4588-guest-migration-parity-refresh.md`. Depends on: T001 through T009. Acceptance: each gate prints its exact result. Each file scores 80 or above on STE. The citation, link, and task-audit results are recorded, including any failure. Verify: `ste-linter --config .ste-linter.toml --min-score 80 <each Markdown file>`. Status: open. This run did not run the gates (brief rule 2).
- **T-PR** Commit the planning files with the Conventional Commits title `docs(spec): refresh guest migration parity planning`. Push the branch `docs/4588-guest-migration-parity-refresh`. Open one pull request. Requirements: FR-030. Paths: the record folder and the changelog fragment only. Depends on: T-LOCAL-GATES. Acceptance: the pull request body contains `Closes #4588` as the brief requires. It names #4231 and #4278 with non-closing references. The commit carries the Co-authored-by trailer. Verify: `ste-linter --config .ste-linter.toml --min-score 80 <each Markdown file in the PR>`. Status: open. Warning: merging this pull request with its closing keyword closes #4588 (analysis F12).
- **T-REMOTE-CI** Watch the remote checks for the pull request. Requirements: FR-030. Paths: none. Depends on: T-PR. Acceptance: every required check reports success on the head commit. A skipped or canceled required check counts as unresolved. Verify: `gh pr checks <number> --watch`. This command is the AGENTS.md pull request rule. No local gate row applies. Status: open.
- **T-MERGE** Enable auto-merge only after T-REMOTE-CI passes and the orchestrator authorizes the merge. Requirements: FR-035. Paths: none. Depends on: T-REMOTE-CI. Acceptance: the squash commit keeps one planning change. The branch is removed after the merge. No implementation task starts. Verify: `ste-linter --config .ste-linter.toml --min-score 80 <each Markdown file on the head commit>`. Status: open. Caution: enabling auto-merge without owner review may close #4588 before the owner finishes review.

## Requirement coverage

| Requirement | Task IDs | Acceptance family |
| --- | --- | --- |
| FR-001 | T010, T011, T015 | TEST-001 |
| FR-002 | T002, T012 | TEST-002 |
| FR-003 | T012, T019 | TEST-003 |
| FR-004 | T012, T029 | TEST-004 |
| FR-005 | T013, T014, T015 | TEST-005 |
| FR-006 | T013, T014 | TEST-006 |
| FR-007 | T002, T014 | TEST-007 |
| FR-008 | T019, T020 | TEST-008 |
| FR-009 | T016, T017, T021 | TEST-009 |
| FR-010 | T005, T016, T017, T022, T030 | TEST-010 |
| FR-011 | T003, T016, T022, T025 | TEST-011 |
| FR-012 | T003, T016, T020, T022 | TEST-012 |
| FR-013 | T003, T016, T022 | TEST-013 |
| FR-014 | T003, T023, T024 | TEST-014 |
| FR-015 | T025, T027 | TEST-015 |
| FR-016 | T025, T026, T027 | TEST-016 |
| FR-017 | T002, T026, T027 | TEST-017 |
| FR-018 | T004, T025, T026, T028 | TEST-018 |
| FR-019 | T027, T028 | TEST-019 |
| FR-020 | T002, T018 | TEST-020 |
| FR-021 | T002, T018, T024, T028 | TEST-021 |
| FR-022 | T003, T019, T024 | TEST-022 |
| FR-023 | T024, T029 | TEST-023 |
| FR-024 | T005, T024, T030 | TEST-024 |
| FR-025 | T008, T030, T031 | TEST-025 |
| FR-026 | T008, T010, T031 | TEST-026 |
| FR-027 | T006, T032, T034, T038 | TEST-027 |
| FR-028 | T006, T033, T034 | TEST-028 |
| FR-029 | T009, T013 | TEST-029 |
| FR-030 | T001, T032, T035, T037, T038 | TEST-030 |
| FR-031 | T036, T039, T040 | TEST-031 |
| FR-032 | T001, T036 | TEST-032 |
| FR-033 | T012, T014, T021, T027, T029 | TEST-033 |
| FR-034 | T003, T006, T017, T033 | TEST-034 |
| FR-035 | T031, T035, T039, T040 | TEST-035 |

Each functional requirement maps to at least one task and one test family. The count is 35 requirements, 40 migration tasks, four planning tasks, and 35 test families.

## Dependencies and execution order

- The explicit `Depends on` lists define the graph. They do not follow task number order.
- T007 precedes T003 because contract tests need an approved destination.
- T030 precedes T018. T018 precedes T024. T024 precedes each dispatch integration.
- T019 precedes T012 and T020.
- Read-only work still passes its own access and contract gates.
- T032 and T034 need target screens. They cannot finish before implementation.
- The planning tasks run in order: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.

## Parallel opportunities

- After T001, the decision tasks T004, T005, and T006 can run in parallel. Each writes different sections of the research file, so keep their evidence separate.
- After T024, CSV unit work (T025) can run in parallel with edit and revoke integration.
- After T032, source capture and target accessibility review can run in parallel on separate evidence outputs.
- Do not assign two agents the same file or the same shared integration surface.

## Implementation strategy

First, approve D-5, D-6, and the planning gates. Then implement the offline projection move with its 22 tests. Next add read-only review. Add grant, edit, and extension only after D-14 and the audit store pass. Add CSV import last. Finish with paired visual review, regressions, documentation, recovery rehearsal, and operator approval.
