Plan to remediate and test Menu #42 (security_events):

1. Add explicit api_function_name when saving each artifact:
   - OrgSecurityPolicies.csv -> api_function_name="listOrgSecPolicies"
   - OrgSecIntelProfiles.csv -> api_function_name="listOrgSecIntelProfiles"
   - OrgRogueData.csv -> api_function_name="listSiteRogueAPs" (or use a synthetic key like "orgRogueData_aggregated" and add a strategy entry)
2. If code changes are approved, add ENDPOINT_PRIMARY_KEY_STRATEGIES entries for secintelprofiles and for any synthetic/aggregated keys.
3. Add unit tests to verify DataExporter receives api_function_name for each artifact and integration tests to validate SQLite schema uses expected PK/indexes.
4. Run full test suite.

Note: User requested no code changes now 
- this plan documents recommended fixes.