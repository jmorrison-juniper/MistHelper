Plan:
1. Inspect OrgAdminExporter.sso and OrgExportUtils.export_data usage
2. Identify canonical API function name (listOrgSsos / GET_orgs_org_id_ssos)
3. Map to ENDPOINT_PRIMARY_KEY_STRATEGIES
4. Inspect OrgExportUtils implementation for api_function_name propagation
5. Search tests/ for SSO export coverage
