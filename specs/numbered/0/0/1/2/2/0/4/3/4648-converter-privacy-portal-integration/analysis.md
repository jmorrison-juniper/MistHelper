# Specification Analysis Report: Converter Privacy and Shared Portal Integration

## Result

The spec, plan, tasks, data model, contracts, and research agree on scope, paths, and gates. The integration splits into two phases. Phase A adds offline tests and edits no shared file. Phase B edits the two shared files only after the G3 handover and the prerequisite issues close.

The record finds fourteen defects in existing work. Five are high severity. Fifteen decisions appear in `design/research.md`. One decision needs a human owner (D-9).

Nothing was executed in this drafting pass. The repository rules forbid tests, linters, and builds in this pass. The read-only checks in `design/research.md` ran against GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Metrics

| Measure | Value |
| - | - |
| Functional requirements | 20 (FR-001 to FR-020) |
| Success criteria | 8 (SC-001 to SC-008) |
| User stories | 3 (2 at P1, 1 at P2) |
| Tasks | 18 (14 implementation tasks and 4 final tasks) |
| Planned test functions | 28 (32 cases) |
| Decisions | 15, of which 1 needs a human owner (D-9) |
| Remote checks | 94 rows in `design/research.md`, section Remote Verification |
| Defects in existing work | 14 (5 high, 6 medium, 3 low) |
| Unresolved items | 6 (U-1 to U-6) |

## Coverage Summary

Each requirement maps to at least one task and at least one test. The existing tests and guards cover FR-015, FR-018, and FR-019.

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T002, T003, T007, T012 | `test_health_reply_keeps_exact_shape`, `test_other_upload_routes_keep_flask_limits` |
| FR-002 | T003 | `test_health_reply_keeps_exact_shape`, `test_ready_reply_unchanged_with_converter` |
| FR-003 | T004 | `test_converter_post_without_token_returns_400` |
| FR-004 | T004 | `test_json_client_gets_csrf_expired_answer`, `test_html_client_gets_html_csrf_answer`, `test_api_prefix_keeps_json_csrf_answer` |
| FR-005 | T005 | `test_error_bodies_hide_traceback_and_source`, `test_oversize_converter_body_returns_413` |
| FR-006 | T005 | `test_debug_off_in_real_factory`, `test_container_runner_forces_debug_false` |
| FR-007 | T006 | `test_logs_omit_source_name_and_secret`, `test_session_holds_digest_only` |
| FR-008 | T006 | `test_converter_package_imports_no_network_module`, `test_offline_journey_opens_no_socket` |
| FR-009 | T008, T014 | `test_comparison_rows_have_dispositions`, `test_every_row_links_test_or_task` |
| FR-010 | T002, T006, T014 | `test_logs_omit_source_name_and_secret` |
| FR-011 | T001, T008 | `test_handover_state_matches_shared_files` |
| FR-012 | T007, T008, T009 | `test_registration_refused_without_request_class`, `test_handover_state_matches_shared_files` |
| FR-013 | T010, T011 | `test_nav_entry_opens_converter_in_real_portal` |
| FR-014 | T011 | `test_upload_preview_review_export_in_real_portal`, `test_invalid_upload_shows_safe_error` |
| FR-015 | T012 | Existing: `tests/e2e/web_portal/test_portal_smoke.py`, `tests/integration/web_portal/cisco_config_converter/test_routes.py` |
| FR-016 | T007 | `test_route_allowlist_has_no_cloud_write_route` |
| FR-017 | T007 | `test_compose_has_no_converter_service` |
| FR-018 | T-LOCAL-GATES | Existing: `tests/guardrails/test_nested_package_structure.py` |
| FR-019 | T013 | Existing: `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-020 | T011 | `test_evidence_path_stays_under_test_artifacts` |

## Success Criteria Coverage

| Criterion | Tasks | Evidence |
| - | - | - |
| SC-001 | T002 to T008 | Pytest reports the case count for `test_parity.py` (28 cases) |
| SC-002 | T001, T008 | `test_handover_state_matches_shared_files` |
| SC-003 | T009 | Health and ready tests after the registration |
| SC-004 | T011 | `test_evidence_path_stays_under_test_artifacts` and the browser failure branch |
| SC-005 | T008, T014 | Matrix guards |
| SC-006 | T006 | `test_logs_omit_source_name_and_secret` |
| SC-007 | T012 | Pass counts recorded before and after the integration |
| SC-008 | T007 | `test_route_allowlist_has_no_cloud_write_route` |

## Consistency Review

- The plan's file table lists the same paths as the task list. Each path appears in one phase only.
- The Phase B dependencies match the prerequisites in issue #4648. They also match the live dependency rows for T031 and T032 (live `tasks.md` lines 155 and 156).
- The decisions D-1 to D-15 in `design/research.md` match the decision list in the STATUS file. The human flag appears on D-9 only.
- The remote checks R-01 to R-94 in `design/research.md` match the `remote_checks` array in the STATUS file. The summary repeats the count of 94.
- The browser module path `tests/integration/web_portal/cisco_config_converter/test_portal_browser.py` appears in the spec, the plan, the tasks, the contracts, and the quickstart. No other browser path appears.
- Each test name appears once in the tasks and once in the test plan summary.

## Defects in Existing Work

| ID | Severity | Location | Summary | Disposition |
| - | - | - | - | - |
| E-01 | HIGH | `web_portal/app.py` and `web_portal/templates/base.html`. Live `tasks.md` line 113, and parent `tasks.md` line 51. PR #4208 is OPEN. | Open PR #4208 owns both shared files. A registration edit now would conflict with it. | D-3. T009 and T010 wait for the handover and PR #4208. |
| E-02 | HIGH | Live `tasks.md` line 104 names `tests/e2e/web_portal/test_cisco_parity.py`. Remote folder `tests/e2e/web_portal` holds 32 children (R-26). | The constitution bars a new direct child in a noncompliant parent. | D-4. This record uses the feature folder. Issue #4647 must align (U-3). |
| E-03 | HIGH | `web_portal/app.py` sets no request class (R-30). `routes.py` lines 105 to 106 raise `ValueError` without it. | Registration fails until the portal sets `ConverterRequest`. | D-7. T009 sets the class before registration. |
| E-04 | HIGH | `web_portal/services/config.py` line 113 (R-37). | Without `PORTAL_SECRET_KEY`, each process uses a random key. CSRF and session state break across processes and restarts. | D-9. Tests use a synthetic key. The production policy is human (U-1). |
| E-05 | HIGH | Live `tasks.md` line 155 (T031 depends on T006), line 156 (T032 depends on T022, T028, and T030). | "Every comparison row" cannot pass until the dependent work lands. | D-1. Tests for rows that exist now run first. T014 finishes the matrix later. |
| E-06 | MEDIUM | `tests/e2e/web_portal/test_portal_smoke.py` lines 23 to 37 (R-19, R-20). Line 24 says "while shared registration remains blocked". | The isolated host test does not use the real portal factory. | Real-factory tests are added (T002 to T008, T011). The docstring becomes stale after T009. |
| E-07 | MEDIUM | Parent `tasks.md` line 40 names `tests/unit/gateway/overrides/test_cisco_config_converter.py`. The path is absent (R-18). The file exists at `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` (R-17). | The parent record names a wrong path. | Correction belongs to the parent record. This record does not edit it. |
| E-08 | MEDIUM | Parent `plan.md` line 15 states Python 3.13 (R-68, stale). The floor is 3.15 (R-47). | The parent record names an old floor. | This record uses 3.15. Correction belongs to the parent record. |
| E-09 | MEDIUM | `web_portal/services/config.py` lines 317 to 328 (R-36) answer CSRF failures for every route. The isolated host test at `test_routes.py` lines 94 to 96 does not use that handler. | The isolated test does not prove the real CSRF answer. | T004 tests the real answer through the composition harness. |
| E-10 | MEDIUM | Live contract, section "Integration Evidence and Blockers". `web_portal/services/output_scan.py` and `web_portal/services/data_browser.py` protect only the firmware backup folder. | A future converter-private folder has no listing or scan guard. | D-10. T014 adds exposure tests when storage exists. |
| E-11 | LOW | `src/interfaces/portals/cisco_config_converter/routes.py` line 35 checks the prefix with its trailing slash. | A request without the slash uses the default upload path. | Test `test_prefix_without_slash_redirects_before_parse` documents the redirect. No code change. |
| E-12 | LOW | Issue #4633 comment of 2026-11-08 names PR #4615 as the owner of `data_browser.py`. PR #4615 merged on 2026-11-13. | The coordinator record is stale. | This record uses current PR states. |
| E-13 | LOW | `tests/e2e/web_portal/test_portal_smoke.py` line 18 imports the `test_routes` module as a fixture source. | One test module depends on another. | No change in this issue. |
| E-14 | MEDIUM | Parent `tasks.md` line 51 (T015) and this record's T009 both register the converter in the shared files. | Two records own one registration step. | The handover checklist names issue #4224 T015 as closed by T009. |

## Remediation Actions

These actions track structure debt that this issue does not touch. Each action needs its own issue.

- A-1: `tests/e2e/web_portal` holds 32 children (R-26). Group the children into compliant folders.
- A-2: `web_portal` holds seven children (R-75). Group `routes`, `services`, or `templates` content into a compliant package.
- A-3: `src/interfaces/portals` holds six children (R-76). Issue #4636 remediation R-1 covers `guest_authorizations.py`.

## Unresolved Items

| ID | Owner | Action |
| - | - | - |
| U-1 | Owner | HUMAN-DECISION-REQUIRED: decide the production policy for the shared `PORTAL_SECRET_KEY` fallback (decision D-9, same question as issue #4636 D-15). |
| U-2 | Owner | Record the close or merge state of PR #4208 before T009. |
| U-3 | Owner of issue #4647 | Place its browser tests under the feature folder that decision D-4 names. |
| U-4 | Owner | Confirm that the prerequisite rule in issue #4648 applies to the converter tab. |
| U-5 | Implementer | Run the browser module on Windows, macOS, and Linux during T011. |
| U-6 | Owner of issue #4635 | Record the license basis for the converter (decision D-14). |

## Constitution Alignment

The plan's constitution table covers Principles I to VII. It also covers the Mist SDK, test container, data directory, and security findings rules. Each principle has a result and a reason. No principle fails. Principle VI (inline comments) and Principle VII (action logging) apply to each task that edits product code.

## Validation Commands and Results

No test, linter, formatter, type checker, or build ran in this drafting pass. The read-only checks ran against GitHub `main` in full. The self-review step checked the forbidden tokens, the style rules, the five-children rule, and the count consistency. Its results appear in the summary of this record.
