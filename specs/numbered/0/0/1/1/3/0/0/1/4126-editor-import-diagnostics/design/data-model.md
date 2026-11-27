# Data Model: Editor Import Diagnostics

## Entities

### Affected file

One file that the issue lists. The natural key is the current path on `main`.

| Field | Meaning |
| - | - |
| `listed_path` | The path in the issue. Equals `current_path` when the file did not move. |
| `current_path` | The path on `main` at commit `f03c6c9b`. |
| `blob_sha` | The Git blob SHA of `current_path` on `main` (research rows R01 to R27). |
| `moved` | `true` when `listed_path` differs from `current_path`. |
| `issue_e0401` | The E0401 count that the issue reports for the file. |
| `issue_e0611` | The E0611 count that the issue reports for the file. |
| `live_state` | `open`, `verified`, `failed`, or `unverified`. |

### Evidence row

One observation of one affected file. The natural key is the issue number, the current path, and the UTC time of the observation. The output contract in `design/contracts/editor-evidence.md` lists its fields.

### Cited line

One line number from the issue and its content on `main`. The natural key is the path and the cited line number. Its status is `stale`, `absent`, or `present` (research rows R29 to R36).

## State Transitions

The `live_state` of an affected file changes as follows.

- `open` changes to `verified` when a live evidence row shows zero E0401 and zero E0611 with the Pylint source.
- `open` changes to `failed` when a live evidence row shows at least one E0401 or E0611 diagnostic.
- `open` changes to `unverified` when a native permission is missing or an interpreter is unavailable. The row records the cause.
- `failed` or `unverified` changes to `open` after the cause is fixed and the check repeats.
- `verified` changes to `open` when the current path changes, the Pylint extension version changes, or the worktree base changes.

## Affected File Set

The table lists the 27 affected files in the order of the issue. The E0401 and E0611 counts come from the issue body. The current paths and blob SHAs come from the remote tree (research rows R01 to R27). The blob SHA column shows the first eight characters. For rows 3, 4, 5, 7, 11, 15, 18, 19, 25, and 26, the listed path starts below the retired `src` root.

| # | Listed path | Current path | Moved | Blob SHA | Issue E0401 | Issue E0611 |
| - | - | - | - | - | - | - |
| 1 | `MistHelper.py` | `MistHelper.py` | no | 98d78284 | 172 | 179 |
| 2 | `web_portal/services/operation.py` | `web_portal/services/operation.py` | no | 39f9446d | 18 | 18 |
| 3 | `org/juniper_rma/workflows/correlation.py` | `src/operations/exporting/juniper_rma/workflows/correlation.py` | yes | 5687bf11 | 8 | 8 |
| 4 | `org/juniper_rma/workflows/asset_lookup.py` | `src/operations/exporting/juniper_rma/workflows/asset_lookup.py` | yes | d4e34076 | 7 | 7 |
| 5 | `org/juniper_rma/workflows/lookup.py` | `src/operations/exporting/juniper_rma/workflows/lookup.py` | yes | 58b5d099 | 7 | 7 |
| 6 | `tests/unit/juniper_rma/fixtures/fake_gateway.py` | `tests/unit/juniper_rma/fixtures/fake_gateway.py` | no | 13072a7b | 5 | 5 |
| 7 | `org/juniper_rma/settings.py` | `src/operations/exporting/juniper_rma/settings.py` | yes | 43667e5c | 4 | 5 |
| 8 | `tests/unit/juniper_rma/workflows/test_lookups.py` | `tests/unit/juniper_rma/workflows/test_lookups.py` | no | 779b9ae4 | 4 | 4 |
| 9 | `tests/unit/juniper_rma/api/test_asset_service.py` | `tests/unit/juniper_rma/api/test_asset_service.py` | no | 1296b016 | 4 | 4 |
| 10 | `tests/unit/juniper_rma/workflows/test_correlation.py` | `tests/unit/juniper_rma/workflows/test_correlation.py` | no | 77b38481 | 3 | 3 |
| 11 | `org/juniper_rma/workflows/access_check.py` | `src/operations/exporting/juniper_rma/workflows/access_check.py` | yes | ed39f4e1 | 3 | 3 |
| 12 | `tests/unit/juniper_rma/api/test_case_service.py` | `tests/unit/juniper_rma/api/test_case_service.py` | no | 4c484570 | 3 | 3 |
| 13 | `tests/unit/juniper_rma/workflows/test_access_check.py` | `tests/unit/juniper_rma/workflows/test_access_check.py` | no | ce27c701 | 3 | 3 |
| 14 | `tests/unit/juniper_rma/model/test_export_rows.py` | `tests/unit/juniper_rma/model/test_export_rows.py` | no | 13eca341 | 3 | 3 |
| 15 | `org/juniper_rma/api/case_service.py` | `src/operations/exporting/juniper_rma/api/case_service.py` | yes | 51f1042b | 2 | 2 |
| 16 | `tests/unit/juniper_rma/workflows/test_read_only_boundary.py` | `tests/unit/juniper_rma/workflows/test_read_only_boundary.py` | no | fdae6c9e | 2 | 2 |
| 17 | `tests/unit/juniper_rma/api/test_messages.py` | `tests/unit/juniper_rma/api/test_messages.py` | no | 8a04bc3b | 2 | 2 |
| 18 | `org/juniper_rma/api/asset_service.py` | `src/operations/exporting/juniper_rma/api/asset_service.py` | yes | 38283543 | 2 | 2 |
| 19 | `org/juniper_rma/model/export_rows.py` | `src/operations/exporting/juniper_rma/model/export_rows.py` | yes | 6d83f955 | 2 | 2 |
| 20 | `tests/unit/juniper_rma/api/test_gateway.py` | `tests/unit/juniper_rma/api/test_gateway.py` | no | 33cd8f17 | 2 | 2 |
| 21 | `tests/unit/juniper_rma/model/test_asset.py` | `tests/unit/juniper_rma/model/test_asset.py` | no | 82c41371 | 1 | 1 |
| 22 | `tests/unit/juniper_rma/model/test_run_record.py` | `tests/unit/juniper_rma/model/test_run_record.py` | no | 35326936 | 1 | 1 |
| 23 | `tests/unit/juniper_rma/model/test_service_request.py` | `tests/unit/juniper_rma/model/test_service_request.py` | no | 002ff367 | 1 | 1 |
| 24 | `tests/unit/test_menu_entry_metadata.py` | `tests/unit/test_menu_entry_metadata.py` | no | d9b4d79e | 1 | 1 |
| 25 | `org/juniper_rma/model/asset.py` | `src/operations/exporting/juniper_rma/model/asset.py` | yes | 97a26e5b | 1 | 1 |
| 26 | `org/juniper_rma/api/gateway.py` | `src/operations/exporting/juniper_rma/api/gateway.py` | yes | 9f857510 | 1 | 1 |
| 27 | `tests/unit/juniper_rma/api/test_settings.py` | `tests/unit/juniper_rma/api/test_settings.py` | no | 54102ec0 | 1 | 1 |

The issue reports 534 diagnostics in total. The counts above add up to 263 E0401 and 271 E0611, which is 534. Ten files moved. Seventeen files did not move.

## Natural Key Rule

Use the current path as the key in every evidence row. Do not use the listed path. A listed path that moved is a stale key.
