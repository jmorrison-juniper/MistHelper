# Research: CSV imports for PSKs, user MACs, and assets

## Mist API operation review

The feature reads `documentation/mist-api-openapi3json.json` and the generated API pages before it calls Mist.

| Operation ID | Method and path | Scope parameters | Query parameters | Request content in OpenAPI | SDK function to call | Response |
| - | - | - | - | - | - | - |
| `importOrgPsks` | `POST /api/v1/orgs/{org_id}/psks/import` | `org_id` path, required | none | `multipart/form-data` with `file` | `mistapi.api.v1.orgs.psks.importOrgPsksFile` | `200` returns a PSK array. |
| `importOrgUserMacs` | `POST /api/v1/orgs/{org_id}/usermacs/import` | `org_id` path, required | none | `multipart/form-data` with required `file` | `mistapi.api.v1.orgs.usermacs.importOrgUserMacsFile` | `200` returns an object with `added`, `updated`, and `errors` arrays. |
| `importOrgAssets` | `POST /api/v1/orgs/{org_id}/assets/import` | `org_id` path, required | none | `multipart/form-data` with `file` | `mistapi.api.v1.orgs.assets.importOrgAssetsFile` | `200` OK. |
| `importSitePsks` | `POST /api/v1/sites/{site_id}/psks/import` | `site_id` path, required | none | `multipart/form-data` with `file` | `mistapi.api.v1.sites.psks.importSitePsksFile` | `200` returns a PSK array. |
| `importSiteAssets` | `POST /api/v1/sites/{site_id}/assets/import` | `site_id` path, required | `upsert` optional | `multipart/form-data` with `file` | `mistapi.api.v1.sites.assets.importSiteAssetsFile` | `200` OK. |

The installed SDK also exposes JSON-body functions named `importOrgPsks`, `importOrgUserMacs`, `importOrgAssets`, `importSitePsks`, and `importSiteAssets`. The OpenAPI file and the `*File` functions agree on multipart file upload, so this feature uses the `*File` functions. No supported import endpoint is JSON-only in the checked OpenAPI file. The generated API pages say that PSK and asset imports can also be done with JSON payloads, but the accepted CSV workflow maps directly to the file-upload functions.

## CSV column findings

| Import type | Required columns | Optional columns from API examples |
| - | - | - |
| `org_psks` | `name`, `ssid`, `passphrase` | `usage`, `vlan_id`, `mac`, `max_usage`, `role`, `expire_time`, `notify_expiry`, `expiry_notification_time`, `notify_on_create_or_edit`, `email` |
| `site_psks` | `name`, `ssid`, `passphrase` | `usage`, `vlan_id`, `mac`, `max_usage`, `role`, `expire_time`, `notify_expiry`, `expiry_notification_time`, `notify_on_create_or_edit`, `email` |
| `org_user_macs` | `mac` | `labels`, `vlan`, `notes`, `name`, `radius_group` |
| `org_assets` | `name`, `mac` | none in the generated page example |
| `site_assets` | `name`, `mac` | none in the generated page example |

The asset visibility skill states that the portal CSV import for named assets uses `Asset Name` and `MAC Address`. The Mist API generated page for asset import uses `name` and `mac`, so the API import operation uses `name` and `mac`.

## Existing MistHelper CSV input rule

Menu 171 reads `NorthAmericanTestSites.csv` through `FilePathUtils.get_csv_path`, so the file is anchored under `data/`. Menu 162 reads `VCConvert.CSV` through the same helper. This feature follows the same rule and never reads a CSV outside `data/`.

## Skill citations

- `juniper-mist-wireless/05-wlan-security-radius-and-psk/02-security-types-psk-and-personal-wlans.md`: PSK keys can carry name, accountability, VLAN assignment, role assignment, rotation state, and local lookup has a `5000` key limit.
- `juniper-mist-location/06-asset-visibility/01-ble-clients-page-and-named-assets.md`: Named asset import exists on `Clients > BLE Clients` and uses a CSV workflow for asset names and MAC addresses.
- `juniper-access-assurance-nac/03-protocol-transport/01-radius-aaa-and-8021x-exchange.md`: MAB uses the MAC address as the device identity and can return `Access-Accept` with a VLAN assignment.
- `juniper-mist-automation/01-rest-api-model/01-call-structure-and-http-methods.md`: Mist API calls use `/api/v1/{scope}/{scope_id}/...`, and `POST` creates or overwrites target records.

## Decision log

1. Use SDK `*File` functions instead of JSON-body functions because the OpenAPI import schemas declare multipart CSV uploads.
2. Keep validation local and conservative. The operation checks required columns, but Mist remains the source of truth for row-level values.
3. Mask `passphrase` and `old_passphrase` in preview rows and all structured summaries.
4. Write the import log with the standard CSV module instead of the multi-backend exporter, because this is an audit log for a destructive operation and must always land in `data/CsvImportLog.csv`.
