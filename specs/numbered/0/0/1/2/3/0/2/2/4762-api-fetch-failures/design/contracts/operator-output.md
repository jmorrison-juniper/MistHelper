# Contract: Operator Output

## Rule

This table lists what an operator sees after a Mist read fails. The menu numbers come from the menu registry. Their line numbers are in `design/research.md` under Unverified item U-6.

## Output by Operation

| Operation | Menu or entry | Site read | Inventory or required read | Output after a failure |
| - | - | - | - | - |
| Devices with site info | Menu 10 | Optional | Required | A warning when the site read fails. An error when the inventory read fails. |
| Gateways with site info | Menu 11 | Optional | Required | A warning when the site read fails. An error when the inventory read fails. |
| Combined inventory with site info | Menu 12 | Optional through the same lookup | Required | A warning when the site read fails. An error when the inventory read fails. |
| Offline device report | Menu 26 | Optional | Required (device statistics) | A warning when the site read fails. The report shows `Unknown Site` in the device rows. |
| Site device statistics | Menu 61 | Optional (site name only) | Required (device statistics) | A warning when the site read fails. The file uses the site ID as the site name. |
| AP models by site | Menu 88 | Optional | Required (AP inventory) | A warning when the site read fails. The file keeps the AP rows and leaves the site detail fields empty. An error when the inventory read fails. |
| MSP inventory export | Menu 144 | Optional | Required (organization inventory is a direct reader, unchanged) | A warning from the site lookup. The devices keep the existing fallback text. |
| Switch, AP, and WAN scorecards | Scorecard menus | Optional (through `SiteNameLookup.fetch`) | Not applicable | A warning from the lookup. The rows keep the site IDs. |
| Organization site list | Site export menu | Required | Not applicable | An error. No empty file is written. |
| Zone analysis | Zone menu | Required | Not applicable | An error. The analysis stops. |
| CLI `--site` option | Command line | Required | Not applicable | The top-level entry logs the error and exits with code 1 (rows R57 and R58). |

## Menu Dispatcher

The menu dispatcher handles each unexpected exception (rows R59 and R60):

- In direct mode, the dispatcher logs the error with its traceback and exits with code 1 (row R61).
- In container mode, the dispatcher logs the error, prints the existing return-to-menu message, and returns to the menu.

Caution: a direct-mode operator loses the session after a required read fails. The operator must start the tool again. Unresolved item U-B in `analysis.md` records the owner review.

## Unchanged Output

The change does not change these outputs:

- Menu titles and menu text.
- CSV column names and file names.
- Successful output rows and their order.
