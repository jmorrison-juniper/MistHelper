# Coding Guideline Compliance Report

- **Generated**: 2026-07-06 05:26:50 UTC
- **Tool**: compliance-analyzer (tools/compliance_analyzer)
- **Files analyzed**: 254

Files are graded against the project guidelines: the 5-Item Rule, no
wrappers/delegators/aliases/shims, complexity limits, inline comments,
safe input handling, and portable file paths. Use the SpecKit Remediation
Plan at the end to drive fixes.

## Summary

- **Overall score**: 99.5 / 100
- **Overall grade**: A+

| File | Score | Grade | Critical | High | Medium | Low | Total |
| - | - | - | - | - | - | - | - |
| MistHelper.py | 93.0 | A | 0 | 0 | 2 | 1 | 3 |
| src\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\analytics\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\analytics\site_analytics_configurator.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\analytics\site_inventory_health_analyzer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\analytics\zone_analyzer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\api\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\api\tenant_fetch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_delta.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_format.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_html.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_mermaid.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\_renderer_time.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\analyzer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\filter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\renderer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\audit\time_parser.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\auth\interactive\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\clouds.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\credential_prompter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\login_orchestrator.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\auth\interactive\msp_org_selector.py | 98.0 | A+ | 0 | 0 | 0 | 2 | 2 |
| src\bootstrap\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\bootstrap\dependency_check.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\bootstrap\package_installer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\bootstrap\uv_runtime.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\capture\_packet_capture_exec.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\_packet_capture_org.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\_packet_capture_prompts.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\_packet_capture_tcpdump.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\multi_ap_scan_workflow.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\org_capture_workflow.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\org_pcap_wait_download_workflow.py | 94.0 | A | 0 | 0 | 2 | 0 | 2 |
| src\capture\packet_capture.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\packet_capture_download.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\capture\site_capture_loop.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
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
| src\db\arango_writer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\db\redis_writer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\db\retention.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\db\router.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
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
| src\export\device_events_52w_exporter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\site_export_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\site_insights\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\site_insights\device_metric_operation.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\site_insights\site_metric_operation.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\site_insights_exporter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\export\wifi_clients_exporter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
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
| src\gateway\device_template_cloner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\gateway_export_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\gateway_stats_exporter.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\_deps.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\device_data_fetcher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\override_classifier.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\override_report_writer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\overrides\wan_override_walker.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\template_config.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\wan2_migration_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\wan2_variable.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\gateway\wan_probe_device_override_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\csv_comparator.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\inventory_summary\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\inventory_summary\pivot_renderer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\inventory_summary\version_per_model_fetcher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\org_device_inventory_msp.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\inventory\org_device_inventory_summary.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_container_detection.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_flask_viewer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_backup.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_clone.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_coverage.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_matplotlib.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_testing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_maps_wizard.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_plotly_viewer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\_viewer_launch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_clone.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_drawing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_refresh.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_site_switch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_ui.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\_viewer_url_switch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\viewer_callbacks.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\launcher\viewer_state.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\maps_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\plotly_heatmap_renderer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\plotly_map_callback_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\plotly_map_figure_builder.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\plotly_map_serializer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\maps\plotly_map_templates.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\marvis\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\marvis\marvis_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_display.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_forwarding.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_parsing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_payload.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_routing.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\_routing_utils_ssr.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\network\routing_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\org_data_collector.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\data_directory_checker.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\maps_manager_launcher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\global_assignments_builder.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\import_initialization_service.py | 95.0 | A | 0 | 0 | 1 | 2 | 3 |
| src\refactors\serial_cc\security_events.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\site_client_insights.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\sle_metrics.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\start_site_client_capture_wireless.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\start_site_scan_capture.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\switch_vc_stats.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\serial_cc\test_results_by_site.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\sqlite_database_writer.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\refactors\tui_launcher.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\reports\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\reports\e911_bssid.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\address_audit\address_corrector.py | 94.0 | A | 0 | 0 | 1 | 3 | 4 |
| src\site\address_audit\address_resolver.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
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
| src\site\address_audit\ui_geocoder.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\site\site_config_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\batch_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\host_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\interactive_batch_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\batch\multi_host_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\command\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\command\command_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\command_parser.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\csv_loader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\env_loader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\host_parser.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\config\validators.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\connection\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\connection\connector.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\runtime\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\runtime\app_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\runtime\interactive_mode.py | 97.0 | A+ | 0 | 0 | 1 | 0 | 1 |
| src\ssh\shell_execution\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\shell_execution\shell_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\ssh_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssh\ssh_runner_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_cache.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_cluster.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_phase1.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_phase2.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_phase3.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\_ssid_template_phase45.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ssid_consolidation\ssid_template_consolidation.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\troubleshooting\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\troubleshooting\interactive_test_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\troubleshooting\marvis_troubleshoot_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\execution\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\execution\debug_saver.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\execution\function_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\execution\item_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\execution\output_formatter.py | 93.0 | A | 0 | 1 | 0 | 1 | 2 |
| src\ui\execution\parameter_collector.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\input_handlers\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\input_handlers\key_poller.py | 95.0 | A | 0 | 0 | 1 | 2 | 3 |
| src\ui\input_handlers\keyboard_dispatch.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\layout\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\layout\layout_builder.py | 94.0 | A | 0 | 0 | 2 | 0 | 2 |
| src\ui\layout\results_grid_builder.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\runtime\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\ui\runtime\dotenv_loader.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\runtime\level_discoverer.py | 93.0 | A | 0 | 1 | 0 | 1 | 2 |
| src\ui\runtime\tui_runner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\ui\tui.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\address_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\input_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\logger_utils.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\utils\rate_limiting.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\wan_hub_group_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\wan_vpn_builder.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\__init__.py | 94.0 | A | 0 | 1 | 0 | 0 | 1 |
| src\websocket\commands.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\context.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\diagnostics\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\diagnostics\arp_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\diagnostics\common.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\diagnostics\ping_executor.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\__init__.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\completion_detector.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\message_router.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\result_collector.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\polling\result_combiner.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\service_ping_discovery.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |
| src\websocket\service_ping_manager.py | 100.0 | A+ | 0 | 0 | 0 | 0 | 0 |

## Machine-Readable Summary

```json
{
  "overall_score": 99.5,
  "overall_grade": "A+",
  "severity_totals": {
    "critical": 0,
    "high": 11,
    "medium": 13,
    "low": 14
  },
  "rule_totals": {
    "CONV-COMMENTS": 16,
    "STRUCT-BLOCKS": 1,
    "STRUCT-COMPLEXITY": 13,
    "STRUCT-LENGTH": 8
  },
  "files": [
    {
      "path": "MistHelper.py",
      "score": 93.0,
      "grade": "A",
      "violations": 3
    },
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\bootstrap\\package_installer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\org_capture_workflow.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\capture\\site_capture_loop.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\db\\redis_writer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\db\\retention.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\db\\router.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\export\\site_insights\\site_metric_operation.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\export\\site_insights_exporter.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\export\\wifi_clients_exporter.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\gateway_export_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\gateway_stats_exporter.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\overrides\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\gateway\\overrides\\_deps.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_backup.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_clone.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_coverage.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_matplotlib.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_testing.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\_maps_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\plotly_map_callback_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\plotly_map_figure_builder.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\plotly_map_serializer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\maps\\plotly_map_templates.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\marvis\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\marvis\\marvis_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\data_directory_checker.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\maps_manager_launcher.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\site_client_insights.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\sle_metrics.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\start_site_client_capture_wireless.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\start_site_scan_capture.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\switch_vc_stats.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\serial_cc\\test_results_by_site.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\sqlite_database_writer.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\refactors\\tui_launcher.py",
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\runtime\\__init__.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\runtime\\app_runner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\ssh_runner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssh\\ssh_runner_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_phase3.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\ssid_consolidation\\_ssid_template_phase45.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\troubleshooting\\marvis_troubleshoot_utils.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\wan_hub_group_manager.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\diagnostics\\common.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\diagnostics\\ping_executor.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\polling\\result_collector.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
    },
    {
      "path": "src\\websocket\\polling\\result_combiner.py",
      "score": 100.0,
      "grade": "A+",
      "violations": 0
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

## File: MistHelper.py

- **Score**: 93.0 / 100
- **Grade**: A

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 23864 |
| Executable code lines | 11003 |
| Functions | 1345 |
| Classes | 90 |
| Average complexity | 2.6 |
| Max complexity | 6 |
| Inline comment coverage | 80.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| execute | 6 |
| _parse_requirement_line | 5 |
| _parse_requirements_file | 5 |
| _msp_resolve_name | 5 |
| _msp_parse_one_privilege | 5 |

### Violations

#### Complexity

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 16239 | low | STRUCT-COMPLEXITY | execute | Cyclomatic complexity is 6 (target <= 5). | Reduce branching by extracting helpers, using guard clauses, or simplifying logic. |

#### Structure

| Line | Severity | Rule | Symbol | Issue | Remediation |
| - | - | - | - | - | - |
| 16285 | medium | STRUCT-LENGTH | _make_ws_callbacks | Function spans 28 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |
| 16523 | medium | STRUCT-LENGTH | _build_impl_args | Function spans 26 lines (limit 25). | Extract logical sections into well-named helper methods to shrink the function. |

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 397 |
| Executable code lines | 206 |
| Functions | 27 |
| Classes | 3 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 85.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _print_missing_totals | 5 |
| _collect_inventory | 4 |
| _print_device_summary | 4 |
| _group_devices_by_site | 4 |
| _build_offline_entry | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 328 |
| Executable code lines | 172 |
| Functions | 20 |
| Classes | 1 |
| Average complexity | 3.0 |
| Max complexity | 4 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| organization_tenants | 4 |
| site_tenants | 4 |
| _extract_tenants_from_templates | 4 |
| _fetch_org_policy_tenants | 4 |
| _fetch_site_policy_tenants | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 234 |
| Executable code lines | 104 |
| Functions | 11 |
| Classes | 6 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 87.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _accumulate_admin_entry | 5 |
| _diff_for_changelog | 5 |
| _build_object_changelogs | 3 |
| _accumulate_object_entry | 3 |
| _build_rollback_diffs | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 199 |
| Executable code lines | 100 |
| Functions | 12 |
| Classes | 2 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 85.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| to_api_kwargs | 5 |
| parse | 4 |
| validate | 4 |
| _describe_simple | 3 |
| _parse_range | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 251 |
| Executable code lines | 161 |
| Functions | 18 |
| Classes | 2 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 99.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| run | 5 |
| _check_installed | 5 |
| _classify_one | 3 |
| _bootstrap_uv_via_pip | 3 |
| _install_missing_packages | 3 |

No violations found. This file complies with the guidelines.

## File: src\bootstrap\package_installer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 158 |
| Executable code lines | 91 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 4 |
| Inline comment coverage | 92.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _probe_uv_command | 4 |
| find_uv_executable | 3 |
| _uv_candidate_commands | 3 |
| _candidate_is_runnable | 3 |
| _run_install | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 387 |
| Executable code lines | 232 |
| Functions | 21 |
| Classes | 3 |
| Average complexity | 2.1 |
| Max complexity | 5 |
| Inline comment coverage | 98.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _check_existing_captures | 5 |
| _handle_launch_error | 5 |
| _parse_bounded_int | 4 |
| _gather_capture_config | 4 |
| _print_bandwidth_menu | 3 |

No violations found. This file complies with the guidelines.

## File: src\capture\org_capture_workflow.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 74 |
| Executable code lines | 42 |
| Functions | 4 |
| Classes | 1 |
| Average complexity | 2.5 |
| Max complexity | 4 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _collect_org_selection | 4 |
| run | 3 |
| _collect_capture_config | 2 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 556 |
| Executable code lines | 268 |
| Functions | 36 |
| Classes | 3 |
| Average complexity | 2.0 |
| Max complexity | 4 |
| Inline comment coverage | 85.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| parse_captures_response | 4 |
| find_capture_url | 4 |
| fetch_completed_pcaps | 3 |
| _select_completed_captures | 3 |
| download_pending_pcaps | 3 |

No violations found. This file complies with the guidelines.

## File: src\capture\site_capture_loop.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 83 |
| Executable code lines | 50 |
| Functions | 4 |
| Classes | 2 |
| Average complexity | 2.0 |
| Max complexity | 3 |
| Inline comment coverage | 98.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| run | 3 |
| _run_one_iteration | 2 |
| _attempt_capture | 2 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 4429 |
| Executable code lines | 323 |
| Functions | 45 |
| Classes | 1 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 90.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _as_nonempty_list | 5 |
| _build_key_lookup | 5 |
| _refresh_graph_if_stale | 4 |
| write | 4 |
| _populate_graph | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 182 |
| Executable code lines | 98 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 2.1 |
| Max complexity | 3 |
| Inline comment coverage | 84.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _get_storage_usage_gb | 3 |
| check_redis_retention | 3 |
| _sweep_loop | 3 |
| _execute_purge | 2 |
| check_arango_retention | 2 |

No violations found. This file complies with the guidelines.

## File: src\db\router.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 382 |
| Executable code lines | 192 |
| Functions | 23 |
| Classes | 2 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 84.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _write_arango | 5 |
| write | 4 |
| _snapshot_if_config | 4 |
| _write_redis | 4 |
| _write_redis_json | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 337 |
| Executable code lines | 198 |
| Functions | 22 |
| Classes | 2 |
| Average complexity | 2.3 |
| Max complexity | 4 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _read_checkpoint | 4 |
| _normalize_page | 4 |
| _preload_rows | 4 |
| _fetch_with_retries | 4 |
| _first_present | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 297 |
| Executable code lines | 144 |
| Functions | 18 |
| Classes | 2 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 82.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_device_info | 5 |
| _resolve_site_name | 4 |
| execute | 3 |
| _prompt_site_and_device | 3 |
| _validate_mac | 3 |

No violations found. This file complies with the guidelines.

## File: src\export\site_insights\site_metric_operation.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 210 |
| Executable code lines | 106 |
| Functions | 15 |
| Classes | 2 |
| Average complexity | 2.0 |
| Max complexity | 4 |
| Inline comment coverage | 84.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_site_name | 4 |
| _collect_metrics | 3 |
| _fetch_one_metric | 3 |
| _finalize | 3 |
| execute | 2 |

No violations found. This file complies with the guidelines.

## File: src\export\site_insights_exporter.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 99 |
| Executable code lines | 67 |
| Functions | 5 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 94.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _classify_device_platform | 5 |
| _allowed_platforms_for_metric | 4 |
| _metric_compatible_with_platform | 3 |
| _normalize_device_mac_or_none | 3 |

No violations found. This file complies with the guidelines.

## File: src\export\wifi_clients_exporter.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 325 |
| Executable code lines | 197 |
| Functions | 23 |
| Classes | 2 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 82.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_clients_and_sessions | 5 |
| _merge_session_only_pass | 5 |
| _attach_latest_session | 5 |
| _index_sessions_by_mac | 4 |
| execute | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 485 |
| Executable code lines | 221 |
| Functions | 27 |
| Classes | 2 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 86.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _prompt_template_name | 5 |
| _list_gateways | 4 |
| _fetch_existing_template_names | 4 |
| _resolve_hardware_choice | 4 |
| _strip_device_metadata | 4 |

No violations found. This file complies with the guidelines.

## File: src\gateway\gateway_export_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 553 |
| Executable code lines | 266 |
| Functions | 37 |
| Classes | 1 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 83.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _load_gateways_from_inventory_csv | 5 |
| _project_api_gateway_devices | 5 |
| _get_site_ids_with_devices | 5 |
| _build_management_ip_lookups | 4 |
| _classify_connected_status | 3 |

No violations found. This file complies with the guidelines.

## File: src\gateway\gateway_stats_exporter.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 467 |
| Executable code lines | 243 |
| Functions | 29 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 82.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| device_stats | 5 |
| _build_conflict_records | 5 |
| _fetch_one_device_stats | 4 |
| _collect_concurrent_results | 4 |
| _log_export_summary | 4 |

No violations found. This file complies with the guidelines.

## File: src\gateway\overrides\__init__.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 21 |
| Executable code lines | 7 |
| Functions | 0 |
| Classes | 0 |
| Average complexity | 0.0 |
| Max complexity | 0 |
| Inline comment coverage | 100.0% |

No violations found. This file complies with the guidelines.

## File: src\gateway\overrides\_deps.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 51 |
| Executable code lines | 38 |
| Functions | 1 |
| Classes | 1 |
| Average complexity | 1.0 |
| Max complexity | 1 |
| Inline comment coverage | 94.7% |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 681 |
| Executable code lines | 410 |
| Functions | 44 |
| Classes | 2 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 84.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _find_template_sites | 5 |
| _scan_single_site | 5 |
| _extract_overridden_wan_ports | 5 |
| _show_preview | 5 |
| _print_apply_summary | 5 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 453 |
| Executable code lines | 251 |
| Functions | 28 |
| Classes | 1 |
| Average complexity | 2.9 |
| Max complexity | 5 |
| Inline comment coverage | 98.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _search_switch_page | 5 |
| _fetch_switch_physical_inventory | 5 |
| _aggregate_switch_counts | 5 |
| _ap_inventory_bucket | 5 |
| _merge_counts | 5 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 1332 |
| Executable code lines | 175 |
| Functions | 22 |
| Classes | 3 |
| Average complexity | 1.8 |
| Max complexity | 4 |
| Inline comment coverage | 86.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _handle_site_maps_request | 4 |
| _fetch_map_image_bytes | 4 |
| _handle_map_image_request | 4 |
| _handle_map_data_request | 3 |
| _run_flask_server | 3 |

No violations found. This file complies with the guidelines.

## File: src\maps\_maps_backup.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 354 |
| Executable code lines | 171 |
| Functions | 26 |
| Classes | 1 |
| Average complexity | 2.5 |
| Max complexity | 4 |
| Inline comment coverage | 81.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _safe_name | 4 |
| _download_image | 4 |
| _response_items | 4 |
| _fetch_items | 4 |
| _fetch_device_placements | 4 |

No violations found. This file complies with the guidelines.

## File: src\maps\_maps_clone.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 435 |
| Executable code lines | 272 |
| Functions | 25 |
| Classes | 3 |
| Average complexity | 3.1 |
| Max complexity | 5 |
| Inline comment coverage | 83.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _fetch_source_zone_count | 5 |
| _clone_single_zone | 5 |
| _clone_zones | 5 |
| _print_clone_summary | 5 |
| _print_source_map_details | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 429 |
| Executable code lines | 210 |
| Functions | 31 |
| Classes | 5 |
| Average complexity | 2.0 |
| Max complexity | 4 |
| Inline comment coverage | 81.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _entries_for_map | 4 |
| _resolve_initial_site | 4 |
| _fetch_site_maps | 4 |
| _plot_devices | 3 |
| _device_to_marker | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 153 |
| Executable code lines | 76 |
| Functions | 6 |
| Classes | 0 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 90.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| flatten_dict_recursively | 5 |
| _flatten_list_value | 4 |
| sanitize_filename | 4 |
| write_data_with_format_selection | 3 |
| _write_csv_rows | 2 |

No violations found. This file complies with the guidelines.

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
| Lines of code | 1532 |
| Executable code lines | 278 |
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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 411 |
| Executable code lines | 205 |
| Functions | 27 |
| Classes | 1 |
| Average complexity | 2.6 |
| Max complexity | 5 |
| Inline comment coverage | 93.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _validate_clone_inputs | 5 |
| execute_clone_operation | 4 |
| _download_source_image | 4 |
| _clone_zones_for_map | 4 |
| _fetch_source_zones | 4 |

No violations found. This file complies with the guidelines.

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
| Lines of code | 387 |
| Executable code lines | 98 |
| Functions | 24 |
| Classes | 1 |
| Average complexity | 1.0 |
| Max complexity | 1 |
| Inline comment coverage | 84.7% |

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
| Lines of code | 2794 |
| Executable code lines | 1595 |
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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 261 |
| Executable code lines | 127 |
| Functions | 14 |
| Classes | 4 |
| Average complexity | 2.4 |
| Max complexity | 4 |
| Inline comment coverage | 96.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| build_heatmap_trace | 4 |
| _rssi_bounds | 4 |
| _extract_results | 3 |
| _assemble_trace | 3 |
| _resolve_indices | 3 |

No violations found. This file complies with the guidelines.

## File: src\maps\plotly_map_callback_manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 223 |
| Executable code lines | 102 |
| Functions | 16 |
| Classes | 2 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 81.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_trace_visibility | 5 |
| _build_hover_paragraphs | 4 |
| build_click_details | 4 |
| _resolve_by_rules | 3 |
| _resolve_annotation_visibility | 3 |

No violations found. This file complies with the guidelines.

## File: src\maps\plotly_map_figure_builder.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 327 |
| Executable code lines | 127 |
| Functions | 17 |
| Classes | 2 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 85.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _add_node_edges | 5 |
| add_zones | 3 |
| _extract_nodes | 3 |
| _register_node | 3 |
| _closed_polygon_xy | 3 |

No violations found. This file complies with the guidelines.

## File: src\maps\plotly_map_serializer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 106 |
| Executable code lines | 46 |
| Functions | 7 |
| Classes | 2 |
| Average complexity | 1.7 |
| Max complexity | 3 |
| Inline comment coverage | 82.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| build_named_items | 3 |
| build_dropdown_options | 3 |
| increment_cache_bust | 2 |

No violations found. This file complies with the guidelines.

## File: src\maps\plotly_map_templates.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 263 |
| Executable code lines | 60 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 1.9 |
| Max complexity | 3 |
| Inline comment coverage | 98.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _rule_html_style | 3 |
| _rule_meta_shape | 3 |
| _rule_css_length | 2 |
| _rule_html_entry | 2 |
| validate_template | 2 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 313 |
| Executable code lines | 101 |
| Functions | 16 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 98.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_site_row | 5 |
| _store_typed_value | 4 |
| _collect_rows | 3 |
| _dispatch_item | 3 |
| _is_sites_expansion | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 629 |
| Executable code lines | 213 |
| Functions | 10 |
| Classes | 3 |
| Average complexity | 1.7 |
| Max complexity | 3 |
| Inline comment coverage | 90.6% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _build_export_kwargs | 3 |
| _confirm_run | 2 |
| _collect_all | 2 |
| _maybe_print_category | 2 |
| _run_single | 2 |

No violations found. This file complies with the guidelines.

## File: src\refactors\data_directory_checker.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 128 |
| Executable code lines | 63 |
| Functions | 9 |
| Classes | 1 |
| Average complexity | 1.4 |
| Max complexity | 3 |
| Inline comment coverage | 98.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| check | 3 |
| _handle_permission_error | 2 |
| _is_running_in_container | 2 |

No violations found. This file complies with the guidelines.

## File: src\refactors\maps_manager_launcher.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 116 |
| Executable code lines | 66 |
| Functions | 10 |
| Classes | 1 |
| Average complexity | 1.6 |
| Max complexity | 3 |
| Inline comment coverage | 83.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| launch | 3 |
| _run_interactive_menu | 3 |
| _import_module | 2 |
| _get_org_id | 2 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 282 |
| Executable code lines | 147 |
| Functions | 12 |
| Classes | 3 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 81.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _all_outputs_fresh | 5 |
| _run_export_workflow | 4 |
| _iterate_site_rogue | 4 |
| execute | 3 |
| _fetch_dataset | 3 |

No violations found. This file complies with the guidelines.

## File: src\refactors\serial_cc\site_client_insights.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 326 |
| Executable code lines | 207 |
| Functions | 17 |
| Classes | 3 |
| Average complexity | 2.6 |
| Max complexity | 4 |
| Inline comment coverage | 90.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _resolve_site_name | 4 |
| _list_and_display_clients | 4 |
| _resolve_client_mac | 4 |
| _fetch_single_metric | 4 |
| _resolve_normalized_mac | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 371 |
| Executable code lines | 205 |
| Functions | 19 |
| Classes | 3 |
| Average complexity | 2.3 |
| Max complexity | 5 |
| Inline comment coverage | 85.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _prompt_bounded_int | 5 |
| _gather_settings | 4 |
| _read_client_mac | 3 |
| _select_client_mac | 3 |
| _select_ap_filter | 3 |

No violations found. This file complies with the guidelines.

## File: src\refactors\serial_cc\start_site_scan_capture.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 444 |
| Executable code lines | 256 |
| Functions | 24 |
| Classes | 3 |
| Average complexity | 2.3 |
| Max complexity | 5 |
| Inline comment coverage | 87.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _prompt_bounded_int | 5 |
| _list_existing_captures | 4 |
| _gather_prompted_values | 4 |
| execute | 4 |
| _select_ap | 3 |

No violations found. This file complies with the guidelines.

## File: src\refactors\serial_cc\switch_vc_stats.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 190 |
| Executable code lines | 98 |
| Functions | 11 |
| Classes | 1 |
| Average complexity | 2.9 |
| Max complexity | 5 |
| Inline comment coverage | 87.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _collect_vc_stats_parallel | 5 |
| _build_preview_table | 5 |
| _load_switches | 4 |
| _fetch_vc_for_switch | 4 |
| _collect_vc_stats_sequential | 4 |

No violations found. This file complies with the guidelines.

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

## File: src\refactors\sqlite_database_writer.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 446 |
| Executable code lines | 229 |
| Functions | 32 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 97.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| write | 5 |
| _ensure_database_directory | 4 |
| _determine_fields_and_strategy | 4 |
| _create_schema_indexes | 4 |
| _validate_data | 3 |

No violations found. This file complies with the guidelines.

## File: src\refactors\tui_launcher.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 165 |
| Executable code lines | 92 |
| Functions | 13 |
| Classes | 1 |
| Average complexity | 1.9 |
| Max complexity | 5 |
| Inline comment coverage | 84.8% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _suppress_console_logging | 5 |
| launch | 4 |
| _ensure_api_session | 3 |
| _run_tui | 2 |
| _restore_console_logging | 2 |

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 538 |
| Executable code lines | 273 |
| Functions | 40 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 86.4% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _maybe_ui | 5 |
| _consensus_address | 5 |
| has_conflicting_hints | 5 |
| _pick_tier_winner | 4 |
| _resolve_validated | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 654 |
| Executable code lines | 353 |
| Functions | 44 |
| Classes | 1 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 84.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| ensure_location_field_ready | 5 |
| geocode_via_ui | 5 |
| _evaluate_suite | 5 |
| close | 5 |
| _cdp_port | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 330 |
| Executable code lines | 119 |
| Functions | 15 |
| Classes | 3 |
| Average complexity | 2.2 |
| Max complexity | 3 |
| Inline comment coverage | 80.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| __post_init__ | 3 |
| from_configs | 3 |
| _log_invocation | 3 |
| _collect_results | 3 |
| _handle_loop_failure | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 389 |
| Executable code lines | 199 |
| Functions | 29 |
| Classes | 2 |
| Average complexity | 1.9 |
| Max complexity | 5 |
| Inline comment coverage | 81.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _validate_inputs | 5 |
| connect | 4 |
| _preflight | 3 |
| _paramiko_available | 3 |
| _tighten_kh_permissions | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 445 |
| Executable code lines | 258 |
| Functions | 32 |
| Classes | 2 |
| Average complexity | 3.1 |
| Max complexity | 5 |
| Inline comment coverage | 83.7% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _make_line_tracer | 5 |
| _ssh_line_tracer | 5 |
| _resolve_password | 5 |
| _validate_hosts | 5 |
| _resolve_commands | 5 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 609 |
| Executable code lines | 296 |
| Functions | 35 |
| Classes | 3 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 85.1% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _evaluate_success | 5 |
| _loop_step | 4 |
| _drain_excess | 4 |
| _cleanup_shell | 4 |
| _drain_cleanup_tail | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 565 |
| Executable code lines | 289 |
| Functions | 38 |
| Classes | 2 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 82.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _count_template_gateways | 5 |
| _resolve_template_by_substring | 5 |
| _resolve_by_template_config | 5 |
| interactive | 4 |
| _run_interactive_workflow | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 272 |
| Executable code lines | 128 |
| Functions | 17 |
| Classes | 1 |
| Average complexity | 3.2 |
| Max complexity | 5 |
| Inline comment coverage | 92.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _plan_entries_for_row | 5 |
| _classify_variable | 5 |
| _get_cached_site_vars | 4 |
| _display_variable_summary | 4 |
| _select_pending_entries | 4 |

No violations found. This file complies with the guidelines.

## File: src\ssid_consolidation\_ssid_template_phase3.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 365 |
| Executable code lines | 146 |
| Functions | 24 |
| Classes | 2 |
| Average complexity | 2.3 |
| Max complexity | 4 |
| Inline comment coverage | 99.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _assign_matrix_sites | 4 |
| _get_existing_group_site_ids | 4 |
| phase3_site_groups | 4 |
| _assign_sites_to_groups | 4 |
| _compute_group_plan | 3 |

No violations found. This file complies with the guidelines.

## File: src\ssid_consolidation\_ssid_template_phase45.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 663 |
| Executable code lines | 314 |
| Functions | 40 |
| Classes | 3 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 86.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _skip_reason_for_row | 5 |
| phase5_disable_old | 5 |
| _process_disable_entry | 5 |
| _load_group_plan_from_results | 4 |
| _cluster_deviation_params | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 437 |
| Executable code lines | 246 |
| Functions | 26 |
| Classes | 3 |
| Average complexity | 2.0 |
| Max complexity | 4 |
| Inline comment coverage | 80.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _find_selector_match | 4 |
| _print_skipped_options | 4 |
| _run_option_loop | 4 |
| _resolve_test_site | 3 |
| _build_option_lists | 3 |

No violations found. This file complies with the guidelines.

## File: src\troubleshooting\marvis_troubleshoot_utils.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 599 |
| Executable code lines | 360 |
| Functions | 41 |
| Classes | 2 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 87.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _filter_marvis_features | 5 |
| device_performance | 4 |
| _display_response_summary | 4 |
| _render_summary_fallback | 4 |
| _handle_network_response | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 343 |
| Executable code lines | 221 |
| Functions | 28 |
| Classes | 3 |
| Average complexity | 2.5 |
| Max complexity | 4 |
| Inline comment coverage | 84.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _preview_sequence | 4 |
| execute | 4 |
| _extract_callable | 4 |
| _collect_params_interactively | 4 |
| _prompt_outcome | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 296 |
| Executable code lines | 165 |
| Functions | 29 |
| Classes | 3 |
| Average complexity | 2.3 |
| Max complexity | 4 |
| Inline comment coverage | 87.3% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| format | 4 |
| _format_list | 4 |
| _is_ipv4_like | 3 |
| _is_list_of_dicts | 3 |
| _format_string | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 595 |
| Executable code lines | 301 |
| Functions | 34 |
| Classes | 3 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _read_existing_entries | 5 |
| _needs_refresh | 5 |
| _reset_gains_if_needed | 5 |
| _is_finite_number | 4 |
| _adjust_gains | 4 |

No violations found. This file complies with the guidelines.

## File: src\wan_hub_group_manager.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 541 |
| Executable code lines | 277 |
| Functions | 26 |
| Classes | 1 |
| Average complexity | 2.8 |
| Max complexity | 5 |
| Inline comment coverage | 98.9% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _report_no_hub_spoke | 5 |
| _format_pod_display | 5 |
| run | 4 |
| _fetch_hub_spoke_vpns | 4 |
| _find_matching_paths | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 286 |
| Executable code lines | 175 |
| Functions | 16 |
| Classes | 1 |
| Average complexity | 2.9 |
| Max complexity | 4 |
| Inline comment coverage | 84.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _run_workflow | 4 |
| _resolve_targets | 4 |
| _post_show_mac_table | 4 |
| _await_and_display | 4 |
| _render_primary_output | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 561 |
| Executable code lines | 310 |
| Functions | 33 |
| Classes | 1 |
| Average complexity | 2.7 |
| Max complexity | 5 |
| Inline comment coverage | 95.2% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _run_workflow | 5 |
| _lookup_device_record | 5 |
| _maybe_warn_and_confirm | 4 |
| _render_output_sections | 4 |
| _render_raw_output_block | 4 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 334 |
| Executable code lines | 201 |
| Functions | 20 |
| Classes | 3 |
| Average complexity | 2.5 |
| Max complexity | 5 |
| Inline comment coverage | 90.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _parse_ping_count | 5 |
| _run_workflow | 4 |
| _prompt_target_host | 4 |
| _render_output_sections | 4 |
| _select_device | 3 |

No violations found. This file complies with the guidelines.

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

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 324 |
| Executable code lines | 209 |
| Functions | 28 |
| Classes | 2 |
| Average complexity | 2.4 |
| Max complexity | 5 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _unwrap_payload | 5 |
| _parse_string | 4 |
| _print_packet_body | 4 |
| _handle_data | 4 |
| _store_segment | 4 |

No violations found. This file complies with the guidelines.

## File: src\websocket\polling\result_collector.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 465 |
| Executable code lines | 269 |
| Functions | 32 |
| Classes | 4 |
| Average complexity | 2.2 |
| Max complexity | 5 |
| Inline comment coverage | 82.5% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _try_completion | 5 |
| _maybe_emit_combined_trace | 4 |
| __post_init__ | 3 |
| _maybe_log | 3 |
| _finalize | 3 |

No violations found. This file complies with the guidelines.

## File: src\websocket\polling\result_combiner.py

- **Score**: 100.0 / 100
- **Grade**: A+

### Metrics

| Metric | Value |
| - | - |
| Lines of code | 117 |
| Executable code lines | 77 |
| Functions | 8 |
| Classes | 1 |
| Average complexity | 2.4 |
| Max complexity | 3 |
| Inline comment coverage | 100.0% |

### Complexity Hotspots

| Function | Cyclomatic Complexity |
| - | - |
| _emit_debug_trailer | 3 |
| _merge_segments | 3 |
| _absorb_raw_chunk | 3 |
| _absorb_extras | 3 |
| combine_segments | 2 |

No violations found. This file complies with the guidelines.

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

### Phase: High (11 task(s))

- [ ] **CMP-001** `src\analytics\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 6.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\analytics\__init__.py`.
- [ ] **CMP-002** `src\auth\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\auth\__init__.py`.
- [ ] **CMP-003** `src\capture\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 5.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\__init__.py`.
- [ ] **CMP-004** `src\db\__init__.py:8` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 1.7%; uncommented lines: 8, 10, 11, 12, 13, 15, 18, 20, 39, 42, 43, 44.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\db\__init__.py`.
- [ ] **CMP-005** `src\ui\execution\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5, 6, 7, 8.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\execution\__init__.py`.
- [ ] **CMP-006** `src\ui\execution\output_formatter.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 34.5%; uncommented lines: 7, 9, 10, 15, 18, 21, 22, 26, 29, 34, 35, 37.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\execution\output_formatter.py`.
- [ ] **CMP-007** `src\ui\input_handlers\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\input_handlers\__init__.py`.
- [ ] **CMP-008** `src\ui\layout\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\layout\__init__.py`.
- [ ] **CMP-009** `src\ui\runtime\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\runtime\__init__.py`.
- [ ] **CMP-010** `src\ui\runtime\level_discoverer.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 44.8%; uncommented lines: 3, 5, 6, 7, 8, 13, 16, 20, 29, 32, 34, 36.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\runtime\level_discoverer.py`.
- [ ] **CMP-011** `src\websocket\__init__.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 0.0%; uncommented lines: 3, 4, 5, 6, 7, 8, 10.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\websocket\__init__.py`.

### Phase: Medium (13 task(s))

- [ ] **CMP-012** `MistHelper.py:16285` - STRUCT-LENGTH (Structure)
  - Symbol: `_make_ws_callbacks`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_make_ws_callbacks` in `MistHelper.py`.
- [ ] **CMP-013** `MistHelper.py:16523` - STRUCT-LENGTH (Structure)
  - Symbol: `_build_impl_args`
  - Problem: Function spans 26 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `_build_impl_args` in `MistHelper.py`.
- [ ] **CMP-014** `src\capture\org_pcap_wait_download_workflow.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 52.2%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 20, 62.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\org_pcap_wait_download_workflow.py`.
- [ ] **CMP-015** `src\capture\org_pcap_wait_download_workflow.py:20` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\capture\org_pcap_wait_download_workflow.py`.
- [ ] **CMP-016** `src\capture\site_pcap_wait_download_workflow.py:3` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 52.2%; uncommented lines: 3, 5, 6, 7, 9, 13, 16, 17, 18, 20, 62.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\capture\site_pcap_wait_download_workflow.py`.
- [ ] **CMP-017** `src\capture\site_pcap_wait_download_workflow.py:20` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 41 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\capture\site_pcap_wait_download_workflow.py`.
- [ ] **CMP-018** `src\refactors\serial_cc\import_initialization_service.py:71` - STRUCT-LENGTH (Structure)
  - Symbol: `execute`
  - Problem: Function spans 29 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `execute` in `src\refactors\serial_cc\import_initialization_service.py`.
- [ ] **CMP-019** `src\site\address_audit\address_corrector.py:30` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 79.3%; uncommented lines: 30, 34, 37, 41, 51, 61, 73, 79, 82, 85, 93, 96.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\site\address_audit\address_corrector.py`.
- [ ] **CMP-020** `src\site\address_audit\business_authority_ingester.py:73` - STRUCT-LENGTH (Structure)
  - Symbol: `match`
  - Problem: Function spans 38 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `match` in `src\site\address_audit\business_authority_ingester.py`.
- [ ] **CMP-021** `src\ssh\runtime\interactive_mode.py:151` - STRUCT-LENGTH (Structure)
  - Symbol: `run`
  - Problem: Function spans 28 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `run` in `src\ssh\runtime\interactive_mode.py`.
- [ ] **CMP-022** `src\ui\input_handlers\key_poller.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 58.2%; uncommented lines: 7, 9, 10, 11, 12, 31, 41, 44, 48, 55, 62, 66.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\input_handlers\key_poller.py`.
- [ ] **CMP-023** `src\ui\layout\layout_builder.py:7` - CONV-COMMENTS (Conventions)
  - Symbol: `<file>`
  - Problem: Inline-comment coverage is 51.2%; uncommented lines: 7, 9, 10, 11, 18, 21, 25, 38, 39, 48, 49, 50.
  - Fix: Add a same-line comment explaining intent on each executable line of changed code.
  - Done when: analyzer reports no CONV-COMMENTS for `<file>` in `src\ui\layout\layout_builder.py`.
- [ ] **CMP-024** `src\ui\layout\layout_builder.py:25` - STRUCT-LENGTH (Structure)
  - Symbol: `build`
  - Problem: Function spans 27 lines (limit 25).
  - Fix: Extract logical sections into well-named helper methods to shrink the function.
  - Done when: analyzer reports no STRUCT-LENGTH for `build` in `src\ui\layout\layout_builder.py`.

### Phase: Low (14 task(s))

- [ ] **CMP-025** `MistHelper.py:16239` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `execute`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `execute` in `MistHelper.py`.
- [ ] **CMP-026** `src\auth\interactive\msp_org_selector.py:118` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_fetch_msp_orgs`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_fetch_msp_orgs` in `src\auth\interactive\msp_org_selector.py`.
- [ ] **CMP-027** `src\auth\interactive\msp_org_selector.py:192` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_interpret_choice`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_interpret_choice` in `src\auth\interactive\msp_org_selector.py`.
- [ ] **CMP-028** `src\refactors\serial_cc\import_initialization_service.py:24` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_import_package_group`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_import_package_group` in `src\refactors\serial_cc\import_initialization_service.py`.
- [ ] **CMP-029** `src\refactors\serial_cc\import_initialization_service.py:49` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_log_summary`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_log_summary` in `src\refactors\serial_cc\import_initialization_service.py`.
- [ ] **CMP-030** `src\site\address_audit\address_corrector.py:51` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_is_correctable`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_is_correctable` in `src\site\address_audit\address_corrector.py`.
- [ ] **CMP-031** `src\site\address_audit\address_corrector.py:73` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_review_one`
  - Problem: Cyclomatic complexity is 8 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_review_one` in `src\site\address_audit\address_corrector.py`.
- [ ] **CMP-032** `src\site\address_audit\address_corrector.py:128` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_print_summary`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_print_summary` in `src\site\address_audit\address_corrector.py`.
- [ ] **CMP-033** `src\site\address_audit\business_authority_ingester.py:73` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `match`
  - Problem: Cyclomatic complexity is 7 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `match` in `src\site\address_audit\business_authority_ingester.py`.
- [ ] **CMP-034** `src\site\address_audit\business_authority_ingester.py:112` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_row`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_row` in `src\site\address_audit\business_authority_ingester.py`.
- [ ] **CMP-035** `src\ui\execution\output_formatter.py:78` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_render_sequence`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_render_sequence` in `src\ui\execution\output_formatter.py`.
- [ ] **CMP-036** `src\ui\input_handlers\key_poller.py:95` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `_parse_unix_csi`
  - Problem: Cyclomatic complexity is 10 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `_parse_unix_csi` in `src\ui\input_handlers\key_poller.py`.
- [ ] **CMP-037** `src\ui\input_handlers\key_poller.py:95` - STRUCT-BLOCKS (Structure)
  - Symbol: `_parse_unix_csi`
  - Problem: Function has 6 logical blocks (limit 5).
  - Fix: Split the function so each helper owns a single cohesive block of logic.
  - Done when: analyzer reports no STRUCT-BLOCKS for `_parse_unix_csi` in `src\ui\input_handlers\key_poller.py`.
- [ ] **CMP-038** `src\ui\runtime\level_discoverer.py:20` - STRUCT-COMPLEXITY (Complexity)
  - Symbol: `discover`
  - Problem: Cyclomatic complexity is 6 (target <= 5).
  - Fix: Reduce branching by extracting helpers, using guard clauses, or simplifying logic.
  - Done when: analyzer reports no STRUCT-COMPLEXITY for `discover` in `src\ui\runtime\level_discoverer.py`.

