Plan:
1. Inspect OrgConfigExporter.mx_edges and OrgExportUtils.export_data usage
2. Identify canonical API function name (listOrgMxEdges / GET_orgs_org_id_mxedges)
3. Map to ENDPOINT_PRIMARY_KEY_STRATEGIES entry
4. Inspect OrgExportUtils for api_function_name propagation
5. Search tests/ for mx_edges coverage
