# Analysis: Ship the preserved admission scope work

This review checks the consistency of `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, and the remote code. It lists the defects in the preserved work, the gaps in the gate evidence, and the unresolved items.

## Consistency Review

| Check | Result |
|-------|--------|
| Requirement count | 29 requirements (FR-001 to FR-029) in `spec.md`. `tasks.md` covers each one. |
| Task count | 17 tasks: T001 to T013 and the four final tasks. |
| Test count | 12 test functions in the two changed modules. Six exist on the branch. Six are new. Three main tests stay unchanged: `test_ledger_hashes_auth_and_counts_org`, `test_missing_authentication_is_rejected`, and `test_site_request_requires_organization_context`. |
| Decision count | 13 decisions (D-1 to D-13). None needs a human decision. |
| Remote check count | 52 rows in `design/research.md` and 52 entries in `remote_checks` of the status file. The summary states the same count. |
| Task numbering | `plan.md` cited earlier task numbers. This pass corrected those references to the numbering of `tasks.md`: the repairs are T008 to T011, the tests are T005 and T006, the red run is T007, the operator guide is T012, and the changelog is T013. |
| Test names | Each new test name is identical in `spec.md`, `plan.md`, and `tasks.md`. |
| Record folder limits | The record root holds five children. The `design` folder holds five children. The `contracts` and `checklists` folders hold three files each. |

## FR Traceability

| FR | Task | Test or verification |
|----|------|----------------------|
| FR-001 | T001, T003 | Blob equality (T001). Branch name check (T003). |
| FR-002 | T002 | `gh pr view 4208` state check. |
| FR-003 | T-MERGE | Branch ref check after the merge. |
| FR-004 | T008 | `test_site_request_uses_the_scoped_organization` |
| FR-005 | T008 | `test_site_request_requires_organization_context`, `test_organization_scope_ends_with_its_block` |
| FR-006 | T005, T008 | `test_organization_scope_resets_after_exception` |
| FR-007 | T005, T008 | `test_nested_organization_scope_restores_outer_value` |
| FR-008 | T005, T008 | `test_organization_scope_rejects_empty_identifier` |
| FR-009 | T008 | `test_ledger_hashes_auth_and_counts_org` |
| FR-010 | T008 | `test_credential_never_appears_in_exception_locals`, `test_ledger_hashes_auth_and_counts_org` |
| FR-011 | T008 | `test_missing_authentication_is_rejected` |
| FR-012 | T009 | `test_console_renderer_hides_frame_locals` |
| FR-013 | T005, T009 | `test_console_renderer_output_has_no_ansi_on_non_terminal` |
| FR-014 | T011 | `test_virtual_chassis_read_is_admitted_under_its_organization` |
| FR-015 | T011 | `test_failed_msp_listing_logs_one_outcome_and_no_sdk_error_lines` (403 and 500) |
| FR-016 | T010, T011 | `test_failed_msp_listing_logs_one_outcome_and_no_sdk_error_lines` |
| FR-017 | T010, T011 | The filter removal assertion in `test_failed_msp_listing_logs_one_outcome_and_no_sdk_error_lines` |
| FR-018 | T011 | `test_transport_failure_keeps_the_client_error_line` |
| FR-019 | T011 | The failure row assertion in `test_failed_msp_listing_logs_one_outcome_and_no_sdk_error_lines` |
| FR-020 | T011 | `test_msp_listing_logs_info_before_and_debug_after` |
| FR-021 | T008, T010, T011 | Top-level name count in `design/quickstart.md`, step 6. |
| FR-022 | T005 | `test_credential_never_appears_in_exception_locals` with the type check at line 141 |
| FR-023 | T-LOCAL-GATES, T-REMOTE-CI | Gate rows in `design/checklists/gates.md`. |
| FR-024 | T007 | Red run: three failures expected, and three regression guards pass. |
| FR-025 | T-LOCAL-GATES | `tests/integration/test_mistapi_sdk_compatibility.py` |
| FR-026 | T012 | STE gate on `documentation/operator-guide.md`, and a search for the phrase. |
| FR-027 | T013 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-028 | T-PR | Pull request body and title check. |
| FR-029 | T004 | `git show --stat` of the first commit. |

## Defects in Existing Work

| ID | Finding | Evidence | Severity | Fix task |
|----|---------|----------|----------|----------|
| A-1 | The traceback formatter writes ANSI escape sequences to non-terminal streams. The explicit `truecolor` bypasses the monochrome switch. | `logger_utils.py:152` (branch). Structlog switches only the default formatter (`structlog/dev.py:713-714`). Rich writes styles when a color system is set (`rich/console.py:707-712` and `:2136-2144`). | Medium | T009 |
| A-2 | `request_admission.py` holds seven top-level names, and `client.py` holds nine. | Branch name counts. Limit: five per module (constitution Principle I). | Medium | T008, T010, T011 |
| A-3 | The branch adds module-level functions with state: `organization_scope`, `_credential_fingerprint`, `_authentication_header`, and `_sdk_error_lines_muted`. | Constitution Principle II requires classes. | Medium | T008, T010, T011 |
| A-4 | The MSP organization list call has no info line before it and no debug line after it. | `client.py:170` on main. Constitution Principle VII. | Medium | T011 |
| A-5 | The admission test ends with `assert frame is not None`, which the test quality ratchet flags as `weak_is_not_none`. | `test_request_admission.py:141` (branch). Issue #4943 comment. | Low | T005 |
| A-6 | `organization_scope` accepts an empty identifier. The scope then sets an empty value, and the ledger fails later with a message that names no organization. | `organization_scope` (branch) has no check. Constitution Principle III requires early validation. | Medium | T005, T008 |
| A-7 | The operator guide says that a denied MSP list "uses one organization". The code says that the report continues with direct organizations. | `documentation/operator-guide.md:502` (main) and `client.py:191-194` (branch). | Low | T012 |
| A-8 | The frame-locals test checks text only, and pytest captures a non-terminal stream. The test cannot detect ANSI escape sequences. | `test_console_renderer_hides_frame_locals` (branch). | Medium | T005 adds TN4 |
| A-9 | PR #4208 changes the same two files, and it moves the admission test. The branch cannot merge into the open PR without a port. | RC-43, RC-44, RC-45. The compare of main with 843be63b reports diverged, 33 ahead, and 82 files. | High | T002, T008, R-1, R-2 |
| A-10 | The issue comment reports the gate results for the five files, and the list omits several gates. | See the gate review below. | Medium | T-LOCAL-GATES |
| A-11 | The branch base `ccff03e05` is one commit behind `main`. The one commit (PR #4941) changes none of the five files. | The compare of ccff03e05 with main reports ahead by 1, 31 files, and no overlap. | Low | T003 uses `main` as the base |

## Gate Review

The issue comment reports these gates on the five files:

- `py_compile` on three sources.
- `ruff check` and `black --check` on five files.
- `mypy`, `bandit`, the complexity gate at 10, and `pydocstyle` on three sources.

The comment also reports the tests of the two changed modules, with 985 passed and 2 skipped. It reports the test quality gate against `main` with one new finding.

The local gates table in `.github/copilot-instructions.md:50` names more gates. The issue comment does not report these rows:

- Pylint with threshold 9.5 (`.github/workflows/ci.yml:122`).
- Vulture with confidence 70 (`ci.yml:101`).
- Interrogate with threshold 90 (`ci.yml:107`).
- The full test suite and the coverage run with threshold 80.
- The guardrail tests, which include the changelog guard.
- The safe sweep with `python MistHelper.py --test`.
- The symbol gate, which reports the names that move into classes.
- The mistapi SDK compatibility test.
- The STE gate on each changed Markdown file.
- The menu reference gate, which needs no run, because the change edits no registry row.
- The dependency audit, which needs no run, because the change edits no requirement.

`T-LOCAL-GATES` runs each row. The ship step records each result.

## Remote and Branch State

- The preservation branch holds the five files byte for byte. The local files and the branch blobs match (T001, RC-46 to RC-50).
- `main` moved from `ccff03e05` to `f03c6c9b`. The issue body and comment name the older commit. The change starts from `f03c6c9b` or from a later `main` commit (T003).
- PR #4208 is a draft, and its base is `2a6a5844`. Its head holds the admission code without the scope (RC-43). Its head moved the admission test (RC-44, RC-45).
- The branch has no pull request. A search with `--head` returned no pull request (`gh pr list --head chore/4943-preserve-wip-2026-11-24`).

## Drift Outside This Change

- `documentation/architecture.md:202-207` lists an `api/` directory under `src/`. The directory does not exist on main (RC-25, RC-26). Record for the owner (RA-4).
- `pyproject.toml:29` requires `mistapi>=0.64.1,<0.65`. The repository guide states `mistapi>=0.64.0,<0.65`. The requirements file pins `mistapi==0.64.1` (RC-37, RC-40). Record for the owner (RA-5).
- The issue body names a copy of `client.py` in a sibling worktree. That copy lies outside the repository, so this record does not compare it (U-2).

## Observations

- O-1: The VC test asserts that `admitted` equals `["org-one"]`. That assertion checks the caller argument, not the scope. The test detects a missing scope through the raised `ConnectionError`, so the test stays valid.
- O-2: Shared admission runs only with Redis (`request_admission.py:44-53` on main, and `initialize_mist_session.py:72-73`). Unit tests need the fake ledger to exercise the defect.
- O-3: The organization scope does not apply when the ledger holds an organization. This matches FR-009 and the existing attribution order.
- O-4: The MSP organization list path uses `msps` in the URL, so the scope does not apply to it (`documentation/mist-api-openapi31yaml.yaml:4081`).
- O-5: The safe sweep runs menu 308, because the registry lists it as `safe` (`operation_registry.py:536`). Without a token, the sweep skips the Mist checks with a credential reason.
- O-6: A transport failure shows `HTTP 0` in the failure row. The expression that builds the error text in `_discover_msp` returns that text for every status that is not None. The change keeps that expression, so the text stays as it is on main (`design/data-model.md`, section Observation).

## Unresolved Items

- UR-1: The owner decides the disposition of PR #4208: merge it, release the two files, or close it. T002 waits for that decision.
- UR-2: The owner opens follow-up issues for RA-1 to RA-5 and for decision D-5 after the merge.
- UR-3: An operator runs menu 308 with a real token after the merge (decision D-13). Unit tests do not cover live output.
- UR-4: The owner decides when to delete the preservation branch (decision D-11).
- UR-5: The ship step reproduces the gate results that the issue comment reports (U-1).
- UR-6: The unverified items U-2 to U-9 in `design/research.md` stay open until the ship step or the owner closes them.
- UR-7: The owner corrects the failure row text for a transport failure, which reads `HTTP 0` (observation O-6). The correction changes an operator-visible string, so it needs its own issue.
