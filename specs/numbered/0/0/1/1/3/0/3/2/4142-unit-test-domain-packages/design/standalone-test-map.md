# Test Path Map

This file preserves the prior branch map and the fresh-main candidate map. The prior map records history and is not authoritative for this candidate. Use the `Fresh-main candidate map` section at the end for the current 360 moves.
The candidate uses base `31b752f060d4d10cbe87b5880b071b6570d0b3c9`. It leaves 22 claimed paths unchanged and does not claim full hierarchy acceptance.

The user approved a scope that reduces the `tests/unit/` root and limits each new group to five children. Split unowned packages by test topic when a destination group would exceed five children. Keep each claimed package and file at its current path until its owner releases it.

## Preserved-branch package destinations, historical

The count includes each direct file and directory, including `__init__.py` and `conftest.py`. Keep package markers with their logical group. Split a package into the listed topic groups when the destination would exceed five direct children.

Pytest first imported the moved `site` tests as the standard-library `site` module because their new parents lacked package markers. Add `__init__.py` to `mist/` and `mist/resources/`. Keep each parent at five children or fewer.

| Source package | Destination package | Existing children | Reserved path |
|---|---|---:|---|
| `tests/unit/analytics/` | `tests/unit/marvis/mist/intelligence/analytics/` | 5 | Defer `test_insight_metrics_utils.py` because a historical specification links to its source path. Keep that file at source until the historical-link constraint changes |
| `tests/unit/api/` | `tests/unit/marvis/mist/access/api/` | 4 | PR #4313 merged; issue #2752 retains API and record claims |
| `tests/unit/arango_indexes/` | `tests/unit/config/foundation/persistence/storage/arango_indexes/` | 5 | Moved under the PR #4208 owner's approved handoff in T047 |
| `tests/unit/audit/` | `tests/unit/marvis/mist/access/audit/` | 4 (1 marker) | |
| `tests/unit/auth/` | `tests/unit/marvis/mist/access/auth/` | 4 (1 marker) | |
| `tests/unit/benchmarks/` | `tests/unit/config/foundation/support/benchmarks/` | 1 | |
| `tests/unit/bootstrap/` | `tests/unit/config/foundation/runtime/startup/bootstrap/` | 7 split into 3 + 4 + 2 children | |
| `tests/unit/cache/` | `tests/unit/config/foundation/persistence/storage/cache/` | 2 (1 marker) | |
| `tests/unit/capture/` | `tests/unit/prod_readiness/operations/execution/capture/` | 8 modules, split into four groups | |
| `tests/unit/config/` | `tests/unit/config/foundation/runtime/startup/config/` | 1 | |
| `tests/unit/container/` | `tests/unit/prod_readiness/operations/exporting/container/` | 11 (2 markers), split into four groups | |
| `tests/unit/dataclasses/` | `tests/unit/config/foundation/models/dataclasses/` | 3 (1 marker) | PR #4287 owns `test_service_measurement.py`; PR #4314 and PR #4289 merged |
| `tests/unit/dataproc/` | `tests/unit/config/foundation/models/dataproc/` | 2 (1 marker) | |
| `tests/unit/db/` | `tests/unit/config/foundation/persistence/storage/db/` | 4 (1 marker) | |
| `tests/unit/db_discovery/` | `tests/unit/config/foundation/persistence/storage/db_discovery/` | 5 (1 marker) | `tests/unit/upgrade_portal/test_store.py` imports `tests.unit.db_discovery.fakes`; defer until its #2752/#4208 ownership hold clears |
| `tests/unit/device/` | `tests/unit/marvis/mist/resources/device/` | 7 (1 marker) | `test_device_handler_narrowing.py` moved. PR #4317 owns `test_arp_command_manager.py`. Issue #2753 claims `test_ap_profile_migration_manager.py`. Issues #2746 and #2747 claim `test_device_utils.py` |
| `tests/unit/export/` | `tests/unit/prod_readiness/operations/exporting/export/` | 53 (1 marker) | PR #4313 merged; issue #2752 retains export and record claims |
| `tests/unit/firmware/` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/` | 18 (1 marker), split into three groups | Issues #2746 and #2747 claim `test_running_version.py`; recheck each candidate before moving |
| `tests/unit/firmware_policy/` | `tests/unit/prod_readiness/operations/execution/firmware/policy/` | 8, split into policy and recovery groups | |
| `tests/unit/firmware_policy_jobs/` | `tests/unit/prod_readiness/operations/execution/firmware/policy_jobs/` | 3 (1 marker) | |
| `tests/unit/gateway/` | `tests/unit/marvis/mist/resources/gateway/` | 14 | WAN override, exporter, override, and SSR tests moved to topic groups. The Cisco converter test moved after PR #4226 merged and its owner released the path. Issues #2746 and #2747 claim other gateway tests |
| `tests/unit/helpers/` | `tests/unit/config/foundation/support/helpers/` | 1 | |
| `tests/unit/input/` | `tests/unit/config/foundation/runtime/core/input/` | 1 | |
| `tests/unit/inventory/` | `tests/unit/marvis/mist/resources/inventory/` | 9, split into five groups | `test_org_device_inventory_summary.py` was a prior #2746 candidate; recheck before moving |
| `tests/unit/juniper_docs/` | `tests/unit/marvis/mist/intelligence/juniper_docs/` | 22 (2 markers) | Issue #3158 claims the package. Issue #2977 lists canonical test paths |
| `tests/unit/juniper_rma/` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/` | 5 (1 marker) | |
| `tests/unit/maps/` | `tests/unit/maps/interfaces/maps/` | 1 | |
| `tests/unit/marvis/` | `tests/unit/marvis/mist/intelligence/marvis/` | 2 (1 marker) | |
| `tests/unit/metrics_gateway/` | `tests/unit/maps/interfaces/monitoring/metrics_gateway/` | 5 (1 marker) | |
| `tests/unit/mib_generator/` | `tests/unit/prod_readiness/operations/hardware/mib_generator/` | 6, split into three groups | |
| `tests/unit/org/` | `tests/unit/marvis/mist/resources/org/` | 8 (1 marker) | PR #4310 merged; recheck issue #2746 before each batch |
| `tests/unit/prod_readiness/` | `tests/unit/prod_readiness/operations/execution/prod_readiness/` | 3 (1 marker) | |
| `tests/unit/refactors/` | `tests/unit/config/foundation/support/refactors/` | 27 (1 marker), split into four groups | Issue #2746 lists test candidates; recheck before moving |
| `tests/unit/reports/` | `tests/unit/marvis/mist/intelligence/reports/` | 3 | PSK and both wired-client report tests remain deferred until their previous owners clear the claims |
| `tests/unit/scripts/` | `tests/unit/maps/interfaces/handlers/scripts/` | 7 | Defer for PR #4208 workflow selectors |
| `tests/unit/security/` | `tests/unit/prod_readiness/operations/protection/security/` | 3 (1 marker) | |
| `tests/unit/serial_cc/` | `tests/unit/config/foundation/support/serial_cc/` | 11 split into five topic groups | |
| `tests/unit/site/` | `tests/unit/marvis/mist/resources/site/` | 5 (1 marker) | |
| `tests/unit/ssh/` | `tests/unit/prod_readiness/operations/execution/ssh/` | 9 | PR #4312 merged; issues #2746 and #2747 claim `test_cli_shell_manager.py` |
| `tests/unit/time/` | `tests/unit/config/foundation/runtime/core/time/` | 1 | |
| `tests/unit/troubleshooting/` | `tests/unit/marvis/mist/intelligence/troubleshooting/` | 9 | |
| `tests/unit/ui/` | `tests/unit/maps/interfaces/ui/` | 19 (2 markers), split into two groups | Issue #2746 lists test candidates; recheck before moving |
| `tests/unit/upgrade_portal/` | `tests/unit/maps/interfaces/portals/upgrade_portal/` | 168 (2 markers) | PR #4208 workflow selectors and issue #2752 upgrade-path work |
| `tests/unit/utils/` | `tests/unit/config/foundation/support/utils/` | 14, split into three groups | `test_tls_policy.py` is a #2746 candidate; recheck before moving |
| `tests/unit/validation/` | `tests/unit/config/foundation/runtime/core/validation/` | 2 (1 marker) | |
| `tests/unit/web_portal/` | `tests/unit/maps/interfaces/portals/web_portal/` | 48 (1 marker), split into four groups | `test_operations_silent_failure.py` is a #2746 candidate; recheck before moving |
| `tests/unit/websocket/` | `tests/unit/marvis/mist/realtime/websocket/` | 7 | PR #4317 owns `test_manager.py` |
| `tests/unit/websocket_streams/` | `tests/unit/marvis/mist/realtime/websocket_streams/` | 5 (1 marker) | PR #4208 owns the workflow-selected paths; PRs #4308 and #4315 merged |

### Cleared package topic groups

#### Gateway WAN overrides

Keep the two related WAN override tests together in one group.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/resources/gateway/wan_overrides/` | `tests/unit/gateway/test_wan_override_walker.py`, `tests/unit/gateway/test_wan_override_walker_extended.py` |

#### Gateway exporters

Keep the gateway high-availability and statistics exporters together.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/resources/gateway/exporters/` | `tests/unit/gateway/test_gateway_ha_exporter.py`, `tests/unit/gateway/test_gateway_stats_exporter.py` |

#### Gateway overrides

Keep the override reader, classifier, report writer, and released Cisco converter test together. PR #4226 merged, and its owner released the Cisco test for the move.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/resources/gateway/overrides/` | `tests/unit/gateway/overrides/__init__.py`, `tests/unit/gateway/overrides/test_device_data_fetcher.py`, `tests/unit/gateway/overrides/test_override_classifier.py`, `tests/unit/gateway/overrides/test_override_report_writer.py` |

The Cisco converter test now resides at `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`.
The group has five direct children, including its package marker.

#### Gateway SSR registration

Keep the SSR registration test with its package marker.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/resources/gateway/ssr_registration/` | `tests/unit/gateway/ssr_registration/__init__.py`, `tests/unit/gateway/ssr_registration/test_ssr_registration_commands.py` |

Move only the listed unclaimed files. Keep each new group at five or fewer direct children, including retained package markers and helper files. Refresh ownership before each move.

#### Manufacturer input

Group the wired-client manufacturer input test under the Mist intelligence reports package.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/intelligence/reports/manufacturer_input/` | `tests/unit/reports/test_issue_4053_manufacturer_input.py` |

#### Juniper RMA bounded groups

These sources already occupy the initial Juniper RMA destination.
The table gives paths relative to `tests/unit/prod_readiness/operations/exporting/juniper_rma/`.
Keep existing package markers and helpers at their current paths.
The API root has four children. The model, workflow, and fixture roots each have five.
Each new group has five children or fewer.

| Source paths | Destination group |
| - | - |
| `api/test_asset_service.py`, `api/test_case_service.py` | `api/services/` |
| `api/test_gateway.py`, `api/test_messages.py`, `api/test_fixture_replies.py`, `api/test_read_gets.py` | `api/transport/` |
| `model/test_export_rows.py`, `model/test_request_rows.py` | `model/rows/` |
| `workflows/test_read_menus_live.py`, `workflows/test_read_menus_offline.py` | `workflows/menus/` |
| `workflows/test_correlation.py`, `workflows/test_lookups.py` | `workflows/lookups/` |
| `fixtures/asset/` | `fixtures/payloads/asset/` |
| `fixtures/case/` | `fixtures/payloads/case/` |

#### Device health reports

Keep offline-device, transceiver, and SSID coverage reports together.
All three modules test `src.mist.intelligence.reports`.
The destination root has three children, including its marker and manufacturer input group.
The new topic group has three test files.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/intelligence/reports/device_health/` | `tests/unit/reports/test_offline_device_reporter.py`, `tests/unit/reports/test_sfp_transceiver_data_processor.py`, `tests/unit/reports/test_ssid_broadcast_gap_report.py` |

#### Assurance reports

Group the three scorecards and alert digest under assurance.
Keep each existing package marker and shared fixture with its tests.
The AP package has six children before the move.
Move its three behavior tests into `cases/` and retain its support-file test at the package root.
The AP root then has four children. Its cases group has three.
The other packages retain their four or five children.

| Source paths | Destination group |
| - | - |
| `tests/unit/reports/ap_scorecard/__init__.py`, `tests/unit/reports/ap_scorecard/conftest.py`, `tests/unit/reports/ap_scorecard/test_ap_scorecard_support_files.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/` |
| `tests/unit/reports/ap_scorecard/test_ap_scorecard_client.py`, `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py`, `tests/unit/reports/ap_scorecard/test_ap_scorecard_operation.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/cases/` |
| `tests/unit/reports/switch_scorecard/` | `tests/unit/marvis/mist/intelligence/reports/assurance/switch_scorecard/` |
| `tests/unit/reports/wan_edge_scorecard/` | `tests/unit/marvis/mist/intelligence/reports/assurance/wan_edge_scorecard/` |
| `tests/unit/reports/alert_digest/` | `tests/unit/marvis/mist/intelligence/reports/assurance/alert_digest/` |

#### Audit reports

Group certificate and subscription tests under credentials.
Group rogue-network evidence and client census tests under posture.
Retain each package marker. Each moved package has four children.
Both audit topic groups have two children in this batch.
The reports root reaches five children without adding a unit-root child.

| Source package | Destination package |
| - | - |
| `tests/unit/reports/certificate_expiry/` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/certificate_expiry/` |
| `tests/unit/reports/subscription_expiry/` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/` |
| `tests/unit/reports/rogue_pci_evidence/` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/rogue_pci_evidence/` |
| `tests/unit/reports/client_fingerprint_census/` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/client_fingerprint_census/` |

#### Remaining unowned audit groups

Split the three oversized packages by behavior and retain helpers at their package roots.
Paths in the source column start at `tests/unit/reports/`.
Paths in the destination column start at `tests/unit/marvis/mist/intelligence/reports/audits/`.
Keep the admin artifact test at its package root and update its repository depth.

| Source paths | Destination group |
| - | - |
| `admin_token_hygiene/__init__.py`, `admin_token_hygiene/test_admin_token_hygiene_artifacts.py` | `credentials/admin_token_hygiene/` |
| `admin_token_hygiene/test_admin_token_hygiene_client.py`, `admin_token_hygiene/test_admin_token_hygiene_model.py`, `admin_token_hygiene/test_admin_token_hygiene_operation.py`, `admin_token_hygiene/test_admin_token_hygiene_redaction.py` | `credentials/admin_token_hygiene/cases/` |
| `org_security_posture/fixtures/` | `posture/org_security_posture/fixtures/` |
| `org_security_posture/test_api_checks.py`, `org_security_posture/test_setting_switch_checks.py`, `org_security_posture/test_password_checks.py`, `org_security_posture/test_session_checks.py` | `posture/org_security_posture/checks/` |
| `org_security_posture/test_console_summary.py`, `org_security_posture/test_result_formatting.py`, `org_security_posture/test_output_contract.py` | `posture/org_security_posture/presentation/` |
| `org_security_posture/test_registry.py`, `org_security_posture/test_package_imports.py`, `org_security_posture/test_quickstart_contract.py`, `org_security_posture/test_mist_api_sources.py`, `org_security_posture/test_operation_outcome.py` | `posture/org_security_posture/contracts/` |
| `site_variable_audit/__init__.py` | `posture/site_variable_audit/` |
| `site_variable_audit/site_variable_audit_fixtures_test.py` | `posture/site_variable_audit/fixtures_test.py` |
| `site_variable_audit/site_variable_audit_operation_test.py`, `site_variable_audit/site_variable_audit_client_test.py`, `site_variable_audit/site_variable_audit_contract_test.py`, `site_variable_audit/site_variable_audit_model_test.py`, `site_variable_audit/site_variable_audit_summary_test.py` | `posture/site_variable_audit/cases/` |

The credential and posture groups have three and four children.
Every new descendant group has five children or fewer.
Rename `org_security_posture/fixtures/representative_org_security_posture.py` to `posture/org_security_posture/fixtures/representative.py`.
These shorter helper names keep imports within the line-length limit without suppressions.
Preserve the fixture test suffix and its existing collected test.
Keep the PSK and wired-client report source paths deferred until their previous owners release them.

#### Packet capture

The destination root has four topic groups.

| Destination group | Source files |
| - | - |
| `tests/unit/prod_readiness/operations/execution/capture/client_download/` | `tests/unit/capture/test_client_pcap_downloader.py`, `tests/unit/capture/test_client_pcap_downloader_network_paths.py` |
| `tests/unit/prod_readiness/operations/execution/capture/device_scan/` | `tests/unit/capture/test_multi_ap_scan_workflow.py` |
| `tests/unit/prod_readiness/operations/execution/capture/packet_capture/` | `tests/unit/capture/test_packet_capture_download.py`, `tests/unit/capture/test_packet_capture_manager.py`, `tests/unit/capture/test_packet_capture_payload_logging.py` |
| `tests/unit/prod_readiness/operations/execution/capture/site_download/` | `tests/unit/capture/test_org_pcap_wait_download_workflow.py`, `tests/unit/capture/test_site_pcap_wait_download_workflow.py` |

#### Firmware policy

Keep the existing root package marker, fixture module, and shared fake at the policy root. Group the four policy tests and split recovery tests by topic.

| Destination group | Source files |
| - | - |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/` | `tests/unit/firmware_policy/__init__.py`, `tests/unit/firmware_policy/conftest.py`, `tests/unit/firmware_policy/fakes.py`, `tests/unit/firmware_policy/recovery/` |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/changes/` | `tests/unit/firmware_policy/test_admission.py`, `tests/unit/firmware_policy/test_backup.py`, `tests/unit/firmware_policy/test_catalog.py`, `tests/unit/firmware_policy/test_changes.py` |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/` | `tests/unit/firmware_policy/recovery/__init__.py`, `tests/unit/firmware_policy/recovery/fakes.py`, `tests/unit/firmware_policy/recovery/bundles/`, `tests/unit/firmware_policy/recovery/selection/` |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/bundles/` | `tests/unit/firmware_policy/recovery/test_bundle.py`, `tests/unit/firmware_policy/recovery/test_schema.py` |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/selection/` | `tests/unit/firmware_policy/recovery/test_selection.py`, `tests/unit/firmware_policy/recovery/test_windows_access.py` |

#### MIB generator

Keep the existing package marker. Move the fixture beside the generator tests that use it.

| Destination group | Source files |
| - | - |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/cli/` | `tests/unit/mib_generator/test_cli_wiring.py` |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/` | `tests/unit/mib_generator/test_mib_generator.py`, `tests/unit/mib_generator/test_properties.py`, `tests/unit/mib_generator/fixtures/mini_openapi.json` |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/performance/` | `tests/unit/mib_generator/test_performance.py` |

#### Troubleshooting

The current-main package has five standalone tests and four subpackages. Group those entries so the destination root has five children. Split the RF diagnostics package because it has more than five children.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/intelligence/troubleshooting/core/` | `tests/unit/troubleshooting/test_interactive_test_runner.py`, `tests/unit/troubleshooting/test_logged_error_observer_filter.py`, `tests/unit/troubleshooting/test_marvis_troubleshoot_utils.py`, `tests/unit/troubleshooting/test_marvis_troubleshoot_utils_extended.py`, `tests/unit/troubleshooting/test_troubleshoot_utils.py` |
| `tests/unit/marvis/mist/intelligence/troubleshooting/credential_tests/` | `tests/unit/troubleshooting/nac_idp_credential_test/__init__.py`, `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_client.py`, `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_model.py`, `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py`, `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_package.py` |
| `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/` | `tests/unit/troubleshooting/rf_diagnostics/__init__.py`, `tests/unit/troubleshooting/rf_diagnostics/audit_requests/`, `tests/unit/troubleshooting/rf_diagnostics/recording_spectrum/` |
| `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/audit_requests/` | `tests/unit/troubleshooting/rf_diagnostics/test_audit.py`, `tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py`, `tests/unit/troubleshooting/rf_diagnostics/test_file_naming.py`, `tests/unit/troubleshooting/rf_diagnostics/test_operation_flow.py` |
| `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/recording_spectrum/` | `tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py`, `tests/unit/troubleshooting/rf_diagnostics/test_spectrum_flow.py` |
| `tests/unit/marvis/mist/intelligence/troubleshooting/sms_provider_tests/` | `tests/unit/troubleshooting/sms_provider_test/__init__.py`, `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_client.py`, `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_model.py`, `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_operation.py` |
| `tests/unit/marvis/mist/intelligence/troubleshooting/synthetic_trigger/` | `tests/unit/troubleshooting/synthetic_test_trigger/__init__.py`, `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` |

#### Juniper Docs

Keep the existing root package marker and `conftest.py`. The root then has three topic groups and two existing files.
Rows that name a parent group list its exact destination child groups.

| Destination group | Source files |
| - | - |
| `tests/unit/marvis/mist/intelligence/juniper_docs/content/` | `tests/unit/juniper_docs/content/classification/`, `tests/unit/juniper_docs/content/quality/` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/content/classification/` | `tests/unit/juniper_docs/test_asset_classifier.py`, `tests/unit/juniper_docs/test_collision_repair.py`, `tests/unit/juniper_docs/test_reclassifier.py`, `tests/unit/juniper_docs/test_slug_classifier.py` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/content/quality/` | `tests/unit/juniper_docs/test_content_dedup.py`, `tests/unit/juniper_docs/test_content_sampler.py`, `tests/unit/juniper_docs/test_privacy_invariant.py`, `tests/unit/juniper_docs/test_release_note_selector.py` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/` | `tests/unit/juniper_docs/corpus/clients/`, `tests/unit/juniper_docs/corpus/documents/`, `tests/unit/juniper_docs/corpus/fixtures/` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/clients/` | `tests/unit/juniper_docs/test_catalog_client.py`, `tests/unit/juniper_docs/test_corpus_downloader.py`, `tests/unit/juniper_docs/test_http_config.py`, `tests/unit/juniper_docs/test_sitemap_reader.py` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/documents/` | `tests/unit/juniper_docs/test_companion_pdf_resolver.py`, `tests/unit/juniper_docs/test_pdf_paths.py`, `tests/unit/juniper_docs/test_signal_scorer.py` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/` | `tests/unit/juniper_docs/fixtures/__init__.py`, `tests/unit/juniper_docs/fixtures/html_pages/`, `tests/unit/juniper_docs/fixtures/pdf_samples/`, `tests/unit/juniper_docs/fixtures/scripts/`, `tests/unit/juniper_docs/fixtures/sitemaps/` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/html_pages/` | `tests/unit/juniper_docs/fixtures/error_page_200.html`, `tests/unit/juniper_docs/fixtures/root_index_multi_pdf.html`, `tests/unit/juniper_docs/fixtures/root_index_single_pdf.html` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/pdf_samples/` | `tests/unit/juniper_docs/fixtures/image_only.pdf`, `tests/unit/juniper_docs/fixtures/minimal.pdf`, `tests/unit/juniper_docs/fixtures/sample_evpn_fabric.pdf`, `tests/unit/juniper_docs/fixtures/sample_routing.pdf`, `tests/unit/juniper_docs/fixtures/sample_uncategorized.pdf` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/scripts/` | `tests/unit/juniper_docs/fixtures/sample_toc.js` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/sitemaps/` | `tests/unit/juniper_docs/fixtures/sitemap_index.xml`, `tests/unit/juniper_docs/fixtures/sitemap_marketing.xml`, `tests/unit/juniper_docs/fixtures/sitemap_subset.xml` |
| `tests/unit/marvis/mist/intelligence/juniper_docs/workflow/` | `tests/unit/juniper_docs/test_inventory_builder.py`, `tests/unit/juniper_docs/test_manifest_writer.py`, `tests/unit/juniper_docs/test_runner.py`, `tests/unit/juniper_docs/test_state_store.py` |

#### Firmware

Keep the existing package marker. The destination root has three topic groups.

| Destination group | Source files |
| - | - |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/` | `tests/unit/firmware/test_aggregate_child_controls.py`, `tests/unit/firmware/test_aggregate_ended_child_cancel.py`, `tests/unit/firmware/test_aggregate_final_cancel.py`, `tests/unit/firmware/test_aggregate_mixed_cancel_state.py`, `tests/unit/firmware/test_aggregate_upgrade_service.py` |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/site/`, `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/platform/` |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/site/` | `tests/unit/firmware/test_firmware_manager_ap_msp.py`, `tests/unit/firmware/test_firmware_manager_config.py`, `tests/unit/firmware/test_firmware_manager_proxy.py` |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/platform/` | `tests/unit/firmware/test_firmware_manager_monitoring.py`, `tests/unit/firmware/test_firmware_manager_ssr.py`, `tests/unit/firmware/test_firmware_manager_template.py`, `tests/unit/firmware/test_firmware_manager_version.py` |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/` | `tests/unit/firmware/test_bulk_ap_running_version.py`, `tests/unit/firmware/test_firmware_upgrade_status_checker.py`, `tests/unit/firmware/test_org_advanced_bodies.py`, `tests/unit/firmware/test_org_cancel_sort.py`, `tests/unit/firmware/test_running_version.py` |

#### Inventory

The destination root has five topic groups. Keep the three existing subpackages with their markers.

| Destination group | Source files or child groups |
| - | - |
| `tests/unit/marvis/mist/resources/inventory/` | `tests/unit/marvis/mist/resources/inventory/organization/`, `tests/unit/marvis/mist/resources/inventory/csv_imports/`, `tests/unit/marvis/mist/resources/inventory/device_replace/`, `tests/unit/marvis/mist/resources/inventory/inventory_summary/`, `tests/unit/marvis/mist/resources/inventory/support/` |
| `tests/unit/marvis/mist/resources/inventory/organization/` | `tests/unit/inventory/test_org_device_inventory_msp.py`, `tests/unit/inventory/test_org_device_inventory_summary.py`, `tests/unit/inventory/test_org_device_inventory_summary_facade.py`, `tests/unit/inventory/test_org_device_inventory_summary_wave8.py` |
| `tests/unit/marvis/mist/resources/inventory/csv_imports/` | `tests/unit/inventory/csv_imports/__init__.py`, `tests/unit/inventory/csv_imports/test_csv_imports_client.py`, `tests/unit/inventory/csv_imports/test_csv_imports_model.py`, `tests/unit/inventory/csv_imports/test_csv_imports_operation.py` |
| `tests/unit/marvis/mist/resources/inventory/device_replace/` | `tests/unit/inventory/device_replace/__init__.py`, `tests/unit/inventory/device_replace/test_rma_device_replace_client.py`, `tests/unit/inventory/device_replace/test_rma_device_replace_model.py`, `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py` |
| `tests/unit/marvis/mist/resources/inventory/inventory_summary/` | `tests/unit/marvis/mist/resources/inventory/inventory_summary/__init__.py`, `tests/unit/marvis/mist/resources/inventory/inventory_summary/test_pivot_renderer.py` |
| `tests/unit/marvis/mist/resources/inventory/support/` | `tests/unit/marvis/mist/resources/inventory/support/comparison/`, `tests/unit/marvis/mist/resources/inventory/support/versioning/` |
| `tests/unit/marvis/mist/resources/inventory/support/comparison/` | `tests/unit/inventory/test_csv_comparator_broad_handlers.py` |
| `tests/unit/marvis/mist/resources/inventory/support/versioning/` | `tests/unit/marvis/mist/resources/inventory/support/versioning/test_version_per_model_fetcher_wave3.py` |

#### Refactors

Keep the existing package marker. The destination root has four topic groups.

| Destination group | Source files or child groups |
| - | - |
| `tests/unit/config/foundation/support/refactors/` | `tests/unit/config/foundation/support/refactors/runtime/`, `tests/unit/config/foundation/support/refactors/network/`, `tests/unit/config/foundation/support/refactors/data/`, `tests/unit/config/foundation/support/refactors/telemetry/` |
| `tests/unit/config/foundation/support/refactors/runtime/` | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/`, `tests/unit/config/foundation/support/refactors/runtime/session/`, `tests/unit/config/foundation/support/refactors/runtime/console/` |
| `tests/unit/config/foundation/support/refactors/runtime/entrypoint/` | `tests/unit/refactors/test_help_invocation_side_effect_free.py`, `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py`, `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py`, `tests/unit/refactors/test_run_interactive_test.py` |
| `tests/unit/config/foundation/support/refactors/runtime/session/` | `tests/unit/refactors/test_app_context_session_state.py`, `tests/unit/refactors/test_initialize_mist_session.py`, `tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py`, `tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py` |
| `tests/unit/config/foundation/support/refactors/runtime/console/` | `tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py`, `tests/unit/config/foundation/support/refactors/runtime/console/test_keyboard_listener.py`, `tests/unit/config/foundation/support/refactors/runtime/console/test_tui_launcher.py` |
| `tests/unit/config/foundation/support/refactors/network/` | `tests/unit/config/foundation/support/refactors/network/clients/`, `tests/unit/config/foundation/support/refactors/network/configuration/`, `tests/unit/config/foundation/support/refactors/network/launchers/` |
| `tests/unit/config/foundation/support/refactors/network/clients/` | `tests/unit/refactors/test_device_data_fetcher.py`, `tests/unit/refactors/test_issue_3732_read_retry.py`, `tests/unit/config/foundation/support/refactors/network/clients/test_service_ping_launcher.py` |
| `tests/unit/config/foundation/support/refactors/network/configuration/` | `tests/unit/config/foundation/support/refactors/network/configuration/test_device_config_template_cloner_manager.py`, `tests/unit/refactors/test_wan_probe_device_override_manager.py`, `tests/unit/config/foundation/support/refactors/network/configuration/test_wanprobe_config_manager.py`, `tests/unit/config/foundation/support/refactors/network/configuration/test_wlanradius_timer_manager_paths.py` |
| `tests/unit/config/foundation/support/refactors/network/launchers/` | `tests/unit/refactors/test_connection_pool_executor.py`, `tests/unit/refactors/test_maps_manager_launcher.py`, `tests/unit/refactors/test_wan2_migration_launcher.py` |
| `tests/unit/config/foundation/support/refactors/data/` | `tests/unit/config/foundation/support/refactors/data/inventory/`, `tests/unit/config/foundation/support/refactors/data/storage/`, `tests/unit/config/foundation/support/refactors/data/filesystem/` |
| `tests/unit/config/foundation/support/refactors/data/inventory/` | `tests/unit/refactors/test_inventory_csvcomparator.py`, `tests/unit/refactors/test_marvis_data_utils.py` |
| `tests/unit/config/foundation/support/refactors/data/storage/` | `tests/unit/refactors/test_sqlite_database_writer.py` |
| `tests/unit/config/foundation/support/refactors/data/filesystem/` | `tests/unit/config/foundation/support/refactors/data/filesystem/test_data_directory_checker.py` |
| `tests/unit/config/foundation/support/refactors/telemetry/` | `tests/unit/refactors/test_anomaly_metrics_discovery.py` |

#### User interface

Keep the existing package marker and `conftest.py`. The destination root has two topic groups.

| Destination group | Source files or child groups |
| - | - |
| `tests/unit/maps/interfaces/ui/` | `tests/unit/maps/interfaces/ui/display/`, `tests/unit/maps/interfaces/ui/interaction/` |
| `tests/unit/maps/interfaces/ui/display/` | `tests/unit/ui/test_debug_saver.py`, `tests/unit/maps/interfaces/ui/display/test_display_utils.py`, `tests/unit/ui/test_layout_builder.py`, `tests/unit/maps/interfaces/ui/display/test_output_formatter.py`, `tests/unit/ui/test_results_grid_builder.py` |
| `tests/unit/maps/interfaces/ui/interaction/` | `tests/unit/maps/interfaces/ui/interaction/input/`, `tests/unit/maps/interfaces/ui/interaction/dispatch/`, `tests/unit/maps/interfaces/ui/interaction/tui/` |
| `tests/unit/maps/interfaces/ui/interaction/input/` | `tests/unit/ui/test_dotenv_loader.py`, `tests/unit/ui/test_key_poller.py`, `tests/unit/ui/test_keyboard_dispatch.py`, `tests/unit/ui/test_parameter_collector.py`, `tests/unit/ui/test_prompt_utils.py` |
| `tests/unit/maps/interfaces/ui/interaction/dispatch/` | `tests/unit/maps/interfaces/ui/interaction/dispatch/test_device_prompt_rename_guard.py`, `tests/unit/ui/test_function_executor.py`, `tests/unit/maps/interfaces/ui/interaction/dispatch/test_interactive_display_utils.py`, `tests/unit/ui/test_item_executor.py`, `tests/unit/ui/test_level_discoverer.py` |
| `tests/unit/maps/interfaces/ui/interaction/tui/` | `tests/unit/maps/interfaces/ui/interaction/tui/test_tui.py`, `tests/unit/ui/test_tui_runner.py` |

#### Utilities

Keep the existing fixture and performance directories. Group the 12 direct test modules into three groups.

| Destination group | Source files |
| - | - |
| `tests/unit/config/foundation/support/utils/network/` | `tests/unit/utils/test_environment_utils.py`, `tests/unit/utils/test_zscaler_catalogue.py`, `tests/unit/utils/test_zscaler_probe.py`, `tests/unit/utils/test_zscaler_probe_transport.py` |
| `tests/unit/config/foundation/support/utils/interaction/` | `tests/unit/utils/test_console.py`, `tests/unit/utils/test_input_utils_wave9.py`, `tests/unit/utils/test_operation_registry_1029.py`, `tests/unit/utils/test_prompting_menus_not_safe.py` |
| `tests/unit/config/foundation/support/utils/logging/` | `tests/unit/utils/test_filter_operator_engine.py`, `tests/unit/utils/test_logger_utils_private_digest.py`, `tests/unit/utils/test_process_safe_log_handler.py`, `tests/unit/utils/test_tls_policy.py` |

#### Web portal

Keep the existing package marker. The destination root has four topic groups.

| Destination group | Source files or child groups |
| - | - |
| `tests/unit/maps/interfaces/portals/web_portal/` | `tests/unit/maps/interfaces/portals/web_portal/data/`, `tests/unit/maps/interfaces/portals/web_portal/operations/`, `tests/unit/maps/interfaces/portals/web_portal/security/`, `tests/unit/maps/interfaces/portals/web_portal/lifecycle/` |
| `tests/unit/maps/interfaces/portals/web_portal/data/` | `tests/unit/maps/interfaces/portals/web_portal/data/browser_controls/`, `tests/unit/maps/interfaces/portals/web_portal/data/browser_previews/`, `tests/unit/maps/interfaces/portals/web_portal/data/map_views/`, `tests/unit/maps/interfaces/portals/web_portal/data/portal_data/` |
| `tests/unit/maps/interfaces/portals/web_portal/data/browser_controls/` | `tests/unit/web_portal/test_data_browser_pagination_bounds.py`, `tests/unit/web_portal/test_data_browser_sorting.py`, `tests/unit/web_portal/test_dropdown_sort_order.py` |
| `tests/unit/maps/interfaces/portals/web_portal/data/browser_previews/` | `tests/unit/web_portal/test_compact_data_preview.py`, `tests/unit/web_portal/test_data_browser_preview_streaming.py`, `tests/unit/web_portal/test_preview_column_order.py`, `tests/unit/web_portal/test_preview_row_order.py` |
| `tests/unit/maps/interfaces/portals/web_portal/data/map_views/` | `tests/unit/web_portal/test_brand_theme_default.py`, `tests/unit/web_portal/test_map_image_route.py`, `tests/unit/web_portal/test_map_site_selection_race.py`, `tests/unit/web_portal/test_map_title_theme.py`, `tests/unit/web_portal/test_map_viewer_xss.py` |
| `tests/unit/maps/interfaces/portals/web_portal/data/portal_data/` | `tests/unit/web_portal/test_dashboard_readiness.py`, `tests/unit/web_portal/test_issue_3915_empty_site_filter.py`, `tests/unit/web_portal/test_juniper_portal_rows.py` |
| `tests/unit/maps/interfaces/portals/web_portal/operations/` | `tests/unit/maps/interfaces/portals/web_portal/operations/gates/`, `tests/unit/maps/interfaces/portals/web_portal/operations/picklists/`, `tests/unit/maps/interfaces/portals/web_portal/operations/presentation/` |
| `tests/unit/maps/interfaces/portals/web_portal/operations/gates/` | `tests/unit/web_portal/test_operation_destructive_gate.py`, `tests/unit/web_portal/test_operation_eligibility_logging.py`, `tests/unit/web_portal/test_operation_frontend_state.py`, `tests/unit/web_portal/test_operation_output_files_cap.py`, `tests/unit/web_portal/test_operation_run_registry_caps.py` |
| `tests/unit/maps/interfaces/portals/web_portal/operations/picklists/` | `tests/unit/web_portal/test_operations_msp_selector.py`, `tests/unit/web_portal/test_operations_silent_failure.py`, `tests/unit/web_portal/test_portal_picklist_reason.py`, `tests/unit/web_portal/test_portal_required_answers.py`, `tests/unit/web_portal/test_portal_required_controls.py` |
| `tests/unit/maps/interfaces/portals/web_portal/operations/presentation/` | `tests/unit/web_portal/test_portal_category_accuracy.py`, `tests/unit/web_portal/test_portal_label_accuracy.py`, `tests/unit/web_portal/test_portal_log_routing.py`, `tests/unit/web_portal/test_portal_operation_ordering.py`, `tests/unit/web_portal/test_portal_sdk_calls.py` |
| `tests/unit/maps/interfaces/portals/web_portal/security/` | `tests/unit/maps/interfaces/portals/web_portal/security/access/`, `tests/unit/maps/interfaces/portals/web_portal/security/webhooks/` |
| `tests/unit/maps/interfaces/portals/web_portal/security/access/` | `tests/unit/web_portal/test_config_ip_allowlist.py`, `tests/unit/web_portal/test_csrf_expiry_answer.py`, `tests/unit/web_portal/test_guest_authorization_read_model.py`, `tests/unit/web_portal/test_portal_access_control_default.py` |
| `tests/unit/maps/interfaces/portals/web_portal/security/webhooks/` | `tests/unit/web_portal/test_issue_3188_webhook_parameters.py`, `tests/unit/web_portal/test_webhook_signature.py` |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/` | `tests/unit/maps/interfaces/portals/web_portal/lifecycle/events/`, `tests/unit/maps/interfaces/portals/web_portal/lifecycle/runtime/`, `tests/unit/maps/interfaces/portals/web_portal/lifecycle/experience/` |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/events/` | `tests/unit/web_portal/test_event_bus.py`, `tests/unit/web_portal/test_event_bus_deadlock.py`, `tests/unit/web_portal/test_output_scan_clock_race.py`, `tests/unit/web_portal/test_output_scan_runtime_files.py`, `tests/unit/web_portal/test_portal_graceful_shutdown.py` |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/runtime/` | `tests/unit/web_portal/test_issue_4053_runtime_answers.py`, `tests/unit/web_portal/test_portal_run_isolation.py`, `tests/unit/web_portal/test_portal_silent_completion.py`, `tests/unit/web_portal/test_portal_stream_thread_release.py`, `tests/unit/web_portal/test_portal_terminal_state_4025.py` |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/experience/` | `tests/unit/web_portal/test_portal_accent_button.py` |

### Serial console test groups

Place each test in the listed group. Each group has five or fewer files.

| Destination group | Source files |
| - | - |
| `tests/unit/config/foundation/support/serial_cc/setup/` | `test_global_assignments_builder.py`, `test_import_initialization_service.py` |
| `tests/unit/config/foundation/support/serial_cc/security/` | `test_security_events.py`, `test_security_events_wave8.py` |
| `tests/unit/config/foundation/support/serial_cc/clients/` | `test_site_client_insight_path.py`, `test_site_client_insights.py`, `test_start_site_client_capture_wireless.py` |
| `tests/unit/config/foundation/support/serial_cc/capture_results/` | `test_start_site_scan_capture.py`, `test_test_results_by_site.py` |
| `tests/unit/config/foundation/support/serial_cc/telemetry/` | `test_sle_metrics.py`, `test_switch_vc_stats.py` |

### Container test groups

Keep `tests/unit/prod_readiness/operations/exporting/container/__init__.py` at the group root. The root then has four topic groups and one package marker.

| Destination group | Source files |
| - | - |
| `tests/unit/prod_readiness/operations/exporting/container/build_support/` | `bash_support.py`, `owner_only.py`, `test_build_files_match.py`, `test_openapi_in_image.py` |
| `tests/unit/prod_readiness/operations/exporting/container/runtime/` | `test_access_log_format.py`, `test_misthelper_session_script.py`, `test_startup_no_recursive_chown.py`, `test_write_session_env_script.py` |
| `tests/unit/prod_readiness/operations/exporting/container/output_defaults/` | Keep the existing package and its five direct children. |
| `tests/unit/prod_readiness/operations/exporting/container/session_database/` | Keep the existing package and its four direct children. |

`tests/unit/wan_performance/` is not present on the inspected main revision. PR #4208 adds 13 test modules in that package. Move the package intact to `tests/unit/maps/interfaces/portals/wan_performance/` only after PR #4208 merges and its owner accepts the handoff. The package is an existing package from #4208 and stays intact under the approved scope. PR #4208 also owns `.github/workflows/ci.yml`. Do not rebase, edit, or move any #4208 path. Keep its paths reserved until the PR merges and its owner accepts the handoff.

PR #4309 merged as `cdc965f5`. PR #4313 owns `api_fetch_utils.py`, `gateway_test_exporter.py`, their unit tests, and the issue #2752 specification and changelog records. Issue #2752 work continues. Keep both the API and export packages reserved until PR #4313 merges and the owner clears the remaining claims.

Issue #2752 also reserves `tests/unit/upgrade_portal/` and related files until its capture-timeout and tracker-error work finishes and a human reviews it. The confirmed source paths are `src/interfaces/portals/upgrade_portal/capture/service.py`, `src/interfaces/portals/upgrade_portal/upgrade/driver.py`, and `src/interfaces/portals/upgrade_portal/settle/service.py`, plus their tests. Do not enable auto-merge for this portal work.

## Root test destinations

Each section names the exact destination directory. Append the source filename to that path. The evidence notes identify the source import or the test topic. New directories have no `__init__.py` file unless later import evidence requires one.

### `tests/unit/config/standalone/foundation/models/core/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_data_processing.py` | Foundation data model test topic |
| `tests/unit/test_telemetry.py` | Imports `src.foundation.models.dataclasses` |

### `tests/unit/config/standalone/foundation/persistence/arango_writer/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_arango_writer.py` | Imports `src.foundation.persistence.db.writers.arango_writer` |
| `tests/unit/_test_arango_writer_helpers.py` | Helper imported by `test_arango_writer.py` |

### `tests/unit/config/standalone/foundation/persistence/database/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_data_browser_path_guard.py` | Foundation data-path test topic |
| `tests/unit/test_data_browser_sqlite_handles.py` | Foundation SQLite test topic |
| `tests/unit/test_retention.py` | Imports `src.foundation.persistence.db.retention` |
| `tests/unit/test_router.py` | Imports `src.foundation.persistence.db.router` |
| `tests/unit/test_standalone.py` | Imports `src.foundation.persistence.db`. Issue #2861 claims this path |

### `tests/unit/config/standalone/foundation/persistence/redis/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_redis_json_writer.py` | Imports `src.foundation.persistence.db.writers.redis_writer` |
| `tests/unit/test_redis_writer.py` | Imports `src.foundation.persistence.db.writers.redis_writer` |
| `tests/unit/test_webhook_ingestion.py` | Imports `src.foundation.persistence.db.router` |

### `tests/unit/config/standalone/foundation/runtime/configuration/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_dotenv_precedence.py` | Configuration test topic |
| `tests/unit/test_environment_guards.py` | Configuration test topic |

### `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_config_utils.py` | Uses a unique package path to avoid a duplicate pytest module name |
| `tests/unit/test_config_utils_org_id_preflight.py` | Imports `src.foundation.runtime.config` |
| `tests/unit/test_config_utils_wave3.py` | Imports `src.foundation.runtime.config.config_utils` |

### `tests/unit/config/standalone/foundation/runtime/startup/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_dependency_check.py` | Imports `src.foundation.runtime.bootstrap.dependency_check` |
| `tests/unit/test_fast_mode_flag.py` | Runtime flag test topic |
| `tests/unit/test_interactive_test_runner.py` | Runtime test-runner topic; use destination name `test_standalone_interactive_test_runner.py` to avoid a pytest module-name collision |
| `tests/unit/test_credential_preflight.py` | Foundation credential preflight topic |
| `tests/unit/test_container_health_probe.py` | Foundation container health topic |

### `tests/unit/config/standalone/foundation/runtime/release/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_log_rotation.py` | Foundation runtime logging topic |
| `tests/unit/test_release_body.py` | Release-body utility topic |
| `tests/unit/test_source_dependency_external_symbols.py` | Imports `src.foundation.runtime.config.source_dependency_resolver` |
| `tests/unit/test_thread_scoped_sleep.py` | Foundation runtime support topic |
| `tests/unit/test_version_compare.py` | Foundation runtime version topic |

### `tests/unit/config/standalone/foundation/support/utilities/network/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_adaptive_pacer.py` | Imports `src.foundation.support.utils.rate_limiting` |
| `tests/unit/test_address_utils.py` | Imports `src.foundation.support.utils.address_utils` |
| `tests/unit/test_rate_limiting.py` | Imports `src.foundation.support.utils.rate_limiting` |

### `tests/unit/config/standalone/foundation/support/utilities/system/` — 4 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_file_path_utils.py` | Imports `src.foundation.support.utils.file_path_utils` |
| `tests/unit/test_logger_utils.py` | Imports `src.foundation.support.utils.logger_utils` |
| `tests/unit/test_subprocess_runner.py` | Imports `src.foundation.support.utils.subprocess_runner` |
| `tests/unit/test_tqdm_wrapper.py` | Foundation support utility topic |

### `tests/unit/config/standalone/foundation/support/registry/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_menu_entry_metadata.py` | Imports `src.foundation.support.utils.menu_entry` |
| `tests/unit/test_msp_privilege_detection.py` | Imports `src.foundation.support.refactors.msp_privilege_detection` |
| `tests/unit/test_operation_registry_fail_closed.py` | Imports `src.foundation.support.utils.operation_registry` |
| `tests/unit/test_systematic_test_offline_mode.py` | Imports `src.foundation.support.utils.menu_entry` |
| `tests/unit/test_systematic_test_unregistered_semantics.py` | Imports `src.foundation.support.utils.operation_registry` |

### `tests/unit/config/standalone/foundation/support/quality/assertions/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_bare_assert_replacements.py` | Cross-domain test topic |
| `tests/unit/test_hypothesis_example.py` | Test-quality example topic |
| `tests/unit/test_issue_1709_narrow_except.py` | Test-quality guard topic |
| `tests/unit/test_markdown_control_bytes.py` | Test-quality guard topic |
| `tests/unit/test_ste_writing_guide.py` | Writing-guide test topic |

### `tests/unit/config/standalone/foundation/support/quality/imports/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_global_import_manager_package_spec_guards.py` | Package import guard topic |
| `tests/unit/test_no_mistapi_stub_leak.py` | Cross-domain import guard topic |
| `tests/unit/test_no_new_legacy_facade_imports.py` | Cross-domain import guard topic |

### `tests/unit/config/standalone/foundation/support/quality/scope/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_config_package_tracked.py` | Configuration package guard topic |
| `tests/unit/test_no_export_legacy_callsites.py` | Cross-domain import guard topic |
| `tests/unit/test_src_public_imports.py` | Source package guard topic |

### `tests/unit/config/standalone/foundation/support/quality/cross_domain/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_device_events_52w_exporter_extended.py` | Imports foundation models and operations export code |
| `tests/unit/test_issue_2971_status_slice3.py` | Imports Mist API and operations export code |
| `tests/unit/test_site_auto_upgrade.py` | Imports foundation models and operations firmware code |

### `tests/unit/config/standalone/foundation/support/quality/risk/` — 1 file

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_top5_risk_controls.py` | Cross-domain control test topic |

### `tests/unit/marvis/standalone/mist/access/api/` — 4 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_api_tenant_fetch.py` | Imports `src.mist.access.api.tenant_fetch` |
| `tests/unit/test_issue_2971_status_before_count.py` | Mist API imports outnumber other domain imports |
| `tests/unit/test_mistapi_api_response_boundary.py` | Mist API response-boundary topic |
| `tests/unit/test_openapi_spec_refresh.py` | Mist API specification topic |

### `tests/unit/marvis/standalone/mist/access/audit/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_audit_analyzer.py` | Imports `src.mist.access.audit.analyzer` |
| `tests/unit/test_audit_filter.py` | Imports `src.mist.access.audit.filter` |
| `tests/unit/test_audit_time_parser.py` | Imports `src.mist.access.audit.time_parser` |

### `tests/unit/marvis/standalone/mist/intelligence/analytics/` — 1 file

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_zone_analyzer.py` | Imports `src.mist.intelligence.analytics.zone_analyzer` |

### `tests/unit/marvis/standalone/mist/intelligence/marvis/` — 1 file

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_marvis_utils.py` | Imports `src.mist.intelligence.marvis.marvis_utils` |

### `tests/unit/marvis/standalone/mist/intelligence/reports/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_e911_bssid.py` | Imports `src.mist.intelligence.reports.e911_bssid` |
| `tests/unit/test_offline_device_reporter.py` | Mist intelligence report topic; use destination name `test_standalone_offline_device_reporter.py` to avoid a pytest module-name collision |
| `tests/unit/test_issue_2971_status_slice4.py` | Mist imports outnumber operations imports |

### `tests/unit/marvis/standalone/mist/networking/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_routing_utils.py` | Imports `src.mist.networking.network.routing_utils` |
| `tests/unit/test_unparseable_response_guards.py` | Mist imports outnumber foundation imports. Issue #4006 claims this path |

### `tests/unit/marvis/standalone/mist/resources/device/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_device_utility_commands.py` | Imports `src.mist.resources.device` |
| `tests/unit/test_device_utility_commands_wave3.py` | Imports `src.mist.resources.device.utility_commands` |
| `tests/unit/test_multi_ap_scan_workflow.py` | Device scan test topic; use destination name `test_device_multi_ap_scan_workflow.py` to avoid a pytest module-name collision |
| `tests/unit/test_prompt_network_device_utils.py` | Imports `src.mist.resources.device.prompt_utils`. Issue #2746 claims this path |
| `tests/unit/test_virtual_chassis.py` | Imports `src.mist.resources.device.virtual_chassis` |

### `tests/unit/marvis/standalone/mist/resources/gateway/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_gateway_override_analysis.py` | Imports `src.mist.resources.gateway.overrides` |
| `tests/unit/test_template_config.py` | Imports `src.mist.resources.gateway.template_config` |
| `tests/unit/test_wan2_variable.py` | Imports `src.mist.resources.gateway` |

### `tests/unit/marvis/standalone/mist/resources/inventory/` — 1 file

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_csv_comparator.py` | Imports `src.mist.resources.inventory.csv_comparator` |

### `tests/unit/marvis/standalone/mist/resources/org/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_org_license_async_claim_status.py` | Organization license test topic |
| `tests/unit/test_org_ticket_manager.py` | Imports `src.mist.resources.org.org_ticket_manager` |

### `tests/unit/marvis/standalone/mist/resources/site/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_bulk_radius_wlan_config_manager.py` | Imports `src.mist.resources.site` |
| `tests/unit/test_bulk_radius_wlan_snapshot.py` | Wireless configuration test topic |

### `tests/unit/prod_readiness/standalone/operations/execution/capture/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_org_pcap_wait_download.py` | Organization capture test topic |
| `tests/unit/test_packet_capture.py` | Imports `src.operations.execution.capture.packet_capture` |
| `tests/unit/test_site_pcap_wait_download.py` | Site capture test topic |

### `tests/unit/prod_readiness/standalone/operations/execution/firmware/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_bulk_ap_upgrader.py` | Imports `src.operations.execution.firmware.bulk_ap_upgrader` |
| `tests/unit/test_bulk_switch_upgrader.py` | Imports `src.operations.execution.firmware.bulk_switch_upgrader` |
| `tests/unit/test_org_ap_upgrader.py` | Imports `src.operations.execution.firmware.org_ap_upgrader` |

### `tests/unit/prod_readiness/standalone/operations/execution/ssh/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_ssh_host_key_tofu.py` | Imports `src.operations.execution.ssh.connection.connector` |
| `tests/unit/test_ssh_runner.py` | Imports `src.operations.execution.ssh.batch` |

### `tests/unit/prod_readiness/standalone/operations/execution/ssid/` — 1 file

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_ssid_template_consolidation.py` | Imports `src.operations.execution.ssid_consolidation` |

### `tests/unit/prod_readiness/standalone/operations/exporting/inventory/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_menu_12_inventory.py` | Menu 12 inventory test topic |
| `tests/unit/test_menu_13_device_stats.py` | Menu 13 device statistics topic |
| `tests/unit/test_menu_19_device_port_stats.py` | Menu 19 device port statistics topic |
| `tests/unit/test_menu_25_combined_inventory.py` | Menu 25 inventory test topic |
| `tests/unit/test_device_events_52w_exporter.py` | Imports `src.operations.exporting.export.device_events_52w_exporter` |

### `tests/unit/prod_readiness/standalone/operations/exporting/reports/` — 5 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_exports.py` | Imports `src.operations.exporting.export.site_insights_exporter` |
| `tests/unit/test_issue_2971_census_repairs.py` | Imports operations export modules |
| `tests/unit/test_org_inventory_exporter_helpers.py` | Imports `src.operations.exporting.export.org_inventory_exporter`. Issues #2746 and #2747 claim this path |
| `tests/unit/test_pk_strategies.py` | Operations export imports outnumber foundation imports |
| `tests/unit/test_wifi_clients_exporter.py` | Wi-Fi client export test topic |

### `tests/unit/prod_readiness/standalone/operations/exporting/quality/` — 1 file

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_operation_output_file_discovery.py` | Operations output discovery test topic |

### `tests/unit/prod_readiness/standalone/operations/wan/` — 3 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_org_data_collector.py` | Imports `src.operations.wan.org_data_collector` |
| `tests/unit/test_wan_hub_group_manager.py` | Imports `src.operations.wan.wan_hub_group_manager` |
| `tests/unit/test_wan_vpn_builder.py` | Imports `src.operations.wan.wan_vpn_builder` |

### `tests/unit/maps/standalone/interfaces/monitoring/` — 1 file

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_metrics_gateway_org_selection.py` | Metrics gateway selection test topic |

### `tests/unit/maps/standalone/interfaces/portals/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_favicon.py` | Imports `src.interfaces.portals.upgrade_portal.app` |
| `tests/unit/test_web_portal_bind_address.py` | Web portal bind test topic |

### `tests/unit/maps/standalone/interfaces/ui/` — 2 files

| Source file | Routing evidence |
|---|---|
| `tests/unit/test_issue_2971_status_final.py` | Interface imports outnumber operations imports |
| `tests/unit/test_issue_2971_status_slice5.py` | Interface imports outnumber other domain imports |

## Direct-child counts

New grouping directories use a package marker only when pytest needs a unique module path. Existing package markers remain inside the moved package. The root `__init__.py` stays in place. The `portals` count includes `upgrade_portal`, `web_portal`, and the reserved `wan_performance` package after #4208 merges.

| Destination parent | Direct children | Markers | Limit |
|---|---:|---:|---:|
| `tests/unit/` | 5 | 1 | 5 |
| `tests/unit/config/` | 2 | 0 | 5 |
| `tests/unit/marvis/` | 2 | 0 | 5 |
| `tests/unit/maps/` | 2 | 0 | 5 |
| `tests/unit/prod_readiness/` | 2 | 0 | 5 |
| `tests/unit/config/foundation/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/models/` | 2 | 0 | 5 |
| `tests/unit/config/foundation/persistence/` | 1 | 0 | 5 |
| `tests/unit/config/foundation/persistence/storage/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/runtime/` | 2 | 0 | 5 |
| `tests/unit/config/foundation/runtime/startup/` | 2 | 0 | 5 |
| `tests/unit/config/foundation/runtime/core/` | 3 | 0 | 5 |
| `tests/unit/config/foundation/support/` | 5 | 0 | 5 |
| `tests/unit/marvis/mist/` | 4 | 0 | 5 |
| `tests/unit/marvis/mist/access/` | 3 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/` | 5 | 0 | 5 |
| `tests/unit/marvis/mist/realtime/` | 2 | 0 | 5 |
| `tests/unit/marvis/mist/resources/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/handlers/` | 1 | 0 | 5 |
| `tests/unit/maps/interfaces/monitoring/` | 1 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/` | 3 | 0 | 5 |
| `tests/unit/maps/interfaces/ui/` | 4 | 2 | 5 |
| `tests/unit/prod_readiness/operations/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/` | 3 | 0 | 5 |
| `tests/unit/prod_readiness/operations/exporting/` | 3 | 0 | 5 |
| `tests/unit/prod_readiness/operations/exporting/container/` | 5 | 1 | 5 |
| `tests/unit/prod_readiness/operations/exporting/container/build_support/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/exporting/container/runtime/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/exporting/container/output_defaults/` | 5 | 1 | 5 |
| `tests/unit/prod_readiness/operations/exporting/container/session_database/` | 4 | 1 | 5 |
| `tests/unit/prod_readiness/operations/execution/capture/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/capture/client_download/` | 2 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/capture/device_scan/` | 1 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/capture/packet_capture/` | 3 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/capture/site_download/` | 2 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/` | 5 | 1 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/changes/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/` | 4 | 1 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/bundles/` | 2 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/selection/` | 2 | 0 | 5 |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/` | 4 | 1 | 5 |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/cli/` | 1 | 0 | 5 |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/` | 3 | 0 | 5 |
| `tests/unit/prod_readiness/operations/hardware/mib_generator/performance/` | 1 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/` | 5 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/core/` | 5 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/credential_tests/` | 5 | 1 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/` | 3 | 1 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/audit_requests/` | 4 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/recording_spectrum/` | 2 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/sms_provider_tests/` | 4 | 1 | 5 |
| `tests/unit/marvis/mist/intelligence/troubleshooting/synthetic_trigger/` | 2 | 1 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/` | 5 | 1 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/content/` | 2 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/content/classification/` | 4 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/content/quality/` | 4 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/` | 3 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/clients/` | 4 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/documents/` | 3 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/` | 5 | 1 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/html_pages/` | 3 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/pdf_samples/` | 5 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/scripts/` | 1 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/corpus/fixtures/sitemaps/` | 3 | 0 | 5 |
| `tests/unit/marvis/mist/intelligence/juniper_docs/workflow/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/` | 4 | 1 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/` | 5 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/` | 2 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/site/` | 3 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/platform/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/` | 5 | 0 | 5 |
| `tests/unit/marvis/mist/resources/inventory/` | 5 | 0 | 5 |
| `tests/unit/marvis/mist/resources/inventory/organization/` | 4 | 0 | 5 |
| `tests/unit/marvis/mist/resources/inventory/csv_imports/` | 4 | 1 | 5 |
| `tests/unit/marvis/mist/resources/inventory/device_replace/` | 4 | 1 | 5 |
| `tests/unit/marvis/mist/resources/inventory/inventory_summary/` | 2 | 1 | 5 |
| `tests/unit/marvis/mist/resources/inventory/support/` | 2 | 0 | 5 |
| `tests/unit/marvis/mist/resources/inventory/support/comparison/` | 1 | 0 | 5 |
| `tests/unit/marvis/mist/resources/inventory/support/versioning/` | 1 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/` | 5 | 1 | 5 |
| `tests/unit/config/foundation/support/refactors/runtime/` | 3 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/runtime/entrypoint/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/runtime/session/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/runtime/console/` | 3 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/network/` | 3 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/network/clients/` | 3 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/network/configuration/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/network/launchers/` | 3 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/data/` | 3 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/data/inventory/` | 2 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/data/storage/` | 1 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/data/filesystem/` | 1 | 0 | 5 |
| `tests/unit/config/foundation/support/refactors/telemetry/` | 1 | 0 | 5 |
| `tests/unit/maps/interfaces/ui/display/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/ui/interaction/` | 3 | 0 | 5 |
| `tests/unit/maps/interfaces/ui/interaction/input/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/ui/interaction/dispatch/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/ui/interaction/tui/` | 2 | 0 | 5 |
| `tests/unit/config/foundation/support/utils/` | 5 | 0 | 5 |
| `tests/unit/config/foundation/support/utils/network/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/support/utils/interaction/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/support/utils/logging/` | 4 | 0 | 5 |
| `tests/unit/config/foundation/support/utils/fixtures/` | 2 | 0 | 5 |
| `tests/unit/config/foundation/support/utils/performance/` | 1 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/` | 5 | 1 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/data/` | 4 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/data/browser_controls/` | 3 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/data/browser_previews/` | 4 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/data/map_views/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/data/portal_data/` | 3 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/operations/` | 3 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/operations/gates/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/operations/picklists/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/operations/presentation/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/security/` | 2 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/security/access/` | 4 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/security/webhooks/` | 2 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/` | 3 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/events/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/runtime/` | 5 | 0 | 5 |
| `tests/unit/maps/interfaces/portals/web_portal/lifecycle/experience/` | 1 | 0 | 5 |
| `tests/unit/prod_readiness/operations/hardware/` | 1 | 0 | 5 |
| `tests/unit/prod_readiness/operations/protection/` | 1 | 0 | 5 |
| `tests/unit/config/standalone/` | 1 | 0 | 5 |
| `tests/unit/config/standalone/foundation/` | 4 | 0 | 5 |
| `tests/unit/config/standalone/foundation/models/` | 1 | 0 | 5 |
| `tests/unit/config/standalone/foundation/persistence/` | 3 | 0 | 5 |
| `tests/unit/config/standalone/foundation/runtime/` | 3 | 0 | 5 |
| `tests/unit/config/standalone/foundation/runtime/configuration/` | 3 | 0 | 5 |
| `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/` | 4 | 1 | 5 |
| `tests/unit/config/standalone/foundation/support/` | 3 | 0 | 5 |
| `tests/unit/config/standalone/foundation/support/utilities/` | 2 | 0 | 5 |
| `tests/unit/config/standalone/foundation/support/quality/` | 5 | 0 | 5 |
| `tests/unit/marvis/standalone/` | 1 | 0 | 5 |
| `tests/unit/marvis/standalone/mist/` | 4 | 0 | 5 |
| `tests/unit/marvis/standalone/mist/access/` | 2 | 0 | 5 |
| `tests/unit/marvis/standalone/mist/intelligence/` | 3 | 0 | 5 |
| `tests/unit/marvis/standalone/mist/resources/` | 5 | 0 | 5 |
| `tests/unit/prod_readiness/standalone/` | 1 | 0 | 5 |
| `tests/unit/prod_readiness/standalone/operations/` | 3 | 0 | 5 |
| `tests/unit/prod_readiness/standalone/operations/execution/` | 4 | 0 | 5 |
| `tests/unit/prod_readiness/standalone/operations/exporting/` | 3 | 0 | 5 |
| `tests/unit/maps/standalone/` | 1 | 0 | 5 |
| `tests/unit/maps/standalone/interfaces/` | 3 | 0 | 5 |

Each destination leaf holds the file count shown in its section heading. The maximum is five. The destination counts include any package marker. Split every unowned package by test topic before moving it when a group would exceed five children. Keep packages with current claims deferred until each owner clears the exact paths.

## Deferred paths

Do not move a reserved package or file until its pull request merges, its owner accepts the handoff, and active issue and session claims clear. Refresh pull request files, issue claims, and session claims before each batch. An issue campaign inventory is not an active file claim unless an owner has claimed that exact path. Current exact claims include `tests/unit/ssh/test_cli_shell_manager.py` for issues #2746 and #2747, and `tests/test_upgrade_portal_mist.py` for issue #2746 and PR #4324. Keep PR #4208 draft, unmerged, and unchanged until its owner approves a handoff. Keep the #2752 portal work for human review and do not enable auto-merge.

## Fresh-main candidate map, 2026-11-13

This table records 360 moves from the requested base. It includes 359 Python files and one JSON file.
Keep 17 site address-audit paths and six rogue-DHCP paths at source. Their proposed target groups would exceed five children.
Keep four `output_defaults` files at source because `test_session.py` uses relative package imports.
Keep eight Juniper RMA JSON replies beside their shared fixture loader.
Keep the separate 22 claimed paths unchanged. This partial candidate does not establish full hierarchy acceptance.
The candidate adds ten package markers. `tests/unit/config/standalone/foundation/persistence/arango_writer/__init__.py` enables the moved test's relative helper import. The leaf has three children, including the marker.

| Source | Destination |
| - | - |
| `tests/unit/audit/__init__.py` | `tests/unit/config/foundation/models/dataproc/__init__.py` |
| `tests/unit/dataproc/test_data_processing_utils.py` | `tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py` |
| `tests/unit/arango_indexes/conftest.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/conftest.py` |
| `tests/unit/arango_indexes/fakes.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/fakes.py` |
| `tests/unit/arango_indexes/test_declared_indexes.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_declared_indexes.py` |
| `tests/unit/arango_indexes/test_preservation.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py` |
| `tests/unit/arango_indexes/test_retry_concurrency.py` | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_retry_concurrency.py` |
| `tests/unit/cache/__init__.py` | `tests/unit/config/foundation/persistence/storage/cache/__init__.py` |
| `tests/unit/cache/test_cache_utils.py` | `tests/unit/config/foundation/persistence/storage/cache/test_cache_utils.py` |
| `tests/unit/db/__init__.py` | `tests/unit/config/foundation/persistence/storage/db/__init__.py` |
| `tests/unit/db/test_retention_redis_scan.py` | `tests/unit/config/foundation/persistence/storage/db/test_retention_redis_scan.py` |
| `tests/unit/db/test_sqlite_database_writer_logging.py` | `tests/unit/config/foundation/persistence/storage/db/test_sqlite_database_writer_logging.py` |
| `tests/unit/input/test_prompt_client_utils.py` | `tests/unit/config/foundation/runtime/core/input/test_prompt_client_utils.py` |
| `tests/unit/time/test_time_utils.py` | `tests/unit/config/foundation/runtime/core/time/test_time_utils.py` |
| `tests/unit/validation/__init__.py` | `tests/unit/config/foundation/runtime/core/validation/__init__.py` |
| `tests/unit/validation/test_validation_utils.py` | `tests/unit/config/foundation/runtime/core/validation/test_validation_utils.py` |
| `tests/unit/auth/interactive/__init__.py` | `tests/unit/config/foundation/runtime/startup/bootstrap/__init__.py` |
| `tests/unit/bootstrap/test_dependency_check_paths.py` | `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py` |
| `tests/unit/bootstrap/test_package_installer_wave9.py` | `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_package_installer_wave9.py` |
| `tests/unit/bootstrap/test_uv_runtime.py` | `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_runtime.py` |
| `tests/unit/bootstrap/test_dns_preflight.py` | `tests/unit/config/foundation/runtime/startup/bootstrap/preflight/test_dns_preflight.py` |
| `tests/unit/bootstrap/test_github_account_checker.py` | `tests/unit/config/foundation/runtime/startup/bootstrap/preflight/test_github_account_checker.py` |
| `tests/unit/config/test_config_utils.py` | `tests/unit/config/foundation/runtime/startup/config/test_config_utils.py` |
| `tests/unit/benchmarks/test_capture_concurrency_benchmark.py` | `tests/unit/config/foundation/support/benchmarks/test_capture_concurrency_benchmark.py` |
| `tests/unit/helpers/test_complexity_thresholds.py` | `tests/unit/config/foundation/support/helpers/test_complexity_thresholds.py` |
| `tests/unit/refactors/test_data_directory_checker.py` | `tests/unit/config/foundation/support/refactors/data/filesystem/test_data_directory_checker.py` |
| `tests/unit/refactors/test_inventory_csvcomparator.py` | `tests/unit/config/foundation/support/refactors/data/inventory/test_inventory_csvcomparator.py` |
| `tests/unit/refactors/test_marvis_data_utils.py` | `tests/unit/config/foundation/support/refactors/data/inventory/test_marvis_data_utils.py` |
| `tests/unit/refactors/test_sqlite_database_writer.py` | `tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py` |
| `tests/unit/refactors/test_service_ping_launcher.py` | `tests/unit/config/foundation/support/refactors/network/clients/test_service_ping_launcher.py` |
| `tests/unit/refactors/test_device_config_template_cloner_manager.py` | `tests/unit/config/foundation/support/refactors/network/configuration/test_device_config_template_cloner_manager.py` |
| `tests/unit/refactors/test_wanprobe_config_manager.py` | `tests/unit/config/foundation/support/refactors/network/configuration/test_wanprobe_config_manager.py` |
| `tests/unit/refactors/test_connection_pool_executor.py` | `tests/unit/config/foundation/support/refactors/network/launchers/test_connection_pool_executor.py` |
| `tests/unit/refactors/test_maps_manager_launcher.py` | `tests/unit/config/foundation/support/refactors/network/launchers/test_maps_manager_launcher.py` |
| `tests/unit/refactors/test_wan2_migration_launcher.py` | `tests/unit/config/foundation/support/refactors/network/launchers/test_wan2_migration_launcher.py` |
| `tests/unit/refactors/test_fast_mode_small_seams.py` | `tests/unit/config/foundation/support/refactors/runtime/console/test_fast_mode_small_seams.py` |
| `tests/unit/refactors/test_keyboard_listener.py` | `tests/unit/config/foundation/support/refactors/runtime/console/test_keyboard_listener.py` |
| `tests/unit/refactors/test_help_invocation_side_effect_free.py` | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py` |
| `tests/unit/refactors/test_main_entrypoint.py` | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` |
| `tests/unit/refactors/test_reject_unsupported_flag_variants.py` | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py` |
| `tests/unit/refactors/test_run_interactive_test.py` | `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_run_interactive_test.py` |
| `tests/unit/refactors/test_initialize_mist_session_interactive_wave9.py` | `tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py` |
| `tests/unit/refactors/test_switch_to_interactive_login.py` | `tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py` |
| `tests/unit/refactors/test_anomaly_metrics_discovery.py` | `tests/unit/config/foundation/support/refactors/telemetry/test_anomaly_metrics_discovery.py` |
| `tests/unit/serial_cc/test_start_site_scan_capture.py` | `tests/unit/config/foundation/support/serial_cc/capture_results/test_start_site_scan_capture.py` |
| `tests/unit/serial_cc/test_test_results_by_site.py` | `tests/unit/config/foundation/support/serial_cc/capture_results/test_test_results_by_site.py` |
| `tests/unit/serial_cc/test_site_client_insight_path.py` | `tests/unit/config/foundation/support/serial_cc/clients/test_site_client_insight_path.py` |
| `tests/unit/serial_cc/test_site_client_insights.py` | `tests/unit/config/foundation/support/serial_cc/clients/test_site_client_insights.py` |
| `tests/unit/serial_cc/test_start_site_client_capture_wireless.py` | `tests/unit/config/foundation/support/serial_cc/clients/test_start_site_client_capture_wireless.py` |
| `tests/unit/serial_cc/test_security_events.py` | `tests/unit/config/foundation/support/serial_cc/security/test_security_events.py` |
| `tests/unit/serial_cc/test_security_events_wave8.py` | `tests/unit/config/foundation/support/serial_cc/security/test_security_events_wave8.py` |
| `tests/unit/serial_cc/test_global_assignments_builder.py` | `tests/unit/config/foundation/support/serial_cc/setup/test_global_assignments_builder.py` |
| `tests/unit/serial_cc/test_import_initialization_service.py` | `tests/unit/config/foundation/support/serial_cc/setup/test_import_initialization_service.py` |
| `tests/unit/serial_cc/test_sle_metrics.py` | `tests/unit/config/foundation/support/serial_cc/telemetry/test_sle_metrics.py` |
| `tests/unit/serial_cc/test_switch_vc_stats.py` | `tests/unit/config/foundation/support/serial_cc/telemetry/test_switch_vc_stats.py` |
| `tests/unit/test_data_processing.py` | `tests/unit/config/standalone/foundation/models/core/test_data_processing.py` |
| `tests/unit/test_telemetry.py` | `tests/unit/config/standalone/foundation/models/core/test_telemetry.py` |
| `tests/unit/_test_arango_writer_helpers.py` | `tests/unit/config/standalone/foundation/persistence/arango_writer/_test_arango_writer_helpers.py` |
| `tests/unit/test_arango_writer.py` | `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py` |
| `tests/unit/test_data_browser_path_guard.py` | `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py` |
| `tests/unit/test_data_browser_sqlite_handles.py` | `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_sqlite_handles.py` |
| `tests/unit/test_retention.py` | `tests/unit/config/standalone/foundation/persistence/database/test_retention.py` |
| `tests/unit/test_router.py` | `tests/unit/config/standalone/foundation/persistence/database/test_router.py` |
| `tests/unit/test_redis_json_writer.py` | `tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py` |
| `tests/unit/test_redis_writer.py` | `tests/unit/config/standalone/foundation/persistence/redis/test_redis_writer.py` |
| `tests/unit/test_webhook_ingestion.py` | `tests/unit/config/standalone/foundation/persistence/redis/test_webhook_ingestion.py` |
| `tests/unit/test_config_utils.py` | `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/test_config_utils.py` |
| `tests/unit/test_config_utils_org_id_preflight.py` | `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/test_config_utils_org_id_preflight.py` |
| `tests/unit/test_config_utils_wave3.py` | `tests/unit/config/standalone/foundation/runtime/configuration/standalone_config_utils_tests/test_config_utils_wave3.py` |
| `tests/unit/test_dotenv_precedence.py` | `tests/unit/config/standalone/foundation/runtime/configuration/test_dotenv_precedence.py` |
| `tests/unit/test_environment_guards.py` | `tests/unit/config/standalone/foundation/runtime/configuration/test_environment_guards.py` |
| `tests/unit/test_log_rotation.py` | `tests/unit/config/standalone/foundation/runtime/release/test_log_rotation.py` |
| `tests/unit/test_release_body.py` | `tests/unit/config/standalone/foundation/runtime/release/test_release_body.py` |
| `tests/unit/test_source_dependency_external_symbols.py` | `tests/unit/config/standalone/foundation/runtime/release/test_source_dependency_external_symbols.py` |
| `tests/unit/test_thread_scoped_sleep.py` | `tests/unit/config/standalone/foundation/runtime/release/test_thread_scoped_sleep.py` |
| `tests/unit/test_version_compare.py` | `tests/unit/config/standalone/foundation/runtime/release/test_version_compare.py` |
| `tests/unit/test_container_health_probe.py` | `tests/unit/config/standalone/foundation/runtime/startup/test_container_health_probe.py` |
| `tests/unit/test_dependency_check.py` | `tests/unit/config/standalone/foundation/runtime/startup/test_dependency_check.py` |
| `tests/unit/test_fast_mode_flag.py` | `tests/unit/config/standalone/foundation/runtime/startup/test_fast_mode_flag.py` |
| `tests/unit/test_interactive_test_runner.py` | `tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py` |
| `tests/unit/test_bare_assert_replacements.py` | `tests/unit/config/standalone/foundation/support/quality/assertions/test_bare_assert_replacements.py` |
| `tests/unit/test_hypothesis_example.py` | `tests/unit/config/standalone/foundation/support/quality/assertions/test_hypothesis_example.py` |
| `tests/unit/test_markdown_control_bytes.py` | `tests/unit/config/standalone/foundation/support/quality/assertions/test_markdown_control_bytes.py` |
| `tests/unit/test_ste_writing_guide.py` | `tests/unit/config/standalone/foundation/support/quality/assertions/test_ste_writing_guide.py` |
| `tests/unit/test_issue_2971_status_slice3.py` | `tests/unit/config/standalone/foundation/support/quality/cross_domain/test_issue_2971_status_slice3.py` |
| `tests/unit/test_global_import_manager_package_spec_guards.py` | `tests/unit/config/standalone/foundation/support/quality/imports/test_global_import_manager_package_spec_guards.py` |
| `tests/unit/test_no_mistapi_stub_leak.py` | `tests/unit/config/standalone/foundation/support/quality/imports/test_no_mistapi_stub_leak.py` |
| `tests/unit/test_no_new_legacy_facade_imports.py` | `tests/unit/config/standalone/foundation/support/quality/imports/test_no_new_legacy_facade_imports.py` |
| `tests/unit/test_top5_risk_controls.py` | `tests/unit/config/standalone/foundation/support/quality/risk/test_top5_risk_controls.py` |
| `tests/unit/test_config_package_tracked.py` | `tests/unit/config/standalone/foundation/support/quality/scope/test_config_package_tracked.py` |
| `tests/unit/test_no_export_legacy_callsites.py` | `tests/unit/config/standalone/foundation/support/quality/scope/test_no_export_legacy_callsites.py` |
| `tests/unit/test_src_public_imports.py` | `tests/unit/config/standalone/foundation/support/quality/scope/test_src_public_imports.py` |
| `tests/unit/test_msp_privilege_detection.py` | `tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py` |
| `tests/unit/test_operation_registry_fail_closed.py` | `tests/unit/config/standalone/foundation/support/registry/test_operation_registry_fail_closed.py` |
| `tests/unit/test_systematic_test_offline_mode.py` | `tests/unit/config/standalone/foundation/support/registry/test_systematic_test_offline_mode.py` |
| `tests/unit/test_systematic_test_unregistered_semantics.py` | `tests/unit/config/standalone/foundation/support/registry/test_systematic_test_unregistered_semantics.py` |
| `tests/unit/test_adaptive_pacer.py` | `tests/unit/config/standalone/foundation/support/utilities/network/test_adaptive_pacer.py` |
| `tests/unit/test_address_utils.py` | `tests/unit/config/standalone/foundation/support/utilities/network/test_address_utils.py` |
| `tests/unit/test_rate_limiting.py` | `tests/unit/config/standalone/foundation/support/utilities/network/test_rate_limiting.py` |
| `tests/unit/test_file_path_utils.py` | `tests/unit/config/standalone/foundation/support/utilities/system/test_file_path_utils.py` |
| `tests/unit/test_logger_utils.py` | `tests/unit/config/standalone/foundation/support/utilities/system/test_logger_utils.py` |
| `tests/unit/test_subprocess_runner.py` | `tests/unit/config/standalone/foundation/support/utilities/system/test_subprocess_runner.py` |
| `tests/unit/test_tqdm_wrapper.py` | `tests/unit/config/standalone/foundation/support/utilities/system/test_tqdm_wrapper.py` |
| `tests/unit/maps/test_handler_narrowing.py` | `tests/unit/maps/interfaces/maps/test_handler_narrowing.py` |
| `tests/unit/metrics_gateway/conftest.py` | `tests/unit/maps/interfaces/monitoring/metrics_gateway/conftest.py` |
| `tests/unit/metrics_gateway/test_collector.py` | `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_collector.py` |
| `tests/unit/metrics_gateway/test_prometheus_and_cache.py` | `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_prometheus_and_cache.py` |
| `tests/unit/metrics_gateway/test_snmp_and_service.py` | `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_and_service.py` |
| `tests/unit/metrics_gateway/test_snmp_integration.py` | `tests/unit/maps/interfaces/monitoring/metrics_gateway/test_snmp_integration.py` |
| `tests/unit/ui/test_display_utils.py` | `tests/unit/maps/interfaces/ui/display/test_display_utils.py` |
| `tests/unit/ui/test_output_formatter.py` | `tests/unit/maps/interfaces/ui/display/test_output_formatter.py` |
| `tests/unit/ui/test_device_prompt_rename_guard.py` | `tests/unit/maps/interfaces/ui/interaction/dispatch/test_device_prompt_rename_guard.py` |
| `tests/unit/ui/test_interactive_display_utils.py` | `tests/unit/maps/interfaces/ui/interaction/dispatch/test_interactive_display_utils.py` |
| `tests/unit/ui/test_tui.py` | `tests/unit/maps/interfaces/ui/interaction/tui/test_tui.py` |
| `tests/unit/test_metrics_gateway_org_selection.py` | `tests/unit/maps/standalone/interfaces/monitoring/test_metrics_gateway_org_selection.py` |
| `tests/unit/test_favicon.py` | `tests/unit/maps/standalone/interfaces/portals/test_favicon.py` |
| `tests/unit/test_web_portal_bind_address.py` | `tests/unit/maps/standalone/interfaces/portals/test_web_portal_bind_address.py` |
| `tests/unit/test_issue_2971_status_final.py` | `tests/unit/maps/standalone/interfaces/ui/test_issue_2971_status_final.py` |
| `tests/unit/test_issue_2971_status_slice5.py` | `tests/unit/maps/standalone/interfaces/ui/test_issue_2971_status_slice5.py` |
| `tests/unit/bootstrap/__init__.py` | `tests/unit/marvis/mist/access/audit/__init__.py` |
| `tests/unit/audit/test_audit_analysis_ops.py` | `tests/unit/marvis/mist/access/audit/test_audit_analysis_ops.py` |
| `tests/unit/audit/test_renderer_format_wave9.py` | `tests/unit/marvis/mist/access/audit/test_renderer_format_wave9.py` |
| `tests/unit/audit/test_renderer_time_wave9.py` | `tests/unit/marvis/mist/access/audit/test_renderer_time_wave9.py` |
| `tests/unit/dataproc/__init__.py` | `tests/unit/marvis/mist/access/auth/interactive/__init__.py` |
| `tests/unit/auth/interactive/test_credential_prompter.py` | `tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py` |
| `tests/unit/auth/interactive/test_login_orchestrator.py` | `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` |
| `tests/unit/auth/interactive/test_msp_org_selector.py` | `tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py` |
| `tests/unit/auth/test_interactive_session.py` | `tests/unit/marvis/mist/access/auth/test_interactive_session.py` |
| `tests/unit/analytics/test_data_collection_manager.py` | `tests/unit/marvis/mist/intelligence/analytics/test_data_collection_manager.py` |
| `tests/unit/analytics/test_site_analytics_configurator.py` | `tests/unit/marvis/mist/intelligence/analytics/test_site_analytics_configurator.py` |
| `tests/unit/analytics/test_site_inventory_health_analyzer.py` | `tests/unit/marvis/mist/intelligence/analytics/test_site_inventory_health_analyzer.py` |
| `tests/unit/analytics/test_telemetry_emitter.py` | `tests/unit/marvis/mist/intelligence/analytics/test_telemetry_emitter.py` |
| `tests/unit/reports/alert_digest/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/alert_digest/__init__.py` |
| `tests/unit/reports/alert_digest/conftest.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/alert_digest/conftest.py` |
| `tests/unit/reports/alert_digest/test_alert_digest_client.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/alert_digest/test_alert_digest_client.py` |
| `tests/unit/reports/alert_digest/test_alert_digest_model.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/alert_digest/test_alert_digest_model.py` |
| `tests/unit/reports/alert_digest/test_alert_digest_operation.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/alert_digest/test_alert_digest_operation.py` |
| `tests/unit/reports/ap_scorecard/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/__init__.py` |
| `tests/unit/reports/ap_scorecard/test_ap_scorecard_client.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/cases/test_ap_scorecard_client.py` |
| `tests/unit/reports/ap_scorecard/test_ap_scorecard_model.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/cases/test_ap_scorecard_model.py` |
| `tests/unit/reports/ap_scorecard/test_ap_scorecard_operation.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/cases/test_ap_scorecard_operation.py` |
| `tests/unit/reports/ap_scorecard/conftest.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/conftest.py` |
| `tests/unit/reports/ap_scorecard/test_ap_scorecard_support_files.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/ap_scorecard/test_ap_scorecard_support_files.py` |
| `tests/unit/reports/switch_scorecard/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/switch_scorecard/__init__.py` |
| `tests/unit/reports/switch_scorecard/test_switch_scorecard_client.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/switch_scorecard/test_switch_scorecard_client.py` |
| `tests/unit/reports/switch_scorecard/test_switch_scorecard_model.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/switch_scorecard/test_switch_scorecard_model.py` |
| `tests/unit/reports/switch_scorecard/test_switch_scorecard_operation.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/switch_scorecard/test_switch_scorecard_operation.py` |
| `tests/unit/reports/wan_edge_scorecard/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/wan_edge_scorecard/__init__.py` |
| `tests/unit/reports/wan_edge_scorecard/conftest.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/wan_edge_scorecard/conftest.py` |
| `tests/unit/reports/wan_edge_scorecard/test_scorecard.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/wan_edge_scorecard/test_scorecard.py` |
| `tests/unit/reports/wan_edge_scorecard/test_scoring.py` | `tests/unit/marvis/mist/intelligence/reports/assurance/wan_edge_scorecard/test_scoring.py` |
| `tests/unit/reports/admin_token_hygiene/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/admin_token_hygiene/__init__.py` |
| `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_client.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/admin_token_hygiene/cases/test_admin_token_hygiene_client.py` |
| `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_model.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/admin_token_hygiene/cases/test_admin_token_hygiene_model.py` |
| `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_operation.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/admin_token_hygiene/cases/test_admin_token_hygiene_operation.py` |
| `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_redaction.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/admin_token_hygiene/cases/test_admin_token_hygiene_redaction.py` |
| `tests/unit/reports/admin_token_hygiene/test_admin_token_hygiene_artifacts.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/admin_token_hygiene/test_admin_token_hygiene_artifacts.py` |
| `tests/unit/reports/certificate_expiry/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/certificate_expiry/__init__.py` |
| `tests/unit/reports/certificate_expiry/test_client.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/certificate_expiry/test_client.py` |
| `tests/unit/reports/certificate_expiry/test_model.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/certificate_expiry/test_model.py` |
| `tests/unit/reports/certificate_expiry/test_operation.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/certificate_expiry/test_operation.py` |
| `tests/unit/reports/subscription_expiry/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/__init__.py` |
| `tests/unit/reports/subscription_expiry/test_client.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py` |
| `tests/unit/reports/subscription_expiry/test_model.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py` |
| `tests/unit/reports/subscription_expiry/test_operation.py` | `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py` |
| `tests/unit/reports/client_fingerprint_census/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/client_fingerprint_census/__init__.py` |
| `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_client.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/client_fingerprint_census/test_client_fingerprint_census_client.py` |
| `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_model.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/client_fingerprint_census/test_client_fingerprint_census_model.py` |
| `tests/unit/reports/client_fingerprint_census/test_client_fingerprint_census_operation.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/client_fingerprint_census/test_client_fingerprint_census_operation.py` |
| `tests/unit/reports/org_security_posture/test_api_checks.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/checks/test_api_checks.py` |
| `tests/unit/reports/org_security_posture/test_password_checks.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/checks/test_password_checks.py` |
| `tests/unit/reports/org_security_posture/test_session_checks.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/checks/test_session_checks.py` |
| `tests/unit/reports/org_security_posture/test_setting_switch_checks.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/checks/test_setting_switch_checks.py` |
| `tests/unit/reports/org_security_posture/test_mist_api_sources.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/contracts/test_mist_api_sources.py` |
| `tests/unit/reports/org_security_posture/test_operation_outcome.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/contracts/test_operation_outcome.py` |
| `tests/unit/reports/org_security_posture/test_package_imports.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/contracts/test_package_imports.py` |
| `tests/unit/reports/org_security_posture/test_quickstart_contract.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/contracts/test_quickstart_contract.py` |
| `tests/unit/reports/org_security_posture/test_registry.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/contracts/test_registry.py` |
| `tests/unit/reports/org_security_posture/fixtures/api_posture_cases.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/fixtures/api_posture_cases.py` |
| `tests/unit/reports/org_security_posture/fixtures/representative_org_security_posture.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/fixtures/representative.py` |
| `tests/unit/reports/org_security_posture/test_console_summary.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/presentation/test_console_summary.py` |
| `tests/unit/reports/org_security_posture/test_output_contract.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/presentation/test_output_contract.py` |
| `tests/unit/reports/org_security_posture/test_result_formatting.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/org_security_posture/presentation/test_result_formatting.py` |
| `tests/unit/reports/rogue_pci_evidence/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/rogue_pci_evidence/__init__.py` |
| `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_client.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/rogue_pci_evidence/test_rogue_pci_evidence_client.py` |
| `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_model.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/rogue_pci_evidence/test_rogue_pci_evidence_model.py` |
| `tests/unit/reports/rogue_pci_evidence/test_rogue_pci_evidence_operation.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/rogue_pci_evidence/test_rogue_pci_evidence_operation.py` |
| `tests/unit/reports/site_variable_audit/__init__.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/site_variable_audit/__init__.py` |
| `tests/unit/reports/site_variable_audit/site_variable_audit_client_test.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/site_variable_audit/cases/site_variable_audit_client_test.py` |
| `tests/unit/reports/site_variable_audit/site_variable_audit_contract_test.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/site_variable_audit/cases/site_variable_audit_contract_test.py` |
| `tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/site_variable_audit/cases/site_variable_audit_model_test.py` |
| `tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/site_variable_audit/cases/site_variable_audit_operation_test.py` |
| `tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/site_variable_audit/cases/site_variable_audit_summary_test.py` |
| `tests/unit/reports/site_variable_audit/site_variable_audit_fixtures_test.py` | `tests/unit/marvis/mist/intelligence/reports/audits/posture/site_variable_audit/fixtures_test.py` |
| `tests/unit/reports/test_offline_device_reporter.py` | `tests/unit/marvis/mist/intelligence/reports/device_health/test_offline_device_reporter.py` |
| `tests/unit/reports/test_sfp_transceiver_data_processor.py` | `tests/unit/marvis/mist/intelligence/reports/device_health/test_sfp_transceiver_data_processor.py` |
| `tests/unit/reports/test_ssid_broadcast_gap_report.py` | `tests/unit/marvis/mist/intelligence/reports/device_health/test_ssid_broadcast_gap_report.py` |
| `tests/unit/reports/test_issue_4053_manufacturer_input.py` | `tests/unit/marvis/mist/intelligence/reports/manufacturer_input/test_issue_4053_manufacturer_input.py` |
| `tests/unit/troubleshooting/test_interactive_test_runner.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py` |
| `tests/unit/troubleshooting/test_logged_error_observer_filter.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_logged_error_observer_filter.py` |
| `tests/unit/troubleshooting/test_marvis_troubleshoot_utils.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_marvis_troubleshoot_utils.py` |
| `tests/unit/troubleshooting/test_marvis_troubleshoot_utils_extended.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_marvis_troubleshoot_utils_extended.py` |
| `tests/unit/troubleshooting/test_troubleshoot_utils.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_troubleshoot_utils.py` |
| `tests/unit/troubleshooting/nac_idp_credential_test/__init__.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/credential_tests/__init__.py` |
| `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_client.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/credential_tests/test_nac_idp_credential_test_client.py` |
| `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_model.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/credential_tests/test_nac_idp_credential_test_model.py` |
| `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_operation.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/credential_tests/test_nac_idp_credential_test_operation.py` |
| `tests/unit/troubleshooting/nac_idp_credential_test/test_nac_idp_credential_test_package.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/credential_tests/test_nac_idp_credential_test_package.py` |
| `tests/unit/troubleshooting/rf_diagnostics/__init__.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/__init__.py` |
| `tests/unit/troubleshooting/rf_diagnostics/test_audit.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/audit_requests/test_audit.py` |
| `tests/unit/troubleshooting/rf_diagnostics/test_client_requests.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/audit_requests/test_client_requests.py` |
| `tests/unit/troubleshooting/rf_diagnostics/test_file_naming.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/audit_requests/test_file_naming.py` |
| `tests/unit/troubleshooting/rf_diagnostics/test_operation_flow.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/audit_requests/test_operation_flow.py` |
| `tests/unit/troubleshooting/rf_diagnostics/test_recording_flow.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/recording_spectrum/test_recording_flow.py` |
| `tests/unit/troubleshooting/rf_diagnostics/test_spectrum_flow.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/rf_diagnostics/recording_spectrum/test_spectrum_flow.py` |
| `tests/unit/troubleshooting/sms_provider_test/__init__.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/sms_provider_tests/__init__.py` |
| `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_client.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/sms_provider_tests/test_sms_provider_test_client.py` |
| `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_model.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/sms_provider_tests/test_sms_provider_test_model.py` |
| `tests/unit/troubleshooting/sms_provider_test/test_sms_provider_test_operation.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/sms_provider_tests/test_sms_provider_test_operation.py` |
| `tests/unit/troubleshooting/synthetic_test_trigger/__init__.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/synthetic_trigger/__init__.py` |
| `tests/unit/troubleshooting/synthetic_test_trigger/test_synthetic_test_trigger.py` | `tests/unit/marvis/mist/intelligence/troubleshooting/synthetic_trigger/test_synthetic_test_trigger.py` |
| `tests/unit/device/test_device_handler_narrowing.py` | `tests/unit/marvis/mist/resources/device/test_device_handler_narrowing.py` |
| `tests/unit/gateway/test_gateway_ha_exporter.py` | `tests/unit/marvis/mist/resources/gateway/exporters/test_gateway_ha_exporter.py` |
| `tests/unit/gateway/test_gateway_stats_exporter.py` | `tests/unit/marvis/mist/resources/gateway/exporters/test_gateway_stats_exporter.py` |
| `tests/unit/gateway/overrides/__init__.py` | `tests/unit/marvis/mist/resources/gateway/overrides/__init__.py` |
| `tests/unit/gateway/overrides/test_cisco_config_converter.py` | `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` |
| `tests/unit/gateway/overrides/test_device_data_fetcher.py` | `tests/unit/marvis/mist/resources/gateway/overrides/test_device_data_fetcher.py` |
| `tests/unit/gateway/overrides/test_override_classifier.py` | `tests/unit/marvis/mist/resources/gateway/overrides/test_override_classifier.py` |
| `tests/unit/gateway/overrides/test_override_report_writer.py` | `tests/unit/marvis/mist/resources/gateway/overrides/test_override_report_writer.py` |
| `tests/unit/gateway/ssr_registration/__init__.py` | `tests/unit/marvis/mist/resources/gateway/ssr_registration/__init__.py` |
| `tests/unit/gateway/ssr_registration/test_ssr_registration_commands.py` | `tests/unit/marvis/mist/resources/gateway/ssr_registration/test_ssr_registration_commands.py` |
| `tests/unit/gateway/test_wan_override_walker.py` | `tests/unit/marvis/mist/resources/gateway/wan_overrides/test_wan_override_walker.py` |
| `tests/unit/gateway/test_wan_override_walker_extended.py` | `tests/unit/marvis/mist/resources/gateway/wan_overrides/test_wan_override_walker_extended.py` |
| `tests/unit/inventory/csv_imports/__init__.py` | `tests/unit/marvis/mist/resources/inventory/csv_imports/__init__.py` |
| `tests/unit/inventory/csv_imports/test_csv_imports_client.py` | `tests/unit/marvis/mist/resources/inventory/csv_imports/test_csv_imports_client.py` |
| `tests/unit/inventory/csv_imports/test_csv_imports_model.py` | `tests/unit/marvis/mist/resources/inventory/csv_imports/test_csv_imports_model.py` |
| `tests/unit/inventory/csv_imports/test_csv_imports_operation.py` | `tests/unit/marvis/mist/resources/inventory/csv_imports/test_csv_imports_operation.py` |
| `tests/unit/inventory/device_replace/__init__.py` | `tests/unit/marvis/mist/resources/inventory/device_replace/__init__.py` |
| `tests/unit/inventory/device_replace/test_rma_device_replace_client.py` | `tests/unit/marvis/mist/resources/inventory/device_replace/test_rma_device_replace_client.py` |
| `tests/unit/inventory/device_replace/test_rma_device_replace_model.py` | `tests/unit/marvis/mist/resources/inventory/device_replace/test_rma_device_replace_model.py` |
| `tests/unit/inventory/device_replace/test_rma_device_replace_operation.py` | `tests/unit/marvis/mist/resources/inventory/device_replace/test_rma_device_replace_operation.py` |
| `tests/unit/inventory/inventory_summary/__init__.py` | `tests/unit/marvis/mist/resources/inventory/inventory_summary/__init__.py` |
| `tests/unit/inventory/inventory_summary/test_pivot_renderer.py` | `tests/unit/marvis/mist/resources/inventory/inventory_summary/test_pivot_renderer.py` |
| `tests/unit/inventory/test_version_per_model_fetcher_wave3.py` | `tests/unit/marvis/mist/resources/inventory/support/versioning/test_version_per_model_fetcher_wave3.py` |
| `tests/unit/prod_readiness/__init__.py` | `tests/unit/marvis/mist/resources/site/__init__.py` |
| `tests/unit/site/rrm_reset/__init__.py` | `tests/unit/marvis/mist/resources/site/rrm_reset/__init__.py` |
| `tests/unit/site/rrm_reset/test_rrm_dry_run_policy.py` | `tests/unit/marvis/mist/resources/site/rrm_reset/test_rrm_dry_run_policy.py` |
| `tests/unit/site/rrm_reset/test_rrm_reset_client.py` | `tests/unit/marvis/mist/resources/site/rrm_reset/test_rrm_reset_client.py` |
| `tests/unit/site/rrm_reset/test_rrm_reset_model.py` | `tests/unit/marvis/mist/resources/site/rrm_reset/test_rrm_reset_model.py` |
| `tests/unit/site/rrm_reset/test_rrm_reset_operation.py` | `tests/unit/marvis/mist/resources/site/rrm_reset/test_rrm_reset_operation.py` |
| `tests/unit/site/test_site_config_manager.py` | `tests/unit/marvis/mist/resources/site/test_site_config_manager.py` |
| `tests/unit/site/test_site_config_manager_extended.py` | `tests/unit/marvis/mist/resources/site/test_site_config_manager_extended.py` |
| `tests/unit/test_api_tenant_fetch.py` | `tests/unit/marvis/standalone/mist/access/api/test_api_tenant_fetch.py` |
| `tests/unit/test_issue_2971_status_before_count.py` | `tests/unit/marvis/standalone/mist/access/api/test_issue_2971_status_before_count.py` |
| `tests/unit/test_mistapi_api_response_boundary.py` | `tests/unit/marvis/standalone/mist/access/api/test_mistapi_api_response_boundary.py` |
| `tests/unit/test_openapi_spec_refresh.py` | `tests/unit/marvis/standalone/mist/access/api/test_openapi_spec_refresh.py` |
| `tests/unit/test_audit_analyzer.py` | `tests/unit/marvis/standalone/mist/access/audit/test_audit_analyzer.py` |
| `tests/unit/test_audit_filter.py` | `tests/unit/marvis/standalone/mist/access/audit/test_audit_filter.py` |
| `tests/unit/test_audit_time_parser.py` | `tests/unit/marvis/standalone/mist/access/audit/test_audit_time_parser.py` |
| `tests/unit/test_marvis_utils.py` | `tests/unit/marvis/standalone/mist/intelligence/marvis/test_marvis_utils.py` |
| `tests/unit/test_e911_bssid.py` | `tests/unit/marvis/standalone/mist/intelligence/reports/test_e911_bssid.py` |
| `tests/unit/test_issue_2971_status_slice4.py` | `tests/unit/marvis/standalone/mist/intelligence/reports/test_issue_2971_status_slice4.py` |
| `tests/unit/test_offline_device_reporter.py` | `tests/unit/marvis/standalone/mist/intelligence/reports/test_standalone_offline_device_reporter.py` |
| `tests/unit/test_multi_ap_scan_workflow.py` | `tests/unit/marvis/standalone/mist/resources/device/test_device_multi_ap_scan_workflow.py` |
| `tests/unit/test_device_utility_commands_wave3.py` | `tests/unit/marvis/standalone/mist/resources/device/test_device_utility_commands_wave3.py` |
| `tests/unit/test_gateway_override_analysis.py` | `tests/unit/marvis/standalone/mist/resources/gateway/test_gateway_override_analysis.py` |
| `tests/unit/test_org_license_async_claim_status.py` | `tests/unit/marvis/standalone/mist/resources/org/test_org_license_async_claim_status.py` |
| `tests/unit/test_org_ticket_manager.py` | `tests/unit/marvis/standalone/mist/resources/org/test_org_ticket_manager.py` |
| `tests/unit/test_bulk_radius_wlan_config_manager.py` | `tests/unit/marvis/standalone/mist/resources/site/test_bulk_radius_wlan_config_manager.py` |
| `tests/unit/test_bulk_radius_wlan_snapshot.py` | `tests/unit/marvis/standalone/mist/resources/site/test_bulk_radius_wlan_snapshot.py` |
| `tests/unit/capture/test_client_pcap_downloader.py` | `tests/unit/prod_readiness/operations/execution/capture/client_download/test_client_pcap_downloader.py` |
| `tests/unit/capture/test_client_pcap_downloader_network_paths.py` | `tests/unit/prod_readiness/operations/execution/capture/client_download/test_client_pcap_downloader_network_paths.py` |
| `tests/unit/capture/test_multi_ap_scan_workflow.py` | `tests/unit/prod_readiness/operations/execution/capture/device_scan/test_multi_ap_scan_workflow.py` |
| `tests/unit/capture/test_packet_capture_download.py` | `tests/unit/prod_readiness/operations/execution/capture/packet_capture/test_packet_capture_download.py` |
| `tests/unit/capture/test_packet_capture_manager.py` | `tests/unit/prod_readiness/operations/execution/capture/packet_capture/test_packet_capture_manager.py` |
| `tests/unit/capture/test_packet_capture_payload_logging.py` | `tests/unit/prod_readiness/operations/execution/capture/packet_capture/test_packet_capture_payload_logging.py` |
| `tests/unit/capture/test_org_pcap_wait_download_workflow.py` | `tests/unit/prod_readiness/operations/execution/capture/site_download/test_org_pcap_wait_download_workflow.py` |
| `tests/unit/capture/test_site_pcap_wait_download_workflow.py` | `tests/unit/prod_readiness/operations/execution/capture/site_download/test_site_pcap_wait_download_workflow.py` |
| `tests/unit/firmware_policy/__init__.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/__init__.py` |
| `tests/unit/firmware_policy/test_admission.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/changes/test_admission.py` |
| `tests/unit/firmware_policy/test_backup.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/changes/test_backup.py` |
| `tests/unit/firmware_policy/test_catalog.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/changes/test_catalog.py` |
| `tests/unit/firmware_policy/test_changes.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/changes/test_changes.py` |
| `tests/unit/firmware_policy/conftest.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/conftest.py` |
| `tests/unit/firmware_policy/fakes.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/fakes.py` |
| `tests/unit/firmware_policy/recovery/__init__.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/__init__.py` |
| `tests/unit/firmware_policy/recovery/test_bundle.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/bundles/test_bundle.py` |
| `tests/unit/firmware_policy/recovery/test_schema.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/bundles/test_schema.py` |
| `tests/unit/firmware_policy/recovery/fakes.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/fakes.py` |
| `tests/unit/firmware_policy/recovery/test_selection.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/selection/test_selection.py` |
| `tests/unit/firmware_policy/recovery/test_windows_access.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy/recovery/selection/test_windows_access.py` |
| `tests/unit/firmware_policy_jobs/__init__.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy_jobs/__init__.py` |
| `tests/unit/firmware_policy_jobs/comparisons/conftest.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy_jobs/comparisons/conftest.py` |
| `tests/unit/firmware_policy_jobs/comparisons/test_evidence.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy_jobs/comparisons/test_evidence.py` |
| `tests/unit/firmware_policy_jobs/comparisons/test_policies.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy_jobs/comparisons/test_policies.py` |
| `tests/unit/firmware_policy_jobs/comparisons/test_progress.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy_jobs/comparisons/test_progress.py` |
| `tests/unit/firmware_policy_jobs/test_manager.py` | `tests/unit/prod_readiness/operations/execution/firmware/policy_jobs/test_manager.py` |
| `tests/unit/firmware/test_aggregate_child_controls.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_child_controls.py` |
| `tests/unit/firmware/test_aggregate_ended_child_cancel.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_ended_child_cancel.py` |
| `tests/unit/firmware/test_aggregate_final_cancel.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_final_cancel.py` |
| `tests/unit/firmware/test_aggregate_mixed_cancel_state.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/aggregations/test_aggregate_mixed_cancel_state.py` |
| `tests/unit/firmware/test_firmware_manager_ssr.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/platform/test_firmware_manager_ssr.py` |
| `tests/unit/firmware/test_firmware_manager_ap_msp.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/site/test_firmware_manager_ap_msp.py` |
| `tests/unit/firmware/test_firmware_manager_proxy.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/manager/site/test_firmware_manager_proxy.py` |
| `tests/unit/firmware/test_org_advanced_bodies.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py` |
| `tests/unit/firmware/test_org_cancel_sort.py` | `tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_cancel_sort.py` |
| `tests/unit/site/address_audit/__init__.py` | `tests/unit/prod_readiness/operations/execution/prod_readiness/__init__.py` |
| `tests/unit/prod_readiness/test_resource_cleanup_on_error_paths.py` | `tests/unit/prod_readiness/operations/execution/prod_readiness/test_resource_cleanup_on_error_paths.py` |
| `tests/unit/prod_readiness/test_subprocess_timeouts.py` | `tests/unit/prod_readiness/operations/execution/prod_readiness/test_subprocess_timeouts.py` |
| `tests/unit/container/__init__.py` | `tests/unit/prod_readiness/operations/exporting/container/__init__.py` |
| `tests/unit/container/bash_support.py` | `tests/unit/prod_readiness/operations/exporting/container/build_support/bash_support.py` |
| `tests/unit/container/owner_only.py` | `tests/unit/prod_readiness/operations/exporting/container/build_support/owner_only.py` |
| `tests/unit/container/test_build_files_match.py` | `tests/unit/prod_readiness/operations/exporting/container/build_support/test_build_files_match.py` |
| `tests/unit/container/test_openapi_in_image.py` | `tests/unit/prod_readiness/operations/exporting/container/build_support/test_openapi_in_image.py` |
| `tests/unit/container/test_access_log_format.py` | `tests/unit/prod_readiness/operations/exporting/container/runtime/test_access_log_format.py` |
| `tests/unit/container/test_misthelper_session_script.py` | `tests/unit/prod_readiness/operations/exporting/container/runtime/test_misthelper_session_script.py` |
| `tests/unit/container/test_startup_no_recursive_chown.py` | `tests/unit/prod_readiness/operations/exporting/container/runtime/test_startup_no_recursive_chown.py` |
| `tests/unit/container/test_write_session_env_script.py` | `tests/unit/prod_readiness/operations/exporting/container/runtime/test_write_session_env_script.py` |
| `tests/unit/container/session_database/__init__.py` | `tests/unit/prod_readiness/operations/exporting/container/session_database/__init__.py` |
| `tests/unit/container/session_database/harness.py` | `tests/unit/prod_readiness/operations/exporting/container/session_database/harness.py` |
| `tests/unit/container/session_database/test_environment.py` | `tests/unit/prod_readiness/operations/exporting/container/session_database/test_environment.py` |
| `tests/unit/container/session_database/test_export.py` | `tests/unit/prod_readiness/operations/exporting/container/session_database/test_export.py` |
| `tests/unit/juniper_rma/__init__.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/__init__.py` |
| `tests/unit/juniper_rma/api/__init__.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/api/__init__.py` |
| `tests/unit/juniper_rma/api/test_fixture_replies.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/api/transport/test_fixture_replies.py` |
| `tests/unit/juniper_rma/api/test_read_gets.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/api/transport/test_read_gets.py` |
| `tests/unit/juniper_rma/fixtures/__init__.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/fixtures/__init__.py` |
| `tests/unit/juniper_rma/fixtures/capturing.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/fixtures/capturing.py` |
| `tests/unit/juniper_rma/fixtures/read_replies.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/fixtures/read_replies.py` |
| `tests/unit/juniper_rma/model/__init__.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/model/__init__.py` |
| `tests/unit/juniper_rma/model/test_request_rows.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/model/rows/test_request_rows.py` |
| `tests/unit/juniper_rma/workflows/__init__.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/workflows/__init__.py` |
| `tests/unit/juniper_rma/workflows/test_read_menus_live.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/workflows/menus/test_read_menus_live.py` |
| `tests/unit/juniper_rma/workflows/test_read_menus_offline.py` | `tests/unit/prod_readiness/operations/exporting/juniper_rma/workflows/menus/test_read_menus_offline.py` |
| `tests/unit/mib_generator/__init__.py` | `tests/unit/prod_readiness/operations/hardware/mib_generator/__init__.py` |
| `tests/unit/mib_generator/test_cli_wiring.py` | `tests/unit/prod_readiness/operations/hardware/mib_generator/cli/test_cli_wiring.py` |
| `tests/unit/mib_generator/fixtures/mini_openapi.json` | `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/fixtures/mini_openapi.json` |
| `tests/unit/mib_generator/test_mib_generator.py` | `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_mib_generator.py` |
| `tests/unit/mib_generator/test_properties.py` | `tests/unit/prod_readiness/operations/hardware/mib_generator/generator/test_properties.py` |
| `tests/unit/mib_generator/test_performance.py` | `tests/unit/prod_readiness/operations/hardware/mib_generator/performance/test_performance.py` |
| `tests/unit/security/__init__.py` | `tests/unit/prod_readiness/operations/protection/security/__init__.py` |
| `tests/unit/security/test_credential_redaction.py` | `tests/unit/prod_readiness/operations/protection/security/test_credential_redaction.py` |
| `tests/unit/test_org_pcap_wait_download.py` | `tests/unit/prod_readiness/standalone/operations/execution/capture/test_org_pcap_wait_download.py` |
| `tests/unit/test_packet_capture.py` | `tests/unit/prod_readiness/standalone/operations/execution/capture/test_packet_capture.py` |
| `tests/unit/test_site_pcap_wait_download.py` | `tests/unit/prod_readiness/standalone/operations/execution/capture/test_site_pcap_wait_download.py` |
| `tests/unit/test_bulk_ap_upgrader.py` | `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_bulk_ap_upgrader.py` |
| `tests/unit/test_org_ap_upgrader.py` | `tests/unit/prod_readiness/standalone/operations/execution/firmware/test_org_ap_upgrader.py` |
| `tests/unit/test_ssh_runner.py` | `tests/unit/prod_readiness/standalone/operations/execution/ssh/test_ssh_runner.py` |
| `tests/unit/test_ssid_template_consolidation.py` | `tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py` |
| `tests/unit/test_menu_12_inventory.py` | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_12_inventory.py` |
| `tests/unit/test_menu_13_device_stats.py` | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py` |
| `tests/unit/test_menu_19_device_port_stats.py` | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_19_device_port_stats.py` |
| `tests/unit/test_menu_25_combined_inventory.py` | `tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_25_combined_inventory.py` |
| `tests/unit/test_operation_output_file_discovery.py` | `tests/unit/prod_readiness/standalone/operations/exporting/quality/test_operation_output_file_discovery.py` |
| `tests/unit/test_exports.py` | `tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py` |
| `tests/unit/test_pk_strategies.py` | `tests/unit/prod_readiness/standalone/operations/exporting/reports/test_pk_strategies.py` |
| `tests/unit/test_wifi_clients_exporter.py` | `tests/unit/prod_readiness/standalone/operations/exporting/reports/test_wifi_clients_exporter.py` |
| `tests/unit/test_org_data_collector.py` | `tests/unit/prod_readiness/standalone/operations/wan/test_org_data_collector.py` |
| `tests/unit/test_wan_hub_group_manager.py` | `tests/unit/prod_readiness/standalone/operations/wan/test_wan_hub_group_manager.py` |
| `tests/unit/test_wan_vpn_builder.py` | `tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py` |
