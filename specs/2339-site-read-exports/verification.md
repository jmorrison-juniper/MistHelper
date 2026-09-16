# Verification update

**Date:** 2026-09-16.
**Scope:** GitHub issue #2339, twenty site-read export plans.
**Live Mist requests:** None.
**SDK:** `mistapi` 0.64.0 from the worktree virtual environment.
**OpenAPI:** `documentation/mist-api-openapi31json.json` version 2607.1.1 with 756 paths.

## Result

Verified 20 of 20 planned endpoints.
Found 0 drift items.
The handoff is safe to hand off for implementation.
Implementation remains out of scope for this verification pass.

## Method

1. Imported each planned SDK module from `mistapi` 0.64.0.
2. Checked that each planned SDK function exists.
3. Compared the planned parameter names with `inspect.signature`.
4. Called each function with a fake session, so no network request occurred.
5. Compared the generated URI with the planned OpenAPI path.
6. Checked the OpenAPI `operationId` and the 200-response shape.
7. Checked each existing primary-key strategy and planned storage key.

## Endpoint evidence

| # | Issue | Operation | SDK | OpenAPI | URI | Response | Primary key | Storage key |
| - | - | - | - | - | - | - | - | - |
| 1 | #1313 | `listSiteAssetFilters` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 2 | #1314 | `listSiteAssets` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 3 | #1330 | `listSiteOtherDevices` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 4 | #1335 | `listSiteRssiZones` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 5 | #1357 | `listSiteWxRules` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 6 | #1358 | `listSiteWxTags` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 7 | #1359 | `listSiteWxTunnels` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 8 | #1323 | `listSiteEvpnTopologies` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 9 | #1307 | `listSiteAAMWProfilesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 10 | #1310 | `listSiteAntivirusProfilesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 11 | #1324 | `listSiteIdpProfilesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 12 | #1311 | `listSiteApTemplatesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 13 | #1319 | `listSiteDeviceProfilesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 14 | #1332 | `listSiteRfTemplatesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 15 | #1337 | `listSiteSecIntelProfilesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 16 | #1338 | `listSiteServicesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 17 | #1339 | `listSiteSiteTemplatesDerived` | present | present | match | array | `natural_pk ['id']` | `[site_id, id]` |
| 18 | #1328 | `listSiteMxEdgesStats` | present | present | match | array | `composite_pk ['id', 'mac']` | `[site_id, id, mac]` |
| 19 | #1336 | `listSiteRssiZonesStats` | present | present | match | array | `composite_pk ['id', 'map_id']` | `[site_id, id, map_id]` |
| 20 | #1360 | `listSiteZonesStats` | present | present | match | array | `composite_pk ['id', 'map_id']` | `[site_id, id, map_id]` |

## Drift report

No endpoint drift was found.

## Implementation split

Use several pull requests, not one large pull request.

1. Add the shared site-read catalog, service, storage checks, and family menu shell.
2. Add packets 1 through 7 for asset, third-party device, RSSI, and WxLAN reads.
3. Add packets 8 through 17 for EVPN and derived profile reads.
4. Add packets 18 through 20 for site statistics reads.
5. Update the README and close only source issues with passing acceptance tests.

## Issue disposition

Keep issue #2339 open until an authorized implementation completes the twenty exports.
This verification pass makes the handoff current, but it does not deliver the runtime feature.
