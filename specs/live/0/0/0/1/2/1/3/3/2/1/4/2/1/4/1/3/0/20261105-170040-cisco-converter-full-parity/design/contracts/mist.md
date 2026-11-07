# Mist Contract Evidence and Write Gates

## Authority and Scope

Use `documentation/mist-api-openapi31json.json` from the recorded MistHelper revision.
Use the installed `mistapi` signatures, not remembered signatures or the source mapping document.
Use independent request and response fixtures.
The current inspection found operation identifiers for templates, profiles, sites, settings, devices, networks, services, and policies.
SDK 0.64.1 exposes candidate methods below.
Presence and signatures do not verify payload fields, hardware support, inheritance, or safe retries.
All payload and failure contracts remain pending.

Context7 documentation for `/tmunzer/mistapi_python` confirmed the general session/path/body pattern and response-status requirement.
That documentation is supplementary. The installed package and target OpenAPI remain the contract evidence.
Do not enable verbose SDK request logging with credentials during tests.

## Candidate SDK Inventory

Every call supplies `mist_session` first.
List calls use explicit `limit` and `page` when available.
No feature call may forward arbitrary `*args` or `**kwargs`.

| Module after `mistapi.api.v1.` | Methods inspected | Required explicit arguments after session |
| --- | --- | --- |
| `const.device_models` | `listDeviceModels` | None |
| `orgs.sites` | `listOrgSites`, `createOrgSite` | `org_id`, list pagination or create `body` |
| `sites.sites` | `updateSiteInfo` | `site_id`, `body` |
| `orgs.inventory` | `getOrgInventory` | `org_id`, `type`, `site_id` or `unassigned`, pagination |
| `orgs.inventory` | `updateOrgInventoryAssignment` | `org_id`, `body` |
| `sites.devices` | `listSiteDevices`, `getSiteDevice`, `updateSiteDevice` | `site_id`, explicit list `type`, or `device_id` and update `body` |
| `orgs.gatewaytemplates` | `listOrgGatewayTemplates`, `getOrgGatewayTemplate`, `createOrgGatewayTemplate`, `updateOrgGatewayTemplate`, `deleteOrgGatewayTemplate` | `org_id`, pagination, `gatewaytemplate_id`, or approved `body` as applicable |
| `orgs.deviceprofiles` | `listOrgDeviceProfiles`, `getOrgDeviceProfile`, `createOrgDeviceProfile`, `updateOrgDeviceProfile`, `deleteOrgDeviceProfile` | `org_id`, explicit gateway `type`, pagination, `deviceprofile_id`, or approved `body` |
| `orgs.deviceprofiles` | `assignOrgDeviceProfile`, `unassignOrgDeviceProfile` | `org_id`, `deviceprofile_id`, approved scoped `body` |
| `sites.setting` | `getSiteSetting`, `updateSiteSettings` | `site_id`, update `body` |
| `orgs.networks` | `listOrgNetworks`, `getOrgNetwork`, `createOrgNetwork`, `updateOrgNetwork`, `deleteOrgNetwork` | `org_id`, pagination, `network_id`, or approved `body` |
| `orgs.services` | `listOrgServices`, `getOrgService`, `createOrgService`, `updateOrgService`, `deleteOrgService` | `org_id`, pagination, `service_id`, or approved `body` |
| `orgs.servicepolicies` | `listOrgServicePolicies`, `getOrgServicePolicy`, `createOrgServicePolicy`, `updateOrgServicePolicy` | `org_id`, pagination, `servicepolicy_id`, or approved `body` |

Initial candidate names `orgs.sites.updateOrgSite` and `orgs.inventory.updateOrgInventory` were absent.
Use the inspected `sites.sites.updateSiteInfo` and `orgs.inventory.updateOrgInventoryAssignment` candidates instead.
An initial `_constants` import was invalid. The inspected model method is `const.device_models.listDeviceModels`.
These corrections are inspection findings, not product defects.
Do not create an alternate HTTP transport for an incorrect method name.

## Write Operation and Schema Inventory

The target OpenAPI and installed SDK were inspected without a cloud session.
The installed version was 0.64.1.
Each row below remains **blocked** for use until its payload, response, permission, and recovery evidence passes G2 and G4.
The schema names below are under `#/components/schemas/`.
The SDK prefix is `mistapi.api.v1.` and each signature starts with `mist_session`.
The OpenAPI request bodies did not declare `required: true`.
This absence does not establish that an empty body is valid.

| OpenAPI method and path | Operation ID and SDK module | Arguments after session | JSON schema |
| --- | --- | --- | --- |
| POST `/api/v1/orgs/{org_id}/sites` | `createOrgSite`, `orgs.sites` | `org_id, body: dict \| list` | `site` |
| PUT `/api/v1/sites/{site_id}` | `updateSiteInfo`, `sites.sites` | `site_id, body: dict` | `site` |
| PUT `/api/v1/orgs/{org_id}/inventory` | `updateOrgInventoryAssignment`, `orgs.inventory` | `org_id, body: dict` | `inventory_update` |
| PUT `/api/v1/sites/{site_id}/devices/{device_id}` | `updateSiteDevice`, `sites.devices` | `site_id, device_id, body: dict` | `mist_device` |
| POST `/api/v1/orgs/{org_id}/gatewaytemplates` | `createOrgGatewayTemplate`, `orgs.gatewaytemplates` | `org_id, body: dict \| list` | `gateway_template` |
| PUT `/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}` | `updateOrgGatewayTemplate`, `orgs.gatewaytemplates` | `org_id, gatewaytemplate_id, body: dict` | `gateway_template` |
| DELETE `/api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}` | `deleteOrgGatewayTemplate`, `orgs.gatewaytemplates` | `org_id, gatewaytemplate_id` | None |
| POST `/api/v1/orgs/{org_id}/deviceprofiles` | `createOrgDeviceProfile`, `orgs.deviceprofiles` | `org_id, body: dict \| list` | `deviceprofile` |
| PUT `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` | `updateOrgDeviceProfile`, `orgs.deviceprofiles` | `org_id, deviceprofile_id, body: dict` | `deviceprofile` |
| DELETE `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` | `deleteOrgDeviceProfile`, `orgs.deviceprofiles` | `org_id, deviceprofile_id` | None |
| POST `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/assign` | `assignOrgDeviceProfile`, `orgs.deviceprofiles` | `org_id, deviceprofile_id, body: dict \| list` | `mac_addresses` |
| POST `/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}/unassign` | `unassignOrgDeviceProfile`, `orgs.deviceprofiles` | `org_id, deviceprofile_id, body: dict \| list` | `mac_addresses` |
| PUT `/api/v1/sites/{site_id}/setting` | `updateSiteSettings`, `sites.setting` | `site_id, body: dict` | `site_setting` |
| POST `/api/v1/orgs/{org_id}/networks` | `createOrgNetwork`, `orgs.networks` | `org_id, body: dict \| list` | `network` |
| PUT `/api/v1/orgs/{org_id}/networks/{network_id}` | `updateOrgNetwork`, `orgs.networks` | `org_id, network_id, body: dict` | `network` |
| DELETE `/api/v1/orgs/{org_id}/networks/{network_id}` | `deleteOrgNetwork`, `orgs.networks` | `org_id, network_id` | None |
| POST `/api/v1/orgs/{org_id}/services` | `createOrgService`, `orgs.services` | `org_id, body: dict \| list` | `service` |
| PUT `/api/v1/orgs/{org_id}/services/{service_id}` | `updateOrgService`, `orgs.services` | `org_id, service_id, body: dict` | `service` |
| DELETE `/api/v1/orgs/{org_id}/services/{service_id}` | `deleteOrgService`, `orgs.services` | `org_id, service_id` | None |
| POST `/api/v1/orgs/{org_id}/servicepolicies` | `createOrgServicePolicy`, `orgs.servicepolicies` | `org_id, body: dict \| list` | `org_service_policy` |
| PUT `/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` | `updateOrgServicePolicy`, `orgs.servicepolicies` | `org_id, servicepolicy_id, body: dict` | `org_service_policy` |

These are candidates, not an approved execution sequence.
Each operation declares 200, 400, 401, 403, 404, and 429 responses in the inspected OpenAPI.
The presence of these responses does not prove complete failure behavior.
No field-level mapping, destructive side effect, retry guarantee, or live API behavior was verified.
Any required operation absent from this inventory must stay blocked until T003 records its exact evidence.

## Required Mapping Evidence

| Family | Evidence needed before conversion or write |
| --- | --- |
| Role and object placement | Branch/Standalone template type, Hub profile type, site association, and device assignment |
| Hardware and ports | Current model inventory, SRX/SSR capabilities, port identifiers, VLAN, aggregation, WAN/LAN, and redundancy |
| Addresses and routing | IPv4/IPv6 limits, valid masks, DHCP/exclusions, routes, BGP, VRF, variables, and inheritance |
| Management | DNS/NTP overrides, syslog placement, SNMP, egress policy, and site/device/profile differences |
| Identity and security | AAA/TACACS/local-account field support, privilege intent, secret handling, ACL/policy/zone/crypto limits |
| Cellular and flow export | Parser-only review versus verified target support. No unapproved raw device commands |
| Administration | Complete pagination, references, restore matching, permitted deletion, and assignment removal semantics |

Record the OpenAPI path, operation ID, schema pointer, valid values, rejected values, SDK signature, and test name for every generated field.
Preserve unrelated settings during updates.
Reject unknown fields instead of forwarding source parser dictionaries.
Do not assume a generic `body: dict` signature validates a body schema.
Reinspect signatures after a dependency update.

S4 contains inconsistent syslog placement statements and references an older SDK.
Verify placement and inheritance independently for each role.
Do not automatically clear site template associations when switching to Hub.
That removal must be a separately visible, backed-up, approved change.

## Discovery and Approval

Treat unavailable, denied, failed, pending, stale, and verified cloud checks as different states.
Paginate all site, inventory, template, profile, network, service, and policy lists.
Verify organization and site membership for every selected gateway ID.
Show hostname matches as suggestions only.
Duplicate names require explicit conflict resolution.
No preview or lookup may create objects.

Before a write, verify operator permission, owner-enabled operation family, current proposal digest, scope digest, and exact typed word.
Verify current cloud before-state and complete private backups.
If state changed, stop and require a new proposal.
The exact `APPLY` word applies to migration writes.
The exact `CONFIRM` word follows a separate scope confirmation for administrative writes.
A browser control is not a server authorization boundary.

## Execution and Unknown Results

Create an operation record before the first approved write.
Serialize competing writes to the same object scope through an approved existing service.
Define bounded lock lifetime, ownership, renewal, and release in contract tests.
Use natural object IDs and operation identity to detect duplicates.
Do not rely on name-only matching.

Use bounded exponential backoff for eligible read requests and verified repeat-safe operations.
Honor rate-limit timing.
A timeout, connection loss, malformed success response, or missing created-object ID can leave a write result unknown.
Stop automatic write retries in that state.
Reconcile through read-only lookup and recorded object evidence.
A new write requires refreshed state and approval.
Show per-object verified, failed, partial, or indeterminate outcomes.

## Backup and Recovery

Capture complete before-state and relationship data before destructive updates.
Verify checksums, organization, object family, schema version, count, and pagination completeness.
Preserve private secret-bearing recovery material without exposing it through normal exports.
A refused backup or failed verification blocks the write.

Recovery uses object IDs and the operation record, not a blind full-organization overwrite.
Preserve objects created or changed by another operator after the backup.
Propose reverse changes only where current state and recorded outcomes prove the change belongs to this operation.
Never delete an object merely because it does not appear in a backup.
Stop on conflict or uncertain ownership.
Require fresh owner-enabled scope, operator review, confirmation, and recovery backups.
Verify readback after each recovery action.
Report irreversible effects and failed recovery explicitly.

## Contract Test Requirements

Each method family needs successful status/data fixtures and 4xx, 5xx, 429, timeout, malformed-response, and pagination tests.
Each write family needs zero-call tests for every approval refusal.
Test duplicate submission, cross-session scope, stale state, changed proposals, backup failure, partial write, and unknown result.
Test redaction in HTTP responses, browser output, exports, operation summaries, and logs.
Use no production credentials, real customer configurations, live Mist requests, or copied source tests.
G2 and G4 remain closed until this evidence and owner decisions exist.
