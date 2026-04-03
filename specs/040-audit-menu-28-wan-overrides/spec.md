# Spec: Audit Menu 28 - Find gateway ports overridden from template

Scope
- Location: MistHelper.py, class GatewayExportUtils, method with_wan_overrides (menu option #28, data_export category).
- Purpose: Verify correctness, observability, and DB export strategy for the "Gateway Ports Overridden from Template" export.

Current behavior (summary)
- Reads cached CSVs: AllSiteGatewayConfigs.csv, SiteList_ListAPI.csv, OrgGatewayTemplates.csv.
- Identifies devices with overridden ports using MIST_WAN_TARGET_PORTS env var.
- Fetches live device config/stats for devices with overrides (fast mode has connection pool optimization).
- Builds overridden_port_info list and calls DataExporter.save_data_to_output(overridden_port_info, "GatewayOverriddenPorts.csv").

Observations / Risks
- save_data_to_output delegates to DataExporter.write_with_format_selection, but with_wan_overrides does not pass an api_function_name.
  - Without api_function_name, SQLiteDatabaseWriter will use the generic/default strategy which may select suboptimal primary keys/indexes in ENDPOINT_PRIMARY_KEY_STRATEGIES.
- No unit/integration tests found covering with_wan_overrides or GatewayOverriddenPorts export.
- Requires MIST_WAN_TARGET_PORTS env variable; missing config causes early exit returning [] or skipping analysis.
- Potential for incomplete field extraction: CSV-derived port_config field detection uses CSV headers heuristics; edge cases for subinterfaces may be missed.

Acceptance criteria
- Spec files and tasks created (this audit only).
- Findings recorded and actionable plan provided (plan.md, tasks.md).
- Recommended changes identified (include passing explicit api_function_name to DataExporter.write_with_format_selection, add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for the function if needed, and add unit tests to cover branches).

