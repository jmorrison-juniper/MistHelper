# Issue 1772 test-quality triage

## Measurement

| Run | Findings | Critical | High | Medium | Low | Skipped | Parse errors | Stale baseline paths |
| - | - | - | - | - | - | - | - | - |
| Before repair | 2693 | 0 | 124 | 2569 | 0 | 28 | 0 | 120 |
| After repair | 2569 | 0 | 0 | 2569 | 0 | 28 | 0 | 120 |

Original issue #1772 reported 1,596 findings and 35 high-severity findings. The current pre-repair run found 2,693 findings and 124 high-severity findings. That is 1,097 more findings and 89 more high-severity findings. The post-repair run found 2,569 findings and zero high-severity findings. That is 973 more findings and 35 fewer high-severity findings than the original issue.

## Group decisions

| Severity | Rule | Pre-repair count | Post-repair count | Decision | Reason | Follow-up |
| - | - | - | - | - | - | - |
| high | `untested_public_function` | 124 | 0 | False positive, fix the analyzer. | The detector scanned pytest roots as source code. It reported fixtures, pytest hooks, xUnit hooks, and test support helpers as untested source functions. | Repaired now in this pull request. |
| medium | `missing_ec_empty_input` | 75 | 75 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2696 |
| medium | `missing_ec_negative_value` | 213 | 213 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2697 |
| medium | `missing_ec_none_input` | 134 | 134 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2698 |
| medium | `missing_ec_zero_value` | 158 | 158 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2699 |
| medium | `missing_fm_connection_error` | 117 | 117 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2700 |
| medium | `missing_fm_connection_timeout` | 116 | 116 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2701 |
| medium | `missing_fm_empty_body` | 120 | 120 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2702 |
| medium | `missing_fm_http_4xx` | 38 | 38 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2703 |
| medium | `missing_fm_http_5xx` | 64 | 64 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2704 |
| medium | `missing_fm_malformed_json` | 122 | 122 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2705 |
| medium | `taut_literal_true` | 2 | 2 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2706 |
| medium | `weak_bare_assert` | 137 | 137 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2707 |
| medium | `weak_is_not_none` | 369 | 369 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2708 |
| medium | `weak_mock_called_no_args` | 27 | 27 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2709 |
| medium | `weak_pytest_raises_exception` | 1 | 1 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2710 |
| medium | `weak_zero_assertions` | 876 | 876 | Real defect, repair later. | The pattern can leave a test weak or incomplete. The group is too large for this pull request. | #2711 |

## High-severity finding decisions

| # | File | Line | Function | Classification | Decision |
| - | - | - | - | - | - |
| 1 | `mist-ops-platform/tests/unit/api/test_rate_limit_middleware.py` | 48 | `redis_clock` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 2 | `mist-ops-platform/tests/unit/api/test_rate_limit_middleware.py` | 56 | `redis_server` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 3 | `mist-ops-platform/tests/unit/api/test_rate_limit_middleware.py` | 62 | `redis_client` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 4 | `mist-ops-platform/tests/unit/api/test_rate_limit_middleware.py` | 91 | `mock_limiter` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 5 | `mist-ops-platform/tests/unit/api/test_rate_limit_middleware.py` | 99 | `pending_redis_failure` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 6 | `tests/conftest.py` | 164 | `tmp_data_dir` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 7 | `tests/conftest.py` | 172 | `tmp_jsonl_file` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 8 | `tests/conftest.py` | 178 | `isolate_working_directory` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 9 | `tests/contract/packaging/test_compose_rebuild_warning.py` | 34 | `fixture_compose_text` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 10 | `tests/contract/packaging/test_compose_rebuild_warning.py` | 43 | `fixture_guide_text` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 11 | `tests/contract/packaging/test_compose_rebuild_warning.py` | 52 | `fixture_compose_build_text` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 12 | `tests/contract/packaging/test_compose_rebuild_warning.py` | 61 | `fixture_script_text` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 13 | `tests/contract/packaging/test_ops_portal_job.py` | 36 | `fixture_ops_portal_job` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 14 | `tests/contract/packaging/test_wheel_layout.py` | 43 | `fixture_wheel_target` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 15 | `tests/contract/test_pytest_coverage_gate.py` | 43 | `fixture_coverage_workflow` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 16 | `tests/contract/upgrade_portal/conftest.py` | 141 | `fake_api_token` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 17 | `tests/contract/upgrade_portal/conftest.py` | 199 | `fake_capture_storage` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 18 | `tests/contract/upgrade_portal/test_page_links_resolve.py` | 152 | `fixture_url_adapter` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 19 | `tests/contract/upgrade_portal/test_reschedule_and_cancel.py` | 104 | `fixture_run_store` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 20 | `tests/contract/upgrade_portal/test_reschedule_and_cancel.py` | 114 | `fixture_upgrade_app` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 21 | `tests/contract/upgrade_portal/test_reschedule_and_cancel.py` | 131 | `fixture_registered_owner` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 22 | `tests/contract/upgrade_portal/test_reschedule_and_cancel.py` | 151 | `fixture_client` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 23 | `tests/contract/upgrade_portal/test_retry_failed_run.py` | 117 | `fixture_run_store` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 24 | `tests/contract/upgrade_portal/test_retry_failed_run.py` | 127 | `fixture_retry_app` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 25 | `tests/contract/upgrade_portal/test_retry_failed_run.py` | 144 | `fixture_registered_owner` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 26 | `tests/contract/upgrade_portal/test_retry_failed_run.py` | 164 | `fixture_client` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 27 | `tests/e2e/conftest.py` | 22 | `pytest_collection_modifyitems` | pytest_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 28 | `tests/e2e/upgrade_portal/conftest.py` | 609 | `playwright_config` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 29 | `tests/e2e/upgrade_portal/conftest.py` | 623 | `base_url` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 30 | `tests/e2e/upgrade_portal/conftest.py` | 638 | `browser_context_args` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 31 | `tests/e2e/upgrade_portal/conftest.py` | 671 | `portal_test_id_attribute` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 32 | `tests/e2e/upgrade_portal/conftest.py` | 740 | `record_browser_token_evidence` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 33 | `tests/e2e/upgrade_portal/conftest.py` | 789 | `stand_in_browser_token_session` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 34 | `tests/e2e/upgrade_portal/conftest.py` | 815 | `stand_in_token_identity` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 35 | `tests/e2e/upgrade_portal/conftest.py` | 930 | `stand_in_cloud_read` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 36 | `tests/e2e/upgrade_portal/conftest.py` | 960 | `stand_in_device` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 37 | `tests/e2e/upgrade_portal/conftest.py` | 984 | `stand_in_device_read` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 38 | `tests/e2e/upgrade_portal/conftest.py` | 1002 | `stand_in_version_map` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 39 | `tests/e2e/upgrade_portal/conftest.py` | 1017 | `stand_in_options_view` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 40 | `tests/e2e/upgrade_portal/conftest.py` | 1041 | `stand_in_options_builder` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 41 | `tests/e2e/upgrade_portal/conftest.py` | 1070 | `stand_in_capture_runner` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 42 | `tests/e2e/upgrade_portal/conftest.py` | 1097 | `stand_in_run_launcher` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 43 | `tests/e2e/upgrade_portal/conftest.py` | 1113 | `stand_in_stop_runner` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 44 | `tests/e2e/upgrade_portal/conftest.py` | 1129 | `stand_in_client` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 45 | `tests/e2e/upgrade_portal/conftest.py` | 1147 | `stand_in_capture` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 46 | `tests/e2e/upgrade_portal/conftest.py` | 1195 | `stand_in_tier3_capture` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 47 | `tests/e2e/upgrade_portal/conftest.py` | 1231 | `stand_in_capture_index` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 48 | `tests/e2e/upgrade_portal/conftest.py` | 1247 | `stand_in_capture_lister` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 49 | `tests/e2e/upgrade_portal/conftest.py` | 1298 | `stand_in_capture_loader` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 50 | `tests/e2e/upgrade_portal/conftest.py` | 1319 | `signed_session_cookie` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 51 | `tests/e2e/upgrade_portal/conftest.py` | 1346 | `operator_session_cookies` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 52 | `tests/e2e/upgrade_portal/conftest.py` | 1375 | `portal_session_cookies` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 53 | `tests/e2e/upgrade_portal/conftest.py` | 1388 | `second_operator_cookies` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 54 | `tests/e2e/upgrade_portal/conftest.py` | 1403 | `firmware_operator_cookies` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 55 | `tests/e2e/upgrade_portal/conftest.py` | 1700 | `build_stand_in_app` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 56 | `tests/e2e/upgrade_portal/conftest.py` | 1789 | `persistent_store_baseline` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 57 | `tests/e2e/upgrade_portal/playwright.config.py` | 32 | `command_line_options` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 58 | `tests/e2e/upgrade_portal/test_capture.py` | 700 | `fixture_walking_page` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 59 | `tests/e2e/upgrade_portal/test_capture_identifier_paint.py` | 192 | `portal_test_id_attribute` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 60 | `tests/e2e/upgrade_portal/test_run_controls/conftest.py` | 101 | `fixture_site_lock` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 61 | `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | 132 | `fixture_portal_page` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 62 | `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | 288 | `fixture_scheduled_run_page` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 63 | `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | 311 | `fixture_failed_run_page` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 64 | `tests/fixtures/ste_linter/sample_module.py` | 11 | `prepare_cache` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 65 | `tests/integration/conftest.py` | 50 | `pytest_collection_modifyitems` | pytest_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 66 | `tests/integration/conftest.py` | 84 | `mist_api_session` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 67 | `tests/integration/test_wan_vpn_builder_live.py` | 68 | `cleanup_stale_vpns` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 68 | `tests/integration/top5_parity_assertions.py` | 6 | `assert_menu_identifiers_unchanged` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 69 | `tests/integration/top5_parity_assertions.py` | 12 | `assert_callable_registered` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 70 | `tests/support/upgrade_portal_e2e/__init__.py` | 90 | `build_e2e_overrides` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 71 | `tests/test_readopt.py` | 15 | `make_mock_response` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 72 | `tests/tools/test_quality_analyzer/conftest.py` | 23 | `run_engine` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 73 | `tests/unit/_test_arango_writer_helpers.py` | 475 | `assert_edge_case` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 74 | `tests/unit/firmware/test_bulk_ap_running_version.py` | 40 | `fixture_upgrader` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 75 | `tests/unit/metrics_gateway/conftest.py` | 35 | `org_stats_payload` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 76 | `tests/unit/metrics_gateway/conftest.py` | 55 | `site_stats_payload` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 77 | `tests/unit/metrics_gateway/conftest.py` | 87 | `device_stats_payload` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 78 | `tests/unit/ste_linter/conftest.py` | 89 | `fixtures_dir` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 79 | `tests/unit/test_bulk_switch_upgrader.py` | 40 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 80 | `tests/unit/test_bulk_switch_upgrader.py` | 45 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 81 | `tests/unit/test_csv_comparator.py` | 38 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 82 | `tests/unit/test_csv_comparator.py` | 43 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 83 | `tests/unit/test_device_utility_commands.py` | 58 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 84 | `tests/unit/test_device_utility_commands.py` | 63 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 85 | `tests/unit/test_fast_mode_flag.py` | 26 | `fixture_restore_fast_mode` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 86 | `tests/unit/test_lint_diagram_refs.py` | 27 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 87 | `tests/unit/test_lint_diagram_refs.py` | 32 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 88 | `tests/unit/test_rate_limiting.py` | 27 | `tuning_file` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 89 | `tests/unit/test_routing_utils.py` | 35 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 90 | `tests/unit/test_routing_utils.py` | 40 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 91 | `tests/unit/test_ssid_template_consolidation.py` | 136 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 92 | `tests/unit/test_ssid_template_consolidation.py` | 141 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 93 | `tests/unit/test_template_config.py` | 45 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 94 | `tests/unit/test_template_config.py` | 50 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 95 | `tests/unit/test_wan2_variable.py` | 31 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 96 | `tests/unit/test_wan2_variable.py` | 36 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 97 | `tests/unit/test_zone_analyzer.py` | 80 | `setup_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 98 | `tests/unit/test_zone_analyzer.py` | 85 | `teardown_module` | xunit_hook | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 99 | `tests/unit/tools/test_symbol_diff.py` | 20 | `fixture_comparator` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 100 | `tests/unit/upgrade_portal/conftest.py` | 233 | `fake_api_token` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 101 | `tests/unit/upgrade_portal/conftest.py` | 272 | `fake_document_store` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 102 | `tests/unit/upgrade_portal/conftest.py` | 286 | `fake_lock_store` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 103 | `tests/unit/upgrade_portal/test_auth.py` | 273 | `clean_registry` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 104 | `tests/unit/upgrade_portal/test_auth.py` | 332 | `token_variable` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 105 | `tests/unit/upgrade_portal/test_auth.py` | 349 | `no_token_variable` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 106 | `tests/unit/upgrade_portal/test_auth.py` | 365 | `scoped_request` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 107 | `tests/unit/upgrade_portal/test_capture_devices.py` | 128 | `chassis_inventory` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 108 | `tests/unit/upgrade_portal/test_capture_devices.py` | 147 | `chassis_statistics` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 109 | `tests/unit/upgrade_portal/test_capture_devices.py` | 169 | `standalone_records` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 110 | `tests/unit/upgrade_portal/test_e2e_portal_owner.py` | 32 | `fixture_portal_conftest` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 111 | `tests/unit/upgrade_portal/test_e2e_strict_guard.py` | 27 | `fixture_guard_module` | pytest_fixture,fixture_prefix | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 112 | `tests/unit/upgrade_portal/test_identity.py` | 214 | `fresh_registry` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 113 | `tests/unit/upgrade_portal/test_identity.py` | 241 | `no_environment_token` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 114 | `tests/unit/upgrade_portal/test_org_upgrade_service.py` | 122 | `request_body` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 115 | `tests/unit/upgrade_portal/test_upgrade_events.py` | 61 | `search_body` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 116 | `tests/unit/upgrade_portal/test_upgrade_events.py` | 81 | `record_search` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 117 | `tests/unit/upgrade_portal/test_upgrade_gate.py` | 84 | `switch_target` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 118 | `tests/unit/upgrade_portal/test_upgrade_gate.py` | 98 | `access_point_target` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 119 | `tests/unit/upgrade_portal/test_upgrade_gate.py` | 112 | `null_uptime_target` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 120 | `tests/unit/upgrade_portal/test_upgrade_gate.py` | 131 | `rebooted_reading` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 121 | `tests/unit/upgrade_portal/test_upgrade_options.py` | 42 | `fixed_clock` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 122 | `tests/unit/upgrade_portal/test_upgrade_options.py` | 118 | `record_inventory_call` | helper | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 123 | `tests/unit/upgrade_portal/test_wiring.py` | 94 | `empty_run_mirror` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |
| 124 | `tests/unit/web_portal/test_portal_access_control_default.py` | 69 | `workstation` | pytest_fixture | False positive. Pytest calls or supports this function implicitly, or the function is test support code rather than source-under-test code. |

## Skipped files

The analyzer skipped 28 files because they matched the Mist API exclusion predicate. This makes the measurement explicit, but those files remain unmeasured by this run.

| File | Reason |
| - | - |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/mist-ops-platform/tests/contract/test_api_contracts.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/mist-ops-platform/tests/unit/api/test_health.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/mist-ops-platform/tests/unit/api/test_rate_limit_middleware.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/mist-ops-platform/tests/unit/api/test_session_security.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/integration/test_wan_vpn_builder_live.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/test_clear_bpdu_error.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/test_clear_learned_macs.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/test_clear_policy_hit_count.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/test_readopt.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/api/test_api_core_fetch_utils.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/api/test_api_data_fetcher.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/api/test_api_fetch_utils.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/export/test_count_exporter.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/export/test_count_exporter_workflows.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/export/test_msp_inventory_exporter.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/export/test_msp_license_exporter.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/export/test_org_config_exporter.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/export/test_site_other_device_events_exporter.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/export/test_site_webhook_deliveries_exporter.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/refactors/test_wanprobe_config_manager.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/reports/test_ssid_broadcast_gap_report.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/security/test_credential_redaction.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/test_api_tenant_fetch.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/upgrade_portal/test_capture_devices.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/upgrade_portal/test_org_upgrade_service.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/upgrade_portal/test_upgrade_events.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/upgrade_portal/test_upgrade_gate.py` | mist_api_excluded |
| `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper-1772-test-quality/tests/unit/upgrade_portal/test_upgrade_options.py` | mist_api_excluded |

## Repair proof

The repaired test still fails when the guarded behavior is broken. I temporarily restored the previous CLI behavior, which passed pytest roots to `UntestedDetector` as source roots. The regression test failed with this assertion:

```text
AssertionError: assert 'untested_public_function' not in ['untested_public_function']
test_quality_analyzer: 1 findings (0/1/0/0), 2 skipped, 0 parse errors
negative_test_exit=1
```

After I restored the repair, the same test passed:

```text
tests\tools\test_quality_analyzer\test_cli.py . [100%]
1 passed in 2.84s
```
