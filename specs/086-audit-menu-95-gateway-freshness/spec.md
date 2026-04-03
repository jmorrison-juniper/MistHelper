# Audit: Menu 95 - Export gateway stats with freshness check

Target: GatewayStatsExporter.device_stats_with_freshness

Purpose: Verify completeness, test coverage, and SQL export compliance (ENDPOINT_PRIMARY_KEY_STRATEGIES + DataExporter usage). Document findings and remediation tasks.

References:
- MistHelper.py: GatewayStatsExporter
- ENDPOINT_PRIMARY_KEY_STRATEGIES (MistHelper.py)
- DataExporter.write_with_format_selection(api_function_name=...)

Assumptions:
- Audit focuses on method behavior, test presence, and SQL export PK mapping.