Audit: Menu #42 
Export security events

Location: MistHelper.py 
Class: OrgClientSecurityExporter.security_events (around line ~13096)

Summary findings:
- security_events fetches three artifacts: OrgSecurityPolicies, OrgSecIntelProfiles, OrgRogueData.
- Policies: fetched via mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies 
  - ENDPOINT_PRIMARY_KEY_STRATEGIES includes "listOrgSecPolicies" (natural_pk: id).
- Secintel profiles: fetched via mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles 
  - NO explicit strategy entry found in ENDPOINT_PRIMARY_KEY_STRATEGIES.
- Rogue aggregate: collected from site-level insights listSiteRogueAPs/listSiteRogueClients and combined into OrgRogueData.csv (site-level endpoints not present in strategies as org-level keys).
- DataExporter.save_data_to_output is called WITHOUT api_function_name for policies, secintel, and rogue aggregate (calls like DataExporter.save_data_to_output(processed, "OrgSecurityPolicies.csv")). Because api_function_name is not passed, DatabaseSchemaUtils.determine_api_function_name_from_context may return 'unknown' and DatabaseSchemaUtils.get_endpoint_strategy will fall back to default/enhanced heuristics rather than using the configured strategy for listOrgSecPolicies.

Risks / Impact:
- SQL export schema selection may not use intended hybrid PK strategy for these files, causing non-optimal PRIMARY KEY and indexes.
- SecIntelProfiles lacks explicit strategy entry; rogue site-level endpoints are not present (site-level names differ) 
  - potential schema mismatch.

Recommendation:
- Pass api_function_name explicitly to DataExporter.save_data_to_output calls (use api_function_name="listOrgSecPolicies" and "listOrgSecIntelProfiles" where applicable).
- For site-level rogue endpoints, either map the aggregated OrgRogueData output to canonical api_function_name (e.g., "listSiteRogueAPs" / "listSiteRogueClients" or a synthetic key) and add corresponding ENDPOINT_PRIMARY_KEY_STRATEGIES entries, or pass a specific api_function_name when writing.

Test coverage: No unit tests detected for security_events; add targeted tests.