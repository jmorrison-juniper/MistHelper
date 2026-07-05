# Coding Guideline Compliance Report

- **Generated**: 2026-07-05 02:03:06 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 249

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 95.0 / 100
- **Overall grade**: A

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| src\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\analytics\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\analytics\site_analytics_configurator.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\analytics\site_inventory_health_analyzer.py | 78.0 | C+ | 0 | 1 | 4 | 4 | 9 |
| src\analytics\zone_analyzer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\api\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\api\tenant_fetch.py | 88.0 | B+ | 0 | 1 | 0 | 6 | 7 |
| src\audit\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_delta.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_format.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_html.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_mermaid.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_time.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\analyzer.py | 80.0 | B- | 0 | 1 | 4 | 2 | 7 |
| src\audit\filter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\renderer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\time_parser.py | 85.0 | B | 0 | 1 | 2 | 3 | 6 |
| src\auth\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\auth\interactive\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\clouds.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\credential_prompter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\login_orchestrator.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\msp_org_selector.py | 98.0 | A+ | 0 | 0 | 0 | 2 | 2 |
| src\bootstrap\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\bootstrap\dependency_check.py | 90.0 | A- | 0 | 1 | 0 | 4 | 5 |
| src\bootstrap\package_installer.py | 89.0 | B+ | 0 | 1 | 1 | 2 | 4 |
| src\bootstrap\uv_runtime.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\capture\_packet_capture_exec.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\_packet_capture_org.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\_packet_capture_prompts.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\_packet_capture_tcpdump.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\multi_ap_scan_workflow.py | 77.0 | C+ | 0 | 2 | 11 | 0 | 13 |
| src\capture\org_capture_workflow.py | 91.0 | A- | 0 | 1 | 1 | 0 | 2 |
| src\capture\org_pcap_wait_download_workflow.py | 94.0 | A | 0 | 0 | 2 | 0 | 2 |
| src\capture\packet_capture.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\packet_capture_download.py | 75.0 | C | 0 | 1 | 5 | 5 | 11 |
| src\capture\site_capture_loop.py | 91.0 | A- | 0 | 1 | 1 | 0 | 2 |
| src\capture\site_pcap_wait_download_workflow.py | 94.0 | A | 0 | 0 | 2 | 0 | 2 |
| src\constants.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\batch_worker.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\export_backend_options.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\family_selection_context.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\map_clone_deps.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\map_marker_deps.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\map_scaling_deps.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\map_viewer_deps.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\map_wizard_deps.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\msp_org_context.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\progress_event.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\site_auto_upgrade_deps.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\systematic_test_option.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\dataclasses\websocket_stream_target.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\db\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\db\arango_writer.py | 75.0 | C | 0 | 1 | 4 | 7 | 12 |
| src\db\redis_writer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\db\retention.py | 91.0 | A- | 0 | 1 | 1 | 0 | 2 |
| src\db\router.py | 84.0 | B | 0 | 1 | 3 | 1 | 5 |
| src\device\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\_utility_commands_action.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\_utility_commands_clear.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\_utility_commands_cluster.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\_utility_commands_selection.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\_utility_commands_show.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\_utility_commands_websocket.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\prompt_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\utility_commands.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\device\virtual_chassis.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\device_events_52w_exporter.py | 84.0 | B | 0 | 2 | 1 | 1 | 4 |
| src\export\site_export_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\site_insights\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\site_insights\device_metric_operation.py | 79.0 | C+ | 0 | 1 | 5 | 0 | 6 |
| src\export\site_insights\site_metric_operation.py | 91.0 | A- | 0 | 0 | 3 | 0 | 3 |
| src\export\site_insights_exporter.py | 84.0 | B | 0 | 2 | 1 | 1 | 4 |
| src\export\wifi_clients_exporter.py | 86.0 | B | 0 | 0 | 4 | 2 | 6 |
| src\firmware\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\firmware\bulk_ap_upgrader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\firmware\bulk_switch_upgrader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\firmware\firmware_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\firmware\org_ap_upgrader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\firmware\site_auto_upgrade.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\_wan2_variable_cluster.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\_wan2_variable_device.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\_wan2_variable_io.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\_wan2_variable_reporting.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\_wan2_variable_selection.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\_wan2_variable_template.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\device_template_cloner.py | 84.0 | B | 0 | 1 | 2 | 4 | 7 |
| src\gateway\gateway_export_utils.py | 69.0 | D+ | 0 | 4 | 2 | 5 | 11 |
| src\gateway\gateway_stats_exporter.py | 75.0 | C | 0 | 2 | 3 | 4 | 9 |
| src\gateway\overrides\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\_deps.py | 91.0 | A- | 0 | 1 | 1 | 0 | 2 |
| src\gateway\overrides\device_data_fetcher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\override_classifier.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\override_report_writer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\wan_override_walker.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\template_config.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\wan2_migration_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\wan2_variable.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\wan_probe_device_override_manager.py | 71.0 | C- | 0 | 2 | 3 | 8 | 13 |
| src\inventory\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\csv_comparator.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\inventory_summary\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\inventory_summary\pivot_renderer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\inventory_summary\version_per_model_fetcher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\org_device_inventory_msp.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\org_device_inventory_summary.py | 79.0 | C+ | 0 | 1 | 3 | 6 | 10 |
| src\maps\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_container_detection.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_flask_viewer.py | 74.0 | C | 0 | 5 | 0 | 0 | 5 |
| src\maps\_maps_backup.py | 65.0 | D | 0 | 4 | 2 | 5 | 11 |
| src\maps\_maps_clone.py | 84.0 | B | 0 | 1 | 2 | 4 | 7 |
| src\maps\_maps_coverage.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_matplotlib.py | 82.0 | B- | 0 | 2 | 1 | 3 | 6 |
| src\maps\_maps_testing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_utils.py | 91.0 | A- | 0 | 1 | 1 | 0 | 2 |
| src\maps\_maps_wizard.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_plotly_viewer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_viewer_launch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_clone.py | 77.0 | C+ | 0 | 0 | 5 | 8 | 13 |
| src\maps\launcher\_viewer_drawing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_refresh.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_site_switch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_ui.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_url_switch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\viewer_callbacks.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\viewer_state.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\maps_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\plotly_heatmap_renderer.py | 73.0 | C | 0 | 4 | 1 | 1 | 6 |
| src\maps\plotly_map_callback_manager.py | 82.0 | B- | 0 | 2 | 1 | 3 | 6 |
| src\maps\plotly_map_figure_builder.py | 75.0 | C | 0 | 2 | 3 | 4 | 9 |
| src\maps\plotly_map_serializer.py | 88.0 | B+ | 0 | 2 | 0 | 0 | 2 |
| src\maps\plotly_map_templates.py | 84.0 | B | 0 | 2 | 1 | 1 | 4 |
| src\marvis\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\marvis\marvis_utils.py | 78.0 | C+ | 0 | 1 | 4 | 4 | 9 |
| src\network\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_display.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_forwarding.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_parsing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_payload.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_routing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_ssr.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\routing_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\org_data_collector.py | 82.0 | B- | 0 | 1 | 4 | 0 | 5 |
| src\refactors\serial_cc\global_assignments_builder.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\import_initialization_service.py | 95.0 | A | 0 | 0 | 1 | 2 | 3 |
| src\refactors\serial_cc\security_events.py | 75.0 | C | 0 | 2 | 4 | 1 | 7 |
| src\refactors\serial_cc\site_client_insights.py | 89.0 | B+ | 0 | 1 | 1 | 2 | 4 |
| src\refactors\serial_cc\sle_metrics.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\start_site_client_capture_wireless.py | 88.0 | B+ | 0 | 1 | 1 | 3 | 5 |
| src\refactors\serial_cc\start_site_scan_capture.py | 88.0 | B+ | 0 | 1 | 1 | 3 | 5 |
| src\refactors\serial_cc\switch_vc_stats.py | 85.0 | B | 0 | 0 | 4 | 3 | 7 |
| src\refactors\serial_cc\test_results_by_site.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\reports\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\reports\e911_bssid.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\address_corrector.py | 94.0 | A | 0 | 0 | 1 | 3 | 4 |
| src\site\address_audit\address_resolver.py | 86.0 | B | 0 | 0 | 3 | 5 | 8 |
| src\site\address_audit\audit_engine.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\audit_reporter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\business_authority_ingester.py | 95.0 | A | 0 | 0 | 1 | 2 | 3 |
| src\site\address_audit\comparison_display.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\csv_ingester.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\models.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\perf.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\site_matcher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\snmp_enricher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\suite_patterns.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\ui_geocoder.py | 88.0 | B+ | 0 | 0 | 3 | 3 | 6 |
| src\site\site_config_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\batch_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\host_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\interactive_batch_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\multi_host_runner.py | 73.0 | C | 0 | 6 | 5 | 1 | 12 |
| src\ssh\command\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\command\command_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\command_parser.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\csv_loader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\env_loader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\host_parser.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\validators.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\connection\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\connection\connector.py | 86.0 | B | 0 | 0 | 4 | 2 | 6 |
| src\ssh\runtime\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\runtime\app_runner.py | 68.0 | D+ | 0 | 3 | 4 | 4 | 11 |
| src\ssh\runtime\interactive_mode.py | 97.0 | A+ | 0 | 0 | 1 | 0 | 1 |
| src\ssh\shell_execution\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\shell_execution\shell_executor.py | 88.0 | B+ | 0 | 0 | 3 | 3 | 6 |
| src\ssh\ssh_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\ssh_runner_manager.py | 75.0 | C | 0 | 1 | 4 | 7 | 12 |
| src\ssid_consolidation\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_cache.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_cluster.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_phase1.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_phase2.py | 84.0 | B | 0 | 1 | 2 | 4 | 7 |
| src\ssid_consolidation\_ssid_template_phase3.py | 86.0 | B | 0 | 1 | 2 | 2 | 5 |
| src\ssid_consolidation\_ssid_template_phase45.py | 86.0 | B | 0 | 1 | 2 | 2 | 5 |
| src\ssid_consolidation\ssid_template_consolidation.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\troubleshooting\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\troubleshooting\interactive_test_runner.py | 75.0 | C | 0 | 3 | 3 | 2 | 8 |
| src\troubleshooting\marvis_troubleshoot_utils.py | 72.0 | C- | 0 | 1 | 6 | 4 | 11 |
| src\ui\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\execution\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\execution\debug_saver.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\execution\function_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\execution\item_executor.py | 88.0 | B+ | 0 | 1 | 1 | 3 | 5 |
| src\ui\execution\output_formatter.py | 93.0 | A | 0 | 1 | 0 | 1 | 2 |
| src\ui\execution\parameter_collector.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\input_handlers\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\input_handlers\key_poller.py | 95.0 | A | 0 | 0 | 1 | 2 | 3 |
| src\ui\input_handlers\keyboard_dispatch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\layout\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\layout\layout_builder.py | 94.0 | A | 0 | 0 | 2 | 0 | 2 |
| src\ui\layout\results_grid_builder.py | 88.0 | B+ | 0 | 1 | 0 | 6 | 7 |
| src\ui\runtime\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\runtime\dotenv_loader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\runtime\level_discoverer.py | 93.0 | A | 0 | 1 | 0 | 1 | 2 |
| src\ui\runtime\tui_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\tui.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\address_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\input_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\logger_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\rate_limiting.py | 75.0 | C | 0 | 3 | 2 | 1 | 6 |
| src\wan_hub_group_manager.py | 88.0 | B+ | 0 | 1 | 2 | 0 | 3 |
| src\wan_vpn_builder.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\websocket\commands.py | 86.0 | B | 0 | 0 | 3 | 5 | 8 |
| src\websocket\context.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\diagnostics\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\diagnostics\arp_executor.py | 80.0 | B- | 0 | 0 | 6 | 2 | 8 |
| src\websocket\diagnostics\common.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\diagnostics\ping_executor.py | 79.0 | C+ | 0 | 2 | 3 | 1 | 6 |
| src\websocket\manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\completion_detector.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\message_router.py | 90.0 | A- | 0 | 1 | 0 | 4 | 5 |
| src\websocket\polling\result_collector.py | 89.0 | B+ | 0 | 1 | 1 | 2 | 4 |
| src\websocket\polling\result_combiner.py | 83.0 | B | 0 | 2 | 1 | 2 | 5 |
| src\websocket\service_ping_discovery.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\service_ping_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |

## Machine-Readable Summary

```json
{
  "overall_score": 95.0,
  "overall_grade": "A",
  "severity_totals": {
    "critical": 0,
    "high": 102,
    "medium": 172,
    "low": 188
  },
  "rule_totals": {
    "ARCH-DELEGATE": 1,
    "CONV-COMMENTS": 68,
    "STRUCT-BLOCKS": 33,
    "STRUCT-COMPLEXITY": 156,
    "STRUCT-LENGTH": 171,
    "STRUCT-NESTING": 1,
    "STRUCT-PARAMS": 32
  },
  "files": [
    {
      "path": "src\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\analytics\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\analytics\\site_analytics_configurator.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\analytics\\site_inventory_health_analyzer.py",
      "score": 78.0,
      "grade": "C+",
      "violations": 9
    },
    {
      "path": "src\\analytics\\zone_analyzer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\api\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\api\\tenant_fetch.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 7
    },
    {
      "path": "src\\audit\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\_renderer_delta.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\_renderer_format.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\_renderer_html.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\_renderer_mermaid.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\_renderer_time.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\analyzer.py",
      "score": 80.0,
      "grade": "B-",
      "violations": 7
    },
    {
      "path": "src\\audit\\filter.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\renderer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\audit\\time_parser.py",
      "score": 85.0,
      "grade": "B",
      "violations": 6
    },
    {
      "path": "src\\auth\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\auth\\interactive\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\auth\\interactive\\clouds.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\auth\\interactive\\credential_prompter.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\auth\\interactive\\login_orchestrator.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\auth\\interactive\\msp_org_selector.py",
      "score": 98.0,
      "grade": "A+",
      "violations": 2
    },
    {
      "path": "src\\bootstrap\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\bootstrap\\dependency_check.py",
      "score": 90.0,
      "grade": "A-",
      "violations": 5
    },
    {
      "path": "src\\bootstrap\\package_installer.py",
      "score": 89.0,
      "grade": "B+",
      "violations": 4
    },
    {
      "path": "src\\bootstrap\\uv_runtime.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\capture\\_packet_capture_exec.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\_packet_capture_org.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\_packet_capture_prompts.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\_packet_capture_tcpdump.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\multi_ap_scan_workflow.py",
      "score": 77.0,
      "grade": "C+",
      "violations": 13
    },
    {
      "path": "src\\capture\\org_capture_workflow.py",
      "score": 91.0,
      "grade": "A-",
      "violations": 2
    },
    {
      "path": "src\\capture\\org_pcap_wait_download_workflow.py",
      "score": 94.0,
      "grade": "A",
      "violations": 2
    },
    {
      "path": "src\\capture\\packet_capture.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\packet_capture_download.py",
      "score": 75.0,
      "grade": "C",
      "violations": 11
    },
    {
      "path": "src\\capture\\site_capture_loop.py",
      "score": 91.0,
      "grade": "A-",
      "violations": 2
    },
    {
      "path": "src\\capture\\site_pcap_wait_download_workflow.py",
      "score": 94.0,
      "grade": "A",
      "violations": 2
    },
    {
      "path": "src\\constants.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\batch_worker.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\export_backend_options.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\family_selection_context.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\map_clone_deps.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\map_marker_deps.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\map_scaling_deps.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\map_viewer_deps.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\map_wizard_deps.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\msp_org_context.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\progress_event.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\site_auto_upgrade_deps.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\systematic_test_option.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\dataclasses\\websocket_stream_target.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\db\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\db\\arango_writer.py",
      "score": 75.0,
      "grade": "C",
      "violations": 12
    },
    {
      "path": "src\\db\\redis_writer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\db\\retention.py",
      "score": 91.0,
      "grade": "A-",
      "violations": 2
    },
    {
      "path": "src\\db\\router.py",
      "score": 84.0,
      "grade": "B",
      "violations": 5
    },
    {
      "path": "src\\device\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\_utility_commands_action.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\_utility_commands_clear.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\_utility_commands_cluster.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\_utility_commands_selection.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\_utility_commands_show.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\_utility_commands_websocket.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\prompt_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\utility_commands.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\device\\virtual_chassis.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\export\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\export\\device_events_52w_exporter.py",
      "score": 84.0,
      "grade": "B",
      "violations": 4
    },
    {
      "path": "src\\export\\site_export_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\export\\site_insights\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\export\\site_insights\\device_metric_operation.py",
      "score": 79.0,
      "grade": "C+",
      "violations": 6
    },
    {
      "path": "src\\export\\site_insights\\site_metric_operation.py",
      "score": 91.0,
      "grade": "A-",
      "violations": 3
    },
    {
      "path": "src\\export\\site_insights_exporter.py",
      "score": 84.0,
      "grade": "B",
      "violations": 4
    },
    {
      "path": "src\\export\\wifi_clients_exporter.py",
      "score": 86.0,
      "grade": "B",
      "violations": 6
    },
    {
      "path": "src\\firmware\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\firmware\\bulk_ap_upgrader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\firmware\\bulk_switch_upgrader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\firmware\\firmware_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\firmware\\org_ap_upgrader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\firmware\\site_auto_upgrade.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\_wan2_variable_cluster.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\_wan2_variable_device.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\_wan2_variable_io.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\_wan2_variable_reporting.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\_wan2_variable_selection.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\_wan2_variable_template.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\device_template_cloner.py",
      "score": 84.0,
      "grade": "B",
      "violations": 7
    },
    {
      "path": "src\\gateway\\gateway_export_utils.py",
      "score": 69.0,
      "grade": "D+",
      "violations": 11
    },
    {
      "path": "src\\gateway\\gateway_stats_exporter.py",
      "score": 75.0,
      "grade": "C",
      "violations": 9
    },
    {
      "path": "src\\gateway\\overrides\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\overrides\\_deps.py",
      "score": 91.0,
      "grade": "A-",
      "violations": 2
    },
    {
      "path": "src\\gateway\\overrides\\device_data_fetcher.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\overrides\\override_classifier.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\overrides\\override_report_writer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\overrides\\wan_override_walker.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\template_config.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\wan2_migration_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\wan2_variable.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\wan_probe_device_override_manager.py",
      "score": 71.0,
      "grade": "C-",
      "violations": 13
    },
    {
      "path": "src\\inventory\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\inventory\\csv_comparator.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\inventory\\inventory_summary\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\inventory\\inventory_summary\\pivot_renderer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\inventory\\inventory_summary\\version_per_model_fetcher.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\inventory\\org_device_inventory_msp.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\inventory\\org_device_inventory_summary.py",
      "score": 79.0,
      "grade": "C+",
      "violations": 10
    },
    {
      "path": "src\\maps\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_container_detection.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_flask_viewer.py",
      "score": 74.0,
      "grade": "C",
      "violations": 5
    },
    {
      "path": "src\\maps\\_maps_backup.py",
      "score": 65.0,
      "grade": "D",
      "violations": 11
    },
    {
      "path": "src\\maps\\_maps_clone.py",
      "score": 84.0,
      "grade": "B",
      "violations": 7
    },
    {
      "path": "src\\maps\\_maps_coverage.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_matplotlib.py",
      "score": 82.0,
      "grade": "B-",
      "violations": 6
    },
    {
      "path": "src\\maps\\_maps_testing.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_utils.py",
      "score": 91.0,
      "grade": "A-",
      "violations": 2
    },
    {
      "path": "src\\maps\\_maps_wizard.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_plotly_viewer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_viewer_launch.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\_viewer_clone.py",
      "score": 77.0,
      "grade": "C+",
      "violations": 13
    },
    {
      "path": "src\\maps\\launcher\\_viewer_drawing.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\_viewer_refresh.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\_viewer_site_switch.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\_viewer_ui.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\_viewer_url_switch.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\viewer_callbacks.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\launcher\\viewer_state.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\maps_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\plotly_heatmap_renderer.py",
      "score": 73.0,
      "grade": "C",
      "violations": 6
    },
    {
      "path": "src\\maps\\plotly_map_callback_manager.py",
      "score": 82.0,
      "grade": "B-",
      "violations": 6
    },
    {
      "path": "src\\maps\\plotly_map_figure_builder.py",
      "score": 75.0,
      "grade": "C",
      "violations": 9
    },
    {
      "path": "src\\maps\\plotly_map_serializer.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 2
    },
    {
      "path": "src\\maps\\plotly_map_templates.py",
      "score": 84.0,
      "grade": "B",
      "violations": 4
    },
    {
      "path": "src\\marvis\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\marvis\\marvis_utils.py",
      "score": 78.0,
      "grade": "C+",
      "violations": 9
    },
    {
      "path": "src\\network\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\network\\_routing_utils_display.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\network\\_routing_utils_forwarding.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\network\\_routing_utils_parsing.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\network\\_routing_utils_payload.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\network\\_routing_utils_routing.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\network\\_routing_utils_ssr.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\network\\routing_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\org_data_collector.py",
      "score": 82.0,
      "grade": "B-",
      "violations": 5
    },
    {
      "path": "src\\refactors\\serial_cc\\global_assignments_builder.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\import_initialization_service.py",
      "score": 95.0,
      "grade": "A",
      "violations": 3
    },
    {
      "path": "src\\refactors\\serial_cc\\security_events.py",
      "score": 75.0,
      "grade": "C",
      "violations": 7
    },
    {
      "path": "src\\refactors\\serial_cc\\site_client_insights.py",
      "score": 89.0,
      "grade": "B+",
      "violations": 4
    },
    {
      "path": "src\\refactors\\serial_cc\\sle_metrics.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\start_site_client_capture_wireless.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 5
    },
    {
      "path": "src\\refactors\\serial_cc\\start_site_scan_capture.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 5
    },
    {
      "path": "src\\refactors\\serial_cc\\switch_vc_stats.py",
      "score": 85.0,
      "grade": "B",
      "violations": 7
    },
    {
      "path": "src\\refactors\\serial_cc\\test_results_by_site.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\reports\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\reports\\e911_bssid.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\address_corrector.py",
      "score": 94.0,
      "grade": "A",
      "violations": 4
    },
    {
      "path": "src\\site\\address_audit\\address_resolver.py",
      "score": 86.0,
      "grade": "B",
      "violations": 8
    },
    {
      "path": "src\\site\\address_audit\\audit_engine.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\audit_reporter.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\business_authority_ingester.py",
      "score": 95.0,
      "grade": "A",
      "violations": 3
    },
    {
      "path": "src\\site\\address_audit\\comparison_display.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\csv_ingester.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\models.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\perf.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\site_matcher.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\snmp_enricher.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\suite_patterns.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\site\\address_audit\\ui_geocoder.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 6
    },
    {
      "path": "src\\site\\site_config_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\batch\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\batch\\batch_executor.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\batch\\host_runner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\batch\\interactive_batch_executor.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\batch\\multi_host_runner.py",
      "score": 73.0,
      "grade": "C",
      "violations": 12
    },
    {
      "path": "src\\ssh\\command\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\command\\command_runner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\config\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\config\\command_parser.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\config\\csv_loader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\config\\env_loader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\config\\host_parser.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\config\\validators.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\connection\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\connection\\connector.py",
      "score": 86.0,
      "grade": "B",
      "violations": 6
    },
    {
      "path": "src\\ssh\\runtime\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\runtime\\app_runner.py",
      "score": 68.0,
      "grade": "D+",
      "violations": 11
    },
    {
      "path": "src\\ssh\\runtime\\interactive_mode.py",
      "score": 97.0,
      "grade": "A+",
      "violations": 1
    },
    {
      "path": "src\\ssh\\shell_execution\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\shell_execution\\shell_executor.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 6
    },
    {
      "path": "src\\ssh\\ssh_runner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\ssh_runner_manager.py",
      "score": 75.0,
      "grade": "C",
      "violations": 12
    },
    {
      "path": "src\\ssid_consolidation\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_cache.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_cluster.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_phase1.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_phase2.py",
      "score": 84.0,
      "grade": "B",
      "violations": 7
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_phase3.py",
      "score": 86.0,
      "grade": "B",
      "violations": 5
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_phase45.py",
      "score": 86.0,
      "grade": "B",
      "violations": 5
    },
    {
      "path": "src\\ssid_consolidation\\ssid_template_consolidation.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\troubleshooting\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\troubleshooting\\interactive_test_runner.py",
      "score": 75.0,
      "grade": "C",
      "violations": 8
    },
    {
      "path": "src\\troubleshooting\\marvis_troubleshoot_utils.py",
      "score": 72.0,
      "grade": "C-",
      "violations": 11
    },
    {
      "path": "src\\ui\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ui\\execution\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\ui\\execution\\debug_saver.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ui\\execution\\function_executor.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ui\\execution\\item_executor.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 5
    },
    {
      "path": "src\\ui\\execution\\output_formatter.py",
      "score": 93.0,
      "grade": "A",
      "violations": 2
    },
    {
      "path": "src\\ui\\execution\\parameter_collector.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ui\\input_handlers\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\ui\\input_handlers\\key_poller.py",
      "score": 95.0,
      "grade": "A",
      "violations": 3
    },
    {
      "path": "src\\ui\\input_handlers\\keyboard_dispatch.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ui\\layout\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\ui\\layout\\layout_builder.py",
      "score": 94.0,
      "grade": "A",
      "violations": 2
    },
    {
      "path": "src\\ui\\layout\\results_grid_builder.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 7
    },
    {
      "path": "src\\ui\\runtime\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\ui\\runtime\\dotenv_loader.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ui\\runtime\\level_discoverer.py",
      "score": 93.0,
      "grade": "A",
      "violations": 2
    },
    {
      "path": "src\\ui\\runtime\\tui_runner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ui\\tui.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\utils\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\utils\\address_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\utils\\input_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\utils\\logger_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\utils\\rate_limiting.py",
      "score": 75.0,
      "grade": "C",
      "violations": 6
    },
    {
      "path": "src\\wan_hub_group_manager.py",
      "score": 88.0,
      "grade": "B+",
      "violations": 3
    },
    {
      "path": "src\\wan_vpn_builder.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\__init__.py",
      "score": 94.0,
      "grade": "A",
      "violations": 1
    },
    {
      "path": "src\\websocket\\commands.py",
      "score": 86.0,
      "grade": "B",
      "violations": 8
    },
    {
      "path": "src\\websocket\\context.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\diagnostics\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\diagnostics\\arp_executor.py",
      "score": 80.0,
      "grade": "B-",
      "violations": 8
    },
    {
      "path": "src\\websocket\\diagnostics\\common.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\diagnostics\\ping_executor.py",
      "score": 79.0,
      "grade": "C+",
      "violations": 6
    },
    {
      "path": "src\\websocket\\manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\polling\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\polling\\completion_detector.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\polling\\message_router.py",
      "score": 90.0,
      "grade": "A-",
      "violations": 5
    },
    {
      "path": "src\\websocket\\polling\\result_collector.py",
      "score": 89.0,
      "grade": "B+",
      "violations": 4
    },
    {
      "path": "src\\websocket\\polling\\result_combiner.py",
      "score": 83.0,
      "grade": "B",
      "violations": 5
    },
    {
      "path": "src\\websocket\\service_ping_discovery.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\service_ping_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    }
  ]
}
```

## File: src\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\analytics\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 11 |
| Executable code lines | 3 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 6. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\analytics\site_analytics_configurator.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 569 |
| Executable code lines | 318 |
| Functions | 32 |
| Classes | 2 |
| Average complexity | 2.9 |
| Max complexity | 5 |
| Inline comment coverage | 86.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _scan_for_deviations | 5 |
| _scan_single_site | 5 |
| _compare_engagement_hours | 5 |
| _count_deviations | 5 |
| _apply_standard_configuration | 5 |

No violations found. This file complies with the guidelines.

## File: src\analytics\site_inventory_health_analyzer.py

- **Score**: 78.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 313 |
| Executable code lines | 173 |
| Functions | 16 |
| Classes | 2 |
| Average complexity | 4.1 |
| Max complexity | 9 |
| Inline comment coverage | 27.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _find_sites_missing_infrastructure | 9 |
| _display_missing_section | 7 |
| _build_offline_entry | 6 |
| _display_offline_section | 6 |
| analyze | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 146 | low | STRUCT-COMPLEXITY | _find_sites_missing_infrastructure | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 199 | low | STRUCT-COMPLEXITY | _build_offline_entry | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 251 | low | STRUCT-COMPLEXITY | _display_missing_section | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 266 | low | STRUCT-COMPLEXITY | _display_offline_section | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 27.2%; uncommented lines: 3, 5, 6, 7, 8, 12, 15, 16, 17, 18, 19, 22. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 26 | medium | STRUCT-LENGTH | analyze | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 146 | medium | STRUCT-LENGTH | _find_sites_missing_infrastructure | Function spans 39 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 199 | medium | STRUCT-LENGTH | _build_offline_entry | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 283 | medium | STRUCT-LENGTH | _export_results | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\analytics\zone_analyzer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1442 |
| Executable code lines | 635 |
| Functions | 84 |
| Classes | 4 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 85.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _find_sites_with_unique | 5 |
| _display_custom_names | 5 |
| _normalize_analyses | 5 |
| _analyze_zone_patterns | 5 |
| _run_all_analyses | 4 |

No violations found. This file complies with the guidelines.

## File: src\api\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\api\tenant_fetch.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 305 |
| Executable code lines | 184 |
| Functions | 15 |
| Classes | 1 |
| Average complexity | 4.7 |
| Max complexity | 10 |
| Inline comment coverage | 22.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _extract_tenants_from_policy_item | 10 |
| _extract_tenants_from_networks | 9 |
| _extract_router_tenants | 8 |
| _extract_network_tenants | 6 |
| organization_tenants | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 139 | low | STRUCT-COMPLEXITY | _extract_tenants_from_networks | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 162 | low | STRUCT-COMPLEXITY | _extract_tenants_from_policy_item | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 197 | low | STRUCT-COMPLEXITY | _extract_router_tenants | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 213 | low | STRUCT-COMPLEXITY | _extract_network_tenants | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 9 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 22.3%; uncommented lines: 9, 11, 12, 13, 15, 16, 17, 18, 19, 20, 23, 32. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 139 | low | STRUCT-BLOCKS | _extract_tenants_from_networks | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 162 | low | STRUCT-BLOCKS | _extract_tenants_from_policy_item | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\audit\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\audit\_renderer_delta.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 336 |
| Executable code lines | 152 |
| Functions | 23 |
| Classes | 1 |
| Average complexity | 3.3 |
| Max complexity | 5 |
| Inline comment coverage | 85.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _empty_side_delta | 5 |
| diff_key | 5 |
| diff_key_list | 5 |
| check_reorder | 5 |
| compute_delta_list | 4 |

No violations found. This file complies with the guidelines.

## File: src\audit\_renderer_format.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 87 |
| Executable code lines | 51 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 4 |
| Inline comment coverage | 86.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _format_list | 4 |
| format_delta_html | 3 |
| _format_dict | 3 |
| _render_dict_item | 2 |

No violations found. This file complies with the guidelines.

## File: src\audit\_renderer_html.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 368 |
| Executable code lines | 119 |
| Functions | 20 |
| Classes | 2 |
| Average complexity | 2.1 |
| Max complexity | 5 |
| Inline comment coverage | 85.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _render_delta_block | 5 |
| _collect_squashed_blocks | 4 |
| _group_changes_by_admin | 4 |
| _render_squashed_block | 3 |
| rollback_table | 3 |

No violations found. This file complies with the guidelines.

## File: src\audit\_renderer_mermaid.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 183 |
| Executable code lines | 103 |
| Functions | 12 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 4 |
| Inline comment coverage | 81.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _emit_rollback_details | 4 |
| _render_admin_subgraphs | 3 |
| _render_one_admin_subgraph | 3 |
| _emit_rollback_summary | 3 |
| admin_timeline | 2 |

No violations found. This file complies with the guidelines.

## File: src\audit\_renderer_time.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 25 |
| Executable code lines | 10 |
| Functions | 2 |
| Classes | 0 |
| Average complexity | 2.0 |
| Max complexity | 2 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| epoch_to_readable | 2 |
| epoch_to_short | 2 |

No violations found. This file complies with the guidelines.

## File: src\audit\analyzer.py

- **Score**: 80.0 / 100
- **Grade**: B-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 242 |
| Executable code lines | 105 |
| Functions | 7 |
| Classes | 6 |
| Average complexity | 3.9 |
| Max complexity | 7 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_rollback_diffs | 7 |
| _build_admin_timelines | 6 |
| _build_object_changelogs | 5 |
| _extract_object_type | 3 |
| _compute_changed_fields | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 121 | low | STRUCT-COMPLEXITY | _build_admin_timelines | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 183 | low | STRUCT-COMPLEXITY | _build_rollback_diffs | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 8, 9, 10, 12, 14, 34, 37, 38, 39, 40, 41, 42. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 92 | medium | STRUCT-LENGTH | analyze | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 121 | medium | STRUCT-LENGTH | _build_admin_timelines | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 150 | medium | STRUCT-LENGTH | _build_object_changelogs | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 183 | medium | STRUCT-LENGTH | _build_rollback_diffs | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\audit\filter.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 110 |
| Executable code lines | 36 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 2.7 |
| Max complexity | 4 |
| Inline comment coverage | 97.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| is_noise | 4 |
| _is_adopted_flag_cascade | 3 |
| filter | 3 |
| filter_with_stats | 3 |
| _is_vpn_cascade | 2 |

No violations found. This file complies with the guidelines.

## File: src\audit\renderer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 101 |
| Executable code lines | 40 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 1.2 |
| Max complexity | 2 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _write_report | 2 |

No violations found. This file complies with the guidelines.

## File: src\audit\time_parser.py

- **Score**: 85.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 158 |
| Executable code lines | 81 |
| Functions | 4 |
| Classes | 2 |
| Average complexity | 5.8 |
| Max complexity | 10 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| validate | 10 |
| parse | 7 |
| to_api_kwargs | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 56 | low | STRUCT-COMPLEXITY | parse | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 117 | low | STRUCT-COMPLEXITY | validate | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 7, 8, 9, 11, 19, 27, 28, 32, 35, 36, 37, 38. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 56 | medium | STRUCT-LENGTH | parse | Function spans 59 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 117 | medium | STRUCT-LENGTH | validate | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 117 | low | STRUCT-BLOCKS | validate | Function has 8 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\auth\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 5 |
| Executable code lines | 2 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\auth\interactive\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 16 |
| Executable code lines | 6 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\auth\interactive\clouds.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 72 |
| Executable code lines | 36 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 2.0 |
| Max complexity | 4 |
| Inline comment coverage | 86.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| prompt | 4 |
| _render_menu | 2 |

No violations found. This file complies with the guidelines.

## File: src\auth\interactive\credential_prompter.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 64 |
| Executable code lines | 47 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 4 |
| Inline comment coverage | 89.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| prompt_password | 4 |
| prompt_email | 3 |
| prompt_two_factor | 3 |

No violations found. This file complies with the guidelines.

## File: src\auth\interactive\login_orchestrator.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 306 |
| Executable code lines | 194 |
| Functions | 23 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 86.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _run_login_pipeline | 5 |
| execute | 4 |
| _authenticate | 4 |
| _needs_two_factor | 4 |
| _announce_msp_privileges | 4 |

No violations found. This file complies with the guidelines.

## File: src\auth\interactive\msp_org_selector.py

- **Score**: 98.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 229 |
| Executable code lines | 163 |
| Functions | 13 |
| Classes | 1 |
| Average complexity | 3.4 |
| Max complexity | 8 |
| Inline comment coverage | 91.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _interpret_choice | 8 |
| _fetch_msp_orgs | 6 |
| _prompt_msp | 5 |
| _select_org_under_msp | 5 |
| _paginated_pick | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 118 | low | STRUCT-COMPLEXITY | _fetch_msp_orgs | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 192 | low | STRUCT-COMPLEXITY | _interpret_choice | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

## File: src\bootstrap\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\bootstrap\dependency_check.py

- **Score**: 90.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 147 |
| Executable code lines | 100 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 5.0 |
| Max complexity | 10 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _classify_packages | 10 |
| _install_missing_packages | 7 |
| _upgrade_outdated_packages | 7 |
| run | 5 |
| _prepare_installer | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 60 | low | STRUCT-COMPLEXITY | _classify_packages | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 103 | low | STRUCT-COMPLEXITY | _install_missing_packages | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 126 | low | STRUCT-COMPLEXITY | _upgrade_outdated_packages | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 19, 20, 21. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 60 | low | STRUCT-BLOCKS | _classify_packages | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\bootstrap\package_installer.py

- **Score**: 89.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 89 |
| Executable code lines | 59 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 4.5 |
| Max complexity | 10 |
| Inline comment coverage | 5.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| find_uv_executable | 10 |
| install_with_uv | 3 |
| install_with_pip | 3 |
| install_uv_with_pip | 2 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 19 | low | STRUCT-COMPLEXITY | find_uv_executable | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 5.1%; uncommented lines: 3, 5, 6, 7, 11, 14, 15, 16, 17, 19, 21, 22. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 19 | medium | STRUCT-LENGTH | find_uv_executable | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 19 | low | STRUCT-BLOCKS | find_uv_executable | Function has 8 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\bootstrap\uv_runtime.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 93 |
| Executable code lines | 50 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 2.7 |
| Max complexity | 4 |
| Inline comment coverage | 86.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_numeric_prefix | 4 |
| _split_operator_and_required | 4 |
| parse_version | 3 |
| version_satisfies | 3 |
| package_name_from_spec | 3 |

No violations found. This file complies with the guidelines.

## File: src\capture\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 5 |
| Executable code lines | 2 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\capture\_packet_capture_exec.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 513 |
| Executable code lines | 306 |
| Functions | 45 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 84.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| read_stream_packets | 5 |
| _find_capture_record | 4 |
| _classify_capture_state | 4 |
| _subscribe_channel | 4 |
| _drain_stream_batch | 4 |

No violations found. This file complies with the guidelines.

## File: src\capture\_packet_capture_org.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 529 |
| Executable code lines | 308 |
| Functions | 34 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 83.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_mxedge_stats_map | 5 |
| gather_org_capture_params | 5 |
| build_org_payload | 5 |
| _prompt_mxedge_index | 4 |
| _format_mxedge_status | 4 |

No violations found. This file complies with the guidelines.

## File: src\capture\_packet_capture_prompts.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 538 |
| Executable code lines | 317 |
| Functions | 42 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 85.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _print_client_summary_tail | 5 |
| prompt_capture_duration | 5 |
| prompt_ap_mac_filter | 4 |
| _fetch_site_pcaps | 4 |
| _handle_multi_ap_conflict | 4 |

No violations found. This file complies with the guidelines.

## File: src\capture\_packet_capture_tcpdump.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 248 |
| Executable code lines | 59 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 1.8 |
| Max complexity | 3 |
| Inline comment coverage | 98.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| print_tcpdump_menu | 3 |
| get_tcpdump_expression_selection | 3 |
| __getattr__ | 2 |
| _announce_expression | 2 |
| _prompt_custom_expression | 2 |

No violations found. This file complies with the guidelines.

## File: src\capture\multi_ap_scan_workflow.py

- **Score**: 77.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 429 |
| Executable code lines | 205 |
| Functions | 14 |
| Classes | 1 |
| Average complexity | 3.1 |
| Max complexity | 5 |
| Inline comment coverage | 78.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _check_existing_captures | 5 |
| _handle_launch_error | 5 |
| _prompt_channel | 4 |
| _prompt_duration | 4 |
| _prompt_num_packets | 4 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 78.0%; uncommented lines: 3, 5, 6, 7, 11, 14, 15, 16, 17, 19, 50, 55. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 175 | high | STRUCT-PARAMS | _build_payload | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 217 | high | STRUCT-PARAMS | _display_summary | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 19 | medium | STRUCT-LENGTH | _prompt_band | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 50 | medium | STRUCT-LENGTH | _prompt_channel | Function spans 35 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 86 | medium | STRUCT-LENGTH | _prompt_bandwidth | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 113 | medium | STRUCT-LENGTH | _prompt_duration | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 144 | medium | STRUCT-LENGTH | _prompt_num_packets | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 175 | medium | STRUCT-LENGTH | _build_payload | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 217 | medium | STRUCT-LENGTH | _display_summary | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 266 | medium | STRUCT-LENGTH | _gather_capture_config | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 357 | medium | STRUCT-LENGTH | _launch_capture | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 388 | medium | STRUCT-LENGTH | run | Function spans 42 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\capture\org_capture_workflow.py

- **Score**: 91.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 41 |
| Executable code lines | 24 |
| Functions | 1 |
| Classes | 1 |
| Average complexity | 5.0 |
| Max complexity | 5 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| run | 5 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 10, 13, 15, 17, 18, 19, 20, 21, 22. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 15 | medium | STRUCT-LENGTH | run | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\capture\org_pcap_wait_download_workflow.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 70 |
| Executable code lines | 23 |
| Functions | 3 |
| Classes | 1 |
| Average complexity | 1.0 |
| Max complexity | 1 |
| Inline comment coverage | 52.2% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 52.2%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 20, 62. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 20 | medium | STRUCT-LENGTH | execute | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\capture\packet_capture.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1264 |
| Executable code lines | 627 |
| Functions | 110 |
| Classes | 1 |
| Average complexity | 1.6 |
| Max complexity | 5 |
| Inline comment coverage | 85.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _wireless_client_gather_core | 5 |
| _run_site_capture | 4 |
| _wired_client_gather_params | 4 |
| _start_site_gateway_capture | 4 |
| _start_site_switch_capture | 4 |

No violations found. This file complies with the guidelines.

## File: src\capture\packet_capture_download.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 408 |
| Executable code lines | 180 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 5.2 |
| Max complexity | 7 |
| Inline comment coverage | 94.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| poll_and_download_pcap | 7 |
| fetch_completed_pcaps | 6 |
| download_pending_pcaps | 6 |
| poll_for_pcap_url | 6 |
| find_capture_url | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 18 | low | STRUCT-COMPLEXITY | fetch_completed_pcaps | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 63 | low | STRUCT-COMPLEXITY | download_pending_pcaps | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 174 | low | STRUCT-COMPLEXITY | poll_and_download_pcap | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 235 | low | STRUCT-COMPLEXITY | poll_for_pcap_url | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 330 | low | STRUCT-COMPLEXITY | find_capture_url | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 235 | high | STRUCT-LENGTH | poll_for_pcap_url | Function spans 70 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 18 | medium | STRUCT-LENGTH | fetch_completed_pcaps | Function spans 44 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 63 | medium | STRUCT-LENGTH | download_pending_pcaps | Function spans 58 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 122 | medium | STRUCT-LENGTH | download_single_pcap | Function spans 51 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 174 | medium | STRUCT-LENGTH | poll_and_download_pcap | Function spans 60 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 355 | medium | STRUCT-LENGTH | save_pcap_file | Function spans 54 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\capture\site_capture_loop.py

- **Score**: 91.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 44 |
| Executable code lines | 33 |
| Functions | 1 |
| Classes | 1 |
| Average complexity | 5.0 |
| Max complexity | 5 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| run | 5 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 7, 8, 12, 15, 17, 19, 20, 21, 22. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 17 | medium | STRUCT-LENGTH | run | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\capture\site_pcap_wait_download_workflow.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 72 |
| Executable code lines | 23 |
| Functions | 3 |
| Classes | 1 |
| Average complexity | 1.0 |
| Max complexity | 1 |
| Inline comment coverage | 52.2% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 52.2%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 20, 62. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 20 | medium | STRUCT-LENGTH | execute | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\constants.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 12 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\batch_worker.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 28 |
| Executable code lines | 10 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 90.0% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\export_backend_options.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 29 |
| Executable code lines | 6 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 83.3% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\family_selection_context.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 31 |
| Executable code lines | 9 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 88.9% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\map_clone_deps.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 31 |
| Executable code lines | 12 |
| Functions | 0 |
| Classes | 2 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 83.3% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\map_marker_deps.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 29 |
| Executable code lines | 10 |
| Functions | 0 |
| Classes | 2 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 80.0% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\map_scaling_deps.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 50 |
| Executable code lines | 21 |
| Functions | 0 |
| Classes | 4 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 81.0% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\map_viewer_deps.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 49 |
| Executable code lines | 20 |
| Functions | 0 |
| Classes | 4 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 80.0% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\map_wizard_deps.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 48 |
| Executable code lines | 19 |
| Functions | 0 |
| Classes | 4 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\msp_org_context.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 23 |
| Executable code lines | 7 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 85.7% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\progress_event.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 41 |
| Executable code lines | 14 |
| Functions | 0 |
| Classes | 2 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 85.7% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\site_auto_upgrade_deps.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 37 |
| Executable code lines | 12 |
| Functions | 0 |
| Classes | 2 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 83.3% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\systematic_test_option.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 28 |
| Executable code lines | 8 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 87.5% |

No violations found. This file complies with the guidelines.

## File: src\dataclasses\websocket_stream_target.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 25 |
| Executable code lines | 8 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 87.5% |

No violations found. This file complies with the guidelines.

## File: src\db\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 154 |
| Executable code lines | 60 |
| Functions | 5 |
| Classes | 3 |
| Average complexity | 2.6 |
| Max complexity | 4 |
| Inline comment coverage | 1.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _hosts_unreachable | 4 |
| combined | 4 |
| _can_resolve | 2 |
| from_env | 2 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 1.7%; uncommented lines: 8, 10, 11, 12, 13, 15, 18, 20, 39, 42, 43, 44. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\db\arango_writer.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 4345 |
| Executable code lines | 268 |
| Functions | 23 |
| Classes | 1 |
| Average complexity | 4.0 |
| Max complexity | 9 |
| Inline comment coverage | 3.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_edges | 9 |
| _ensure_target_vertices | 9 |
| _backfill_snapshot_edges | 9 |
| _build_key_lookup | 6 |
| _build_template_edges | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 4084 | low | STRUCT-COMPLEXITY | _build_edges | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 4121 | low | STRUCT-COMPLEXITY | _build_key_lookup | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 4155 | low | STRUCT-COMPLEXITY | _ensure_target_vertices | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 4176 | low | STRUCT-COMPLEXITY | _build_template_edges | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 4308 | low | STRUCT-COMPLEXITY | _backfill_snapshot_edges | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 3.7%; uncommented lines: 8, 10, 11, 12, 13, 14, 15, 16, 18, 21, 23, 25. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3978 | medium | STRUCT-LENGTH | _batch_import | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 4084 | medium | STRUCT-LENGTH | _build_edges | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 4241 | medium | STRUCT-LENGTH | snapshot | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 4308 | medium | STRUCT-LENGTH | _backfill_snapshot_edges | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 4155 | low | STRUCT-BLOCKS | _ensure_target_vertices | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 4308 | low | STRUCT-BLOCKS | _backfill_snapshot_edges | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\db\redis_writer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 598 |
| Executable code lines | 307 |
| Functions | 42 |
| Classes | 3 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 86.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _extract_parallel | 5 |
| _batch_ensure_keys | 5 |
| _extract_numeric | 5 |
| _build_labels | 5 |
| _pipeline_create_compaction | 4 |

No violations found. This file complies with the guidelines.

## File: src\db\retention.py

- **Score**: 91.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 159 |
| Executable code lines | 77 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 3 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _get_storage_usage_gb | 3 |
| _purge_oldest_snapshots | 3 |
| check_redis_retention | 3 |
| _sweep_loop | 3 |
| check_arango_retention | 2 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 8, 10, 11, 12, 14, 16, 18, 19, 20, 23, 26, 32. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 77 | medium | STRUCT-LENGTH | _purge_oldest_snapshots | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\db\router.py

- **Score**: 84.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 368 |
| Executable code lines | 154 |
| Functions | 17 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 6 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _snapshot_if_config | 6 |
| _write_arango | 5 |
| pull_config_history | 5 |
| close | 5 |
| write | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 147 | low | STRUCT-COMPLEXITY | _snapshot_if_config | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 7, 9, 10, 11, 13, 15, 16, 17, 19, 21, 22, 23. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 115 | medium | STRUCT-LENGTH | _write_arango | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 147 | medium | STRUCT-LENGTH | _snapshot_if_config | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 300 | medium | STRUCT-LENGTH | pull_config_history | Function spans 39 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\device\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\device\_utility_commands_action.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 445 |
| Executable code lines | 214 |
| Functions | 24 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 4 |
| Inline comment coverage | 82.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| bounce_port | 4 |
| _readopt_vc_preflight | 4 |
| _render_config_response | 4 |
| poll_switch_stats | 4 |
| _resolve_support_file_type | 3 |

No violations found. This file complies with the guidelines.

## File: src\device\_utility_commands_clear.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 560 |
| Executable code lines | 251 |
| Functions | 31 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 4 |
| Inline comment coverage | 84.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _assign_session_ids | 4 |
| clear_bgp_routes | 4 |
| clear_session | 4 |
| clear_bpdu_error | 4 |
| clear_learned_macs | 4 |

No violations found. This file complies with the guidelines.

## File: src\device\_utility_commands_cluster.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 72 |
| Executable code lines | 21 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 1.8 |
| Max complexity | 3 |
| Inline comment coverage | 95.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _add_node_port_filters | 3 |
| __getattr__ | 2 |

No violations found. This file complies with the guidelines.

## File: src\device\_utility_commands_selection.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 520 |
| Executable code lines | 294 |
| Functions | 40 |
| Classes | 1 |
| Average complexity | 3.3 |
| Max complexity | 5 |
| Inline comment coverage | 83.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _select_site_and_device | 5 |
| _select_port_from_device | 5 |
| _physical_from_if_stat | 5 |
| _resolve_port_selection | 5 |
| _interfaces_from_ip_stat | 5 |

No violations found. This file complies with the guidelines.

## File: src\device\_utility_commands_show.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 536 |
| Executable code lines | 271 |
| Functions | 27 |
| Classes | 2 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 90.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_ospf_database_body | 5 |
| _build_ospf_neighbors_body | 4 |
| _build_session_body | 4 |
| traceroute | 3 |
| _build_traceroute_body | 3 |

No violations found. This file complies with the guidelines.

## File: src\device\_utility_commands_websocket.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 321 |
| Executable code lines | 126 |
| Functions | 15 |
| Classes | 3 |
| Average complexity | 2.5 |
| Max complexity | 4 |
| Inline comment coverage | 81.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _extract_session_id | 4 |
| _print_result_block | 4 |
| _safe_stream | 3 |
| _prepare_ws_channel | 3 |
| _print_stream_raw | 3 |

No violations found. This file complies with the guidelines.

## File: src\device\prompt_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 792 |
| Executable code lines | 421 |
| Functions | 46 |
| Classes | 2 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 81.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _dispatch_port_input | 5 |
| _format_speed | 5 |
| _gather_available_ports | 4 |
| _build_port_to_config_map | 4 |
| _filter_and_sort_ports | 4 |

No violations found. This file complies with the guidelines.

## File: src\device\utility_commands.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 206 |
| Executable code lines | 63 |
| Functions | 6 |
| Classes | 2 |
| Average complexity | 2.5 |
| Max complexity | 4 |
| Inline comment coverage | 98.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _handle_clear_session_error | 4 |
| __getattr__ | 3 |
| _print_api_result | 3 |
| _extract_error_detail | 2 |
| _print_api_error | 2 |

No violations found. This file complies with the guidelines.

## File: src\device\virtual_chassis.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 927 |
| Executable code lines | 460 |
| Functions | 51 |
| Classes | 4 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 87.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _prepare_bulk_targets | 5 |
| _load_site_switches | 5 |
| _read_vc_site_names | 5 |
| _load_vc_switches | 5 |
| _is_conversion_error | 5 |

No violations found. This file complies with the guidelines.

## File: src\export\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\export\device_events_52w_exporter.py

- **Score**: 84.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 239 |
| Executable code lines | 142 |
| Functions | 13 |
| Classes | 1 |
| Average complexity | 3.4 |
| Max complexity | 6 |
| Inline comment coverage | 2.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _normalize_page | 6 |
| _fetch_with_retries | 5 |
| _read_checkpoint | 4 |
| _preload_rows | 4 |
| _write_initial_batch | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 101 | low | STRUCT-COMPLEXITY | _normalize_page | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 2.1%; uncommented lines: 3, 5, 6, 7, 8, 9, 17, 20, 21, 22, 23, 24. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 192 | high | STRUCT-PARAMS | _stream_remaining_pages | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 29 | medium | STRUCT-LENGTH | export | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\export\site_export_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 559 |
| Executable code lines | 287 |
| Functions | 39 |
| Classes | 2 |
| Average complexity | 2.1 |
| Max complexity | 5 |
| Inline comment coverage | 84.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _flatten_channel_planning_dict | 5 |
| _read_site_response_rows | 4 |
| _export_data | 4 |
| current_channel_planning | 4 |
| _emit_debug_table | 3 |

No violations found. This file complies with the guidelines.

## File: src\export\site_insights\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\export\site_insights\device_metric_operation.py

- **Score**: 79.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 272 |
| Executable code lines | 114 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 3.6 |
| Max complexity | 5 |
| Inline comment coverage | 60.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_device_info | 5 |
| _fetch_one_metric | 5 |
| execute | 4 |
| _resolve_site_name | 4 |
| _prompt_site_and_device | 3 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 60.5%; uncommented lines: 3, 5, 10, 14, 23, 25, 31, 32, 33, 36, 37, 51. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 170 | high | STRUCT-PARAMS | _collect_metrics | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 14 | medium | STRUCT-LENGTH | execute | Function spans 54 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 170 | medium | STRUCT-LENGTH | _collect_metrics | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 200 | medium | STRUCT-LENGTH | _fetch_one_metric | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 229 | medium | STRUCT-LENGTH | _finalize | Function spans 44 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\export\site_insights\site_metric_operation.py

- **Score**: 91.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 164 |
| Executable code lines | 76 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 4 |
| Inline comment coverage | 64.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_site_name | 4 |
| _fetch_one_metric | 4 |
| execute | 3 |
| _collect_metrics | 3 |
| _finalize | 3 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 64.5%; uncommented lines: 3, 5, 12, 16, 22, 23, 42, 54, 57, 59, 60, 63. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 16 | medium | STRUCT-LENGTH | execute | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 132 | medium | STRUCT-LENGTH | _finalize | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\export\site_insights_exporter.py

- **Score**: 84.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 82 |
| Executable code lines | 52 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 4.0 |
| Max complexity | 7 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _metric_compatible_with_platform | 7 |
| _classify_device_platform | 5 |
| _normalize_device_mac_or_none | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 64 | low | STRUCT-COMPLEXITY | _metric_compatible_with_platform | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 17, 29. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 17 | high | STRUCT-PARAMS | configure_site_insights_exporter_dependencies | Function takes 8 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 17 | medium | STRUCT-LENGTH | configure_site_insights_exporter_dependencies | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\export\wifi_clients_exporter.py

- **Score**: 86.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 267 |
| Executable code lines | 163 |
| Functions | 11 |
| Classes | 1 |
| Average complexity | 3.9 |
| Max complexity | 7 |
| Inline comment coverage | 72.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_clients_and_sessions | 7 |
| _merge_clients_and_sessions | 7 |
| execute | 5 |
| _attach_latest_session | 5 |
| _resolve_site_name | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 94 | low | STRUCT-COMPLEXITY | _fetch_clients_and_sessions | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 132 | low | STRUCT-COMPLEXITY | _merge_clients_and_sessions | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 72.4%; uncommented lines: 3, 12, 15, 16, 17, 18, 19, 20, 21, 22, 24, 30. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 24 | medium | STRUCT-LENGTH | execute | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 132 | medium | STRUCT-LENGTH | _merge_clients_and_sessions | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 228 | medium | STRUCT-LENGTH | _finalize_export | Function spans 40 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\firmware\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\firmware\bulk_ap_upgrader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2261 |
| Executable code lines | 1302 |
| Functions | 160 |
| Classes | 2 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 95.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _run_discovery_phase | 5 |
| _read_site_names_from_file | 5 |
| _print_site_ap_breakdown | 5 |
| _index_stats_by_device_id | 5 |
| _get_ap_version | 5 |

No violations found. This file complies with the guidelines.

## File: src\firmware\bulk_switch_upgrader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1096 |
| Executable code lines | 634 |
| Functions | 76 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 85.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _select_reboot_option | 5 |
| _absorb_firmware_entry | 5 |
| _run_post_site_workflow | 4 |
| _apply_site_menu_choice | 4 |
| _select_force_option | 4 |

No violations found. This file complies with the guidelines.

## File: src\firmware\firmware_manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 3057 |
| Executable code lines | 1896 |
| Functions | 198 |
| Classes | 2 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 80.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_site_filter_for_status | 5 |
| _print_upgrade_job_timing_info | 5 |
| _print_upgrade_job_p2p_config | 5 |
| _print_upgrade_job_detail_block | 5 |
| _is_active_fw_update | 5 |

No violations found. This file complies with the guidelines.

## File: src\firmware\org_ap_upgrader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2804 |
| Executable code lines | 1715 |
| Functions | 227 |
| Classes | 2 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 99.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _validate_msp_context | 5 |
| _try_msp_mode | 5 |
| _collect_msp_selection | 5 |
| _parse_dash_selection_range | 5 |
| _step4_fetch_available_firmware | 5 |

No violations found. This file complies with the guidelines.

## File: src\firmware\site_auto_upgrade.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1774 |
| Executable code lines | 946 |
| Functions | 115 |
| Classes | 4 |
| Average complexity | 2.9 |
| Max complexity | 5 |
| Inline comment coverage | 93.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_configurator_kwargs | 5 |
| _execute_msp_mode | 5 |
| _get_family_versions | 5 |
| _parse_hour_minute | 5 |
| _apply_ampm | 5 |

No violations found. This file complies with the guidelines.

## File: src\gateway\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\gateway\_wan2_variable_cluster.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 49 |
| Executable code lines | 14 |
| Functions | 3 |
| Classes | 1 |
| Average complexity | 1.3 |
| Max complexity | 2 |
| Inline comment coverage | 92.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| __getattr__ | 2 |

No violations found. This file complies with the guidelines.

## File: src\gateway\_wan2_variable_device.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 390 |
| Executable code lines | 208 |
| Functions | 23 |
| Classes | 1 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 83.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _classify_site_row | 5 |
| _check_device_override | 5 |
| _scan_one_site | 4 |
| _dispatch_device_migration | 4 |
| _match_port_rename | 3 |

No violations found. This file complies with the guidelines.

## File: src\gateway\_wan2_variable_io.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 106 |
| Executable code lines | 59 |
| Functions | 9 |
| Classes | 1 |
| Average complexity | 1.9 |
| Max complexity | 5 |
| Inline comment coverage | 81.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _filter_excluded_sites | 5 |
| _count_template_assignments | 3 |
| _print_header | 2 |
| _load_csv_data | 2 |

No violations found. This file complies with the guidelines.

## File: src\gateway\_wan2_variable_reporting.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 226 |
| Executable code lines | 116 |
| Functions | 16 |
| Classes | 1 |
| Average complexity | 3.1 |
| Max complexity | 5 |
| Inline comment coverage | 84.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _print_device_failure_warning | 5 |
| _print_live_guidance | 5 |
| _print_final_guidance | 4 |
| _log_operation_summary | 4 |
| _print_dry_run_guidance | 4 |

No violations found. This file complies with the guidelines.

## File: src\gateway\_wan2_variable_selection.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 195 |
| Executable code lines | 123 |
| Functions | 16 |
| Classes | 1 |
| Average complexity | 2.3 |
| Max complexity | 4 |
| Inline comment coverage | 82.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _prompt_template_selection | 4 |
| _parse_index_tokens | 4 |
| _resolve_selection | 3 |
| _print_selection_summary | 3 |
| _select_operation_direction | 3 |

No violations found. This file complies with the guidelines.

## File: src\gateway\_wan2_variable_template.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 246 |
| Executable code lines | 129 |
| Functions | 14 |
| Classes | 1 |
| Average complexity | 2.5 |
| Max complexity | 4 |
| Inline comment coverage | 86.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _classify_port_key | 4 |
| _collect_template_futures | 4 |
| _fetch_template_config | 3 |
| _get_template_config_dict | 3 |
| _build_change_record | 3 |

No violations found. This file complies with the guidelines.

## File: src\gateway\device_template_cloner.py

- **Score**: 84.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 439 |
| Executable code lines | 193 |
| Functions | 18 |
| Classes | 1 |
| Average complexity | 3.4 |
| Max complexity | 7 |
| Inline comment coverage | 90.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| clone | 7 |
| _prompt_hardware_platform | 6 |
| _redact_dict_recursive | 6 |
| _select_site | 5 |
| _select_gateway | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 253 | low | STRUCT-COMPLEXITY | _prompt_hardware_platform | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 311 | low | STRUCT-COMPLEXITY | _redact_dict_recursive | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 398 | low | STRUCT-COMPLEXITY | clone | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 91 | high | STRUCT-PARAMS | __init__ | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 276 | medium | STRUCT-LENGTH | _build_template_payload | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 398 | medium | STRUCT-LENGTH | clone | Function spans 42 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 398 | low | STRUCT-BLOCKS | clone | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\gateway\gateway_export_utils.py

- **Score**: 69.0 / 100
- **Grade**: D+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 481 |
| Executable code lines | 260 |
| Functions | 16 |
| Classes | 1 |
| Average complexity | 3.6 |
| Max complexity | 8 |
| Inline comment coverage | 23.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_filtered_port_rows | 8 |
| _get_devices_from_cache | 8 |
| _build_management_ip_rows | 6 |
| management_ips | 6 |
| _get_devices_from_api | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 184 | low | STRUCT-COMPLEXITY | _build_management_ip_rows | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 235 | low | STRUCT-COMPLEXITY | management_ips | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 305 | low | STRUCT-COMPLEXITY | _build_filtered_port_rows | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 390 | low | STRUCT-COMPLEXITY | _get_devices_from_cache | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 425 | low | STRUCT-COMPLEXITY | _get_devices_from_api | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 23.1%; uncommented lines: 3, 5, 6, 7, 8, 10, 11, 16, 17, 18, 19, 20. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 39 | high | STRUCT-PARAMS | configure_gateway_export_utils_dependencies | Function takes 21 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 39 | high | STRUCT-LENGTH | configure_gateway_export_utils_dependencies | Function spans 98 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 235 | high | STRUCT-LENGTH | management_ips | Function spans 68 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 184 | medium | STRUCT-LENGTH | _build_management_ip_rows | Function spans 49 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 390 | medium | STRUCT-LENGTH | _get_devices_from_cache | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\gateway\gateway_stats_exporter.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 356 |
| Executable code lines | 220 |
| Functions | 16 |
| Classes | 1 |
| Average complexity | 3.5 |
| Max complexity | 7 |
| Inline comment coverage | 20.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_one_device_stats | 7 |
| _export_stats | 6 |
| _collect_device_wan_ips | 6 |
| _process_devices_concurrent | 5 |
| device_stats | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 87 | low | STRUCT-COMPLEXITY | _fetch_one_device_stats | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 195 | low | STRUCT-COMPLEXITY | _export_stats | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 288 | low | STRUCT-COMPLEXITY | _collect_device_wan_ips | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 20.0%; uncommented lines: 3, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 29 | high | STRUCT-PARAMS | configure_gateway_stats_exporter_dependencies | Function takes 15 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 29 | medium | STRUCT-LENGTH | configure_gateway_stats_exporter_dependencies | Function spans 50 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 87 | medium | STRUCT-LENGTH | _fetch_one_device_stats | Function spans 58 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 147 | medium | STRUCT-LENGTH | _process_devices_concurrent | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 87 | low | STRUCT-BLOCKS | _fetch_one_device_stats | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\gateway\overrides\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 17 |
| Executable code lines | 7 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\gateway\overrides\_deps.py

- **Score**: 91.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 51 |
| Executable code lines | 32 |
| Functions | 1 |
| Classes | 0 |
| Average complexity | 1.0 |
| Max complexity | 1 |
| Inline comment coverage | 96.9% |

### Violations

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 19 | high | STRUCT-PARAMS | configure_gateway_override_dependencies | Function takes 9 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 19 | medium | STRUCT-LENGTH | configure_gateway_override_dependencies | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\gateway\overrides\device_data_fetcher.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 148 |
| Executable code lines | 70 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 2.1 |
| Max complexity | 3 |
| Inline comment coverage | 82.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| fetch_all | 3 |
| _build_cache_from_results | 3 |
| _log_stats_failure | 3 |
| _fetch_sequential | 2 |
| _fetch_port_configs | 2 |

No violations found. This file complies with the guidelines.

## File: src\gateway\overrides\override_classifier.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 119 |
| Executable code lines | 46 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _port_has_override | 5 |
| build_port_entry | 4 |
| _format_config_type | 4 |
| classify | 3 |
| _field_matches_port | 2 |

No violations found. This file complies with the guidelines.

## File: src\gateway\overrides\override_report_writer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 139 |
| Executable code lines | 41 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 2.0 |
| Max complexity | 3 |
| Inline comment coverage | 82.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _log_summary | 3 |
| _print_summary | 3 |
| _print_summary_lines | 2 |

No violations found. This file complies with the guidelines.

## File: src\gateway\overrides\wan_override_walker.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 246 |
| Executable code lines | 104 |
| Functions | 12 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 4 |
| Inline comment coverage | 88.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_lookups | 4 |
| _extract_row_identifiers | 4 |
| _identify_devices | 3 |
| _classify_row | 3 |
| _assemble_entries | 3 |

No violations found. This file complies with the guidelines.

## File: src\gateway\template_config.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1292 |
| Executable code lines | 705 |
| Functions | 96 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 86.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _scan_service_policies | 5 |
| _parse_template_indices | 5 |
| parse_state_from_address | 5 |
| _parse_state_comma_separated | 5 |
| _infer_state_without_postal | 5 |

No violations found. This file complies with the guidelines.

## File: src\gateway\wan2_migration_manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 756 |
| Executable code lines | 430 |
| Functions | 64 |
| Classes | 3 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 80.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_json_ip_payload | 5 |
| _parse_site_indices | 5 |
| _accumulate_severity | 5 |
| set_site_variable | 4 |
| _build_site_to_template_mapping | 4 |

No violations found. This file complies with the guidelines.

## File: src\gateway\wan2_variable.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 182 |
| Executable code lines | 84 |
| Functions | 7 |
| Classes | 2 |
| Average complexity | 2.6 |
| Max complexity | 4 |
| Inline comment coverage | 85.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| execute | 4 |
| _select_and_analyze | 4 |
| __getattr__ | 3 |
| _run_and_report | 3 |
| _unpack_deps | 2 |

No violations found. This file complies with the guidelines.

## File: src\gateway\wan_probe_device_override_manager.py

- **Score**: 71.0 / 100
- **Grade**: C-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 594 |
| Executable code lines | 375 |
| Functions | 25 |
| Classes | 1 |
| Average complexity | 4.1 |
| Max complexity | 10 |
| Inline comment coverage | 25.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _select_template | 10 |
| _execute | 8 |
| _show_preview | 8 |
| _find_template_sites | 7 |
| _scan_template_sites_for_gateways | 7 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 111 | low | STRUCT-COMPLEXITY | _execute | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 188 | low | STRUCT-COMPLEXITY | _select_template | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 244 | low | STRUCT-COMPLEXITY | _find_template_sites | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 293 | low | STRUCT-COMPLEXITY | _scan_template_sites_for_gateways | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 357 | low | STRUCT-COMPLEXITY | _show_preview | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 521 | low | STRUCT-COMPLEXITY | _generate_report | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 25.9%; uncommented lines: 3, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 25 | high | STRUCT-PARAMS | configure_wan_probe_device_override_dependencies | Function takes 10 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 25 | medium | STRUCT-LENGTH | configure_wan_probe_device_override_dependencies | Function spans 35 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 111 | medium | STRUCT-LENGTH | _execute | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 188 | medium | STRUCT-LENGTH | _select_template | Function spans 55 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 111 | low | STRUCT-BLOCKS | _execute | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 188 | low | STRUCT-BLOCKS | _select_template | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\inventory\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\inventory\csv_comparator.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1593 |
| Executable code lines | 805 |
| Functions | 111 |
| Classes | 6 |
| Average complexity | 2.3 |
| Max complexity | 5 |
| Inline comment coverage | 84.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _get_user_csv_selection | 5 |
| _load_skip_addresses | 5 |
| _print_detected_fields | 5 |
| _extract_address_from_row | 5 |
| _build_mist_site_addresses | 5 |

No violations found. This file complies with the guidelines.

## File: src\inventory\inventory_summary\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\inventory\inventory_summary\pivot_renderer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 154 |
| Executable code lines | 57 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _compute_pivot | 5 |
| _build_table | 4 |
| _update_row_and_columns | 3 |
| _populate_pivot | 2 |
| _build_export_row | 2 |

No violations found. This file complies with the guidelines.

## File: src\inventory\inventory_summary\version_per_model_fetcher.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 247 |
| Executable code lines | 105 |
| Functions | 13 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 89.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _ap_rows | 5 |
| _accumulate_switch_versions | 5 |
| _gateway_rows | 5 |
| _accumulate_unassigned | 4 |
| _prefetch_switches | 4 |

No violations found. This file complies with the guidelines.

## File: src\inventory\org_device_inventory_msp.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 548 |
| Executable code lines | 308 |
| Functions | 33 |
| Classes | 3 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 88.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| run_single_msp_org | 5 |
| dispatch | 5 |
| _call_list_msp_orgs | 4 |
| _sanitize_msp_name | 4 |
| _build_msp_version_pivot | 4 |

No violations found. This file complies with the guidelines.

## File: src\inventory\org_device_inventory_summary.py

- **Score**: 79.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 411 |
| Executable code lines | 229 |
| Functions | 17 |
| Classes | 1 |
| Average complexity | 4.2 |
| Max complexity | 9 |
| Inline comment coverage | 24.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_switch_physical_inventory | 9 |
| _fetch_all_counts | 8 |
| _resolve_safe_org_name | 7 |
| _aggregate_unassigned_counts | 6 |
| _aggregate_switch_counts | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 43 | low | STRUCT-COMPLEXITY | _fetch_switch_physical_inventory | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 210 | low | STRUCT-COMPLEXITY | _aggregate_unassigned_counts | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 254 | low | STRUCT-COMPLEXITY | _fetch_all_counts | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 336 | low | STRUCT-COMPLEXITY | _resolve_safe_org_name | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 24.5%; uncommented lines: 3, 5, 6, 7, 8, 10, 12, 13, 14, 15, 18, 26. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 43 | medium | STRUCT-LENGTH | _fetch_switch_physical_inventory | Function spans 43 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 254 | medium | STRUCT-LENGTH | _fetch_all_counts | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 352 | medium | STRUCT-LENGTH | run_for_org | Function spans 51 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 43 | low | STRUCT-BLOCKS | _fetch_switch_physical_inventory | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 254 | low | STRUCT-BLOCKS | _fetch_all_counts | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\maps\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\maps\_container_detection.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 151 |
| Executable code lines | 72 |
| Functions | 7 |
| Classes | 0 |
| Average complexity | 3.4 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _check_app_path | 5 |
| _check_cgroup_markers | 4 |
| is_running_in_container | 4 |
| _check_env_override | 3 |
| _check_container_env_vars | 3 |

No violations found. This file complies with the guidelines.

## File: src\maps\_flask_viewer.py

- **Score**: 74.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1242 |
| Executable code lines | 114 |
| Functions | 15 |
| Classes | 0 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 2.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _handle_site_maps_request | 5 |
| _fetch_map_image_bytes | 4 |
| _handle_map_image_request | 4 |
| _handle_map_data_request | 3 |
| _render_viewer_page | 3 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 12 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 2.6%; uncommented lines: 12, 14, 15, 19, 21, 24, 33, 35, 37, 38, 39, 40. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 24 | high | STRUCT-PARAMS | _handle_map_data_request | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 47 | high | STRUCT-PARAMS | _render_viewer_page | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 176 | high | STRUCT-PARAMS | launch_flask_viewer | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 176 | high | STRUCT-LENGTH | launch_flask_viewer | Function spans 1067 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\maps\_maps_backup.py

- **Score**: 65.0 / 100
- **Grade**: D

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 275 |
| Executable code lines | 123 |
| Functions | 11 |
| Classes | 1 |
| Average complexity | 4.4 |
| Max complexity | 9 |
| Inline comment coverage | 1.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _backup_download_image | 9 |
| _backup_fetch_device_placements | 8 |
| _backup_fetch_items | 6 |
| _backup_print_summary | 6 |
| _backup_write_file | 5 |

### Violations

#### Architecture

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 262 | high | ARCH-DELEGATE | backup_map_geometry | Function only forwards its arguments to another call (pass-through wrapper). | Inline the call at its call sites or move the logic into the owning class method. |

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 37 | low | STRUCT-COMPLEXITY | _backup_download_image | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 75 | low | STRUCT-COMPLEXITY | _backup_fetch_items | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 89 | low | STRUCT-COMPLEXITY | _backup_fetch_device_placements | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 152 | low | STRUCT-COMPLEXITY | _backup_print_summary | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 15 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 1.6%; uncommented lines: 15, 17, 18, 22, 25, 28, 29, 31, 32, 34, 35, 37. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 170 | high | STRUCT-LENGTH | _backup_map_geometry | Function spans 90 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 262 | high | STRUCT-PARAMS | backup_map_geometry | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 37 | medium | STRUCT-LENGTH | _backup_download_image | Function spans 37 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 89 | medium | STRUCT-LENGTH | _backup_fetch_device_placements | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 37 | low | STRUCT-BLOCKS | _backup_download_image | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\maps\_maps_clone.py

- **Score**: 84.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 332 |
| Executable code lines | 222 |
| Functions | 15 |
| Classes | 1 |
| Average complexity | 4.4 |
| Max complexity | 10 |
| Inline comment coverage | 4.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| clone_map | 10 |
| _clone_zones | 7 |
| _download_clone_image | 6 |
| _fetch_source_map_with_display | 5 |
| _fetch_source_zone_count | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 127 | low | STRUCT-COMPLEXITY | _download_clone_image | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 220 | low | STRUCT-COMPLEXITY | _clone_zones | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 267 | low | STRUCT-COMPLEXITY | clone_map | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 14 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 4.5%; uncommented lines: 14, 16, 17, 21, 24, 27, 28, 30, 31, 33, 34, 36. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 127 | medium | STRUCT-LENGTH | _download_clone_image | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 267 | medium | STRUCT-LENGTH | clone_map | Function spans 57 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 267 | low | STRUCT-BLOCKS | clone_map | Function has 8 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\maps\_maps_coverage.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 542 |
| Executable code lines | 224 |
| Functions | 44 |
| Classes | 2 |
| Average complexity | 2.1 |
| Max complexity | 5 |
| Inline comment coverage | 84.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _extract_row_values | 5 |
| _fetch_all_coverage | 5 |
| _safe_call | 4 |
| _rows_to_grid_points | 4 |
| _fetch_map_zones | 4 |

No violations found. This file complies with the guidelines.

## File: src\maps\_maps_matplotlib.py

- **Score**: 82.0 / 100
- **Grade**: B-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 211 |
| Executable code lines | 108 |
| Functions | 9 |
| Classes | 1 |
| Average complexity | 3.8 |
| Max complexity | 7 |
| Inline comment coverage | 1.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_initial_site | 7 |
| _launch_matplotlib_viewer | 6 |
| _fetch_entities_on_map | 6 |
| _resolve_initial_map | 4 |
| _fetch_site_maps | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 38 | low | STRUCT-COMPLEXITY | _launch_matplotlib_viewer | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 99 | low | STRUCT-COMPLEXITY | _resolve_initial_site | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 116 | low | STRUCT-COMPLEXITY | _fetch_entities_on_map | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 16 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 1.9%; uncommented lines: 16, 18, 19, 23, 26, 29, 30, 32, 33, 35, 36, 38. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 136 | high | STRUCT-LENGTH | launch_viewer_standalone | Function spans 67 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 38 | medium | STRUCT-LENGTH | _launch_matplotlib_viewer | Function spans 60 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\maps\_maps_testing.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 301 |
| Executable code lines | 179 |
| Functions | 21 |
| Classes | 2 |
| Average complexity | 2.2 |
| Max complexity | 4 |
| Inline comment coverage | 86.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _print_summary | 4 |
| _tally_map_images | 4 |
| _invoke_test | 3 |
| _list_site_maps | 3 |
| _count_maps_across_sites | 3 |

No violations found. This file complies with the guidelines.

## File: src\maps\_maps_utils.py

- **Score**: 91.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 129 |
| Executable code lines | 60 |
| Functions | 5 |
| Classes | 0 |
| Average complexity | 3.6 |
| Max complexity | 5 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| flatten_dict_recursively | 5 |
| _flatten_list_value | 4 |
| sanitize_filename | 4 |
| write_data_with_format_selection | 3 |
| _write_csv_rows | 2 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 10 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 10, 12, 13, 14, 15, 17, 22, 26, 29, 36, 37, 38. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 81 | medium | STRUCT-LENGTH | write_data_with_format_selection | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\maps\_maps_wizard.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 872 |
| Executable code lines | 484 |
| Functions | 60 |
| Classes | 5 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 81.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _filter_records_by_map | 5 |
| _apply_asset_scaling | 5 |
| _wizard_run | 5 |
| _wizard_get_new_image | 4 |
| _is_valid_image_file | 4 |

No violations found. This file complies with the guidelines.

## File: src\maps\_plotly_viewer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 995 |
| Executable code lines | 402 |
| Functions | 57 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 80.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _add_mesh_links | 5 |
| _categorize_devices_by_type | 5 |
| _extract_device_coords | 5 |
| _add_static_map_devices | 5 |
| _get_device_status | 4 |

No violations found. This file complies with the guidelines.

## File: src\maps\_viewer_launch.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1528 |
| Executable code lines | 277 |
| Functions | 64 |
| Classes | 4 |
| Average complexity | 1.1 |
| Max complexity | 3 |
| Inline comment coverage | 95.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _log_startup | 3 |
| _build_layer_toggle_sections | 2 |
| _build_delete_from_mist_buttons | 2 |
| _build_zones_section | 2 |
| run | 2 |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 17 |
| Executable code lines | 3 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\_viewer_clone.py

- **Score**: 77.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 351 |
| Executable code lines | 184 |
| Functions | 15 |
| Classes | 1 |
| Average complexity | 4.5 |
| Max complexity | 10 |
| Inline comment coverage | 59.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _download_source_image | 10 |
| _build_clone_payload | 9 |
| _validate_clone_inputs | 8 |
| _clone_zones_for_map | 7 |
| execute_clone_operation | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 40 | low | STRUCT-COMPLEXITY | execute_clone_operation | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 80 | low | STRUCT-COMPLEXITY | _validate_clone_inputs | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 156 | low | STRUCT-COMPLEXITY | _build_clone_payload | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 176 | low | STRUCT-COMPLEXITY | _download_source_image | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 233 | low | STRUCT-COMPLEXITY | _upload_clone_image | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 263 | low | STRUCT-COMPLEXITY | _clone_zones_for_map | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 40 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 59.8%; uncommented lines: 40, 54, 68, 71, 80, 89, 91, 99, 105, 119, 125, 127. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 40 | medium | STRUCT-LENGTH | execute_clone_operation | Function spans 38 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 176 | medium | STRUCT-LENGTH | _download_source_image | Function spans 35 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 233 | medium | STRUCT-LENGTH | _upload_clone_image | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 303 | medium | STRUCT-LENGTH | _render_clone_success | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 156 | low | STRUCT-BLOCKS | _build_clone_payload | Function has 8 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 176 | low | STRUCT-BLOCKS | _download_source_image | Function has 8 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\maps\launcher\_viewer_drawing.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 609 |
| Executable code lines | 282 |
| Functions | 37 |
| Classes | 5 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 81.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_site_map_ppm | 5 |
| _delete_zones_one_by_one | 5 |
| _dispatch_save_by_mode | 4 |
| _delete_walls | 4 |
| _filter_zones_by_map | 4 |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\_viewer_refresh.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 822 |
| Executable code lines | 386 |
| Functions | 56 |
| Classes | 6 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 81.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_client_map_context | 5 |
| _build_client_entry | 5 |
| _apply_client_traces | 5 |
| _extract_coverage_payload | 5 |
| _aggregate_grid_cells | 5 |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\_viewer_site_switch.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 748 |
| Executable code lines | 313 |
| Functions | 51 |
| Classes | 1 |
| Average complexity | 2.1 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| set_scale | 5 |
| _reannotate_measurements | 4 |
| _resolve_url_site_id | 4 |
| _resolve_url_map_id | 4 |
| _dispatch_site_switch | 4 |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\_viewer_ui.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 900 |
| Executable code lines | 407 |
| Functions | 63 |
| Classes | 4 |
| Average complexity | 2.1 |
| Max complexity | 5 |
| Inline comment coverage | 84.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _dispatch_zone_action | 5 |
| _apply_zone_visibility | 4 |
| _extract_zone_selection | 4 |
| _select_origin_updater | 4 |
| _delete_panel_outputs | 4 |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\_viewer_url_switch.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 958 |
| Executable code lines | 374 |
| Functions | 47 |
| Classes | 7 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 89.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _process_grid_row | 5 |
| _prepare_url_map_switch | 5 |
| _try_fetch_fresh_map_ids | 5 |
| _fetch_clients_for_map | 5 |
| _group_devices_by_type | 5 |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\viewer_callbacks.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 383 |
| Executable code lines | 97 |
| Functions | 24 |
| Classes | 1 |
| Average complexity | 1.0 |
| Max complexity | 1 |
| Inline comment coverage | 84.5% |

No violations found. This file complies with the guidelines.

## File: src\maps\launcher\viewer_state.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 96 |
| Executable code lines | 20 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 90.0% |

No violations found. This file complies with the guidelines.

## File: src\maps\maps_manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 2786 |
| Executable code lines | 1594 |
| Functions | 191 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _pick_org_from_privileges | 5 |
| _resolve_org_id | 5 |
| _match_site_by_name | 5 |
| _select_map_with_list | 5 |
| _dispatch_menu_choice | 5 |

No violations found. This file complies with the guidelines.

## File: src\maps\plotly_heatmap_renderer.py

- **Score**: 73.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 184 |
| Executable code lines | 64 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 3.1 |
| Max complexity | 10 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| build_heatmap_trace | 10 |
| _build_grid_data | 3 |
| _build_z_matrix | 3 |
| __init__ | 2 |
| _resolve_indices | 2 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 18 | low | STRUCT-COMPLEXITY | build_heatmap_trace | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 8, 11, 14, 16, 18, 26, 27, 28, 30. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 18 | high | STRUCT-LENGTH | build_heatmap_trace | Function spans 78 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 110 | high | STRUCT-PARAMS | _build_grid_data | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 144 | high | STRUCT-PARAMS | _log_alignment | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 144 | medium | STRUCT-LENGTH | _log_alignment | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\maps\plotly_map_callback_manager.py

- **Score**: 82.0 / 100
- **Grade**: B-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 131 |
| Executable code lines | 48 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 5.4 |
| Max complexity | 8 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| apply_layer_toggles | 8 |
| build_click_details | 7 |
| _set_trace_visibility | 6 |
| _set_annotation_visibility | 4 |
| _client_layers_enabled | 2 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 42 | low | STRUCT-COMPLEXITY | apply_layer_toggles | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 75 | low | STRUCT-COMPLEXITY | build_click_details | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 100 | low | STRUCT-COMPLEXITY | _set_trace_visibility | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 7, 27, 39, 42, 57, 65, 66, 67, 69, 70. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 42 | high | STRUCT-PARAMS | apply_layer_toggles | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 42 | medium | STRUCT-LENGTH | apply_layer_toggles | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\maps\plotly_map_figure_builder.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 206 |
| Executable code lines | 81 |
| Functions | 6 |
| Classes | 1 |
| Average complexity | 5.0 |
| Max complexity | 8 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| add_wayfinding | 8 |
| add_zones | 7 |
| _add_edge_segments | 6 |
| _build_node_lookup | 4 |
| add_walls | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 46 | low | STRUCT-COMPLEXITY | add_wayfinding | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 94 | low | STRUCT-COMPLEXITY | add_zones | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 178 | low | STRUCT-COMPLEXITY | _add_edge_segments | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 8, 11, 14, 16, 18, 20, 21, 22, 24. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 94 | high | STRUCT-LENGTH | add_zones | Function spans 65 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 18 | medium | STRUCT-LENGTH | add_walls | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 46 | medium | STRUCT-LENGTH | add_wayfinding | Function spans 47 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 178 | medium | STRUCT-LENGTH | _add_edge_segments | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 46 | low | STRUCT-BLOCKS | add_wayfinding | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\maps\plotly_map_serializer.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 61 |
| Executable code lines | 19 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 1.7 |
| Max complexity | 3 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| build_named_items | 3 |
| build_dropdown_options | 3 |
| increment_cache_bust | 2 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 6, 10, 20, 31, 33, 34, 37, 39, 40, 43, 45. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 10 | high | STRUCT-PARAMS | build_map_config | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |

## File: src\maps\plotly_map_templates.py

- **Score**: 84.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 209 |
| Executable code lines | 21 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 7 |
| Inline comment coverage | 0.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| validate_template | 7 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 189 | low | STRUCT-COMPLEXITY | validate_template | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 4 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 4, 11, 18, 19, 20, 22, 28, 149, 155, 177, 183, 189. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 22 | high | STRUCT-LENGTH | get_custom_css | Function spans 126 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 149 | medium | STRUCT-LENGTH | get_html_template | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\marvis\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 8 |
| Executable code lines | 2 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\marvis\marvis_utils.py

- **Score**: 78.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 300 |
| Executable code lines | 84 |
| Functions | 6 |
| Classes | 1 |
| Average complexity | 5.0 |
| Max complexity | 10 |
| Inline comment coverage | 98.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| format_for_csv | 10 |
| _build_flat_row | 7 |
| _expand_sites_rows | 6 |
| _flatten_results_array | 4 |
| _recover_via_flatten_pipeline | 2 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 58 | low | STRUCT-COMPLEXITY | format_for_csv | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 156 | low | STRUCT-COMPLEXITY | _expand_sites_rows | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 200 | low | STRUCT-COMPLEXITY | _build_flat_row | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 58 | high | STRUCT-LENGTH | format_for_csv | Function spans 93 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 156 | medium | STRUCT-LENGTH | _expand_sites_rows | Function spans 43 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 200 | medium | STRUCT-LENGTH | _build_flat_row | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 237 | medium | STRUCT-LENGTH | _flatten_results_array | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 265 | medium | STRUCT-LENGTH | _recover_via_flatten_pipeline | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 58 | low | STRUCT-BLOCKS | format_for_csv | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\network\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\network\_routing_utils_display.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 521 |
| Executable code lines | 268 |
| Functions | 36 |
| Classes | 2 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 84.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _print_routing_stats | 5 |
| _print_forwarding_stats | 4 |
| _extract_prefix_group | 4 |
| _display_prefix_groups | 4 |
| _format_route_status | 4 |

No violations found. This file complies with the guidelines.

## File: src\network\_routing_utils_forwarding.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 514 |
| Executable code lines | 251 |
| Functions | 38 |
| Classes | 1 |
| Average complexity | 2.3 |
| Max complexity | 5 |
| Inline comment coverage | 81.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _try_parse_forwarding_json | 5 |
| _extract_forwarding_from_dict | 5 |
| _run_forwarding_flow | 4 |
| _select_forwarding_table_device | 4 |
| _parse_forwarding_text | 4 |

No violations found. This file complies with the guidelines.

## File: src\network\_routing_utils_parsing.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 461 |
| Executable code lines | 239 |
| Functions | 33 |
| Classes | 1 |
| Average complexity | 3.1 |
| Max complexity | 5 |
| Inline comment coverage | 83.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _update_juniper_via | 5 |
| _parse_ssr_routing | 5 |
| _extract_routes_from_json_dict | 5 |
| _parse_standard_route_line | 5 |
| _classify_route_part | 4 |

No violations found. This file complies with the guidelines.

## File: src\network\_routing_utils_payload.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 361 |
| Executable code lines | 177 |
| Functions | 25 |
| Classes | 2 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 86.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _apply_ssr_scalars | 5 |
| _extract_ssr_session_id | 5 |
| _apply_neighbor | 4 |
| _parse_refresh_interval | 4 |
| _parse_refresh_duration | 4 |

No violations found. This file complies with the guidelines.

## File: src\network\_routing_utils_routing.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 418 |
| Executable code lines | 226 |
| Functions | 29 |
| Classes | 1 |
| Average complexity | 2.3 |
| Max complexity | 5 |
| Inline comment coverage | 81.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _select_routing_table_device | 5 |
| _process_routing_table_results | 5 |
| _verify_gateway_ssr | 4 |
| _run_routing_table_flow | 4 |
| _classify_and_parse_route_line | 3 |

No violations found. This file complies with the guidelines.

## File: src\network\_routing_utils_ssr.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 331 |
| Executable code lines | 166 |
| Functions | 21 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 88.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _select_ssr_device | 5 |
| _run_ssr_flow | 4 |
| _display_ssr_route_output | 4 |
| execute_show_ssr_routes | 3 |
| _start_ssr_session | 3 |

No violations found. This file complies with the guidelines.

## File: src\network\routing_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 330 |
| Executable code lines | 167 |
| Functions | 18 |
| Classes | 5 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 82.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_device_info | 5 |
| __getattr__ | 4 |
| _init_websocket_manager | 4 |
| _cleanup_websocket | 4 |
| _connect_websocket | 3 |

No violations found. This file complies with the guidelines.

## File: src\org_data_collector.py

- **Score**: 82.0 / 100
- **Grade**: B-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1233 |
| Executable code lines | 145 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 5 |
| Inline comment coverage | 2.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _collect_all | 5 |
| _run_single | 4 |
| execute | 2 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 9 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 2.1%; uncommented lines: 9, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 1114 | medium | STRUCT-LENGTH | execute | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1143 | medium | STRUCT-LENGTH | _collect_all | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1174 | medium | STRUCT-LENGTH | _run_single | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 1207 | medium | STRUCT-LENGTH | _print_summary | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\refactors\serial_cc\global_assignments_builder.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 103 |
| Executable code lines | 53 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 2.9 |
| Max complexity | 5 |
| Inline comment coverage | 98.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _apply_optional_imports | 5 |
| _import_scourgify_normalizer | 3 |
| _import_rapidfuzz_matcher | 3 |
| _apply_logged_module | 3 |
| _apply_attribute_exports | 2 |

No violations found. This file complies with the guidelines.

## File: src\refactors\serial_cc\import_initialization_service.py

- **Score**: 95.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 99 |
| Executable code lines | 58 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 5.2 |
| Max complexity | 8 |
| Inline comment coverage | 86.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _import_package_group | 8 |
| _log_summary | 7 |
| _run_dependency_upgrade | 4 |
| execute | 2 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 24 | low | STRUCT-COMPLEXITY | _import_package_group | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 49 | low | STRUCT-COMPLEXITY | _log_summary | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 71 | medium | STRUCT-LENGTH | execute | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\refactors\serial_cc\security_events.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 219 |
| Executable code lines | 118 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 4.0 |
| Max complexity | 6 |
| Inline comment coverage | 47.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_site_rogue | 6 |
| execute | 5 |
| _all_outputs_fresh | 5 |
| _export_rogue_data | 5 |
| _export_flattened_dataset | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 137 | low | STRUCT-COMPLEXITY | _fetch_site_rogue | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 47.5%; uncommented lines: 3, 4, 5, 6, 7, 8, 9, 10, 15, 17, 18, 34. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 105 | high | STRUCT-PARAMS | _export_flattened_dataset | Function takes 8 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 38 | medium | STRUCT-LENGTH | execute | Function spans 49 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 105 | medium | STRUCT-LENGTH | _export_flattened_dataset | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 137 | medium | STRUCT-LENGTH | _fetch_site_rogue | Function spans 34 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 189 | medium | STRUCT-LENGTH | _export_rogue_data | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\refactors\serial_cc\site_client_insights.py

- **Score**: 89.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 198 |
| Executable code lines | 123 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 4.3 |
| Max complexity | 9 |
| Inline comment coverage | 90.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| execute | 9 |
| _list_and_display_clients | 5 |
| _collect_client_metrics | 5 |
| _resolve_site_name | 4 |
| _resolve_client_mac | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 135 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 135 | high | STRUCT-LENGTH | execute | Function spans 64 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 81 | medium | STRUCT-LENGTH | _collect_client_metrics | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 135 | low | STRUCT-BLOCKS | execute | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\refactors\serial_cc\sle_metrics.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 303 |
| Executable code lines | 154 |
| Functions | 17 |
| Classes | 2 |
| Average complexity | 2.3 |
| Max complexity | 4 |
| Inline comment coverage | 81.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_sites_aggregated | 4 |
| _fetch_category_sites | 3 |
| _fetch_single_sle | 3 |
| _fetch_specialized_metric | 3 |
| _run_specialized_loop | 3 |

No violations found. This file complies with the guidelines.

## File: src\refactors\serial_cc\start_site_client_capture_wireless.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 249 |
| Executable code lines | 132 |
| Functions | 9 |
| Classes | 1 |
| Average complexity | 3.8 |
| Max complexity | 8 |
| Inline comment coverage | 85.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| execute | 8 |
| _print_summary | 6 |
| _select_ap_filter | 5 |
| _prompt_bounded_int | 5 |
| _select_client_mac | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 162 | low | STRUCT-COMPLEXITY | _print_summary | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 186 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 186 | high | STRUCT-LENGTH | execute | Function spans 64 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 89 | medium | STRUCT-LENGTH | _select_ap_filter | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 186 | low | STRUCT-BLOCKS | execute | Function has 7 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\refactors\serial_cc\start_site_scan_capture.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 304 |
| Executable code lines | 184 |
| Functions | 12 |
| Classes | 1 |
| Average complexity | 3.6 |
| Max complexity | 10 |
| Inline comment coverage | 88.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| execute | 10 |
| _check_existing_captures | 7 |
| _select_bandwidth | 5 |
| _prompt_channel | 4 |
| _prompt_duration | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 202 | low | STRUCT-COMPLEXITY | _check_existing_captures | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 232 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 232 | high | STRUCT-LENGTH | execute | Function spans 73 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 202 | medium | STRUCT-LENGTH | _check_existing_captures | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 232 | low | STRUCT-BLOCKS | execute | Function has 9 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\refactors\serial_cc\switch_vc_stats.py

- **Score**: 85.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 173 |
| Executable code lines | 88 |
| Functions | 6 |
| Classes | 1 |
| Average complexity | 4.5 |
| Max complexity | 9 |
| Inline comment coverage | 89.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _collect_vc_stats | 9 |
| _emit_debug_preview | 7 |
| _load_switches | 4 |
| _fetch_vc_for_switch | 4 |
| execute | 2 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 91 | low | STRUCT-COMPLEXITY | _collect_vc_stats | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 124 | low | STRUCT-COMPLEXITY | _emit_debug_preview | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 49 | medium | STRUCT-LENGTH | _fetch_vc_for_switch | Function spans 40 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 91 | medium | STRUCT-LENGTH | _collect_vc_stats | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 91 | medium | STRUCT-NESTING | _collect_vc_stats | Maximum nesting depth is 5 (limit 4). | Flatten nesting with early returns, guard clauses, or extracted helper methods. |
| 124 | medium | STRUCT-LENGTH | _emit_debug_preview | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 91 | low | STRUCT-BLOCKS | _collect_vc_stats | Function has 9 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\refactors\serial_cc\test_results_by_site.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 201 |
| Executable code lines | 113 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 88.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _load_fast_site_ids | 5 |
| _resolve_site_ids | 5 |
| _extract_tagged_results | 4 |
| execute | 4 |
| _collect_fast | 3 |

No violations found. This file complies with the guidelines.

## File: src\reports\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\reports\e911_bssid.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1079 |
| Executable code lines | 433 |
| Functions | 56 |
| Classes | 2 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 81.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_site_lookup | 5 |
| _fetch_ap_stats | 5 |
| _load_template_wlans | 5 |
| _infer_radio_bands | 5 |
| _fetch_site_maps | 5 |

No violations found. This file complies with the guidelines.

## File: src\site\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 50 |
| Executable code lines | 12 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\address_corrector.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 133 |
| Executable code lines | 82 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 3.7 |
| Max complexity | 8 |
| Inline comment coverage | 79.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _review_one | 8 |
| _print_summary | 7 |
| _is_correctable | 6 |
| correctable | 3 |
| review_and_apply | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 51 | low | STRUCT-COMPLEXITY | _is_correctable | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 73 | low | STRUCT-COMPLEXITY | _review_one | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 128 | low | STRUCT-COMPLEXITY | _print_summary | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 30 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 79.3%; uncommented lines: 30, 34, 37, 41, 51, 61, 73, 79, 82, 85, 93, 96. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\site\address_audit\address_resolver.py

- **Score**: 86.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 483 |
| Executable code lines | 251 |
| Functions | 31 |
| Classes | 1 |
| Average complexity | 3.3 |
| Max complexity | 8 |
| Inline comment coverage | 84.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| has_conflicting_hints | 8 |
| _combine | 6 |
| _compare_internal | 6 |
| _build_clean_suggestion | 6 |
| _should_consult_ui | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 88 | low | STRUCT-COMPLEXITY | _combine | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 117 | low | STRUCT-COMPLEXITY | _compare_internal | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 148 | low | STRUCT-COMPLEXITY | _build_clean_suggestion | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 249 | low | STRUCT-COMPLEXITY | _should_consult_ui | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 312 | low | STRUCT-COMPLEXITY | has_conflicting_hints | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 88 | medium | STRUCT-LENGTH | _combine | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 161 | medium | STRUCT-LENGTH | _validate_nominatim | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 426 | medium | STRUCT-LENGTH | _from_cache | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\site\address_audit\audit_engine.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 939 |
| Executable code lines | 464 |
| Functions | 74 |
| Classes | 3 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 80.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _prompt_csv_choice | 5 |
| _load_mist_data | 5 |
| _apply_duplicate_flag | 5 |
| _classify_external | 5 |
| _classify_suite | 5 |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\audit_reporter.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 98 |
| Executable code lines | 42 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 4 |
| Inline comment coverage | 85.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_row | 4 |
| _format_address | 3 |
| _format_csv_address | 3 |
| save | 2 |
| save_corrections | 2 |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\business_authority_ingester.py

- **Score**: 95.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 169 |
| Executable code lines | 85 |
| Functions | 10 |
| Classes | 2 |
| Average complexity | 3.4 |
| Max complexity | 10 |
| Inline comment coverage | 83.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_row | 10 |
| match | 7 |
| load | 4 |
| _merge_street_and_space | 3 |
| _address_key | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 73 | low | STRUCT-COMPLEXITY | match | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 112 | low | STRUCT-COMPLEXITY | _parse_row | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 73 | medium | STRUCT-LENGTH | match | Function spans 38 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\site\address_audit\comparison_display.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 121 |
| Executable code lines | 60 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 4 |
| Inline comment coverage | 83.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _row_labels | 4 |
| prompt_post_table | 4 |
| _build_row | 3 |
| _summary_line | 3 |
| _format_address | 3 |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\csv_ingester.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 121 |
| Executable code lines | 74 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 87.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_reader | 5 |
| _choose_delimiter | 5 |
| _parse_row | 5 |
| _read_sample_line | 3 |
| _build_row | 3 |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\models.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 133 |
| Executable code lines | 63 |
| Functions | 0 |
| Classes | 8 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 87.3% |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\perf.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 63 |
| Executable code lines | 29 |
| Functions | 6 |
| Classes | 1 |
| Average complexity | 1.7 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| summary | 5 |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\site_matcher.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 111 |
| Executable code lines | 55 |
| Functions | 6 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 87.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| match_fuzzy | 5 |
| _build_choice_map | 5 |
| match_serial | 3 |
| __init__ | 2 |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\snmp_enricher.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 78 |
| Executable code lines | 35 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 4 |
| Inline comment coverage | 97.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _read_var_location | 4 |
| _read_config_location | 4 |
| _strip_store_prefix | 3 |
| _describe_source | 3 |
| enrich | 2 |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\suite_patterns.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 41 |
| Executable code lines | 6 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\site\address_audit\ui_geocoder.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 583 |
| Executable code lines | 321 |
| Functions | 37 |
| Classes | 1 |
| Average complexity | 2.9 |
| Max complexity | 10 |
| Inline comment coverage | 86.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _read_fresh_suggestions | 10 |
| _preserve_query_suite | 7 |
| ensure_location_field_ready | 5 |
| geocode_via_ui | 5 |
| close | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 306 | low | STRUCT-COMPLEXITY | _read_fresh_suggestions | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 446 | low | STRUCT-COMPLEXITY | _preserve_query_suite | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 306 | medium | STRUCT-LENGTH | _read_fresh_suggestions | Function spans 39 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 446 | medium | STRUCT-LENGTH | _preserve_query_suite | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 541 | medium | STRUCT-LENGTH | spawn_debuggable_browser | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 306 | low | STRUCT-BLOCKS | _read_fresh_suggestions | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\site\site_config_manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1070 |
| Executable code lines | 604 |
| Functions | 59 |
| Classes | 3 |
| Average complexity | 2.9 |
| Max complexity | 5 |
| Inline comment coverage | 81.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _execute_site_creation | 5 |
| _prompt_update_mode | 5 |
| _confirm_rf_template_operation | 5 |
| _assign_sites_to_rf_templates | 5 |
| create_ap_model_device_profiles | 5 |

No violations found. This file complies with the guidelines.

## File: src\ssh\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssh\batch\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 11 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssh\batch\batch_executor.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 425 |
| Executable code lines | 174 |
| Functions | 21 |
| Classes | 5 |
| Average complexity | 2.0 |
| Max complexity | 5 |
| Inline comment coverage | 87.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _iterate_commands | 5 |
| __post_init__ | 4 |
| from_configs | 4 |
| _write_command_output | 3 |
| _write_footer | 3 |

No violations found. This file complies with the guidelines.

## File: src\ssh\batch\host_runner.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 219 |
| Executable code lines | 87 |
| Functions | 10 |
| Classes | 2 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 87.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _needs_interactive | 5 |
| __post_init__ | 4 |
| from_configs | 4 |
| _is_password_reply | 4 |
| _dispatch | 3 |

No violations found. This file complies with the guidelines.

## File: src\ssh\batch\interactive_batch_executor.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 757 |
| Executable code lines | 341 |
| Functions | 41 |
| Classes | 5 |
| Average complexity | 2.3 |
| Max complexity | 5 |
| Inline comment coverage | 80.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _iterate_steps | 5 |
| _prompt_ended_wait | 5 |
| _write_clean_line | 4 |
| __post_init__ | 4 |
| from_configs | 4 |

No violations found. This file complies with the guidelines.

## File: src\ssh\batch\multi_host_runner.py

- **Score**: 73.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 261 |
| Executable code lines | 94 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 3.7 |
| Max complexity | 7 |
| Inline comment coverage | 29.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_params | 7 |
| _collect_results | 5 |
| _process_done_futures | 5 |
| _log_invocation | 3 |
| _print_summary | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 72 | low | STRUCT-COMPLEXITY | _resolve_params | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 29.8%; uncommented lines: 8, 12, 17, 20, 42, 46, 52, 53, 54, 58, 86, 87. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 24 | high | STRUCT-PARAMS | run | Function takes 10 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 72 | high | STRUCT-PARAMS | _resolve_params | Function takes 10 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 107 | high | STRUCT-PARAMS | _log_invocation | Function takes 9 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 144 | high | STRUCT-PARAMS | _dispatch_hosts | Function takes 9 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 206 | high | STRUCT-PARAMS | _process_done_futures | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 24 | medium | STRUCT-LENGTH | run | Function spans 43 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 72 | medium | STRUCT-LENGTH | _resolve_params | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 107 | medium | STRUCT-LENGTH | _log_invocation | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 144 | medium | STRUCT-LENGTH | _dispatch_hosts | Function spans 35 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 206 | medium | STRUCT-LENGTH | _process_done_futures | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ssh\command\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssh\command\command_runner.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 349 |
| Executable code lines | 134 |
| Functions | 17 |
| Classes | 4 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 88.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _write_output_blocks | 5 |
| __post_init__ | 4 |
| _execute_with_connection | 4 |
| _log_execute_return | 3 |
| _write_footer | 3 |

No violations found. This file complies with the guidelines.

## File: src\ssh\config\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssh\config\command_parser.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 82 |
| Executable code lines | 47 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 85.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _split_and_validate | 5 |
| parse | 4 |
| _warn_invalid_commands | 3 |
| _truncate_oversize | 2 |
| _enforce_command_cap | 2 |

No violations found. This file complies with the guidelines.

## File: src\ssh\config\csv_loader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 109 |
| Executable code lines | 67 |
| Functions | 7 |
| Classes | 1 |
| Average complexity | 3.1 |
| Max complexity | 5 |
| Inline comment coverage | 85.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _consume_csv_row | 5 |
| _resolve_csv_path | 4 |
| _warn_invalid_rows | 4 |
| _read_validated_commands | 3 |
| load | 2 |

No violations found. This file complies with the guidelines.

## File: src\ssh\config\env_loader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 186 |
| Executable code lines | 113 |
| Functions | 14 |
| Classes | 1 |
| Average complexity | 3.3 |
| Max complexity | 5 |
| Inline comment coverage | 83.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| load | 5 |
| _is_safe_env_path | 5 |
| _apply_env_line | 5 |
| _unquote_value | 5 |
| _dispatch_known_key | 5 |

No violations found. This file complies with the guidelines.

## File: src\ssh\config\host_parser.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 71 |
| Executable code lines | 45 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 4 |
| Inline comment coverage | 84.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| parse | 4 |
| _split_and_validate | 4 |
| _warn_invalid_hosts | 3 |
| _truncate_oversize | 2 |
| _enforce_host_cap | 2 |

No violations found. This file complies with the guidelines.

## File: src\ssh\config\validators.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 67 |
| Executable code lines | 43 |
| Functions | 3 |
| Classes | 0 |
| Average complexity | 5.0 |
| Max complexity | 5 |
| Inline comment coverage | 86.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| validate_hostname | 5 |
| validate_username | 5 |
| validate_command | 5 |

No violations found. This file complies with the guidelines.

## File: src\ssh\connection\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssh\connection\connector.py

- **Score**: 86.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 297 |
| Executable code lines | 167 |
| Functions | 19 |
| Classes | 1 |
| Average complexity | 2.5 |
| Max complexity | 7 |
| Inline comment coverage | 53.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _handle_connect_exception | 7 |
| connect | 5 |
| _validate_inputs | 5 |
| _ensure_managed_known_hosts_file | 4 |
| _paramiko_available | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 257 | low | STRUCT-COMPLEXITY | _handle_connect_exception | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 9 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 53.3%; uncommented lines: 9, 28, 39, 48, 61, 63, 66, 67, 71, 72, 74, 80. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 48 | medium | STRUCT-LENGTH | connect | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 228 | medium | STRUCT-LENGTH | _attempt_authenticated_connect | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 257 | medium | STRUCT-LENGTH | _handle_connect_exception | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 257 | low | STRUCT-BLOCKS | _handle_connect_exception | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\ssh\runtime\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 7 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssh\runtime\app_runner.py

- **Score**: 68.0 / 100
- **Grade**: D+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 321 |
| Executable code lines | 215 |
| Functions | 18 |
| Classes | 1 |
| Average complexity | 4.4 |
| Max complexity | 11 |
| Inline comment coverage | 51.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _execute_pipeline | 11 |
| _resolve_password | 7 |
| _check_required_params | 6 |
| _validate_commands | 6 |
| _validate_hosts | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 276 | high | STRUCT-COMPLEXITY | _execute_pipeline | Cyclomatic complexity is 11 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 135 | low | STRUCT-COMPLEXITY | _resolve_password | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 162 | low | STRUCT-COMPLEXITY | _check_required_params | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 210 | low | STRUCT-COMPLEXITY | _validate_commands | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 51.2%; uncommented lines: 8, 32, 37, 40, 45, 49, 54, 57, 59, 60, 63, 66. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 228 | high | STRUCT-PARAMS | _dispatch_execution | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 259 | high | STRUCT-PARAMS | _dispatch_multi_host | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 63 | medium | STRUCT-LENGTH | _install_line_tracer | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 228 | medium | STRUCT-LENGTH | _dispatch_execution | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 276 | medium | STRUCT-LENGTH | _execute_pipeline | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 276 | low | STRUCT-BLOCKS | _execute_pipeline | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\ssh\runtime\interactive_mode.py

- **Score**: 97.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 178 |
| Executable code lines | 115 |
| Functions | 9 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 87.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _prompt_port | 5 |
| _read_bounded_timeout | 5 |
| _prompt_hostname | 4 |
| _prompt_username | 4 |
| _prompt_command | 4 |

### Violations

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 151 | medium | STRUCT-LENGTH | run | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ssh\shell_execution\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssh\shell_execution\shell_executor.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 420 |
| Executable code lines | 238 |
| Functions | 21 |
| Classes | 1 |
| Average complexity | 3.5 |
| Max complexity | 8 |
| Inline comment coverage | 58.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _clean_output_lines | 8 |
| _collect_output | 7 |
| _drain_excess | 5 |
| _cleanup_shell | 5 |
| _line_is_artifact_or_prompt | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 189 | low | STRUCT-COMPLEXITY | _collect_output | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 340 | low | STRUCT-COMPLEXITY | _clean_output_lines | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 21 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 58.0%; uncommented lines: 21, 94, 103, 112, 115, 119, 129, 130, 132, 133, 134, 139. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 189 | medium | STRUCT-LENGTH | _collect_output | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 236 | medium | STRUCT-LENGTH | _read_one_chunk | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 189 | low | STRUCT-BLOCKS | _collect_output | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\ssh\ssh_runner.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 561 |
| Executable code lines | 253 |
| Functions | 40 |
| Classes | 3 |
| Average complexity | 1.9 |
| Max complexity | 5 |
| Inline comment coverage | 83.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _write_to_host_log | 5 |
| sanitize_filename | 4 |
| _execute_command | 4 |
| _validate_threads_arg | 3 |
| _validate_thread_count | 3 |

No violations found. This file complies with the guidelines.

## File: src\ssh\ssh_runner_manager.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 438 |
| Executable code lines | 244 |
| Functions | 22 |
| Classes | 3 |
| Average complexity | 4.0 |
| Max complexity | 8 |
| Inline comment coverage | 27.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _collect_missing_data | 8 |
| _run_interactive_workflow | 7 |
| _print_template_menu | 7 |
| by_gateway_template | 6 |
| _execute_ssh | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 61 | low | STRUCT-COMPLEXITY | _run_interactive_workflow | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 94 | low | STRUCT-COMPLEXITY | by_gateway_template | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 128 | low | STRUCT-COMPLEXITY | _collect_missing_data | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 206 | low | STRUCT-COMPLEXITY | _execute_ssh | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 308 | low | STRUCT-COMPLEXITY | _print_template_menu | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 345 | low | STRUCT-COMPLEXITY | _filter_gateways | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 391 | low | STRUCT-COMPLEXITY | _execute_by_template | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 27.5%; uncommented lines: 3, 5, 6, 7, 8, 9, 10, 20, 23, 24, 25, 26. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 94 | medium | STRUCT-LENGTH | by_gateway_template | Function spans 32 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 128 | medium | STRUCT-LENGTH | _collect_missing_data | Function spans 31 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 206 | medium | STRUCT-LENGTH | _execute_ssh | Function spans 54 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 391 | medium | STRUCT-LENGTH | _execute_by_template | Function spans 48 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ssid_consolidation\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ssid_consolidation\_ssid_template_cache.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 201 |
| Executable code lines | 110 |
| Functions | 12 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 86.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _check_prerequisite | 5 |
| _offer_resume | 5 |
| _load_phase_results | 4 |
| _load_cache | 3 |
| _log_cache_age | 3 |

No violations found. This file complies with the guidelines.

## File: src\ssid_consolidation\_ssid_template_cluster.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 73 |
| Executable code lines | 22 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 1.5 |
| Max complexity | 2 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| __getattr__ | 2 |
| _load_cache_or_bail | 2 |

No violations found. This file complies with the guidelines.

## File: src\ssid_consolidation\_ssid_template_phase1.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 776 |
| Executable code lines | 325 |
| Functions | 43 |
| Classes | 5 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 80.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _template_applies_to_site | 5 |
| _build_drift_candidates | 5 |
| _detect_cross_cluster_drift | 5 |
| _classify_ssid_count | 4 |
| _classify_matched | 4 |

No violations found. This file complies with the guidelines.

## File: src\ssid_consolidation\_ssid_template_phase2.py

- **Score**: 84.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 238 |
| Executable code lines | 110 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 5.2 |
| Max complexity | 10 |
| Inline comment coverage | 21.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _display_variable_summary | 10 |
| _write_site_variables | 9 |
| _compute_variable_plan | 7 |
| phase2_site_variables | 7 |
| _build_variable_entry | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 37 | low | STRUCT-COMPLEXITY | _compute_variable_plan | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 127 | low | STRUCT-COMPLEXITY | _display_variable_summary | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 177 | low | STRUCT-COMPLEXITY | phase2_site_variables | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 214 | low | STRUCT-COMPLEXITY | _write_site_variables | Cyclomatic complexity is 9 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 37 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 21.8%; uncommented lines: 37, 44, 47, 48, 49, 50, 52, 54, 55, 56, 57, 60. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 95 | medium | STRUCT-LENGTH | _build_variable_entry | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 177 | medium | STRUCT-LENGTH | phase2_site_variables | Function spans 36 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ssid_consolidation\_ssid_template_phase3.py

- **Score**: 86.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 274 |
| Executable code lines | 100 |
| Functions | 11 |
| Classes | 1 |
| Average complexity | 3.9 |
| Max complexity | 6 |
| Inline comment coverage | 25.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _assign_matrix_sites | 6 |
| _assign_sites_to_groups | 6 |
| _compute_group_plan | 5 |
| _display_group_plan | 5 |
| _get_existing_group_site_ids | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 93 | low | STRUCT-COMPLEXITY | _assign_matrix_sites | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 245 | low | STRUCT-COMPLEXITY | _assign_sites_to_groups | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 39 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 25.0%; uncommented lines: 39, 44, 46, 47, 48, 50, 51, 52, 55, 60, 61, 62. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 191 | medium | STRUCT-LENGTH | phase3_site_groups | Function spans 34 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 245 | medium | STRUCT-LENGTH | _assign_sites_to_groups | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ssid_consolidation\_ssid_template_phase45.py

- **Score**: 86.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 537 |
| Executable code lines | 249 |
| Functions | 27 |
| Classes | 3 |
| Average complexity | 3.3 |
| Max complexity | 7 |
| Inline comment coverage | 31.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _disable_ssids | 7 |
| _cluster_deviation_params | 6 |
| _first_clean_row | 5 |
| _skip_reason_for_row | 5 |
| phase5_disable_old | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 219 | low | STRUCT-COMPLEXITY | _cluster_deviation_params | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 506 | low | STRUCT-COMPLEXITY | _disable_ssids | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 81 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 31.3%; uncommented lines: 81, 100, 105, 106, 108, 109, 112, 120, 121, 122, 125, 132. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 140 | medium | STRUCT-LENGTH | _record_deviation_choice | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 435 | medium | STRUCT-LENGTH | _create_or_update_templates | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ssid_consolidation\ssid_template_consolidation.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 874 |
| Executable code lines | 261 |
| Functions | 30 |
| Classes | 2 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 97.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _handle_menu_choice | 5 |
| _dispatch_template_op | 4 |
| _apply_ssid_disable | 4 |
| _run_all_phases | 4 |
| _write_single_site_vars | 3 |

No violations found. This file complies with the guidelines.

## File: src\troubleshooting\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\troubleshooting\interactive_test_runner.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 336 |
| Executable code lines | 203 |
| Functions | 14 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 10 |
| Inline comment coverage | 72.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_test_site | 10 |
| _print_option_listings | 6 |
| _run_option_loop | 4 |
| _build_option_lists | 3 |
| _emit_skip_events | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 29 | low | STRUCT-COMPLEXITY | _resolve_test_site | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 123 | low | STRUCT-COMPLEXITY | _print_option_listings | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 72.4%; uncommented lines: 3, 5, 6, 7, 8, 9, 10, 11, 17, 20, 21, 22. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 29 | high | STRUCT-LENGTH | _resolve_test_site | Function spans 71 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 256 | high | STRUCT-PARAMS | _finalize_telemetry | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 278 | high | STRUCT-PARAMS | _print_summary | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 208 | medium | STRUCT-LENGTH | _run_single_option | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 278 | medium | STRUCT-LENGTH | _print_summary | Function spans 34 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\troubleshooting\marvis_troubleshoot_utils.py

- **Score**: 72.0 / 100
- **Grade**: C-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 508 |
| Executable code lines | 299 |
| Functions | 23 |
| Classes | 2 |
| Average complexity | 3.5 |
| Max complexity | 7 |
| Inline comment coverage | 45.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _display_response_summary | 7 |
| _process_insight_response | 7 |
| _display_org_features | 6 |
| _fetch_org_insights | 6 |
| device_performance | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 235 | low | STRUCT-COMPLEXITY | _display_response_summary | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 393 | low | STRUCT-COMPLEXITY | _display_org_features | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 410 | low | STRUCT-COMPLEXITY | _fetch_org_insights | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 441 | low | STRUCT-COMPLEXITY | _process_insight_response | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 45.2%; uncommented lines: 3, 12, 26, 46, 52, 59, 60, 80, 84, 88, 89, 92. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 52 | medium | STRUCT-LENGTH | client_connectivity | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 80 | medium | STRUCT-LENGTH | device_performance | Function spans 39 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 121 | medium | STRUCT-LENGTH | network_connectivity | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 203 | medium | STRUCT-LENGTH | _handle_network_response | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 410 | medium | STRUCT-LENGTH | _fetch_org_insights | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 441 | medium | STRUCT-LENGTH | _process_insight_response | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ui\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\ui\execution\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 8 |
| Executable code lines | 6 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5, 6, 7, 8. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\ui\execution\debug_saver.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 109 |
| Executable code lines | 62 |
| Functions | 10 |
| Classes | 2 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 88.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| to_jsonable | 5 |
| _object_to_dict | 5 |
| _redact_params | 4 |
| save | 2 |
| _is_primitive | 2 |

No violations found. This file complies with the guidelines.

## File: src\ui\execution\function_executor.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 220 |
| Executable code lines | 146 |
| Functions | 16 |
| Classes | 1 |
| Average complexity | 2.9 |
| Max complexity | 5 |
| Inline comment coverage | 80.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _process_signature_param | 5 |
| _paginate_if_possible | 5 |
| start | 4 |
| _collect_pages | 4 |
| _redact | 3 |

No violations found. This file complies with the guidelines.

## File: src\ui\execution\item_executor.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 206 |
| Executable code lines | 152 |
| Functions | 14 |
| Classes | 2 |
| Average complexity | 3.9 |
| Max complexity | 8 |
| Inline comment coverage | 48.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| execute | 8 |
| _collect_one_param | 7 |
| build | 7 |
| _collect_params_interactively | 4 |
| _invoke_and_display | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 28 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 90 | low | STRUCT-COMPLEXITY | _collect_one_param | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 162 | low | STRUCT-COMPLEXITY | build | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 48.0%; uncommented lines: 7, 9, 10, 11, 12, 13, 15, 21, 24, 28, 33, 37. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 28 | medium | STRUCT-LENGTH | execute | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ui\execution\output_formatter.py

- **Score**: 93.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 129 |
| Executable code lines | 87 |
| Functions | 9 |
| Classes | 2 |
| Average complexity | 3.3 |
| Max complexity | 6 |
| Inline comment coverage | 34.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _render_sequence | 6 |
| _render_sequence_item | 5 |
| format_result | 4 |
| _render | 4 |
| _render_dict | 3 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 78 | low | STRUCT-COMPLEXITY | _render_sequence | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 34.5%; uncommented lines: 7, 9, 10, 15, 18, 21, 22, 26, 29, 34, 35, 37. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\ui\execution\parameter_collector.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 71 |
| Executable code lines | 50 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 4 |
| Inline comment coverage | 98.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| submit | 4 |
| _capture_nonempty | 4 |
| _capture_empty | 3 |
| _capture_value | 2 |

No violations found. This file complies with the guidelines.

## File: src\ui\input_handlers\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 4 |
| Executable code lines | 2 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 4. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\ui\input_handlers\key_poller.py

- **Score**: 95.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 155 |
| Executable code lines | 91 |
| Functions | 11 |
| Classes | 3 |
| Average complexity | 3.4 |
| Max complexity | 10 |
| Inline comment coverage | 58.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_unix_csi | 10 |
| poll | 4 |
| _read_special_key | 4 |
| poll | 4 |
| _read_csi_payload | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 95 | low | STRUCT-COMPLEXITY | _parse_unix_csi | Cyclomatic complexity is 10 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 58.2%; uncommented lines: 7, 9, 10, 11, 12, 31, 41, 44, 48, 55, 62, 66. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 95 | low | STRUCT-BLOCKS | _parse_unix_csi | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\ui\input_handlers\keyboard_dispatch.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 228 |
| Executable code lines | 118 |
| Functions | 25 |
| Classes | 1 |
| Average complexity | 1.7 |
| Max complexity | 4 |
| Inline comment coverage | 88.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| dispatch | 4 |
| _dispatch_prompting | 4 |
| _nav_enter | 4 |
| _dispatch_with | 3 |
| _safe_results | 3 |

No violations found. This file complies with the guidelines.

## File: src\ui\layout\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 4 |
| Executable code lines | 2 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 4. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\ui\layout\layout_builder.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 380 |
| Executable code lines | 211 |
| Functions | 24 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 51.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _append_selection_details | 5 |
| _append_last_result | 4 |
| _collect_output_lines | 4 |
| _build_prompt_lines | 4 |
| _append_current_param_prompt | 4 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 51.2%; uncommented lines: 7, 9, 10, 11, 18, 21, 25, 38, 39, 48, 49, 50. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 25 | medium | STRUCT-LENGTH | build | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\ui\layout\results_grid_builder.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 227 |
| Executable code lines | 149 |
| Functions | 19 |
| Classes | 3 |
| Average complexity | 3.4 |
| Max complexity | 8 |
| Inline comment coverage | 42.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| format | 8 |
| _format_string | 7 |
| _format_list | 6 |
| _dispatch | 6 |
| _compose_row_info | 6 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 20 | low | STRUCT-COMPLEXITY | format | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 37 | low | STRUCT-COMPLEXITY | _format_string | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 46 | low | STRUCT-COMPLEXITY | _format_list | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 71 | low | STRUCT-COMPLEXITY | _dispatch | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 212 | low | STRUCT-COMPLEXITY | _compose_row_info | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 42.3%; uncommented lines: 7, 9, 10, 15, 20, 23, 25, 27, 29, 30, 31, 32. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 20 | low | STRUCT-BLOCKS | format | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\ui\runtime\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 5 |
| Executable code lines | 3 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\ui\runtime\dotenv_loader.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 58 |
| Executable code lines | 37 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 3.5 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| load | 5 |
| _strip_surrounding_quotes | 4 |
| _parse_line | 4 |

No violations found. This file complies with the guidelines.

## File: src\ui\runtime\level_discoverer.py

- **Score**: 93.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 118 |
| Executable code lines | 67 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 6 |
| Inline comment coverage | 44.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| discover | 6 |
| _classify_item | 5 |
| _append_module_record | 3 |
| _short_doc | 3 |
| _compose_module_path | 2 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 20 | low | STRUCT-COMPLEXITY | discover | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 44.8%; uncommented lines: 3, 5, 6, 7, 8, 13, 16, 20, 29, 32, 34, 36. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\ui\runtime\tui_runner.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 75 |
| Executable code lines | 48 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 4 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _render_loop | 4 |
| _teardown_terminal | 3 |
| run | 2 |
| _setup_terminal | 2 |

No violations found. This file complies with the guidelines.

## File: src\ui\tui.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 218 |
| Executable code lines | 132 |
| Functions | 17 |
| Classes | 1 |
| Average complexity | 1.5 |
| Max complexity | 4 |
| Inline comment coverage | 87.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _should_show_results_grid | 4 |
| _get_terminal_height | 3 |
| __init__ | 2 |
| _init_rich | 2 |
| _init_platform_io | 2 |

No violations found. This file complies with the guidelines.

## File: src\utils\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\utils\address_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1237 |
| Executable code lines | 541 |
| Functions | 68 |
| Classes | 6 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 81.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_address_parts | 5 |
| _detect_country | 5 |
| _single_valid_recommendation | 5 |
| _parse_components | 5 |
| _build_scourgify_result | 5 |

No violations found. This file complies with the guidelines.

## File: src\utils\input_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 87 |
| Executable code lines | 31 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 4 |
| Inline comment coverage | 83.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| safe_input | 4 |
| _handle_empty | 3 |

No violations found. This file complies with the guidelines.

## File: src\utils\logger_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 115 |
| Executable code lines | 22 |
| Functions | 3 |
| Classes | 1 |
| Average complexity | 2.0 |
| Max complexity | 3 |
| Inline comment coverage | 86.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| filter | 3 |
| redact_if_sensitive | 2 |

No violations found. This file complies with the guidelines.

## File: src\utils\rate_limiting.py

- **Score**: 75.0 / 100
- **Grade**: C

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 406 |
| Executable code lines | 214 |
| Functions | 18 |
| Classes | 1 |
| Average complexity | 3.8 |
| Max complexity | 8 |
| Inline comment coverage | 16.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _compute_smoothed_delay | 8 |
| _clean_error_values | 5 |
| _load_pid_tuning_data | 5 |
| _read_existing_entries | 5 |
| _needs_refresh | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 289 | low | STRUCT-COMPLEXITY | _compute_smoothed_delay | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 6 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 16.4%; uncommented lines: 6, 7, 8, 9, 10, 11, 14, 16, 17, 19, 22, 24. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 240 | high | STRUCT-PARAMS | _calculate_pid_delay | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 332 | high | STRUCT-LENGTH | get_rate_limited_delay | Function spans 75 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 170 | medium | STRUCT-LENGTH | _append_delay_metrics_log | Function spans 29 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 240 | medium | STRUCT-LENGTH | _calculate_pid_delay | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\wan_hub_group_manager.py

- **Score**: 88.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 429 |
| Executable code lines | 217 |
| Functions | 20 |
| Classes | 1 |
| Average complexity | 3.3 |
| Max complexity | 5 |
| Inline comment coverage | 0.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _report_no_hub_spoke | 5 |
| _format_pod_display | 5 |
| _prompt_profile_selection | 5 |
| run | 4 |
| _fetch_hub_spoke_vpns | 4 |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 13 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.9%; uncommented lines: 13, 15, 16, 17, 18, 20, 21, 22, 25, 28, 29, 30. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 238 | medium | STRUCT-LENGTH | _prompt_action | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 269 | medium | STRUCT-LENGTH | _prompt_set_pod | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\wan_vpn_builder.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 737 |
| Executable code lines | 406 |
| Functions | 45 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 99.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| run | 5 |
| _prompt_vpn_name | 5 |
| _prompt_profile_updates | 5 |
| _classify_interfaces | 4 |
| _collect_wan_suffixes | 4 |

No violations found. This file complies with the guidelines.

## File: src\websocket\__init__.py

- **Score**: 94.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 18 |
| Executable code lines | 7 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 0.0% |

### Violations

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5, 6, 7, 8, 10. | Add a same-line comment explaining intent on each executable line of changed code. |

## File: src\websocket\commands.py

- **Score**: 86.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 233 |
| Executable code lines | 151 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 4.8 |
| Max complexity | 8 |
| Inline comment coverage | 74.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| execute | 8 |
| _trigger_rpc | 7 |
| _render_extra_fields | 6 |
| _resolve_targets | 4 |
| _await_and_display | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 33 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 114 | low | STRUCT-COMPLEXITY | _trigger_rpc | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 222 | low | STRUCT-COMPLEXITY | _render_extra_fields | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | medium | CONV-COMMENTS | <file> | Inline-comment coverage is 74.8%; uncommented lines: 3, 23, 33, 37, 45, 53, 56, 57, 62, 67, 76, 81. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 33 | medium | STRUCT-LENGTH | execute | Function spans 41 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 114 | medium | STRUCT-LENGTH | _trigger_rpc | Function spans 48 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 33 | low | STRUCT-BLOCKS | execute | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |
| 114 | low | STRUCT-BLOCKS | _trigger_rpc | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\websocket\context.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 23 |
| Executable code lines | 11 |
| Functions | 0 |
| Classes | 1 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\websocket\diagnostics\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 11 |
| Executable code lines | 4 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\websocket\diagnostics\arp_executor.py

- **Score**: 80.0 / 100
- **Grade**: B-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 450 |
| Executable code lines | 287 |
| Functions | 20 |
| Classes | 1 |
| Average complexity | 4.0 |
| Max complexity | 8 |
| Inline comment coverage | 84.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _render_arp_result | 8 |
| _fetch_device_info | 7 |
| _run_workflow | 5 |
| _maybe_warn_and_confirm | 5 |
| _await_and_render | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 67 | low | STRUCT-COMPLEXITY | _fetch_device_info | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 252 | low | STRUCT-COMPLEXITY | _render_arp_result | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 67 | medium | STRUCT-LENGTH | _fetch_device_info | Function spans 33 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 150 | medium | STRUCT-LENGTH | _issue_arp_and_render | Function spans 27 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 178 | medium | STRUCT-LENGTH | _post_arp_command | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 207 | medium | STRUCT-LENGTH | _await_and_render | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 252 | medium | STRUCT-LENGTH | _render_arp_result | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 338 | medium | STRUCT-LENGTH | _render_gateway_arp_table | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\websocket\diagnostics\common.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 116 |
| Executable code lines | 58 |
| Functions | 6 |
| Classes | 0 |
| Average complexity | 2.8 |
| Max complexity | 4 |
| Inline comment coverage | 89.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| print_extra_result_fields | 4 |
| post_device_command | 3 |
| extract_command_session | 3 |
| _print_extra_field_values | 3 |
| detect_debug_mode | 2 |

No violations found. This file complies with the guidelines.

## File: src\websocket\diagnostics\ping_executor.py

- **Score**: 79.0 / 100
- **Grade**: C+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 230 |
| Executable code lines | 145 |
| Functions | 9 |
| Classes | 1 |
| Average complexity | 4.1 |
| Max complexity | 6 |
| Inline comment coverage | 85.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _render_ping_result | 6 |
| _run_workflow | 5 |
| _prompt_ping_count | 5 |
| _await_and_render | 5 |
| _prompt_target_host | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 210 | low | STRUCT-COMPLEXITY | _render_ping_result | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 116 | high | STRUCT-PARAMS | _issue_ping_and_render | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 145 | high | STRUCT-PARAMS | _post_ping_command | Function takes 7 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 116 | medium | STRUCT-LENGTH | _issue_ping_and_render | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 145 | medium | STRUCT-LENGTH | _post_ping_command | Function spans 35 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 181 | medium | STRUCT-LENGTH | _await_and_render | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\websocket\manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 344 |
| Executable code lines | 212 |
| Functions | 28 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 85.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| check_mist_credentials | 5 |
| cleanup_ws_connection | 4 |
| select_ws_site | 4 |
| __init__ | 4 |
| _await_handshake | 4 |

No violations found. This file complies with the guidelines.

## File: src\websocket\polling\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1 |
| Executable code lines | 0 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\websocket\polling\completion_detector.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 450 |
| Executable code lines | 242 |
| Functions | 31 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 5 |
| Inline comment coverage | 88.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _check_generic | 5 |
| _check_ping_statistics | 5 |
| _count_service_ping_patterns | 5 |
| _trace_service_ping | 5 |
| _collect_tail_messages | 5 |

No violations found. This file complies with the guidelines.

## File: src\websocket\polling\message_router.py

- **Score**: 90.0 / 100
- **Grade**: A-

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 199 |
| Executable code lines | 154 |
| Functions | 11 |
| Classes | 1 |
| Average complexity | 4.5 |
| Max complexity | 8 |
| Inline comment coverage | 13.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _unwrap_payload | 8 |
| _parse_string | 6 |
| _trace_packet | 6 |
| route | 5 |
| _parse | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 76 | low | STRUCT-COMPLEXITY | _parse_string | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 97 | low | STRUCT-COMPLEXITY | _trace_packet | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 147 | low | STRUCT-COMPLEXITY | _unwrap_payload | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 7 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 13.6%; uncommented lines: 7, 15, 18, 32, 38, 39, 42, 43, 44, 45, 46, 47. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 147 | low | STRUCT-BLOCKS | _unwrap_payload | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\websocket\polling\result_collector.py

- **Score**: 89.0 / 100
- **Grade**: B+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 323 |
| Executable code lines | 201 |
| Functions | 17 |
| Classes | 3 |
| Average complexity | 3.1 |
| Max complexity | 7 |
| Inline comment coverage | 30.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _maybe_emit_combined_trace | 7 |
| _try_completion | 6 |
| _poll_loop | 5 |
| check_iteration | 4 |
| collect | 4 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 128 | low | STRUCT-COMPLEXITY | _try_completion | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |
| 240 | low | STRUCT-COMPLEXITY | _maybe_emit_combined_trace | Cyclomatic complexity is 7 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 8 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 30.3%; uncommented lines: 8, 19, 21, 23, 25, 28, 31, 39, 43, 45, 48, 49. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 75 | medium | STRUCT-LENGTH | collect | Function spans 30 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

## File: src\websocket\polling\result_combiner.py

- **Score**: 83.0 / 100
- **Grade**: B

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 68 |
| Executable code lines | 46 |
| Functions | 2 |
| Classes | 0 |
| Average complexity | 6.5 |
| Max complexity | 8 |
| Inline comment coverage | 47.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _merge_segments | 8 |
| combine_segments | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 48 | low | STRUCT-COMPLEXITY | _merge_segments | Cyclomatic complexity is 8 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Conventions

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 3 | high | CONV-COMMENTS | <file> | Inline-comment coverage is 47.8%; uncommented lines: 3, 9, 12, 24, 26, 27, 28, 29, 30, 31, 36, 37. | Add a same-line comment explaining intent on each executable line of changed code. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 12 | high | STRUCT-PARAMS | combine_segments | Function takes 6 parameters (limit 5). | Group related parameters into a dataclass/config object or split the function. |
| 12 | medium | STRUCT-LENGTH | combine_segments | Function spans 34 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 48 | low | STRUCT-BLOCKS | _merge_segments | Function has 6 logical blocks (limit 5). | Split the function so each helper owns a single cohesive block of logic. |

## File: src\websocket\service_ping_discovery.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 805 |
| Executable code lines | 455 |
| Functions | 67 |
| Classes | 4 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 88.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _collect_from_routing_instances | 5 |
| _fetch_org_services | 4 |
| _sorted_non_system | 4 |
| _collect_from_service_policies | 4 |
| _add_service_reference | 4 |

No violations found. This file complies with the guidelines.

## File: src\websocket\service_ping_manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 466 |
| Executable code lines | 322 |
| Functions | 31 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 93.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _lookup_device_info | 5 |
| _handle_ping_response | 4 |
| _print_ping_output | 4 |
| _display_success_results | 4 |
| execute | 4 |

No violations found. This file complies with the guidelines.

## SpecKit Remediation Plan

> AI agent: convert each phase below into a SpecKit workflow. For a phase,
> run `speckit.specify` with the phase goal, then `speckit.plan`,
> `speckit.tasks`, and `speckit.implement`. Re-run this analyzer to verify
> every task is resolved before closing the phase.

> Note: showing the 300 highest-severity of 462 tasks.

### Phase: High (102 task(s))

- [ ] **CMP-001** `src\analytics\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 6.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\analytics\__init__.py`.
- [ ] **CMP-002** `src\analytics\site_inventory_health_analyzer.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 27.2%; uncommented lines: 3, 5, 6, 7, 8, 12, 15, 16, 17, 18, 19, 22.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-003** `src\api\tenant_fetch.py:9` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 22.3%; uncommented lines: 9, 11, 12, 13, 15, 16, 17, 18, 19, 20, 23, 32.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\api\tenant_fetch.py`.
- [ ] **CMP-004** `src\audit\analyzer.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 8, 9, 10, 12, 14, 34, 37, 38, 39, 40, 41, 42.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\audit\analyzer.py`.
- [ ] **CMP-005** `src\audit\time_parser.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 7, 8, 9, 11, 19, 27, 28, 32, 35, 36, 37, 38.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\audit\time_parser.py`.
- [ ] **CMP-006** `src\auth\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\auth\__init__.py`.
- [ ] **CMP-007** `src\bootstrap\dependency_check.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 19, 20, 21.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\bootstrap\dependency_check.py`.
- [ ] **CMP-008** `src\bootstrap\package_installer.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 5.1%; uncommented lines: 3, 5, 6, 7, 11, 14, 15, 16, 17, 19, 21, 22.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\bootstrap\package_installer.py`.
- [ ] **CMP-009** `src\capture\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\__init__.py`.
- [ ] **CMP-010** `src\capture\multi_ap_scan_workflow.py:175` - STRUCT-PARAMS (Structure)
  - Symbol: `_build_payload`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_build_payload` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-011** `src\capture\multi_ap_scan_workflow.py:217` - STRUCT-PARAMS (Structure)
  - Symbol: `_display_summary`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_display_summary` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-012** `src\capture\org_capture_workflow.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 10, 13, 15, 17, 18, 19, 20, 21, 22.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\org_capture_workflow.py`.
- [ ] **CMP-013** `src\capture\packet_capture_download.py:235` - STRUCT-LENGTH (Structure)
  - Symbol: `poll_for_pcap_url`
  - Problem: Function spans 70 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `poll_for_pcap_url` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-014** `src\capture\site_capture_loop.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 7, 8, 12, 15, 17, 19, 20, 21, 22.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\site_capture_loop.py`.
- [ ] **CMP-015** `src\db\__init__.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 1.7%; uncommented lines: 8, 10, 11, 12, 13, 15, 18, 20, 39, 42, 43, 44.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\db\__init__.py`.
- [ ] **CMP-016** `src\db\arango_writer.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 3.7%; uncommented lines: 8, 10, 11, 12, 13, 14, 15, 16, 18, 21, 23, 25.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\db\arango_writer.py`.
- [ ] **CMP-017** `src\db\retention.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 8, 10, 11, 12, 14, 16, 18, 19, 20, 23, 26, 32.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\db\retention.py`.
- [ ] **CMP-018** `src\db\router.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 7, 9, 10, 11, 13, 15, 16, 17, 19, 21, 22, 23.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\db\router.py`.
- [ ] **CMP-019** `src\export\device_events_52w_exporter.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 2.1%; uncommented lines: 3, 5, 6, 7, 8, 9, 17, 20, 21, 22, 23, 24.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\export\device_events_52w_exporter.py`.
- [ ] **CMP-020** `src\export\device_events_52w_exporter.py:192` - STRUCT-PARAMS (Structure)
  - Symbol: `_stream_remaining_pages`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_stream_remaining_pages` in `src\export\device_events_52w_exporter.py`.
- [ ] **CMP-021** `src\export\site_insights\device_metric_operation.py:170` - STRUCT-PARAMS (Structure)
  - Symbol: `_collect_metrics`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_collect_metrics` in `src\export\site_insights\device_metric_operation.py`.
- [ ] **CMP-022** `src\export\site_insights_exporter.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 17, 29.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\export\site_insights_exporter.py`.
- [ ] **CMP-023** `src\export\site_insights_exporter.py:17` - STRUCT-PARAMS (Structure)
  - Symbol: `configure_site_insights_exporter_dependencies`
  - Problem: Function takes 8 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `configure_site_insights_exporter_dependencies` in `src\export\site_insights_exporter.py`.
- [ ] **CMP-024** `src\gateway\device_template_cloner.py:91` - STRUCT-PARAMS (Structure)
  - Symbol: `__init__`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `__init__` in `src\gateway\device_template_cloner.py`.
- [ ] **CMP-025** `src\gateway\gateway_export_utils.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 23.1%; uncommented lines: 3, 5, 6, 7, 8, 10, 11, 16, 17, 18, 19, 20.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\gateway\gateway_export_utils.py`.
- [ ] **CMP-026** `src\gateway\gateway_export_utils.py:39` - STRUCT-PARAMS (Structure)
  - Symbol: `configure_gateway_export_utils_dependencies`
  - Problem: Function takes 21 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `configure_gateway_export_utils_dependencies` in `src\gateway\gateway_export_utils.py`.
- [ ] **CMP-027** `src\gateway\gateway_export_utils.py:39` - STRUCT-LENGTH (Structure)
  - Symbol: `configure_gateway_export_utils_dependencies`
  - Problem: Function spans 98 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `configure_gateway_export_utils_dependencies` in `src\gateway\gateway_export_utils.py`.
- [ ] **CMP-028** `src\gateway\gateway_export_utils.py:235` - STRUCT-LENGTH (Structure)
  - Symbol: `management_ips`
  - Problem: Function spans 68 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `management_ips` in `src\gateway\gateway_export_utils.py`.
- [ ] **CMP-029** `src\gateway\gateway_stats_exporter.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 20.0%; uncommented lines: 3, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\gateway\gateway_stats_exporter.py`.
- [ ] **CMP-030** `src\gateway\gateway_stats_exporter.py:29` - STRUCT-PARAMS (Structure)
  - Symbol: `configure_gateway_stats_exporter_dependencies`
  - Problem: Function takes 15 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `configure_gateway_stats_exporter_dependencies` in `src\gateway\gateway_stats_exporter.py`.
- [ ] **CMP-031** `src\gateway\overrides\_deps.py:19` - STRUCT-PARAMS (Structure)
  - Symbol: `configure_gateway_override_dependencies`
  - Problem: Function takes 9 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `configure_gateway_override_dependencies` in `src\gateway\overrides\_deps.py`.
- [ ] **CMP-032** `src\gateway\wan_probe_device_override_manager.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 25.9%; uncommented lines: 3, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\gateway\wan_probe_device_override_manager.py`.
- [ ] **CMP-033** `src\gateway\wan_probe_device_override_manager.py:25` - STRUCT-PARAMS (Structure)
  - Symbol: `configure_wan_probe_device_override_dependencies`
  - Problem: Function takes 10 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `configure_wan_probe_device_override_dependencies` in `src\gateway\wan_probe_device_override_manager.py`.
- [ ] **CMP-034** `src\inventory\org_device_inventory_summary.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 24.5%; uncommented lines: 3, 5, 6, 7, 8, 10, 12, 13, 14, 15, 18, 26.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\inventory\org_device_inventory_summary.py`.
- [ ] **CMP-035** `src\maps\_flask_viewer.py:12` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 2.6%; uncommented lines: 12, 14, 15, 19, 21, 24, 33, 35, 37, 38, 39, 40.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\_flask_viewer.py`.
- [ ] **CMP-036** `src\maps\_flask_viewer.py:24` - STRUCT-PARAMS (Structure)
  - Symbol: `_handle_map_data_request`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_handle_map_data_request` in `src\maps\_flask_viewer.py`.
- [ ] **CMP-037** `src\maps\_flask_viewer.py:47` - STRUCT-PARAMS (Structure)
  - Symbol: `_render_viewer_page`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_render_viewer_page` in `src\maps\_flask_viewer.py`.
- [ ] **CMP-038** `src\maps\_flask_viewer.py:176` - STRUCT-PARAMS (Structure)
  - Symbol: `launch_flask_viewer`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `launch_flask_viewer` in `src\maps\_flask_viewer.py`.
- [ ] **CMP-039** `src\maps\_flask_viewer.py:176` - STRUCT-LENGTH (Structure)
  - Symbol: `launch_flask_viewer`
  - Problem: Function spans 1067 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `launch_flask_viewer` in `src\maps\_flask_viewer.py`.
- [ ] **CMP-040** `src\maps\_maps_backup.py:15` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 1.6%; uncommented lines: 15, 17, 18, 22, 25, 28, 29, 31, 32, 34, 35, 37.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\_maps_backup.py`.
- [ ] **CMP-041** `src\maps\_maps_backup.py:170` - STRUCT-LENGTH (Structure)
  - Symbol: `_backup_map_geometry`
  - Problem: Function spans 90 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_backup_map_geometry` in `src\maps\_maps_backup.py`.
- [ ] **CMP-042** `src\maps\_maps_backup.py:262` - STRUCT-PARAMS (Structure)
  - Symbol: `backup_map_geometry`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `backup_map_geometry` in `src\maps\_maps_backup.py`.
- [ ] **CMP-043** `src\maps\_maps_backup.py:262` - ARCH-DELEGATE (Architecture)
  - Symbol: `backup_map_geometry`
  - Problem: Function only forwards its arguments to another call (pass-through wrapper).
  - Fix: Inline the call at its call sites or move the logic into the owning class method.
  - Done when: analyzer reports no ARCH-DELEGATE for `backup_map_geometry` in `src\maps\_maps_backup.py`.
- [ ] **CMP-044** `src\maps\_maps_clone.py:14` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 4.5%; uncommented lines: 14, 16, 17, 21, 24, 27, 28, 30, 31, 33, 34, 36.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\_maps_clone.py`.
- [ ] **CMP-045** `src\maps\_maps_matplotlib.py:16` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 1.9%; uncommented lines: 16, 18, 19, 23, 26, 29, 30, 32, 33, 35, 36, 38.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\_maps_matplotlib.py`.
- [ ] **CMP-046** `src\maps\_maps_matplotlib.py:136` - STRUCT-LENGTH (Structure)
  - Symbol: `launch_viewer_standalone`
  - Problem: Function spans 67 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `launch_viewer_standalone` in `src\maps\_maps_matplotlib.py`.
- [ ] **CMP-047** `src\maps\_maps_utils.py:10` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 10, 12, 13, 14, 15, 17, 22, 26, 29, 36, 37, 38.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\_maps_utils.py`.
- [ ] **CMP-048** `src\maps\plotly_heatmap_renderer.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 8, 11, 14, 16, 18, 26, 27, 28, 30.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\plotly_heatmap_renderer.py`.
- [ ] **CMP-049** `src\maps\plotly_heatmap_renderer.py:18` - STRUCT-LENGTH (Structure)
  - Symbol: `build_heatmap_trace`
  - Problem: Function spans 78 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `build_heatmap_trace` in `src\maps\plotly_heatmap_renderer.py`.
- [ ] **CMP-050** `src\maps\plotly_heatmap_renderer.py:110` - STRUCT-PARAMS (Structure)
  - Symbol: `_build_grid_data`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_build_grid_data` in `src\maps\plotly_heatmap_renderer.py`.
- [ ] **CMP-051** `src\maps\plotly_heatmap_renderer.py:144` - STRUCT-PARAMS (Structure)
  - Symbol: `_log_alignment`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_log_alignment` in `src\maps\plotly_heatmap_renderer.py`.
- [ ] **CMP-052** `src\maps\plotly_map_callback_manager.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 7, 27, 39, 42, 57, 65, 66, 67, 69, 70.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\plotly_map_callback_manager.py`.
- [ ] **CMP-053** `src\maps\plotly_map_callback_manager.py:42` - STRUCT-PARAMS (Structure)
  - Symbol: `apply_layer_toggles`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `apply_layer_toggles` in `src\maps\plotly_map_callback_manager.py`.
- [ ] **CMP-054** `src\maps\plotly_map_figure_builder.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5, 6, 8, 11, 14, 16, 18, 20, 21, 22, 24.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\plotly_map_figure_builder.py`.
- [ ] **CMP-055** `src\maps\plotly_map_figure_builder.py:94` - STRUCT-LENGTH (Structure)
  - Symbol: `add_zones`
  - Problem: Function spans 65 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `add_zones` in `src\maps\plotly_map_figure_builder.py`.
- [ ] **CMP-056** `src\maps\plotly_map_serializer.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 6, 10, 20, 31, 33, 34, 37, 39, 40, 43, 45.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\plotly_map_serializer.py`.
- [ ] **CMP-057** `src\maps\plotly_map_serializer.py:10` - STRUCT-PARAMS (Structure)
  - Symbol: `build_map_config`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `build_map_config` in `src\maps\plotly_map_serializer.py`.
- [ ] **CMP-058** `src\maps\plotly_map_templates.py:4` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 4, 11, 18, 19, 20, 22, 28, 149, 155, 177, 183, 189.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\plotly_map_templates.py`.
- [ ] **CMP-059** `src\maps\plotly_map_templates.py:22` - STRUCT-LENGTH (Structure)
  - Symbol: `get_custom_css`
  - Problem: Function spans 126 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `get_custom_css` in `src\maps\plotly_map_templates.py`.
- [ ] **CMP-060** `src\marvis\marvis_utils.py:58` - STRUCT-LENGTH (Structure)
  - Symbol: `format_for_csv`
  - Problem: Function spans 93 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `format_for_csv` in `src\marvis\marvis_utils.py`.
- [ ] **CMP-061** `src\org_data_collector.py:9` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 2.1%; uncommented lines: 9, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\org_data_collector.py`.
- [ ] **CMP-062** `src\refactors\serial_cc\security_events.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 47.5%; uncommented lines: 3, 4, 5, 6, 7, 8, 9, 10, 15, 17, 18, 34.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\refactors\serial_cc\security_events.py`.
- [ ] **CMP-063** `src\refactors\serial_cc\security_events.py:105` - STRUCT-PARAMS (Structure)
  - Symbol: `_export_flattened_dataset`
  - Problem: Function takes 8 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_export_flattened_dataset` in `src\refactors\serial_cc\security_events.py`.
- [ ] **CMP-064** `src\refactors\serial_cc\site_client_insights.py:135` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 64 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\refactors\serial_cc\site_client_insights.py`.
- [ ] **CMP-065** `src\refactors\serial_cc\start_site_client_capture_wireless.py:186` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 64 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\refactors\serial_cc\start_site_client_capture_wireless.py`.
- [ ] **CMP-066** `src\refactors\serial_cc\start_site_scan_capture.py:232` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 73 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\refactors\serial_cc\start_site_scan_capture.py`.
- [ ] **CMP-067** `src\ssh\batch\multi_host_runner.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 29.8%; uncommented lines: 8, 12, 17, 20, 42, 46, 52, 53, 54, 58, 86, 87.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-068** `src\ssh\batch\multi_host_runner.py:24` - STRUCT-PARAMS (Structure)
  - Symbol: `run`
  - Problem: Function takes 10 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `run` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-069** `src\ssh\batch\multi_host_runner.py:72` - STRUCT-PARAMS (Structure)
  - Symbol: `_resolve_params`
  - Problem: Function takes 10 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_resolve_params` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-070** `src\ssh\batch\multi_host_runner.py:107` - STRUCT-PARAMS (Structure)
  - Symbol: `_log_invocation`
  - Problem: Function takes 9 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_log_invocation` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-071** `src\ssh\batch\multi_host_runner.py:144` - STRUCT-PARAMS (Structure)
  - Symbol: `_dispatch_hosts`
  - Problem: Function takes 9 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_dispatch_hosts` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-072** `src\ssh\batch\multi_host_runner.py:206` - STRUCT-PARAMS (Structure)
  - Symbol: `_process_done_futures`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_process_done_futures` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-073** `src\ssh\runtime\app_runner.py:228` - STRUCT-PARAMS (Structure)
  - Symbol: `_dispatch_execution`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_dispatch_execution` in `src\ssh\runtime\app_runner.py`.
- [ ] **CMP-074** `src\ssh\runtime\app_runner.py:259` - STRUCT-PARAMS (Structure)
  - Symbol: `_dispatch_multi_host`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_dispatch_multi_host` in `src\ssh\runtime\app_runner.py`.
- [ ] **CMP-075** `src\ssh\runtime\app_runner.py:276` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_execute_pipeline`
  - Problem: Cyclomatic complexity is 11 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_execute_pipeline` in `src\ssh\runtime\app_runner.py`.
- [ ] **CMP-076** `src\ssh\ssh_runner_manager.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 27.5%; uncommented lines: 3, 5, 6, 7, 8, 9, 10, 20, 23, 24, 25, 26.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssh\ssh_runner_manager.py`.
- [ ] **CMP-077** `src\ssid_consolidation\_ssid_template_phase2.py:37` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 21.8%; uncommented lines: 37, 44, 47, 48, 49, 50, 52, 54, 55, 56, 57, 60.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssid_consolidation\_ssid_template_phase2.py`.
- [ ] **CMP-078** `src\ssid_consolidation\_ssid_template_phase3.py:39` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 25.0%; uncommented lines: 39, 44, 46, 47, 48, 50, 51, 52, 55, 60, 61, 62.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssid_consolidation\_ssid_template_phase3.py`.
- [ ] **CMP-079** `src\ssid_consolidation\_ssid_template_phase45.py:81` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 31.3%; uncommented lines: 81, 100, 105, 106, 108, 109, 112, 120, 121, 122, 125, 132.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssid_consolidation\_ssid_template_phase45.py`.
- [ ] **CMP-080** `src\troubleshooting\interactive_test_runner.py:29` - STRUCT-LENGTH (Structure)
  - Symbol: `_resolve_test_site`
  - Problem: Function spans 71 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_resolve_test_site` in `src\troubleshooting\interactive_test_runner.py`.
- [ ] **CMP-081** `src\troubleshooting\interactive_test_runner.py:256` - STRUCT-PARAMS (Structure)
  - Symbol: `_finalize_telemetry`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_finalize_telemetry` in `src\troubleshooting\interactive_test_runner.py`.
- [ ] **CMP-082** `src\troubleshooting\interactive_test_runner.py:278` - STRUCT-PARAMS (Structure)
  - Symbol: `_print_summary`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_print_summary` in `src\troubleshooting\interactive_test_runner.py`.
- [ ] **CMP-083** `src\troubleshooting\marvis_troubleshoot_utils.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 45.2%; uncommented lines: 3, 12, 26, 46, 52, 59, 60, 80, 84, 88, 89, 92.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\troubleshooting\marvis_troubleshoot_utils.py`.
- [ ] **CMP-084** `src\ui\execution\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5, 6, 7, 8.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\execution\__init__.py`.
- [ ] **CMP-085** `src\ui\execution\item_executor.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 48.0%; uncommented lines: 7, 9, 10, 11, 12, 13, 15, 21, 24, 28, 33, 37.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\execution\item_executor.py`.
- [ ] **CMP-086** `src\ui\execution\output_formatter.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 34.5%; uncommented lines: 7, 9, 10, 15, 18, 21, 22, 26, 29, 34, 35, 37.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\execution\output_formatter.py`.
- [ ] **CMP-087** `src\ui\input_handlers\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\input_handlers\__init__.py`.
- [ ] **CMP-088** `src\ui\layout\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\layout\__init__.py`.
- [ ] **CMP-089** `src\ui\layout\results_grid_builder.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 42.3%; uncommented lines: 7, 9, 10, 15, 20, 23, 25, 27, 29, 30, 31, 32.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\layout\results_grid_builder.py`.
- [ ] **CMP-090** `src\ui\runtime\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\runtime\__init__.py`.
- [ ] **CMP-091** `src\ui\runtime\level_discoverer.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 44.8%; uncommented lines: 3, 5, 6, 7, 8, 13, 16, 20, 29, 32, 34, 36.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\runtime\level_discoverer.py`.
- [ ] **CMP-092** `src\utils\rate_limiting.py:6` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 16.4%; uncommented lines: 6, 7, 8, 9, 10, 11, 14, 16, 17, 19, 22, 24.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\utils\rate_limiting.py`.
- [ ] **CMP-093** `src\utils\rate_limiting.py:240` - STRUCT-PARAMS (Structure)
  - Symbol: `_calculate_pid_delay`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_calculate_pid_delay` in `src\utils\rate_limiting.py`.
- [ ] **CMP-094** `src\utils\rate_limiting.py:332` - STRUCT-LENGTH (Structure)
  - Symbol: `get_rate_limited_delay`
  - Problem: Function spans 75 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `get_rate_limited_delay` in `src\utils\rate_limiting.py`.
- [ ] **CMP-095** `src\wan_hub_group_manager.py:13` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.9%; uncommented lines: 13, 15, 16, 17, 18, 20, 21, 22, 25, 28, 29, 30.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\wan_hub_group_manager.py`.
- [ ] **CMP-096** `src\websocket\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5, 6, 7, 8, 10.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\websocket\__init__.py`.
- [ ] **CMP-097** `src\websocket\diagnostics\ping_executor.py:116` - STRUCT-PARAMS (Structure)
  - Symbol: `_issue_ping_and_render`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_issue_ping_and_render` in `src\websocket\diagnostics\ping_executor.py`.
- [ ] **CMP-098** `src\websocket\diagnostics\ping_executor.py:145` - STRUCT-PARAMS (Structure)
  - Symbol: `_post_ping_command`
  - Problem: Function takes 7 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `_post_ping_command` in `src\websocket\diagnostics\ping_executor.py`.
- [ ] **CMP-099** `src\websocket\polling\message_router.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 13.6%; uncommented lines: 7, 15, 18, 32, 38, 39, 42, 43, 44, 45, 46, 47.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\websocket\polling\message_router.py`.
- [ ] **CMP-100** `src\websocket\polling\result_collector.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 30.3%; uncommented lines: 8, 19, 21, 23, 25, 28, 31, 39, 43, 45, 48, 49.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\websocket\polling\result_collector.py`.
- [ ] **CMP-101** `src\websocket\polling\result_combiner.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 47.8%; uncommented lines: 3, 9, 12, 24, 26, 27, 28, 29, 30, 31, 36, 37.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\websocket\polling\result_combiner.py`.
- [ ] **CMP-102** `src\websocket\polling\result_combiner.py:12` - STRUCT-PARAMS (Structure)
  - Symbol: `combine_segments`
  - Problem: Function takes 6 parameters (limit 5).
  - Fix: Group related parameters into a dataclass/config object or split the function.
  - Done when: analyzer reports no STRUCT-PARAMS for `combine_segments` in `src\websocket\polling\result_combiner.py`.

### Phase: Medium (172 task(s))

- [ ] **CMP-103** `src\analytics\site_inventory_health_analyzer.py:26` - STRUCT-LENGTH (Structure)
  - Symbol: `analyze`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `analyze` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-104** `src\analytics\site_inventory_health_analyzer.py:146` - STRUCT-LENGTH (Structure)
  - Symbol: `_find_sites_missing_infrastructure`
  - Problem: Function spans 39 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_find_sites_missing_infrastructure` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-105** `src\analytics\site_inventory_health_analyzer.py:199` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_offline_entry`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_offline_entry` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-106** `src\analytics\site_inventory_health_analyzer.py:283` - STRUCT-LENGTH (Structure)
  - Symbol: `_export_results`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_export_results` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-107** `src\audit\analyzer.py:92` - STRUCT-LENGTH (Structure)
  - Symbol: `analyze`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `analyze` in `src\audit\analyzer.py`.
- [ ] **CMP-108** `src\audit\analyzer.py:121` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_admin_timelines`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_admin_timelines` in `src\audit\analyzer.py`.
- [ ] **CMP-109** `src\audit\analyzer.py:150` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_object_changelogs`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_object_changelogs` in `src\audit\analyzer.py`.
- [ ] **CMP-110** `src\audit\analyzer.py:183` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_rollback_diffs`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_rollback_diffs` in `src\audit\analyzer.py`.
- [ ] **CMP-111** `src\audit\time_parser.py:56` - STRUCT-LENGTH (Structure)
  - Symbol: `parse`
  - Problem: Function spans 59 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `parse` in `src\audit\time_parser.py`.
- [ ] **CMP-112** `src\audit\time_parser.py:117` - STRUCT-LENGTH (Structure)
  - Symbol: `validate`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `validate` in `src\audit\time_parser.py`.
- [ ] **CMP-113** `src\bootstrap\package_installer.py:19` - STRUCT-LENGTH (Structure)
  - Symbol: `find_uv_executable`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `find_uv_executable` in `src\bootstrap\package_installer.py`.
- [ ] **CMP-114** `src\capture\multi_ap_scan_workflow.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 78.0%; uncommented lines: 3, 5, 6, 7, 11, 14, 15, 16, 17, 19, 50, 55.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-115** `src\capture\multi_ap_scan_workflow.py:19` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_band`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_band` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-116** `src\capture\multi_ap_scan_workflow.py:50` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_channel`
  - Problem: Function spans 35 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_channel` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-117** `src\capture\multi_ap_scan_workflow.py:86` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_bandwidth`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_bandwidth` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-118** `src\capture\multi_ap_scan_workflow.py:113` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_duration`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_duration` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-119** `src\capture\multi_ap_scan_workflow.py:144` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_num_packets`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_num_packets` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-120** `src\capture\multi_ap_scan_workflow.py:175` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_payload`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_payload` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-121** `src\capture\multi_ap_scan_workflow.py:217` - STRUCT-LENGTH (Structure)
  - Symbol: `_display_summary`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_display_summary` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-122** `src\capture\multi_ap_scan_workflow.py:266` - STRUCT-LENGTH (Structure)
  - Symbol: `_gather_capture_config`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_gather_capture_config` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-123** `src\capture\multi_ap_scan_workflow.py:357` - STRUCT-LENGTH (Structure)
  - Symbol: `_launch_capture`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_launch_capture` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-124** `src\capture\multi_ap_scan_workflow.py:388` - STRUCT-LENGTH (Structure)
  - Symbol: `run`
  - Problem: Function spans 42 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run` in `src\capture\multi_ap_scan_workflow.py`.
- [ ] **CMP-125** `src\capture\org_capture_workflow.py:15` - STRUCT-LENGTH (Structure)
  - Symbol: `run`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run` in `src\capture\org_capture_workflow.py`.
- [ ] **CMP-126** `src\capture\org_pcap_wait_download_workflow.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 52.2%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 20, 62.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\org_pcap_wait_download_workflow.py`.
- [ ] **CMP-127** `src\capture\org_pcap_wait_download_workflow.py:20` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\capture\org_pcap_wait_download_workflow.py`.
- [ ] **CMP-128** `src\capture\packet_capture_download.py:18` - STRUCT-LENGTH (Structure)
  - Symbol: `fetch_completed_pcaps`
  - Problem: Function spans 44 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `fetch_completed_pcaps` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-129** `src\capture\packet_capture_download.py:63` - STRUCT-LENGTH (Structure)
  - Symbol: `download_pending_pcaps`
  - Problem: Function spans 58 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `download_pending_pcaps` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-130** `src\capture\packet_capture_download.py:122` - STRUCT-LENGTH (Structure)
  - Symbol: `download_single_pcap`
  - Problem: Function spans 51 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `download_single_pcap` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-131** `src\capture\packet_capture_download.py:174` - STRUCT-LENGTH (Structure)
  - Symbol: `poll_and_download_pcap`
  - Problem: Function spans 60 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `poll_and_download_pcap` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-132** `src\capture\packet_capture_download.py:355` - STRUCT-LENGTH (Structure)
  - Symbol: `save_pcap_file`
  - Problem: Function spans 54 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `save_pcap_file` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-133** `src\capture\site_capture_loop.py:17` - STRUCT-LENGTH (Structure)
  - Symbol: `run`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run` in `src\capture\site_capture_loop.py`.
- [ ] **CMP-134** `src\capture\site_pcap_wait_download_workflow.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 52.2%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 20, 62.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\site_pcap_wait_download_workflow.py`.
- [ ] **CMP-135** `src\capture\site_pcap_wait_download_workflow.py:20` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\capture\site_pcap_wait_download_workflow.py`.
- [ ] **CMP-136** `src\db\arango_writer.py:3978` - STRUCT-LENGTH (Structure)
  - Symbol: `_batch_import`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_batch_import` in `src\db\arango_writer.py`.
- [ ] **CMP-137** `src\db\arango_writer.py:4084` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_edges`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_edges` in `src\db\arango_writer.py`.
- [ ] **CMP-138** `src\db\arango_writer.py:4241` - STRUCT-LENGTH (Structure)
  - Symbol: `snapshot`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `snapshot` in `src\db\arango_writer.py`.
- [ ] **CMP-139** `src\db\arango_writer.py:4308` - STRUCT-LENGTH (Structure)
  - Symbol: `_backfill_snapshot_edges`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_backfill_snapshot_edges` in `src\db\arango_writer.py`.
- [ ] **CMP-140** `src\db\retention.py:77` - STRUCT-LENGTH (Structure)
  - Symbol: `_purge_oldest_snapshots`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_purge_oldest_snapshots` in `src\db\retention.py`.
- [ ] **CMP-141** `src\db\router.py:115` - STRUCT-LENGTH (Structure)
  - Symbol: `_write_arango`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_write_arango` in `src\db\router.py`.
- [ ] **CMP-142** `src\db\router.py:147` - STRUCT-LENGTH (Structure)
  - Symbol: `_snapshot_if_config`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_snapshot_if_config` in `src\db\router.py`.
- [ ] **CMP-143** `src\db\router.py:300` - STRUCT-LENGTH (Structure)
  - Symbol: `pull_config_history`
  - Problem: Function spans 39 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `pull_config_history` in `src\db\router.py`.
- [ ] **CMP-144** `src\export\device_events_52w_exporter.py:29` - STRUCT-LENGTH (Structure)
  - Symbol: `export`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `export` in `src\export\device_events_52w_exporter.py`.
- [ ] **CMP-145** `src\export\site_insights\device_metric_operation.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 60.5%; uncommented lines: 3, 5, 10, 14, 23, 25, 31, 32, 33, 36, 37, 51.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\export\site_insights\device_metric_operation.py`.
- [ ] **CMP-146** `src\export\site_insights\device_metric_operation.py:14` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 54 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\export\site_insights\device_metric_operation.py`.
- [ ] **CMP-147** `src\export\site_insights\device_metric_operation.py:170` - STRUCT-LENGTH (Structure)
  - Symbol: `_collect_metrics`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_collect_metrics` in `src\export\site_insights\device_metric_operation.py`.
- [ ] **CMP-148** `src\export\site_insights\device_metric_operation.py:200` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_one_metric`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_one_metric` in `src\export\site_insights\device_metric_operation.py`.
- [ ] **CMP-149** `src\export\site_insights\device_metric_operation.py:229` - STRUCT-LENGTH (Structure)
  - Symbol: `_finalize`
  - Problem: Function spans 44 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_finalize` in `src\export\site_insights\device_metric_operation.py`.
- [ ] **CMP-150** `src\export\site_insights\site_metric_operation.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 64.5%; uncommented lines: 3, 5, 12, 16, 22, 23, 42, 54, 57, 59, 60, 63.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\export\site_insights\site_metric_operation.py`.
- [ ] **CMP-151** `src\export\site_insights\site_metric_operation.py:16` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\export\site_insights\site_metric_operation.py`.
- [ ] **CMP-152** `src\export\site_insights\site_metric_operation.py:132` - STRUCT-LENGTH (Structure)
  - Symbol: `_finalize`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_finalize` in `src\export\site_insights\site_metric_operation.py`.
- [ ] **CMP-153** `src\export\site_insights_exporter.py:17` - STRUCT-LENGTH (Structure)
  - Symbol: `configure_site_insights_exporter_dependencies`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `configure_site_insights_exporter_dependencies` in `src\export\site_insights_exporter.py`.
- [ ] **CMP-154** `src\export\wifi_clients_exporter.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 72.4%; uncommented lines: 3, 12, 15, 16, 17, 18, 19, 20, 21, 22, 24, 30.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\export\wifi_clients_exporter.py`.
- [ ] **CMP-155** `src\export\wifi_clients_exporter.py:24` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\export\wifi_clients_exporter.py`.
- [ ] **CMP-156** `src\export\wifi_clients_exporter.py:132` - STRUCT-LENGTH (Structure)
  - Symbol: `_merge_clients_and_sessions`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_merge_clients_and_sessions` in `src\export\wifi_clients_exporter.py`.
- [ ] **CMP-157** `src\export\wifi_clients_exporter.py:228` - STRUCT-LENGTH (Structure)
  - Symbol: `_finalize_export`
  - Problem: Function spans 40 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_finalize_export` in `src\export\wifi_clients_exporter.py`.
- [ ] **CMP-158** `src\gateway\device_template_cloner.py:276` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_template_payload`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_template_payload` in `src\gateway\device_template_cloner.py`.
- [ ] **CMP-159** `src\gateway\device_template_cloner.py:398` - STRUCT-LENGTH (Structure)
  - Symbol: `clone`
  - Problem: Function spans 42 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `clone` in `src\gateway\device_template_cloner.py`.
- [ ] **CMP-160** `src\gateway\gateway_export_utils.py:184` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_management_ip_rows`
  - Problem: Function spans 49 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_management_ip_rows` in `src\gateway\gateway_export_utils.py`.
- [ ] **CMP-161** `src\gateway\gateway_export_utils.py:390` - STRUCT-LENGTH (Structure)
  - Symbol: `_get_devices_from_cache`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_get_devices_from_cache` in `src\gateway\gateway_export_utils.py`.
- [ ] **CMP-162** `src\gateway\gateway_stats_exporter.py:29` - STRUCT-LENGTH (Structure)
  - Symbol: `configure_gateway_stats_exporter_dependencies`
  - Problem: Function spans 50 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `configure_gateway_stats_exporter_dependencies` in `src\gateway\gateway_stats_exporter.py`.
- [ ] **CMP-163** `src\gateway\gateway_stats_exporter.py:87` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_one_device_stats`
  - Problem: Function spans 58 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_one_device_stats` in `src\gateway\gateway_stats_exporter.py`.
- [ ] **CMP-164** `src\gateway\gateway_stats_exporter.py:147` - STRUCT-LENGTH (Structure)
  - Symbol: `_process_devices_concurrent`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_process_devices_concurrent` in `src\gateway\gateway_stats_exporter.py`.
- [ ] **CMP-165** `src\gateway\overrides\_deps.py:19` - STRUCT-LENGTH (Structure)
  - Symbol: `configure_gateway_override_dependencies`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `configure_gateway_override_dependencies` in `src\gateway\overrides\_deps.py`.
- [ ] **CMP-166** `src\gateway\wan_probe_device_override_manager.py:25` - STRUCT-LENGTH (Structure)
  - Symbol: `configure_wan_probe_device_override_dependencies`
  - Problem: Function spans 35 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `configure_wan_probe_device_override_dependencies` in `src\gateway\wan_probe_device_override_manager.py`.
- [ ] **CMP-167** `src\gateway\wan_probe_device_override_manager.py:111` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute` in `src\gateway\wan_probe_device_override_manager.py`.
- [ ] **CMP-168** `src\gateway\wan_probe_device_override_manager.py:188` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_template`
  - Problem: Function spans 55 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_template` in `src\gateway\wan_probe_device_override_manager.py`.
- [ ] **CMP-169** `src\inventory\org_device_inventory_summary.py:43` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_switch_physical_inventory`
  - Problem: Function spans 43 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_switch_physical_inventory` in `src\inventory\org_device_inventory_summary.py`.
- [ ] **CMP-170** `src\inventory\org_device_inventory_summary.py:254` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_all_counts`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_all_counts` in `src\inventory\org_device_inventory_summary.py`.
- [ ] **CMP-171** `src\inventory\org_device_inventory_summary.py:352` - STRUCT-LENGTH (Structure)
  - Symbol: `run_for_org`
  - Problem: Function spans 51 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run_for_org` in `src\inventory\org_device_inventory_summary.py`.
- [ ] **CMP-172** `src\maps\_maps_backup.py:37` - STRUCT-LENGTH (Structure)
  - Symbol: `_backup_download_image`
  - Problem: Function spans 37 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_backup_download_image` in `src\maps\_maps_backup.py`.
- [ ] **CMP-173** `src\maps\_maps_backup.py:89` - STRUCT-LENGTH (Structure)
  - Symbol: `_backup_fetch_device_placements`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_backup_fetch_device_placements` in `src\maps\_maps_backup.py`.
- [ ] **CMP-174** `src\maps\_maps_clone.py:127` - STRUCT-LENGTH (Structure)
  - Symbol: `_download_clone_image`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_download_clone_image` in `src\maps\_maps_clone.py`.
- [ ] **CMP-175** `src\maps\_maps_clone.py:267` - STRUCT-LENGTH (Structure)
  - Symbol: `clone_map`
  - Problem: Function spans 57 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `clone_map` in `src\maps\_maps_clone.py`.
- [ ] **CMP-176** `src\maps\_maps_matplotlib.py:38` - STRUCT-LENGTH (Structure)
  - Symbol: `_launch_matplotlib_viewer`
  - Problem: Function spans 60 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_launch_matplotlib_viewer` in `src\maps\_maps_matplotlib.py`.
- [ ] **CMP-177** `src\maps\_maps_utils.py:81` - STRUCT-LENGTH (Structure)
  - Symbol: `write_data_with_format_selection`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `write_data_with_format_selection` in `src\maps\_maps_utils.py`.
- [ ] **CMP-178** `src\maps\launcher\_viewer_clone.py:40` - STRUCT-LENGTH (Structure)
  - Symbol: `execute_clone_operation`
  - Problem: Function spans 38 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute_clone_operation` in `src\maps\launcher\_viewer_clone.py`.
- [ ] **CMP-179** `src\maps\launcher\_viewer_clone.py:40` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 59.8%; uncommented lines: 40, 54, 68, 71, 80, 89, 91, 99, 105, 119, 125, 127.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\maps\launcher\_viewer_clone.py`.
- [ ] **CMP-180** `src\maps\launcher\_viewer_clone.py:176` - STRUCT-LENGTH (Structure)
  - Symbol: `_download_source_image`
  - Problem: Function spans 35 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_download_source_image` in `src\maps\launcher\_viewer_clone.py`.
- [ ] **CMP-181** `src\maps\launcher\_viewer_clone.py:233` - STRUCT-LENGTH (Structure)
  - Symbol: `_upload_clone_image`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_upload_clone_image` in `src\maps\launcher\_viewer_clone.py`.
- [ ] **CMP-182** `src\maps\launcher\_viewer_clone.py:303` - STRUCT-LENGTH (Structure)
  - Symbol: `_render_clone_success`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_render_clone_success` in `src\maps\launcher\_viewer_clone.py`.
- [ ] **CMP-183** `src\maps\plotly_heatmap_renderer.py:144` - STRUCT-LENGTH (Structure)
  - Symbol: `_log_alignment`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_log_alignment` in `src\maps\plotly_heatmap_renderer.py`.
- [ ] **CMP-184** `src\maps\plotly_map_callback_manager.py:42` - STRUCT-LENGTH (Structure)
  - Symbol: `apply_layer_toggles`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `apply_layer_toggles` in `src\maps\plotly_map_callback_manager.py`.
- [ ] **CMP-185** `src\maps\plotly_map_figure_builder.py:18` - STRUCT-LENGTH (Structure)
  - Symbol: `add_walls`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `add_walls` in `src\maps\plotly_map_figure_builder.py`.
- [ ] **CMP-186** `src\maps\plotly_map_figure_builder.py:46` - STRUCT-LENGTH (Structure)
  - Symbol: `add_wayfinding`
  - Problem: Function spans 47 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `add_wayfinding` in `src\maps\plotly_map_figure_builder.py`.
- [ ] **CMP-187** `src\maps\plotly_map_figure_builder.py:178` - STRUCT-LENGTH (Structure)
  - Symbol: `_add_edge_segments`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_add_edge_segments` in `src\maps\plotly_map_figure_builder.py`.
- [ ] **CMP-188** `src\maps\plotly_map_templates.py:149` - STRUCT-LENGTH (Structure)
  - Symbol: `get_html_template`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `get_html_template` in `src\maps\plotly_map_templates.py`.
- [ ] **CMP-189** `src\marvis\marvis_utils.py:156` - STRUCT-LENGTH (Structure)
  - Symbol: `_expand_sites_rows`
  - Problem: Function spans 43 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_expand_sites_rows` in `src\marvis\marvis_utils.py`.
- [ ] **CMP-190** `src\marvis\marvis_utils.py:200` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_flat_row`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_flat_row` in `src\marvis\marvis_utils.py`.
- [ ] **CMP-191** `src\marvis\marvis_utils.py:237` - STRUCT-LENGTH (Structure)
  - Symbol: `_flatten_results_array`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_flatten_results_array` in `src\marvis\marvis_utils.py`.
- [ ] **CMP-192** `src\marvis\marvis_utils.py:265` - STRUCT-LENGTH (Structure)
  - Symbol: `_recover_via_flatten_pipeline`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_recover_via_flatten_pipeline` in `src\marvis\marvis_utils.py`.
- [ ] **CMP-193** `src\org_data_collector.py:1114` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\org_data_collector.py`.
- [ ] **CMP-194** `src\org_data_collector.py:1143` - STRUCT-LENGTH (Structure)
  - Symbol: `_collect_all`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_collect_all` in `src\org_data_collector.py`.
- [ ] **CMP-195** `src\org_data_collector.py:1174` - STRUCT-LENGTH (Structure)
  - Symbol: `_run_single`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_run_single` in `src\org_data_collector.py`.
- [ ] **CMP-196** `src\org_data_collector.py:1207` - STRUCT-LENGTH (Structure)
  - Symbol: `_print_summary`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_print_summary` in `src\org_data_collector.py`.
- [ ] **CMP-197** `src\refactors\serial_cc\import_initialization_service.py:71` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\refactors\serial_cc\import_initialization_service.py`.
- [ ] **CMP-198** `src\refactors\serial_cc\security_events.py:38` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 49 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\refactors\serial_cc\security_events.py`.
- [ ] **CMP-199** `src\refactors\serial_cc\security_events.py:105` - STRUCT-LENGTH (Structure)
  - Symbol: `_export_flattened_dataset`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_export_flattened_dataset` in `src\refactors\serial_cc\security_events.py`.
- [ ] **CMP-200** `src\refactors\serial_cc\security_events.py:137` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_site_rogue`
  - Problem: Function spans 34 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_site_rogue` in `src\refactors\serial_cc\security_events.py`.
- [ ] **CMP-201** `src\refactors\serial_cc\security_events.py:189` - STRUCT-LENGTH (Structure)
  - Symbol: `_export_rogue_data`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_export_rogue_data` in `src\refactors\serial_cc\security_events.py`.
- [ ] **CMP-202** `src\refactors\serial_cc\site_client_insights.py:81` - STRUCT-LENGTH (Structure)
  - Symbol: `_collect_client_metrics`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_collect_client_metrics` in `src\refactors\serial_cc\site_client_insights.py`.
- [ ] **CMP-203** `src\refactors\serial_cc\start_site_client_capture_wireless.py:89` - STRUCT-LENGTH (Structure)
  - Symbol: `_select_ap_filter`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_select_ap_filter` in `src\refactors\serial_cc\start_site_client_capture_wireless.py`.
- [ ] **CMP-204** `src\refactors\serial_cc\start_site_scan_capture.py:202` - STRUCT-LENGTH (Structure)
  - Symbol: `_check_existing_captures`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_check_existing_captures` in `src\refactors\serial_cc\start_site_scan_capture.py`.
- [ ] **CMP-205** `src\refactors\serial_cc\switch_vc_stats.py:49` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_vc_for_switch`
  - Problem: Function spans 40 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_vc_for_switch` in `src\refactors\serial_cc\switch_vc_stats.py`.
- [ ] **CMP-206** `src\refactors\serial_cc\switch_vc_stats.py:91` - STRUCT-LENGTH (Structure)
  - Symbol: `_collect_vc_stats`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_collect_vc_stats` in `src\refactors\serial_cc\switch_vc_stats.py`.
- [ ] **CMP-207** `src\refactors\serial_cc\switch_vc_stats.py:91` - STRUCT-NESTING (Structure)
  - Symbol: `_collect_vc_stats`
  - Problem: Maximum nesting depth is 5 (limit 4).
  - Fix: Flatten nesting with early returns, guard clauses, or extracted helper methods.
  - Done when: analyzer reports no STRUCT-NESTING for `_collect_vc_stats` in `src\refactors\serial_cc\switch_vc_stats.py`.
- [ ] **CMP-208** `src\refactors\serial_cc\switch_vc_stats.py:124` - STRUCT-LENGTH (Structure)
  - Symbol: `_emit_debug_preview`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_emit_debug_preview` in `src\refactors\serial_cc\switch_vc_stats.py`.
- [ ] **CMP-209** `src\site\address_audit\address_corrector.py:30` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 79.3%; uncommented lines: 30, 34, 37, 41, 51, 61, 73, 79, 82, 85, 93, 96.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\site\address_audit\address_corrector.py`.
- [ ] **CMP-210** `src\site\address_audit\address_resolver.py:88` - STRUCT-LENGTH (Structure)
  - Symbol: `_combine`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_combine` in `src\site\address_audit\address_resolver.py`.
- [ ] **CMP-211** `src\site\address_audit\address_resolver.py:161` - STRUCT-LENGTH (Structure)
  - Symbol: `_validate_nominatim`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_validate_nominatim` in `src\site\address_audit\address_resolver.py`.
- [ ] **CMP-212** `src\site\address_audit\address_resolver.py:426` - STRUCT-LENGTH (Structure)
  - Symbol: `_from_cache`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_from_cache` in `src\site\address_audit\address_resolver.py`.
- [ ] **CMP-213** `src\site\address_audit\business_authority_ingester.py:73` - STRUCT-LENGTH (Structure)
  - Symbol: `match`
  - Problem: Function spans 38 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `match` in `src\site\address_audit\business_authority_ingester.py`.
- [ ] **CMP-214** `src\site\address_audit\ui_geocoder.py:306` - STRUCT-LENGTH (Structure)
  - Symbol: `_read_fresh_suggestions`
  - Problem: Function spans 39 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_read_fresh_suggestions` in `src\site\address_audit\ui_geocoder.py`.
- [ ] **CMP-215** `src\site\address_audit\ui_geocoder.py:446` - STRUCT-LENGTH (Structure)
  - Symbol: `_preserve_query_suite`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_preserve_query_suite` in `src\site\address_audit\ui_geocoder.py`.
- [ ] **CMP-216** `src\site\address_audit\ui_geocoder.py:541` - STRUCT-LENGTH (Structure)
  - Symbol: `spawn_debuggable_browser`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `spawn_debuggable_browser` in `src\site\address_audit\ui_geocoder.py`.
- [ ] **CMP-217** `src\ssh\batch\multi_host_runner.py:24` - STRUCT-LENGTH (Structure)
  - Symbol: `run`
  - Problem: Function spans 43 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-218** `src\ssh\batch\multi_host_runner.py:72` - STRUCT-LENGTH (Structure)
  - Symbol: `_resolve_params`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_resolve_params` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-219** `src\ssh\batch\multi_host_runner.py:107` - STRUCT-LENGTH (Structure)
  - Symbol: `_log_invocation`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_log_invocation` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-220** `src\ssh\batch\multi_host_runner.py:144` - STRUCT-LENGTH (Structure)
  - Symbol: `_dispatch_hosts`
  - Problem: Function spans 35 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_dispatch_hosts` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-221** `src\ssh\batch\multi_host_runner.py:206` - STRUCT-LENGTH (Structure)
  - Symbol: `_process_done_futures`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_process_done_futures` in `src\ssh\batch\multi_host_runner.py`.
- [ ] **CMP-222** `src\ssh\connection\connector.py:9` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 53.3%; uncommented lines: 9, 28, 39, 48, 61, 63, 66, 67, 71, 72, 74, 80.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssh\connection\connector.py`.
- [ ] **CMP-223** `src\ssh\connection\connector.py:48` - STRUCT-LENGTH (Structure)
  - Symbol: `connect`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `connect` in `src\ssh\connection\connector.py`.
- [ ] **CMP-224** `src\ssh\connection\connector.py:228` - STRUCT-LENGTH (Structure)
  - Symbol: `_attempt_authenticated_connect`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_attempt_authenticated_connect` in `src\ssh\connection\connector.py`.
- [ ] **CMP-225** `src\ssh\connection\connector.py:257` - STRUCT-LENGTH (Structure)
  - Symbol: `_handle_connect_exception`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_handle_connect_exception` in `src\ssh\connection\connector.py`.
- [ ] **CMP-226** `src\ssh\runtime\app_runner.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 51.2%; uncommented lines: 8, 32, 37, 40, 45, 49, 54, 57, 59, 60, 63, 66.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssh\runtime\app_runner.py`.
- [ ] **CMP-227** `src\ssh\runtime\app_runner.py:63` - STRUCT-LENGTH (Structure)
  - Symbol: `_install_line_tracer`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_install_line_tracer` in `src\ssh\runtime\app_runner.py`.
- [ ] **CMP-228** `src\ssh\runtime\app_runner.py:228` - STRUCT-LENGTH (Structure)
  - Symbol: `_dispatch_execution`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_dispatch_execution` in `src\ssh\runtime\app_runner.py`.
- [ ] **CMP-229** `src\ssh\runtime\app_runner.py:276` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_pipeline`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_pipeline` in `src\ssh\runtime\app_runner.py`.
- [ ] **CMP-230** `src\ssh\runtime\interactive_mode.py:151` - STRUCT-LENGTH (Structure)
  - Symbol: `run`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run` in `src\ssh\runtime\interactive_mode.py`.
- [ ] **CMP-231** `src\ssh\shell_execution\shell_executor.py:21` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 58.0%; uncommented lines: 21, 94, 103, 112, 115, 119, 129, 130, 132, 133, 134, 139.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ssh\shell_execution\shell_executor.py`.
- [ ] **CMP-232** `src\ssh\shell_execution\shell_executor.py:189` - STRUCT-LENGTH (Structure)
  - Symbol: `_collect_output`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_collect_output` in `src\ssh\shell_execution\shell_executor.py`.
- [ ] **CMP-233** `src\ssh\shell_execution\shell_executor.py:236` - STRUCT-LENGTH (Structure)
  - Symbol: `_read_one_chunk`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_read_one_chunk` in `src\ssh\shell_execution\shell_executor.py`.
- [ ] **CMP-234** `src\ssh\ssh_runner_manager.py:94` - STRUCT-LENGTH (Structure)
  - Symbol: `by_gateway_template`
  - Problem: Function spans 32 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `by_gateway_template` in `src\ssh\ssh_runner_manager.py`.
- [ ] **CMP-235** `src\ssh\ssh_runner_manager.py:128` - STRUCT-LENGTH (Structure)
  - Symbol: `_collect_missing_data`
  - Problem: Function spans 31 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_collect_missing_data` in `src\ssh\ssh_runner_manager.py`.
- [ ] **CMP-236** `src\ssh\ssh_runner_manager.py:206` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_ssh`
  - Problem: Function spans 54 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_ssh` in `src\ssh\ssh_runner_manager.py`.
- [ ] **CMP-237** `src\ssh\ssh_runner_manager.py:391` - STRUCT-LENGTH (Structure)
  - Symbol: `_execute_by_template`
  - Problem: Function spans 48 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_execute_by_template` in `src\ssh\ssh_runner_manager.py`.
- [ ] **CMP-238** `src\ssid_consolidation\_ssid_template_phase2.py:95` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_variable_entry`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_variable_entry` in `src\ssid_consolidation\_ssid_template_phase2.py`.
- [ ] **CMP-239** `src\ssid_consolidation\_ssid_template_phase2.py:177` - STRUCT-LENGTH (Structure)
  - Symbol: `phase2_site_variables`
  - Problem: Function spans 36 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `phase2_site_variables` in `src\ssid_consolidation\_ssid_template_phase2.py`.
- [ ] **CMP-240** `src\ssid_consolidation\_ssid_template_phase3.py:191` - STRUCT-LENGTH (Structure)
  - Symbol: `phase3_site_groups`
  - Problem: Function spans 34 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `phase3_site_groups` in `src\ssid_consolidation\_ssid_template_phase3.py`.
- [ ] **CMP-241** `src\ssid_consolidation\_ssid_template_phase3.py:245` - STRUCT-LENGTH (Structure)
  - Symbol: `_assign_sites_to_groups`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_assign_sites_to_groups` in `src\ssid_consolidation\_ssid_template_phase3.py`.
- [ ] **CMP-242** `src\ssid_consolidation\_ssid_template_phase45.py:140` - STRUCT-LENGTH (Structure)
  - Symbol: `_record_deviation_choice`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_record_deviation_choice` in `src\ssid_consolidation\_ssid_template_phase45.py`.
- [ ] **CMP-243** `src\ssid_consolidation\_ssid_template_phase45.py:435` - STRUCT-LENGTH (Structure)
  - Symbol: `_create_or_update_templates`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_create_or_update_templates` in `src\ssid_consolidation\_ssid_template_phase45.py`.
- [ ] **CMP-244** `src\troubleshooting\interactive_test_runner.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 72.4%; uncommented lines: 3, 5, 6, 7, 8, 9, 10, 11, 17, 20, 21, 22.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\troubleshooting\interactive_test_runner.py`.
- [ ] **CMP-245** `src\troubleshooting\interactive_test_runner.py:208` - STRUCT-LENGTH (Structure)
  - Symbol: `_run_single_option`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_run_single_option` in `src\troubleshooting\interactive_test_runner.py`.
- [ ] **CMP-246** `src\troubleshooting\interactive_test_runner.py:278` - STRUCT-LENGTH (Structure)
  - Symbol: `_print_summary`
  - Problem: Function spans 34 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_print_summary` in `src\troubleshooting\interactive_test_runner.py`.
- [ ] **CMP-247** `src\troubleshooting\marvis_troubleshoot_utils.py:52` - STRUCT-LENGTH (Structure)
  - Symbol: `client_connectivity`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `client_connectivity` in `src\troubleshooting\marvis_troubleshoot_utils.py`.
- [ ] **CMP-248** `src\troubleshooting\marvis_troubleshoot_utils.py:80` - STRUCT-LENGTH (Structure)
  - Symbol: `device_performance`
  - Problem: Function spans 39 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `device_performance` in `src\troubleshooting\marvis_troubleshoot_utils.py`.
- [ ] **CMP-249** `src\troubleshooting\marvis_troubleshoot_utils.py:121` - STRUCT-LENGTH (Structure)
  - Symbol: `network_connectivity`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `network_connectivity` in `src\troubleshooting\marvis_troubleshoot_utils.py`.
- [ ] **CMP-250** `src\troubleshooting\marvis_troubleshoot_utils.py:203` - STRUCT-LENGTH (Structure)
  - Symbol: `_handle_network_response`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_handle_network_response` in `src\troubleshooting\marvis_troubleshoot_utils.py`.
- [ ] **CMP-251** `src\troubleshooting\marvis_troubleshoot_utils.py:410` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_org_insights`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_org_insights` in `src\troubleshooting\marvis_troubleshoot_utils.py`.
- [ ] **CMP-252** `src\troubleshooting\marvis_troubleshoot_utils.py:441` - STRUCT-LENGTH (Structure)
  - Symbol: `_process_insight_response`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_process_insight_response` in `src\troubleshooting\marvis_troubleshoot_utils.py`.
- [ ] **CMP-253** `src\ui\execution\item_executor.py:28` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\ui\execution\item_executor.py`.
- [ ] **CMP-254** `src\ui\input_handlers\key_poller.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 58.2%; uncommented lines: 7, 9, 10, 11, 12, 31, 41, 44, 48, 55, 62, 66.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\input_handlers\key_poller.py`.
- [ ] **CMP-255** `src\ui\layout\layout_builder.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 51.2%; uncommented lines: 7, 9, 10, 11, 18, 21, 25, 38, 39, 48, 49, 50.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\layout\layout_builder.py`.
- [ ] **CMP-256** `src\ui\layout\layout_builder.py:25` - STRUCT-LENGTH (Structure)
  - Symbol: `build`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `build` in `src\ui\layout\layout_builder.py`.
- [ ] **CMP-257** `src\utils\rate_limiting.py:170` - STRUCT-LENGTH (Structure)
  - Symbol: `_append_delay_metrics_log`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_append_delay_metrics_log` in `src\utils\rate_limiting.py`.
- [ ] **CMP-258** `src\utils\rate_limiting.py:240` - STRUCT-LENGTH (Structure)
  - Symbol: `_calculate_pid_delay`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_calculate_pid_delay` in `src\utils\rate_limiting.py`.
- [ ] **CMP-259** `src\wan_hub_group_manager.py:238` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_action`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_action` in `src\wan_hub_group_manager.py`.
- [ ] **CMP-260** `src\wan_hub_group_manager.py:269` - STRUCT-LENGTH (Structure)
  - Symbol: `_prompt_set_pod`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_prompt_set_pod` in `src\wan_hub_group_manager.py`.
- [ ] **CMP-261** `src\websocket\commands.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 74.8%; uncommented lines: 3, 23, 33, 37, 45, 53, 56, 57, 62, 67, 76, 81.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\websocket\commands.py`.
- [ ] **CMP-262** `src\websocket\commands.py:33` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\websocket\commands.py`.
- [ ] **CMP-263** `src\websocket\commands.py:114` - STRUCT-LENGTH (Structure)
  - Symbol: `_trigger_rpc`
  - Problem: Function spans 48 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_trigger_rpc` in `src\websocket\commands.py`.
- [ ] **CMP-264** `src\websocket\diagnostics\arp_executor.py:67` - STRUCT-LENGTH (Structure)
  - Symbol: `_fetch_device_info`
  - Problem: Function spans 33 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_fetch_device_info` in `src\websocket\diagnostics\arp_executor.py`.
- [ ] **CMP-265** `src\websocket\diagnostics\arp_executor.py:150` - STRUCT-LENGTH (Structure)
  - Symbol: `_issue_arp_and_render`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_issue_arp_and_render` in `src\websocket\diagnostics\arp_executor.py`.
- [ ] **CMP-266** `src\websocket\diagnostics\arp_executor.py:178` - STRUCT-LENGTH (Structure)
  - Symbol: `_post_arp_command`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_post_arp_command` in `src\websocket\diagnostics\arp_executor.py`.
- [ ] **CMP-267** `src\websocket\diagnostics\arp_executor.py:207` - STRUCT-LENGTH (Structure)
  - Symbol: `_await_and_render`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_await_and_render` in `src\websocket\diagnostics\arp_executor.py`.
- [ ] **CMP-268** `src\websocket\diagnostics\arp_executor.py:252` - STRUCT-LENGTH (Structure)
  - Symbol: `_render_arp_result`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_render_arp_result` in `src\websocket\diagnostics\arp_executor.py`.
- [ ] **CMP-269** `src\websocket\diagnostics\arp_executor.py:338` - STRUCT-LENGTH (Structure)
  - Symbol: `_render_gateway_arp_table`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_render_gateway_arp_table` in `src\websocket\diagnostics\arp_executor.py`.
- [ ] **CMP-270** `src\websocket\diagnostics\ping_executor.py:116` - STRUCT-LENGTH (Structure)
  - Symbol: `_issue_ping_and_render`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_issue_ping_and_render` in `src\websocket\diagnostics\ping_executor.py`.
- [ ] **CMP-271** `src\websocket\diagnostics\ping_executor.py:145` - STRUCT-LENGTH (Structure)
  - Symbol: `_post_ping_command`
  - Problem: Function spans 35 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_post_ping_command` in `src\websocket\diagnostics\ping_executor.py`.
- [ ] **CMP-272** `src\websocket\diagnostics\ping_executor.py:181` - STRUCT-LENGTH (Structure)
  - Symbol: `_await_and_render`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_await_and_render` in `src\websocket\diagnostics\ping_executor.py`.
- [ ] **CMP-273** `src\websocket\polling\result_collector.py:75` - STRUCT-LENGTH (Structure)
  - Symbol: `collect`
  - Problem: Function spans 30 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `collect` in `src\websocket\polling\result_collector.py`.
- [ ] **CMP-274** `src\websocket\polling\result_combiner.py:12` - STRUCT-LENGTH (Structure)
  - Symbol: `combine_segments`
  - Problem: Function spans 34 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `combine_segments` in `src\websocket\polling\result_combiner.py`.

### Phase: Low (26 task(s))

- [ ] **CMP-275** `src\analytics\site_inventory_health_analyzer.py:146` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_find_sites_missing_infrastructure`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_find_sites_missing_infrastructure` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-276** `src\analytics\site_inventory_health_analyzer.py:199` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_build_offline_entry`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_build_offline_entry` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-277** `src\analytics\site_inventory_health_analyzer.py:251` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_missing_section`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_missing_section` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-278** `src\analytics\site_inventory_health_analyzer.py:266` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_display_offline_section`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_display_offline_section` in `src\analytics\site_inventory_health_analyzer.py`.
- [ ] **CMP-279** `src\api\tenant_fetch.py:139` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_tenants_from_networks`
  - Problem: Cyclomatic complexity is 9 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_tenants_from_networks` in `src\api\tenant_fetch.py`.
- [ ] **CMP-280** `src\api\tenant_fetch.py:139` - STRUCT-BLOCKS (Structure)
  - Symbol: `_extract_tenants_from_networks`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_extract_tenants_from_networks` in `src\api\tenant_fetch.py`.
- [ ] **CMP-281** `src\api\tenant_fetch.py:162` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_tenants_from_policy_item`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_tenants_from_policy_item` in `src\api\tenant_fetch.py`.
- [ ] **CMP-282** `src\api\tenant_fetch.py:162` - STRUCT-BLOCKS (Structure)
  - Symbol: `_extract_tenants_from_policy_item`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_extract_tenants_from_policy_item` in `src\api\tenant_fetch.py`.
- [ ] **CMP-283** `src\api\tenant_fetch.py:197` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_router_tenants`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_router_tenants` in `src\api\tenant_fetch.py`.
- [ ] **CMP-284** `src\api\tenant_fetch.py:213` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_extract_network_tenants`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_extract_network_tenants` in `src\api\tenant_fetch.py`.
- [ ] **CMP-285** `src\audit\analyzer.py:121` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_build_admin_timelines`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_build_admin_timelines` in `src\audit\analyzer.py`.
- [ ] **CMP-286** `src\audit\analyzer.py:183` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_build_rollback_diffs`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_build_rollback_diffs` in `src\audit\analyzer.py`.
- [ ] **CMP-287** `src\audit\time_parser.py:56` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `parse`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `parse` in `src\audit\time_parser.py`.
- [ ] **CMP-288** `src\audit\time_parser.py:117` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `validate`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `validate` in `src\audit\time_parser.py`.
- [ ] **CMP-289** `src\audit\time_parser.py:117` - STRUCT-BLOCKS (Structure)
  - Symbol: `validate`
  - Problem: Function has 8 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `validate` in `src\audit\time_parser.py`.
- [ ] **CMP-290** `src\auth\interactive\msp_org_selector.py:118` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_orgs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_orgs` in `src\auth\interactive\msp_org_selector.py`.
- [ ] **CMP-291** `src\auth\interactive\msp_org_selector.py:192` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_interpret_choice`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_interpret_choice` in `src\auth\interactive\msp_org_selector.py`.
- [ ] **CMP-292** `src\bootstrap\dependency_check.py:60` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_classify_packages`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_classify_packages` in `src\bootstrap\dependency_check.py`.
- [ ] **CMP-293** `src\bootstrap\dependency_check.py:60` - STRUCT-BLOCKS (Structure)
  - Symbol: `_classify_packages`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_classify_packages` in `src\bootstrap\dependency_check.py`.
- [ ] **CMP-294** `src\bootstrap\dependency_check.py:103` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_install_missing_packages`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_install_missing_packages` in `src\bootstrap\dependency_check.py`.
- [ ] **CMP-295** `src\bootstrap\dependency_check.py:126` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_upgrade_outdated_packages`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_upgrade_outdated_packages` in `src\bootstrap\dependency_check.py`.
- [ ] **CMP-296** `src\bootstrap\package_installer.py:19` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `find_uv_executable`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `find_uv_executable` in `src\bootstrap\package_installer.py`.
- [ ] **CMP-297** `src\bootstrap\package_installer.py:19` - STRUCT-BLOCKS (Structure)
  - Symbol: `find_uv_executable`
  - Problem: Function has 8 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `find_uv_executable` in `src\bootstrap\package_installer.py`.
- [ ] **CMP-298** `src\capture\packet_capture_download.py:18` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `fetch_completed_pcaps`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `fetch_completed_pcaps` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-299** `src\capture\packet_capture_download.py:63` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `download_pending_pcaps`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `download_pending_pcaps` in `src\capture\packet_capture_download.py`.
- [ ] **CMP-300** `src\capture\packet_capture_download.py:174` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `poll_and_download_pcap`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `poll_and_download_pcap` in `src\capture\packet_capture_download.py`.

