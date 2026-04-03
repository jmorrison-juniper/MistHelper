Audit: Menu #43 
Export rogue client detections

Location: MistHelper.py 
Class: OrgClientSecurityExporter.rogue_clients (around line ~13231)

Summary findings:
- rogue_clients collects site-level rogue clients via mistapi.api.v1.sites.insights.listSiteRogueClients and aggregates them into OrgRogueClients.csv (filename passed to DataExporter.save_data_to_output is "OrgRogueClients" with no api_function_name).
- ENDPOINT_PRIMARY_KEY_STRATEGIES does not include an org-level entry for aggregated rogue clients; site-level endpoints (listSiteRogueClients) are not present as keys in the strategies dict.
- Because api_function_name is not provided, SQLite writer will try to infer api function name from stack and likely default to heuristics.

Risks:
- Aggregated rogue client data may be written with default auto-increment strategy instead of appropriate composite PK (e.g., combining mac + site_id + timestamp), reducing upsert semantics and query performance.

Recommendations:
- When writing aggregated cross-site outputs, pass a synthetic api_function_name (e.g., "orgAggregatedRogueClients") and add a matching strategy in ENDPOINT_PRIMARY_KEY_STRATEGIES with composite PK fields (mac, site_id, timestamp) to ensure proper upsert/indexing.
- Add unit tests to cover schema selection and write behavior.