Audit: Menu #44 
Export rogue AP detections

Location: MistHelper.py 
Class: OrgClientSecurityExporter.rogue_aps (around line ~13300)

Summary findings:
- rogue_aps collects site-level rogue APs via mistapi.api.v1.sites.insights.listSiteRogueAPs and aggregates them into OrgRogueAPs (DataExporter.save_data_to_output called with "OrgRogueAPs" and no api_function_name).
- ENDPOINT_PRIMARY_KEY_STRATEGIES does not include an entry for the site-level listSiteRogueAPs or for an aggregated org-level key.

Risks:
- Without explicit api_function_name and strategy, SQLite may use default strategy and miss intended composite PK/indexes (e.g., mac/site_id/timestamp).

Recommendation:
- Add a synthetic endpoint key (e.g., "orgAggregatedRogueAps") with composite_pk primary key ["mac","site_id","timestamp"] and pass api_function_name when saving.
- Add unit/integration tests to validate schema.

Test coverage: No tests detected for rogue_aps; add tests.