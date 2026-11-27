# Specification Analysis Report: Safe Cisco Input and Structured Review

## Result

The specification, plan, tasks, contracts, data model, and research agree on the file layout, the test paths, and the gate list. The change keeps the converter root at five children. It converts `state/intake.py` into a five-child package, as issue 4636 requires for later growth. It adds two routes and one catalog route to the isolated blueprint. It keeps the DNS preview, review, and export shapes unchanged. It adds no Mist call and no shared portal change.

The record finds eleven defects in existing work. Three are high severity. The most serious defect is an exposure path: the shared data browser serves stored inputs under `data/`. Production retention therefore stays disabled until a separate exclusion change lands.

No command ran in this drafting pass. The brief forbids builds, tests, linters, and scripts. The GitHub and Git reads ran in full.

## Metrics

| Measure | Value |
| --- | --- |
| Functional requirements | 22 (FR-001 to FR-022) |
| Success criteria | 8 (SC-001 to SC-008) |
| User stories | 4 (3 at P1, 1 at P2) |
| Tasks | 16 (12 implementation, audit, and guard tasks, and 4 final tasks) |
| Planned test functions | 40 |
| Decisions | 20, none needing a human owner |
| Remote checks | 93 rows in `design/research.md`, section R4 |
| Defects in existing work | 11 |
| Remediation actions | 5 |
| Unresolved items | 8 |

## Defects in Existing Work

| ID | Severity | Location | Summary | Disposition |
| --- | --- | --- | --- | --- |
| E-01 | HIGH | `models.py` lines 56 to 68 (blob `815f4b6b`) | The file-name rule refuses directory parts and drive colons. It accepts control characters and null characters. | Decision D-3. Task T007 adds the refusal. |
| E-02 | MEDIUM | `routes.py` lines 36 and 124. `models.py` line 73. | The 16 MiB bound repeats in three places. A change can miss one. | Decision D-2. Task T007 adds `SOURCE_LIMIT_BYTES`. |
| E-03 | HIGH | `web_portal/services/data_browser.py` lines 138 to 161 (blob `247d4111`) | The shared data browser serves each allowed file under `data/`. It refuses only firmware backups. A stored input under `data/` reaches the browser. | Decision D-11. Remediation R-4. |
| E-04 | MEDIUM | `web_portal/services/output_scan.py` lines 84 to 99 (blob `bf97eb8f`) | The output scan names no converter folder. | Decision D-11. Remediation R-4. |
| E-05 | HIGH | PR #4226 body and state | PR #4226 merged on 2026-10-26. Its body says `Do not merge`. The shared app does not register the converter at `web_portal/app.py` lines 182 to 207. | Issue 4224 stays open. Issues 4633 and 4648 own the integration. Remediation R-5. |
| E-06 | MEDIUM | PR #4226 file list and `main` tree | PR #4226 names `tests/unit/gateway/overrides/test_cisco_config_converter.py`. `main` holds the file at `tests/unit/marvis/mist/resources/gateway/overrides/`. | Use the current path. Issue 4636 item E-12 records the same move. |
| E-07 | MEDIUM | `routes.py` and `conversion.py` (blobs `373138dc` and `2b9c4cee`) | Neither file holds a `#` comment. `models.py` holds one comment at line 46. | Task T011 adds a comment to each touched line. |
| E-08 | MEDIUM | `routes.py` lines 68 to 70 and 117 to 127 | `ConverterRoutes.page` and `ConverterInput.source` hold no log call. `ReviewState` holds none. | Task T011 adds a log before and after each action. |
| E-09 | LOW | `routes.py` lines 28 and 35 | The prefix `/cisco-config-converter/` appears in two places. A rename can miss one. | Task T007 adds a shared constant. |
| E-10 | MEDIUM | Issue 4636 plan, section Replacement Layout | Issue 4636 places five names in `state/intake.py`. This record adds more names. | Decision D-16. Task T004 converts the module. Unresolved item U-1. |
| E-11 | MEDIUM | `tests/e2e/web_portal/` (32 children) | The folder is over the limit. A new file in it would add a child. | This change edits one existing file only. Remediation R-3 from issue 4636. |

## Remediation Actions

These actions track debt that this change does not remove. Each action needs its own issue.

- R-1: `src/interfaces/portals/` holds six children. Group `guest_authorizations.py` under a compliant package. Issue 4636 item R-1 names the same action.
- R-2: `tests/contract/` holds 17 children. Group them in compliant folders. Issue 4636 item R-2 names the same action.
- R-3: `tests/e2e/web_portal/` holds 32 children. Choose a compliant path for new browser tests. Issue 4636 item R-3 names the same action.
- R-4: Exclude the converter private folder from `web_portal/services/data_browser.py` and `web_portal/services/output_scan.py`. File a separate issue before any production enablement of stored inputs.
- R-5: Repair the integration blocker for PR #4226. Issues 4633 and 4648 own the work. Keep issue 4224 open until the integration finishes.

## Unresolved Items

| ID | Owner | Action |
| --- | --- | --- |
| U-1 | Orchestrator | Issue 4636 must merge before task T004. Start T004 only after the merge and repeat the file-map check. |
| U-2 | Reviewer | Confirm the logging reading in decision D-18. Issue 4636 item U-2 asks the same question. Alternatively, adopt `structlog` in both records. |
| U-3 | Implementer | Windows has no `O_NOFOLLOW`. A race can replace a checked file before the open. Keep the checks before and after the open. Record the residual race in the pull request. |
| U-4 | Implementer | Windows may refuse symbolic-link creation in tests. Use the documented fallback. Do not skip the test. |
| U-5 | Implementer | Run the `ste-linter` dictionary check on a local machine. Record the scores in the pull request. |
| U-6 | Implementer | Run `symbol-diff` on the removed `state/intake.py` and cite the result in the pull request. |
| U-7 | Implementer | Run the two browser functions on Windows with `UPGRADE_PORTAL_E2E_STRICT` set to `1`. Record the result. |
| U-8 | Portal owner | Read `ALLOWED_EXTENSIONS` and the data browser route layer before remediation R-4 closes. Research item R12 lists both as unverified. |

## Coverage Summary

Each requirement maps to at least one task and at least one test or gate.

| Requirement | Tasks | Tests or gate |
| --- | --- | --- |
| FR-001 | T006, T007 | `test_catalog_lists_only_contained_supported_files`, `test_inputs_route_lists_catalog_without_paths` |
| FR-002 | T006, T007, T009 | `test_inputs_route_lists_catalog_without_paths`, browser function `test_stored_selection_and_sectioned_review_journey` |
| FR-003 | T005, T007 | `test_supported_suffixes_are_accepted`, `test_unsupported_suffixes_are_refused`, `test_invalid_utf8_is_refused`, `test_empty_or_null_text_is_refused` |
| FR-004 | T005, T007 | `test_exact_size_limit_is_accepted`, `test_one_extra_byte_is_refused_before_decoding` |
| FR-005 | T005, T007 | `test_path_like_and_control_names_are_refused`, `test_client_path_is_never_accepted_as_stored_identifier`, `test_symlink_escape_is_refused_for_stored_selection` |
| FR-006 | T006, T007 | `test_retention_uses_exclusive_creation_and_owner_mode`, `test_retention_refuses_collision_without_overwrite`, `test_preview_collision_keeps_review_revoked` |
| FR-007 | T006, T009 | `test_retention_refused_when_disabled_creates_no_file`, `test_retain_saves_only_when_retention_is_enabled` |
| FR-008 | T006, T007 | `test_retention_refuses_symlinked_or_file_root`, `test_inputs_route_lists_catalog_without_paths` |
| FR-009 | T006, T007 | `test_catalog_reports_only_safe_metadata` |
| FR-010 | T009, T010 | `test_stored_selection_change_revokes_review`, browser function `test_changed_selection_invalidates_sections_and_review` |
| FR-011 | T008, T009 | `test_each_family_reports_its_positive_case`, `test_observation_review_makes_no_socket_or_cloud_call`, `test_observation_output_contains_no_conversion_fields` |
| FR-012 | T008, T009 | `test_unknown_syntax_is_listed_with_line_number`, `test_banner_body_is_unsupported_not_observed` |
| FR-013 | T008, T009 | `test_identity_values_are_omitted`, `test_credential_values_are_omitted` |
| FR-014 | T008, T009 | `test_malformed_mask_and_ambiguous_interface_have_status`, `test_duplicate_directive_has_duplicate_status` |
| FR-015 | T006, T007, T009 | `test_observations_route_requires_csrf_and_keeps_review_state`, `test_existing_export_shape_is_unchanged` |
| FR-016 | T002, T004, T009, T010 | Existing `test_routes.py`, the unit module, `test_existing_export_shape_is_unchanged`, and the existing browser class |
| FR-017 | T006, T007, T011 | `test_logs_omit_source_text_and_original_names`, audit task T011 |
| FR-018 | T012 | Empty `git diff` for `web_portal/app.py` and `web_portal/templates/base.html`, and the move guard |
| FR-019 | T009, T010 | Browser functions `test_stored_selection_and_sectioned_review_journey` and `test_changed_selection_invalidates_sections_and_review` |
| FR-020 | T005, T006, T007 | `test_empty_or_null_text_is_refused`, `test_retention_refuses_collision_without_overwrite`, `test_unknown_or_malformed_identifier_is_refused` |
| FR-021 | T001, T003, T004, T011, T012 | `test_intake_package_stays_within_five_children`, the nested package guard, and audit task T011 |
| FR-022 | T008, T010 | `test_observation_review_makes_no_socket_or_cloud_call`, and synthetic fixtures in every module |

## Success Criteria Coverage

| Criterion | Evidence |
| --- | --- |
| SC-001 | `test_exact_size_limit_is_accepted` and `test_one_extra_byte_is_refused_before_decoding` |
| SC-002 | The count of 40 functions in `tasks.md`, and the run summary in T-LOCAL-GATES |
| SC-003 | `test_observation_review_makes_no_socket_or_cloud_call` |
| SC-004 | `test_each_family_reports_its_positive_case` and `test_each_family_omits_absent_family_items` |
| SC-005 | Existing `test_routes.py`, the unit module with the import change, and `test_existing_export_shape_is_unchanged` |
| SC-006 | Browser functions in `test_portal_smoke.py` with the strict environment variable |
| SC-007 | The coverage command in T-LOCAL-GATES |
| SC-008 | The complexity gate in T011 and the pylint command in T-LOCAL-GATES |

## Consistency Review

| Check | Result |
| --- | --- |
| Issue 4636 decision D-1, five children at the converter root | Pass. The root keeps five children. |
| Issue 4636 decision D-2, tests in the integration folder | Pass. Decision D-17 follows it. |
| Issue 4636 decision D-3, private storage under `data/` | Pass. Stored inputs sit under `data/cisco_config_converter/input/`. |
| Issue 4636 decision D-5, `PORTAL_SECRET_KEY` for state records | Pass. Stored inputs carry no seal and read no secret. |
| Issue 4636 decision D-9, no automatic deletion | Pass. The change deletes no record. A failed save removes only the file that it created. |
| Issue 4636 decision D-13, no route registration and no shared change | Pass. This change adds routes to the isolated blueprint only. |
| Issue 4636 decisions D-10, D-14, and D-15 | Not applicable. This change needs no identity, licensing, or secret decision. |
| PR #4596 task map, paths for T007 to T010 | Changed by decision D-17. Behavior and test counts follow the map. |
| Issue 4224, six suffixes and the 16 MiB limit | Pass. Decisions D-1 and D-2 keep both rules. |
| Issue 4920 reference record, shape | Pass. The folders and headings follow the reference. |
| Issue 4644 decision D-14, a move to `state/records/` | Risk. Issue 4644 proposes that move. Its `state/records/` folder does not conflict with `state/intake/`. A later amendment must keep the intake package. |
| Remote count, research R4 | 93 checks. The STATUS file lists 93. The summary states 93. |
| Task count | 16 tasks in `tasks.md`. The STATUS file and the summary state 16. |
| Test count | 40 functions in `tasks.md` and in SC-002. The STATUS file and the summary state 40. |

## Constitution Alignment

The constitution check in `plan.md` lists thirty rules. Principles VI and VII fail now and pass after task T011. Principle V passes with a reviewer check under decision D-18. Principle I passes at every directory. The record adds no child to a noncompliant parent.

## Validation Commands and Results

| Command | Result |
| --- | --- |
| `python -m py_compile`, `ruff`, `black`, `mypy`, `pytest`, `radon`, `bandit`, `pylint`, `vulture`, `pydocstyle`, `interrogate`, `symbol-diff`, and `ste-linter` | Not run. The drafting rules forbid builds, tests, linters, and scripts in this pass. |
| `gh` reads for issues, pull requests, the API, the tree, and blobs | Run. Results appear in research sections R1 and R4. |
| `git rev-parse`, `git log`, and `git hash-object` | Run as read-only commands. Results appear in research sections R1 and R5. |
| `Select-String` on local copies of the governance documents | Run. Results appear in research section R5 and in the line numbers of R4. |
