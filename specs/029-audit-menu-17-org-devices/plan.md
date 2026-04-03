Summary
- Purpose: Document technical context and plan for bringing Menu #17 (OrgInventoryExporter.devices) into SQL export compliance and test coverage.

Technical Context
- OrgInventoryExporter.devices() calls mistapi.api.v1.orgs.devices.listOrgDevices via APIDataFetcher. APIDataFetcher passes api_function_name=api_call.__name__ ("listOrgDevices").
- ENDPOINT_PRIMARY_KEY_STRATEGIES currently contains "getOrgDevices" but not "listOrgDevices". write_with_format_selection looks up strategies by api_function_name and will fall back to "default" when a matching key is missing.

Constitution Check
- Per project constitution, all structured exports must have an ENDPOINT_PRIMARY_KEY_STRATEGIES entry keyed to the API function name used at runtime. If the API SDK exposes "listOrgDevices" as the function name, the strategy must be declared using that exact key.
- Recommended actions conform to the 5-item rule: small focused change (add single mapping) and unit tests to validate strategy presence and pipeline wiring.
