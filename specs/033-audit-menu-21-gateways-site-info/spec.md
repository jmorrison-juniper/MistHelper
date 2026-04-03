# Audit: Menu Option #21 — Gateways with Site and Address Info

Location: MistHelper.py (class OrgInventoryExporter, method gateways_with_site_info)

Objective: Verify completeness, SQL export compliance, and test coverage for menu option #21.

Findings:
- Method exists at ~line 12071 as OrgInventoryExporter.gateways_with_site_info().
- Fetches sites via APICoreFetchUtils.all_sites_with_limit and inventory via APICoreFetchUtils.all_inventory_with_limit.
- Filters devices by device['type'] == 'gateway', enriches with site address parsing, flattens, sorts, and exports.
- Export call uses DataExporter.save_data_to_output(gateways, "GatewaysWithSiteInfo.csv") and DOES NOT pass api_function_name nor use DataExporter.write_with_format_selection().
- ENDPOINT_PRIMARY_KEY_STRATEGIES includes entries for getOrgInventory/listOrgSites but no explicit entry for a Gateways endpoint; inventory strategy: "getOrgInventory" (natural_pk on id).
- No unit test found referencing gateways or GatewaysWithSiteInfo (search in tests/ returned no matches).

Risks / Issues:
- Missing api_function_name on export may prevent correct SQLite primary-key strategy selection (export tooling depends on api_function_name to choose PK strategy).
- No dedicated tests for this menu option (no mocks, no validation of CSV/SQLite export behavior).

Relevant PK strategies:
- getOrgInventory (natural_pk, primary_key: ["id"]) — applicable if export is associated with that API via api_function_name.
- listOrgSites (natural_pk) — relevant for site enrichment.

Output Recommendation (see plan/tasks): add api_function_name to export (use write_with_format_selection or save_data_to_output with api_function_name), add unit tests, and verify SQL export behavior.
