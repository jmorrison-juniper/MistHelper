# Audit spec: Menu option #29 — Export port statistics for a selected site

Purpose
- Audit implementation of SiteDeviceExporter.port_stats (menu #29) to ensure correctness, data integrity, and DB upsert strategy.

Scope
- Review MistHelper.py implementation for port_stats
- Verify ENDPOINT_PRIMARY_KEY_STRATEGIES entry for searchSiteSwOrGwPorts
- Confirm DataExporter.write_with_format_selection call uses api_function_name correctly
- Check related unit tests and add recommendations

Deliverables
- spec.md (this file), plan.md, tasks.md
- Findings summary (to be produced after manual audit)
