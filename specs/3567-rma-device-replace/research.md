# Research: RMA Device Replacement

## Decision: Use the public Mist inventory replacement endpoint

Rationale: The OpenAPI document defines `replaceOrgDevices` as `POST /api/v1/orgs/{org_id}/inventory/replace`. It takes path parameter `org_id` and a JSON body named `replace_device`.

The request body schema has these fields:

- `site_id`: The site of the device to replace.
- `mac`: The MAC address of the device to replace.
- `inventory_mac`: The MAC address of the unassigned inventory device that replaces the old device.
- `discard`: A list of attributes that Mist must not copy.
- `tunterm_port_config`: Optional Ethernet port configurations.

The example body is:

```json
{
  "site_id": "4ac1dcf4-9d8b-7211-65c4-057819f0862b",
  "mac": "5c5b35000101",
  "inventory_mac": "5c5b35000301",
  "discard": []
}
```

Alternatives considered: Releasing and claiming devices was rejected because it loses the copied configuration.

## Decision: Use `getOrgInventory` for old and new device selection

Rationale: The OpenAPI document defines `getOrgInventory` as `GET /api/v1/orgs/{org_id}/inventory`. It takes path parameter `org_id` and query parameters `serial`, `model`, `type`, `mac`, `site_id`, `vc_mac`, `vc`, `unassigned`, `modified_after`, `limit`, and `page`. The `200` response is an array of `inventory` objects.

The inventory schema includes `id`, `mac`, `serial`, `model`, `type`, `site_id`, `name`, `org_id`, `connected`, `adopted`, and `deviceprofile_id`. The unassigned replacement filter uses records with no `site_id`. The client reads page one with `limit=1000`, which matches existing MistHelper inventory export practice.

The installed SDK has `mistapi.api.v1.orgs.inventory.getOrgInventory`. Its signature also includes `disconnected_before`, which the OpenAPI file does not list. The feature does not use that extra SDK parameter.

Alternatives considered: Calling `getOrgInventory` with `unassigned=true` only was rejected because the operation also needs old assigned devices.

## Decision: Use `getSiteDevice` for the old device backup

Rationale: The OpenAPI document defines `getSiteDevice` as `GET /api/v1/sites/{site_id}/devices/{device_id}`. It takes path parameters `site_id` and `device_id`. The `200` response references `mist_device`. The selected old inventory record supplies `site_id` and `id`.

The installed SDK has `mistapi.api.v1.sites.devices.getSiteDevice` with signature `(mist_session, site_id, device_id)`.

Alternatives considered: Backing up the inventory row only was rejected because the acceptance criteria require the old device configuration.

## Decision: Use the installed SDK for all three Mist calls

Rationale: The installed SDK exposes `getOrgInventory`, `getSiteDevice`, and `replaceOrgDevices`. The client can use SDK methods instead of raw `mist_get` and `mist_post` calls.

Alternatives considered: Direct `apisession.mist_post` was rejected because the SDK already exposes the operation.

## Decision: Use an empty discard list for the first version

Rationale: The assignment requires a request body with a discard list, but it does not require an operator prompt for fields to discard. An empty list copies all supported configuration by default.

Alternatives considered: A discard prompt was rejected because it adds a destructive choice outside the issue scope.

## Skill citations

- `juniper-mist-wired/09-wired-visibility-and-switch-management/03-switch-utilities-roles-remote-shell-and-replacement.md`: `Replace Switch` copies old switch configuration to an unassigned replacement. It requires the old switch to be claimed or adopted and assigned to a site. The replacement API path and payload are `POST /api/v1/orgs/:org_id/inventory/replace` with `site_id`, `mac`, `inventory_mac`, and `discard`.
- `juniper-mist-wireless/09-roaming-reason-codes-and-troubleshooting/04-ap-power-reboot-replace-reset-and-packet-capture.md`: AP replacement copies AP settings, WLANs, physical location, AP photos, and related settings. The replacement AP must be claimed and `Unassigned`. The API payload uses `site_id`, `mac`, and `inventory_mac`.
- `juniper-mist-wan/08-wan-edge-device-operations/02-upgrade-replace-dhcp-and-reservations.md`: A standalone WAN Edge replacement requires the old device to be claimed and adopted to the site. The new device must be in organization inventory and unassigned. Mist clones the old configuration, and the old device becomes unassigned.
- `juniper-mist-automation/01-rest-api-model/01-call-structure-and-http-methods.md`: The Mist API uses regional hosts and JSON over REST. A `POST` creates or changes the target object with a JSON payload.
- `juniper-access-assurance-nac/01-overview-use-cases/01-cloud-nac-reference-model.md`: The edge remains the enforcement point. The replacement operation must preserve device configuration that can carry NAC edge enforcement.
