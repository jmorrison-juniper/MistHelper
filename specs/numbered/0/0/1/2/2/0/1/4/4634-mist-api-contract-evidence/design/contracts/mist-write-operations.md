# Contract: Mist Write Operations

This contract lists the 22 write operations of the parity inventory and `deleteOrgServicePolicy`. Each row cites the bundled OpenAPI JSON file (`documentation\mist-api-openapi31json.json`, blob `5f9f4ce94f812f0e818ee65f99f032118a28f56c`). The object column gives the path in the parsed JSON. The YAML column gives the `operationId` line in `documentation\mist-api-openapi31yaml.yaml`. The SDK columns cite the pinned mistapi 0.64.1 source. Each write operation stays disabled in this change.

Caution: A POST create can repeat after an HTTP 429 response, because the SDK retries writes (D-5). The executor reads back before any retry.

Warning: A DELETE operation removes an object from the organization. This change keeps every DELETE operation disabled.

## Identity Evidence

Identity status `verified-present` means the verb, path, operation ID, SDK function, and SDK call match. Object paths use the form `paths[path].verb`.

| ID | Verb and path | Operation ID | OpenAPI object | YAML line | SDK function (file line) | SDK call line | Identity status | Program owner | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W-01 | POST `/api/v1/orgs/{org_id}/sites` | `createOrgSite` | `paths[/api/v1/orgs/{org_id}/sites].post` | 20047 | `orgs/sites.py` (58) | 85 | verified-present | F-01 | in scope, disabled |
| W-02 | PUT `/api/v1/sites/{site_id}` | `updateSiteInfo` | `paths[/api/v1/sites/{site_id}].put` | 26004 | `sites/sites.py` (67) | 92 | verified-present | F-02 | in scope, disabled |
| W-03 | PUT `/api/v1/orgs/{org_id}/inventory` | `updateOrgInventoryAssignment` | `paths[/api/v1/orgs/{org_id}/inventory].put` | 10800 | `orgs/inventory.py` (139) | 166 | verified-present | none (4645 D-13 excludes unassignment) | in scope, disabled |
| W-04 | PUT `/api/v1/sites/{site_id}/devices/{device_id}` | `updateSiteDevice` | `paths[/api/v1/sites/{site_id}/devices/{device_id}].put` | 29076 | `sites/devices.py` (1478) | 1506 | verified-present | none | in scope, disabled |
| W-05 | POST `/api/v1/orgs/{org_id}/gatewaytemplates` | `createOrgGatewayTemplate` | `paths[/api/v1/orgs/{org_id}/gatewaytemplates].post` | 9764 | `orgs/gatewaytemplates.py` (58) | 85 | verified-present | F-04 | in scope, disabled |
| W-06 | PUT `/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}` | `updateOrgGatewayTemplate` | `paths[/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}].put` | 9951 | `orgs/gatewaytemplates.py` (145) | 173 | verified-present | F-05 | in scope, disabled |
| W-07 | DELETE `/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}` | `deleteOrgGatewayTemplate` | `paths[/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}].delete` | 9909 | `orgs/gatewaytemplates.py` (117) | 141 | verified-present | 4645 D-4 (gateway templates only) | in scope, disabled |
| W-08 | POST `/api/v1/orgs/{org_id}/deviceprofiles` | `createOrgDeviceProfile` | `paths[/api/v1/orgs/{org_id}/deviceprofiles].post` | 7988 | `orgs/deviceprofiles.py` (63) | 90 | verified-present | F-06 | in scope, disabled |
| W-09 | PUT `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` | `updateOrgDeviceProfile` | `paths[/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}].put` | 8187 | `orgs/deviceprofiles.py` (150) | 178 | verified-present | F-07 | in scope, disabled |
| W-10 | DELETE `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` | `deleteOrgDeviceProfile` | `paths[/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}].delete` | 8144 | `orgs/deviceprofiles.py` (122) | 146 | verified-present | 4645 D-13 excludes deletion | in scope, disabled |
| W-11 | POST `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/assign` | `assignOrgDeviceProfile` | `paths[/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/assign].post` | 8370 | `orgs/deviceprofiles.py` (182) | 210 | verified-present | F-08 | in scope, disabled |
| W-12 | POST `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/unassign` | `unassignOrgDeviceProfile` | `paths[/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/unassign].post` | 8405 | `orgs/deviceprofiles.py` (214) | 242 | verified-present | 4645 T026 (profile unassignment) | in scope, disabled |
| W-13 | PUT `/api/v1/sites/{site_id}/setting` | `updateSiteSettings` | `paths[/api/v1/sites/{site_id}/setting].put` | 37086 | `sites/setting.py` (42) | 69 | verified-present | F-03 | in scope, disabled |
| W-14 | POST `/api/v1/orgs/{org_id}/networks` | `createOrgNetwork` | `paths[/api/v1/orgs/{org_id}/networks].post` | 15161 | `orgs/networks.py` (58) | 85 | verified-present | none | in scope, disabled |
| W-15 | PUT `/api/v1/orgs/{org_id}/networks/{network_id}` | `updateOrgNetwork` | `paths[/api/v1/orgs/{org_id}/networks/{network_id}].put` | 15322 | `orgs/networks.py` (145) | 173 | verified-present | none | in scope, disabled |
| W-16 | DELETE `/api/v1/orgs/{org_id}/networks/{network_id}` | `deleteOrgNetwork` | `paths[/api/v1/orgs/{org_id}/networks/{network_id}].delete` | 15279 | `orgs/networks.py` (117) | 141 | verified-present | 4645 scoped deletion | in scope, disabled |
| W-17 | POST `/api/v1/orgs/{org_id}/services` | `createOrgService` | `paths[/api/v1/orgs/{org_id}/services].post` | 18527 | `orgs/services.py` (58) | 85 | verified-present | none | in scope, disabled |
| W-18 | PUT `/api/v1/orgs/{org_id}/services/{service_id}` | `updateOrgService` | `paths[/api/v1/orgs/{org_id}/services/{service_id}].put` | 18611 | `orgs/services.py` (145) | 173 | verified-present | none | in scope, disabled |
| W-19 | DELETE `/api/v1/orgs/{org_id}/services/{service_id}` | `deleteOrgService` | `paths[/api/v1/orgs/{org_id}/services/{service_id}].delete` | 18566 | `orgs/services.py` (117) | 141 | verified-present | 4645 scoped deletion | in scope, disabled |
| W-20 | POST `/api/v1/orgs/{org_id}/servicepolicies` | `createOrgServicePolicy` | `paths[/api/v1/orgs/{org_id}/servicepolicies].post` | 18378 | `orgs/servicepolicies.py` (58) | 85 | verified-present | none | in scope, disabled |
| W-21 | PUT `/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` | `updateOrgServicePolicy` | `paths[/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}].put` | 18458 | `orgs/servicepolicies.py` (145) | 173 | verified-present | none | in scope, disabled |
| W-22 | DELETE `/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` | `deleteOrgServicePolicy` | `paths[/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}].delete` | 18413 | `orgs/servicepolicies.py` (117) | 141 | verified-present | D-4 and 4645 D-13 exclude it | excluded, no caller |

All SDK functions take `mist_session` as the first argument. The SDK file for each row lists the function line. The SDK call line names the session method (`mist_post`, `mist_put`, or `mist_delete`) and the URI variable.

## Payload and Behavior Evidence

Field status `partial` means the schema evidence exists and the synthetic fixtures are open. Behavior status `partial` means the declared responses exist, and the service behavior is unverified (see `research.md` Unverified items).

Every write operation declares the responses 200, 400, 401, 403, 404, and 429. No write operation declares a 5xx response (U-03). No write operation sets `requestBody.required`. The empty request body is therefore not proven valid (U-06).

| ID | Request schema | Required fields | Unknown top-level fields | Success schema | Field status | Behavior status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| W-01 | `site` | `name` | accepted by schema | `site` (`id` not required) | partial | partial | Create returns a new object. Duplicate names need resolution. |
| W-02 | `site` | `name` | accepted by schema | `site` | partial | partial | `sitetemplate_id` allows null (D-8). Update semantics unverified (U-02). |
| W-03 | `inventory_update` | `op` | accepted by schema | `response_org_inventory_change` | partial | partial | `op` enum: assign, delete, downgrade_to_jsi, unassign, upgrade_to_mist. Warning: `delete` removes inventory and unassigns devices. |
| W-04 | `mist_device` (one of ap, gateway, switch) | `type` | rejected (additionalProperties false) | `mist_device` | partial | partial | Type constants are read-only in the schema. |
| W-05 | `gateway_template` | `name` | accepted by schema | `gateway_template` (`id` not required) | partial | partial | Verified fields: `name`, `type`, `dns_servers` (D-12). |
| W-06 | `gateway_template` | `name` | accepted by schema | `gateway_template` | partial | partial | Same verified fields as W-05. |
| W-07 | none | none | not applicable | none (200 OK, no content) | not applicable | partial | Deletes a gateway template. |
| W-08 | `deviceprofile` (one of ap, gateway, switch) | `type` for ap, `name` and `type` for gateway and switch | rejected (additionalProperties false) | `deviceprofile` | partial | partial | List bodies refused (D-7). The schema rejects a list. |
| W-09 | `deviceprofile` (one of ap, gateway, switch) | `type` for ap, `name` and `type` for gateway and switch | rejected (additionalProperties false) | `deviceprofile` | partial | partial | Same rules as W-08. |
| W-10 | none | none | not applicable | none (200 OK, no content) | not applicable | partial | Deletes a device profile. |
| W-11 | `mac_addresses` | `macs` | accepted by schema | `response_assign_success` | partial | partial | `macs` needs at least one unique string. No MAC pattern (A-09). |
| W-12 | `mac_addresses` | `macs` | accepted by schema | `response_assign_success` | partial | partial | Same rules as W-11. |
| W-13 | `site_setting` | none | accepted by schema | `site_setting` | partial | partial | 102 properties. Inheritance effect unverified (U-17). |
| W-14 | `network` | `name` | accepted by schema | `network` (`id` not required) | partial | partial | `vlan_id` is a string or an integer from 1 to 4094. |
| W-15 | `network` | `name` | accepted by schema | `network` | partial | partial | Same rules as W-14. |
| W-16 | none | none | not applicable | none (200 OK, no content) | not applicable | partial | Deletes a network. Reference reads R-12 to R-14 apply. |
| W-17 | `service` | none | accepted by schema | `service` (`id` not required) | partial | partial | No required field in schema. Local rule requires `name` (D-18). |
| W-18 | `service` | none | accepted by schema | `service` | partial | partial | Same rules as W-17. |
| W-19 | none | none | not applicable | none (200 OK, no content) | not applicable | partial | Deletes a service. Reference reads R-15 and R-16 apply. |
| W-20 | `org_service_policy` | none | accepted by schema | `org_service_policy` (`id` not required) | partial | partial | No required field in schema. Local rule requires `name` (D-18). |
| W-21 | `org_service_policy` | none | accepted by schema | `org_service_policy` | partial | partial | Same rules as W-20. |
| W-22 | none | none | not applicable | none (200 OK, no content) | not applicable | partial | Excluded (D-4). Warning: deletes a production service policy. |

## Verified Field Set for the Gateway Template

Families F-04 and F-05 send only these fields (D-12):

| Field | Schema pointer | Type and constraint | Meaning from the schema |
| --- | --- | --- | --- |
| `name` | `components.schemas.gateway_template.properties.name` | string, required | Display name of the gateway template |
| `type` | `components.schemas.gateway_template.properties.type` | enum `spoke` or `standalone`, default `standalone` | Deployment type of the template |
| `dns_servers` | `components.schemas.gateway_template.properties.dns_servers` | array of strings | Global DNS settings. The `ip_config` and `oob_ip_config` DNS settings overwrite this list (A-20). |

The converter model (`models.py`, lines 13 to 18) and the converter proposal (`conversion.py`, line 15) use the same three fields (RV-11 and RV-08).

## Discovery Notes

- Each contract row cites one SDK function. The SDK functions match the OpenAPI verb and path for all 22 rows (checked by test 12 in the planned tests).
- The SDK annotates the create and assign functions as accepting a dictionary or a list. The OpenAPI file declares objects only (A-22). Decision D-7 refuses lists.
- The parity contract omits W-22. This change adds it as excluded (A-02).
