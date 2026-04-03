Spec: Audit Menu #38 — Export AP templates (OrgTemplateExporter.ap_templates)

Findings:
- Implementation: ap_templates calls mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(apisession, org_id, type='ap') and then uses DataExporter.save_data_to_output(processed, filename) WITHOUT passing api_function_name.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains 'listOrgAptemplates' (natural_pk primary_key ['id']).
- The canonical endpoint used (listOrgDeviceProfiles) is different from the strategy key (listOrgAptemplates). Because api_function_name is not provided, DataExporter will use the default strategy for SQLite writes, leading to auto-increment PKs and missing useful indexes.

Test Coverage:
- No unit tests currently validate ap_templates behavior or API function name propagation.

SQL Export Compliance: FAIL — ap_templates does not provide api_function_name to DataExporter; SQLite export may use fallback strategy, not the intended 'listOrgAptemplates' strategy.

Recommendation:
- Pass api_function_name='listOrgAptemplates' (or use APIDataFetcher pattern) when calling DataExporter.save_data_to_output so ENDPOINT_PRIMARY_KEY_STRATEGIES maps to the correct schema.