# Contract: Organization access point request for lab check L-AP-STABLE

## Operation

- Route: `POST /api/v1/orgs/{org_id}/devices/upgrade`. The operation is `upgradeOrgDevices` (documentation/mist-api-openapi31yaml.yaml line 9232, operation at line 9260).
- SDK function: `mistapi.api.v1.orgs.devices.upgradeOrgDevices`, defined at `.venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py` line 840 (RC-113).
- Job read: `GET /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` (OpenAPI line 9282, RC-61). The SDK function is `getOrgDeviceUpgrade` (devices.py line 871, RC-114).
- Caution: the access point can reboot during the job. Use a lab device only.

## Request body

The body holds only the fields in this table. Each field value is fixed except where the type says otherwise.

| Field | Type | Value for L-AP-STABLE | Source |
| - | - | - | - |
| all_sites | boolean | false | Schema upgrade_org_devices, lines 115954 to 116209 (RC-68) |
| device_type | string | ap | Schema upgrade_org_devices, lines 115954 to 116209 (RC-68) |
| site_ids | array of UUID strings | one lab site identifier, supplied by the owner | Schema upgrade_org_devices, lines 115954 to 116209 (RC-68) |
| versions | array | one object with firmware_type ap and version stable | Version entries at lines 116171 to 116209 (RC-68, RC-71) |

The `versions` object holds two fields. The field `firmware_type` has the value `ap`. The field `version` has the value `stable`. The optional field `force` is not sent.

The body omits these fields on purpose:

- `strategy`, `download_strategy`, `reboot_strategy`, `start_time`, and `start_datetime`. The top-level `strategy` field is deprecated (RC-70). The other fields add a second variable to the answer (D-13).
- Any canary, peer download, or radio batch field.

Rule: an error that names another field leaves the verdict unknown. The owner repeats the call once with the named field and keeps both answers (EC-1).

## Responses

- `200` returns an upgrade job reference. The job reference is the upgrade identifier. The owner does not post it (see the lab answer record).
- `400`, `401`, `403`, `404`, and `429` are error responses that the operation names (operation block at lines 9232 to 9281, RC-60).
- Any other status leaves the verdict unknown (EC-2).

## Example of the body shape

The shape uses type names, not values. The owner supplies the values outside the repository.

```text
{"all_sites": boolean, "device_type": string, "site_ids": array of UUID strings, "versions": array of objects}
```
