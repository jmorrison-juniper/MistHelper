# Contract: Router request for lab checks L-SSR-STABLE, L-SSR-BETA, and L-SSR-ALPHA

## Operation

- Route: `POST /api/v1/orgs/{org_id}/ssr/upgrade` (OpenAPI line 20956, RC-63). The operation is `upgradeOrgSsrs` (operation identifier at line 20982).
- SDK function: `mistapi.api.v1.orgs.ssr.upgradeOrgSsrs`, defined at `.venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py` line 114 (RC-116).
- Request schema: `ssr_upgrade_multi`, lines 105332 to 105372 (RC-75). The channel enum is at line 105326 (RC-74). The strategy enum is at line 105359 (RC-77).
- Job read: `GET /api/v1/orgs/{org_id}/ssr/upgrade` (OpenAPI line 20956 block, operation identifier listOrgSsrUpgrades at line 20960, RC-65). The description at line 20958 names the release channel of each job (RC-64). The SDK function is `listOrgSsrUpgrades` (orgs/ssr.py line 89, RC-115).
- Warning: do not use `getOrgSsrUpgrade` for the job read. The installed function requests the cancel path (orgs/ssr.py line 167, RC-117).
- Caution: a router can reboot during the job, and the site network can drop during the reboot.

## Request body

Each check sends one body. Only the channel value changes between the three checks.

| Field | Type | Value | Source |
| - | - | - | - |
| device_ids | array with one UUID string | one lab router identifier, supplied by the owner | Schema ssr_upgrade_multi (RC-75). The schema allows one router. |
| channel | string | `stable` for L-SSR-STABLE, `beta` for L-SSR-BETA, or `alpha` for L-SSR-ALPHA | Enum at line 105326 (RC-74) |
| strategy | string | `big_bang` | Enum big_bang and serial at line 105359 (RC-77) |

The body omits these fields on purpose:

- `version`. The multi-device schema has no default for version (RC-75 block). The single-device schema defaults version to stable (RC-73). Omitting the field keeps the answer about the channel word only (D-13).
- `start_time`. The schema defaults the download start to now. A job that starts now is a Caution case for the owner.
- `reboot_at` and `force`.

Rule: an error that names another field leaves the verdict unknown. The owner repeats the call once with the named field and keeps both answers (EC-1).

## Responses

- `200` returns an upgrade job reference. The owner does not post the reference (see the lab answer record).
- `400`, `401`, `403`, `404`, and `429` are error responses that the operation names (OpenAPI line 20956 block).
- Any other status leaves the verdict unknown (EC-2).

## Example of the body shape

The shape uses type names, not values. The owner supplies the values outside the repository.

```text
{"device_ids": array of one UUID string, "channel": string, "strategy": string}
```
