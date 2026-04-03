Spec: Menu 65 — WIP Export gateway configs all sites (GatewayExportUtils.device_configs)

Summary of findings:
- GatewayExportUtils.device_configs exists and is referenced by menu actions (menu 65 mapping). It is used by CacheUtils.check_and_generate_csv in other flows.
- No explicit tests found covering device_configs or asserting SQL-export compliance.
- Ensure device_configs uses DataExporter.write_with_format_selection(..., api_function_name="getOrgGatewayDeviceConfigs" or the exact mistapi function name) so schema and PK strategies apply.
- Identify appropriate primary key strategy (likely natural_pk with device id and site id) and add to ENDPOINT_PRIMARY_KEY_STRATEGIES.
