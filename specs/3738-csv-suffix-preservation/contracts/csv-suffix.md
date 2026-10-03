# CSV suffix contract

## Filename Decision

| Supplied target | CSV target |
| - | - |
| `SiteWiFiClients.csv` | `SiteWiFiClients.csv` |
| `SiteWiFiClients.CSV` | `SiteWiFiClients.CSV` |
| `SiteWiFiClients.Csv` | `SiteWiFiClients.Csv` |
| `SiteWiFiClients.cSv` | `SiteWiFiClients.cSv` |
| `SiteWiFiClients` | `SiteWiFiClients.csv` |
| `records.csv.backup` | `records.csv.backup.csv` |
| `records.json` | `records.json.csv` |
| `directory.csv/records` | `directory.csv/records.csv` |

All eight ASCII case combinations of the final suffix must pass.
Unicode filename content, stem case, and directory case remain unchanged.
A bare name uses the existing `data/` directory. An explicit path remains explicit.

The actual CSV writer retains its existing field order, string escaping,
UTF-8 encoding, and truncation behavior. Empty data creates no new output.
Existing non-string inputs remain refused at the existing boundary.

## Native Menu 64 Measurement

Use the actual `MistHelper.menu_actions["64"].handler`.
Use the shipped `WifiClientsExporter`, SDK endpoint functions, `APIResponse`,
CSV cache reader, and CSV writer. Control `mist_get` and the site answer only.

| Measurement | Required count |
| - | - |
| Handler runs | 1 |
| Site answers | 1 |
| Wireless client requests | 1 |
| Wireless session requests | 1 |
| Cache setup writes | 1 |
| Final client CSV writes | 1 |
| Final fake-router writes | 1 |
| Merged client records | 1 |
| Live HTTP requests | 0 |

The final record must retain the MAC, hostname, site ID, site name, session
count, SSID, and session timestamp. The router receives
`listSiteWirelessClientsStats`. The notice and menu title retain
`SiteWiFiClients.CSV`.

The output scanner reports the final client file. The browser lists it,
resolves it, reads its column names, and previews its complete record.
No browser or server process is necessary for these service contracts.

## Backend Preservation

SQLite retains these input-to-target values:

| Supplied target | SQLite constructor target |
| - | - |
| `SiteWiFiClients.csv` | `SiteWiFiClients` |
| `SiteWiFiClients.CSV` | `SiteWiFiClients.CSV` |
| `SiteWiFiClients.Csv` | `SiteWiFiClients.Csv` |
| `SiteWiFiClients` | `SiteWiFiClients` |

Preserve each constructor's data and API function name. Preserve all external
router data, raw-data selection, endpoint identity, and callback counts.
Run no real ArangoDB or Redis operation.

Preserve writer exceptions and the public boolean result. Existing error logs
must still name the failed target. A router error must not remove valid CSV data.

## Failure Proof

Before the repair, the native uppercase output contract must fail.
After the repair, that contract must pass.

Temporarily restore only the original case-sensitive suffix decision.
The uppercase actual-writer contract must fail again. Lowercase and bare-name
controls must still pass. Restore the repair before final quality checks.

## Source Boundary

Only `DataExporter._write_csv_format` may change its syntax tree.
Every other method remains equal to the immutable starting revision.
The schema, primary key strategy, path helper, client exporter, menu registry,
and existing tests remain byte-identical.
