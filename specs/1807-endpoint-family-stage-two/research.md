# Research: Endpoint family stage two

## Discovery Method

The discovery pass scanned the installed `mistapi` package source for function
definitions. It imported the resolved module and used `inspect.signature()` to
read the required parameters after `mist_session`.

The issue list came from open GitHub issues with titles that match the Mist API
endpoint pattern. The pass did not derive SDK modules from REST paths.

## Measured Counts

| Required identifier tuple | Operations |
| - | -: |
| `site_id, scope, scope_id, metric` | 14 |
| `site_id, map_id` | 5 |
| `msp_id, sso_id` | 4 |
| `org_id, nacportal_id` | 4 |
| `org_id, sso_id` | 4 |
| `org_id, upgrade_id` | 3 |
| `site_id, device_id` | 3 |
| `site_id, zone_id` | 3 |
| 74 other tuples | 84 |

The open endpoint issue list held 137 titles. The pass parsed 137 operation
names. It found 124 real operations with two or more required identifiers.

Stage two ships 134 read-only operations. This includes ten safe remaining
operations that stage one did not cover.

## Phantom and Safety Results

The pass found three entries that do not ship in stage two.

| Issue | Operation | Result |
| - | - | - |
| #991 | `endpoints` | Catalog issue, not an SDK operation. |
| #1369 | `searchOrgClientFingerprints` | Wrong spec name. Menu 261 ships `searchSiteClientFingerprints`. |
| #1366 | `optimizeInstallerRrm` | Active radio optimization endpoint, excluded from the read-only family. |

## Constraints

- Do not infer SDK modules from the endpoint URL.
- Do not use substring search to prove implementation.
- Do not include duplicate operation rows in the prompt table.
- Do not include unresolved operations.
- Do not include active or destructive operations in this read-only family.
