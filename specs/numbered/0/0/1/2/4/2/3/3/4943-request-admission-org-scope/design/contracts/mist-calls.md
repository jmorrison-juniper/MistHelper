# Contract: Mist Calls on the MSP and VC Paths

This contract defines the two existing mistapi calls that the change reuses. The change adds no call and no transport.

## Call 1: MSP organization list

- **SDK function**: `mistapi.api.v1.msps.orgs.listMspOrgs(mist_session, msp_id)`. Source: `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py:17`.
- **HTTP method and path**: GET `/api/v1/msps/{msp_id}/orgs`. Source: `documentation/mist-api-openapi31yaml.yaml:4081-4085`.
- **Inputs**: the active session, which the client holds as `apisession`, and the MSP identifier.
- **Read fields**: the status code, the data rows, and the continuation link.
- **Status handling**:
  - 200: the client reads the rows and follows the continuation pages.
  - 429: the client waits 60 seconds and retries once (`_request_with_retry`).
  - 0: the transport sentinel. The client logs its own error line and records a failure row.
  - Any other status: one warning line and a failure row (`operator-messages.md`).
- **Admission**: this path uses `msps` in the fourth segment. The ledger uses the ledger organization for it, and the scope does not apply (`request_admission.py:107-109` on main).

## Call 2: VC status read

- **SDK function**: `mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(mist_session, site_id, device_id)`. Source: `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py:3529`.
- **HTTP method and path**: GET `/api/v1/sites/{site_id}/devices/{device_id}/vc`. Source: `documentation/mist-api-openapi31yaml.yaml:31433-31464`. Endpoint page: `documentation/api/sites/GET_sites_site_id_devices_device_id_vc.md:7`.
- **Inputs**: the active session, the site identifier, and the device identifier.
- **Read fields**: the status code and the member payload.
- **Status handling**: a status other than 200 returns no members. The client keeps the source row (`client.py:629-631` on main).
- **Admission**: this path uses `sites` in the fourth segment. Under shared admission, the call runs inside `OrganizationScope.block` for the chassis organization (FR-014).

## Rules that apply to both calls

- Each call uses the session that the menu supplies. The change does not create a session.
- The change sends no direct HTTP request. The feature adds no WebSocket transport.
- Each log line names the MSP identifier or the site identifier. No log line names the session, the token, or a header.
- Each path matches the endpoint catalog: `documentation/MIST_API_GET_ENDPOINTS.md:331` for the MSP list and `:1223` for the VC status read.

## Contract tests

- `tests/integration/test_mistapi_sdk_compatibility.py` checks the SDK compatibility rules of the repository (exists on main).
- The fake SDK tests in `test_client.py` check the failure statuses 403 and 500, the transport failure, and the log order of the MSP call.
