Plan to remediate menu #83:

1. Identify canonical API function names used (getOrgSle, getOrgSitesSle) and add appropriate PK strategy entries to ENDPOINT_PRIMARY_KEY_STRATEGIES.
2. Update normalized export stage to call DataExporter.write_with_format_selection for each normalized dataset with api_function_name set per output type.
3. Add unit tests to verify normalized outputs and SQL export invocation.
4. Run py_compile and pytest.
