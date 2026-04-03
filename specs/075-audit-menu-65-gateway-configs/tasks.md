Tasks:
1. Locate GatewayExportUtils.device_configs in MistHelper.py and note the mistapi calls and exported filename (e.g., 'AllSiteGatewayConfigs.csv').
2. Define ENDPOINT_PRIMARY_KEY_STRATEGIES entry; example:
   'getOrgGatewayDeviceConfigs': {'type':'natural_pk','primary_key':['device_id','site_id'],'indexes':['org_id','site_id','device_name']}
3. Replace save_data_to_output with DataExporter.write_with_format_selection(processed_configs, "AllSiteGatewayConfigs", api_function_name="getOrgGatewayDeviceConfigs").
4. Add tests/tests_gateway_configs.py asserting write_with_format_selection invoked and handling empty responses.
5. Run pytest and verify.

Notes: Keep CSV fallback intact when OUTPUT_FORMAT selects CSV. Aim for minimal surgical changes.