# Contract: Mist Read Operations

This contract lists the 18 read operations that support reference checks, read-back, and candidate discovery. Each row cites the bundled OpenAPI JSON file and the pinned mistapi 0.64.1 source, as described in `mist-write-operations.md`. Read operations change no Mist object. Each read operation has an identity status, a role, and the write operations that use it.

Role meanings:

- **reference**: A read that checks for an existing object or a duplicate name before a write.
- **read-back**: A read that confirms the object state after a write.
- **candidate**: A read in the parity inventory that no write family uses yet.

## Identity Evidence

| ID | Verb and path | Operation ID | OpenAPI object | YAML line | SDK function (file line) | SDK call line | Identity status | Role | Used by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | GET `/api/v1/const/device_models` | `listDeviceModels` | `paths[/api/v1/const/device_models].get` | 1863 | `const/device_models.py` (17) | 34 | verified-present | candidate | Hardware checks in the parity map |
| R-02 | GET `/api/v1/orgs/{org_id}/sites` | `listOrgSites` | `paths[/api/v1/orgs/{org_id}/sites].get` | 20022 | `orgs/sites.py` (17) | 54 | verified-present | reference | W-01 |
| R-03 | GET `/api/v1/sites/{site_id}` | `getSiteInfo` | `paths[/api/v1/sites/{site_id}].get` | 25978 | `sites/sites.py` (17) | 38 | verified-present | read-back | W-02 |
| R-04 | GET `/api/v1/sites/{site_id}/setting` | `getSiteSetting` | `paths[/api/v1/sites/{site_id}/setting].get` | 37065 | `sites/setting.py` (17) | 38 | verified-present | read-back | W-13 |
| R-05 | GET `/api/v1/orgs/{org_id}/inventory` | `getOrgInventory` | `paths[/api/v1/orgs/{org_id}/inventory].get` | 10660 | `orgs/inventory.py` (17) | 104 | verified-present | reference and read-back | W-03 |
| R-06 | GET `/api/v1/sites/{site_id}/devices` | `listSiteDevices` | `paths[/api/v1/sites/{site_id}/devices].get` | 27877 | `sites/devices.py` (17) | 64 | verified-present | reference | W-04 |
| R-07 | GET `/api/v1/sites/{site_id}/devices/{device_id}` | `getSiteDevice` | `paths[/api/v1/sites/{site_id}/devices/{device_id}].get` | 29054 | `sites/devices.py` (1450) | 1474 | verified-present | read-back | W-04 |
| R-08 | GET `/api/v1/orgs/{org_id}/gatewaytemplates` | `listOrgGatewayTemplates` | `paths[/api/v1/orgs/{org_id}/gatewaytemplates].get` | 9731 | `orgs/gatewaytemplates.py` (17) | 54 | verified-present | reference | W-05 |
| R-09 | GET `/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}` | `getOrgGatewayTemplate` | `paths[/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}].get` | 9929 | `orgs/gatewaytemplates.py` (89) | 113 | verified-present | read-back | W-06, W-07 |
| R-10 | GET `/api/v1/orgs/{org_id}/deviceprofiles` | `listOrgDeviceProfiles` | `paths[/api/v1/orgs/{org_id}/deviceprofiles].get` | 7957 | `orgs/deviceprofiles.py` (17) | 59 | verified-present | reference | W-08 |
| R-11 | GET `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` | `getOrgDeviceProfile` | `paths[/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}].get` | 8164 | `orgs/deviceprofiles.py` (94) | 118 | verified-present | read-back | W-09, W-10 |
| R-12 | GET `/api/v1/orgs/{org_id}/networks` | `listOrgNetworks` | `paths[/api/v1/orgs/{org_id}/networks].get` | 15122 | `orgs/networks.py` (17) | 54 | verified-present | reference | W-14, W-16 |
| R-13 | GET `/api/v1/orgs/{org_id}/networks/{network_id}` | `getOrgNetwork` | `paths[/api/v1/orgs/{org_id}/networks/{network_id}].get` | 15299 | `orgs/networks.py` (89) | 113 | verified-present | read-back | W-15 |
| R-14 | GET `/api/v1/orgs/{org_id}/networktemplates` | `listOrgNetworkTemplates` | `paths[/api/v1/orgs/{org_id}/networktemplates].get` | 15441 | `orgs/networktemplates.py` (17) | 54 | verified-present | reference | W-16 |
| R-15 | GET `/api/v1/orgs/{org_id}/services` | `listOrgServices` | `paths[/api/v1/orgs/{org_id}/services].get` | 18494 | `orgs/services.py` (17) | 54 | verified-present | reference | W-17, W-19 |
| R-16 | GET `/api/v1/orgs/{org_id}/services/{service_id}` | `getOrgService` | `paths[/api/v1/orgs/{org_id}/services/{service_id}].get` | 18587 | `orgs/services.py` (89) | 113 | verified-present | read-back | W-18, W-19 |
| R-17 | GET `/api/v1/orgs/{org_id}/servicepolicies` | `listOrgServicePolicies` | `paths[/api/v1/orgs/{org_id}/servicepolicies].get` | 18345 | `orgs/servicepolicies.py` (17) | 54 | verified-present | reference | W-20 |
| R-18 | GET `/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` | `getOrgServicePolicy` | `paths[/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}].get` | 18434 | `orgs/servicepolicies.py` (89) | 113 | verified-present | read-back | W-21 |

## Behavior Evidence

Behavior status `partial` for every read operation. Each read operation declares the response codes of the path operation. The response bodies are not verified against the service (U-01). The SDK retry and timeout behavior of `mist_get` follows the same shared loop as the write calls (`mist-sdk-behavior.md`).

## Reference Coverage for Deletion

Record 4645 asks for reference reads before a deletion scope review (its analysis F-04). The reference reads for deletion are these:

- W-16 (`deleteOrgNetwork`) uses R-12 and R-14.
- W-19 (`deleteOrgService`) uses R-15 and R-16.
- W-07 (`deleteOrgGatewayTemplate`) uses R-08 and R-09.

The service behavior for deleting a referenced object is unverified (U-16). A deletion scope review blocks each reference that these reads do not verify.

## Candidate Coverage

R-01 is the only candidate read. It supports the hardware family named in the parity map. The read has no write dependency in this change.

Caution: A list read returns one page at a time. A duplicate check that reads one page can miss a duplicate name. The parity contract requires every page of each list (`mist.md`, Discovery and Approval). None of these reads changes a Mist object.
