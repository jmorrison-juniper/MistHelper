# Contract: Mist Administration Calls

This contract lists each Mist call that the administration path may make. Each row cites the OpenAPI line and the installed SDK line. Each write stays blocked until issue 4634 verifies its row (gate G2) and the owner enables its family (gate G4).

## Authority and Rules

- OpenAPI evidence comes from `documentation/mist-api-openapi31yaml.yaml`. Its local hash equals the remote blob (RC-22). Line numbers apply to `main`.
- SDK evidence comes from the installed `mistapi` 0.64.1 package in `.venv\Lib\site-packages\mistapi`. Each function takes `mist_session` first (RC-59 to RC-70).
- Each call passes explicit arguments. The code does not forward `*args` or `**kwargs` (FR-026).
- Direct HTTP to a Mist endpoint is prohibited. Each call uses one SDK function.
- No call uses a credential from a new source (A-7).

## Write Operations

| Family | Action | SDK function and module | OpenAPI path and operation line | SDK signature line | Request body | Read-back function | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `gateway_templates` | delete | `deleteOrgGatewayTemplate` in `orgs.gatewaytemplates`. Arguments: `org_id` and `gatewaytemplate_id`. | DELETE `/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}`. Path line 9905. Operation line 9909. | 117 in `gatewaytemplates.py` | None | `getOrgGatewayTemplate` (line 89 in `gatewaytemplates.py`) | Blocked until T003 and decision D-2 |
| `networks` | delete | `deleteOrgNetwork` in `orgs.networks`. Arguments: `org_id` and `network_id`. | DELETE `/api/v1/orgs/{org_id}/networks/{network_id}`. Path line 15275. Operation line 15279. | 117 in `networks.py` | None | `getOrgNetwork` (line 89 in `networks.py`) | Blocked until T003 and decision D-2 |
| `services` | delete | `deleteOrgService` in `orgs.services`. Arguments: `org_id` and `service_id`. | DELETE `/api/v1/orgs/{org_id}/services/{service_id}`. Path line 18562. Operation line 18566. | 117 in `services.py` | None | `getOrgService` (line 89 in `services.py`) | Blocked until T003 and decision D-2 |
| `device_profile_unassign` | unassign | `unassignOrgDeviceProfile` in `orgs.deviceprofiles`. Arguments: `org_id`, `deviceprofile_id`, and `body`. | POST `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/unassign`. Path line 8399. Operation line 8405. | 214 in `deviceprofiles.py` | `{"macs": ["5c5b350e0001"]}`, with one or more unique MAC strings. Schema lines 84070 and 84079. | `getOrgDeviceProfile` (line 94 in `deviceprofiles.py`) and a device read (UV-06) | Blocked until T003 and decision D-2 |
| `site_template_unassign` | unassign (candidate) | `updateSiteInfo` in `sites.sites`. Arguments: `site_id` and `body`. | PUT `/api/v1/sites/{site_id}`. Path line 25952. Operation line 26004. Request schema `site` at line 26026. | 67 in `sites.py` | Candidate `{"sitetemplate_id": null}`. Unverified (UV-05). | No read row exists in the live inventory (gap) | Refused under FR-015 until decision D-3 and issue 4634 |

Out of scope and never called by this record:

| Operation | Reason | Evidence |
| --- | --- | --- |
| `deleteOrgServicePolicy` | Not approved. Decision D-13. | OpenAPI operation line 18413. SDK line 117 in `servicepolicies.py`. |
| `deleteOrgDeviceProfile` | Not in the issue scope. Decision D-13. | OpenAPI operation line 8144. SDK line 122 in `deviceprofiles.py`. |
| `deleteSite` | Not in the issue scope. Decision D-13. | OpenAPI path line 25952 covers `delete` for the site. |
| `updateOrgInventoryAssignment` with an unassign or delete operation | Not in the issue scope. Decision D-13. | Issue 4634 comment dated 2026-11-10 names the operation values. |

## Reference and Before-State Reads

| Purpose | SDK function | Evidence | Status |
| --- | --- | --- | --- |
| Gateway template before-state | `getOrgGatewayTemplate` | `gatewaytemplates.py` line 89 | Usable after T003 |
| Network before-state | `getOrgNetwork` | `networks.py` line 89 | Usable after T003 |
| Service before-state | `getOrgService` | `services.py` line 89 | Usable after T003 |
| Device profile before-state | `getOrgDeviceProfile` | `deviceprofiles.py` line 94 | Usable after T003 |
| Network reference lookup | `listOrgNetworkTemplates` | `networktemplates.py` line 17 | Blocked. Reference fields are unverified (UV-01). Pagination is unverified (UV-09). |
| Site state for the site-template path | None in the live inventory | Gap | Blocked until issue 4634 adds a verified read |

## Body Shapes

- `mac_addresses` requires the object `macs` (OpenAPI schema lines 84070 to 84077).
- `mac_addresses_macs` is an array of strings. It requires at least one item and unique items (lines 84079 to 84087).
- The run sends only the reviewed MAC addresses. An empty list returns 400 before a call (FR-013).

## Blocking Rules

- A family stays blocked until issue 4634 records each row above as `verified`.
- A family stays blocked until decision D-2 enables it in `CISCO_CONVERTER_ADMIN_FAMILIES`.
- A reference lookup that cannot verify a reference blocks the scope review (FR-007).
- A write with no verified read-back marks the object `indeterminate` (FR-016).
- No call repeats automatically (FR-017).

## Unknowns

Each unknown below remains open. Issue 4634 owns each one.

- Reference fields for gateway templates, networks, and services (UV-01).
- Mist behavior when a referenced object is deleted (UV-02).
- Response bodies and 5xx behavior for each delete and unassign call (UV-03).
- Partial MAC lists for `unassignOrgDeviceProfile` (UV-04).
- The null value for `sitetemplate_id` (UV-05).
- A MAC lookup for read-back (UV-06).
- Whether a 429 response changes state (UV-07).
- Pagination for reference lists (UV-09).
