# Contract: Operator messages for menus 213 and 214

## Scope

This contract lists the operator-visible messages that the two site exports write through the logger. The menu handlers are `SiteApplicationListExporter.application_list` (menu 213) and `SiteSystemEventsExporter.system_events` (menu 214). The persistence methods are `_persist_applications` and `_persist_system_events`.

The quoted text is exact. Do not change a quoted string.

## Application list export (menu 213)

| Level | Condition | Exact text | Source |
| - | - | - | - |
| INFO | Menu header | `Site Application List:` | `site_application_list_exporter.py` line 83 |
| INFO | Before the API call | `Starting the getSiteApplicationList export`, followed by three periods | line 84 |
| INFO | Before the API call, per site | `Calling getSiteApplicationList for site_id=%s (%s)` | line 90 |
| INFO | No rows returned | `! No application data found for this site` | line 57 |
| INFO | Before the write | `Writing getSiteApplicationList rows to %s` | line 62 |
| ERROR | Writer returns `False` | `getSiteApplicationList failed to write %d rows to %s` | line 67 |
| DEBUG | Writer returns `True` | `getSiteApplicationList persisted %d rows to %s` | line 70 |
| INFO | Writer returns `True` | `! %d application records exported to %s` | line 72 |
| ERROR | Menu catches an exception | `Error fetching the application list for site %s: %s` | line 97 (module `logging`) |
| INFO | Menu catches an exception | `! Error fetching application list data: %s` | line 98 (module `logging`) |

## System event export (menu 214)

| Level | Condition | Exact text | Source |
| - | - | - | - |
| INFO | Menu header | `Site System Event Search:` | `site_system_events_exporter.py` line 83 |
| INFO | Before the API call | `Starting the searchSiteSystemEvents export`, followed by three periods | line 84 |
| INFO | Before the API call, per site | `Calling searchSiteSystemEvents for site_id=%s (%s)` | line 90 |
| INFO | No rows returned | `! No system event data found for this site` | line 57 |
| INFO | Before the write | `Writing searchSiteSystemEvents rows to %s` | line 62 |
| ERROR | Writer returns `False` | `searchSiteSystemEvents failed to write %d rows to %s` | line 67 |
| DEBUG | Writer returns `True` | `searchSiteSystemEvents persisted %d rows to %s` | line 70 |
| INFO | Writer returns `True` | `! %d system event records exported to %s` | line 72 |
| ERROR | Menu catches an exception | `Error fetching system events for site %s: %s` | line 97 (module `logging`) |
| INFO | Menu catches an exception | `! Error fetching system event data: %s` | line 98 (module `logging`) |

## Rules

1. A failed write logs exactly one ERROR message. The message names the endpoint and the output filename.
2. A failed write logs no DEBUG `persisted` message and no INFO `exported` message.
3. A successful write logs the DEBUG `persisted` message and the INFO `exported` message in this order.
4. An empty response logs the empty notice only. The writer is not called.
5. A menu exception logs the two error lines. The menu returns `None`.
6. Filenames follow the pattern `SiteApplicationList_<site>.csv` and `SiteSystemEvents_<site>.csv`. Spaces in the site name become underscores.

## Evidence

- The message lines come from the two exporter files on `main` (blob SHAs in `design/research.md`, rows 1 and 2).
- The test assertions for these messages are in `tests/unit/export/test_site_asset_and_events_exporters.py` lines 369-374, 394-397, 410-414, and 434-435.
