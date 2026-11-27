# Contract: Menu 58 and Menu 187 Messages

The messages below appear in the operator log. Each example uses the values of one run. The prompts and the menu categories do not change.

## Menu 58: export

| Case | Level | Message example |
| --- | --- | --- |
| Start | info | `Menu 58: Starting org config export` |
| Fetch start for each type | info | `Fetching Networks from org 00000000-0000-0000-0000-000000000001` |
| Verified type | warning | `    Networks: 1 objects` |
| Refused response | error | `  X Networks: Not verified for org 00000000-0000-0000-0000-000000000001 (refused, HTTP 503)` |
| Unavailable response | error | `  X Networks: Not verified for org 00000000-0000-0000-0000-000000000001 (unavailable)` |
| Invalid payload | error | `  X Networks: Not verified for org 00000000-0000-0000-0000-000000000001 (invalid, HTTP 200)` |
| Exception | error | `  X Networks: Request failed for org 00000000-0000-0000-0000-000000000001 (exception, RuntimeError)` |
| Stop with unverified types | error | `Menu 58: Export stopped. Not verified: Networks, Services. No bundle was saved.` |
| Success | info | `Menu 58: Export complete.` |

The stop message lists the display names in the order of the configuration type list. The message does not show a file name.

## Menu 58: stopped run output

When the export stops, the run prints no summary table. The operator sees the per-type error lines and the stop message only.

## Menu 187: import

| Case | Level | Message example |
| --- | --- | --- |
| Start | info | `Menu 187: Starting org config import` |
| Rejected bundle, legacy schema | error | `  X Invalid bundle: the bundle format is not schema 1.1` |
| Rejected bundle, no fetch status | error | `  X Invalid bundle: the bundle holds no fetch status` |
| Rejected bundle, unverified types | error | `  X Invalid bundle: not verified: services, vpns` |
| Instruction after rejection | info | `Re-run Menu 58 from the source organization to create a verified bundle.` |
| Destination not verified | error | `Menu 187: Import stopped. Destination not verified: Networks. No object was created.` |

The prompts stay unchanged:

- `Run as dry-run (preview only)? [Y/n]:`
- `Type 'IMPORT' to proceed:`

## Rules for every message

- Use ASCII characters only.
- Do not show a response body, a token, or exception text.
- Show the organization identifier only in the fetch lines.
- Use the display names from the configuration type list for the type names.
