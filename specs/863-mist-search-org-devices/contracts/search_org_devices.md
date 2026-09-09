# Contract: searchOrgDevices

**Method**: `GET`

**Path**: `/api/v1/orgs/{org_id}/devices/search`

**SDK call**: `mistapi.api.v1.orgs.devices.searchOrgDevices(session, org_id)`

**Response**: A paginated list of organization device objects.

**Persistence**: `DataExporter.write_with_format_selection` with
`api_function_name="searchOrgDevices"` and filename `OrgDevices.csv`.

**Errors**: The shared organization search helper logs SDK errors and returns
control to the menu without a traceback.
