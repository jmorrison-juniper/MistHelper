# Contract: Status rows for MSP sources

## Identity

- **File**: `CrossOrgOrganizationStatus.csv`, written by `CrossOrgSubscriptionInventoryReport` in `operation.py`.
- **Row type**: `OrganizationScope` in `model.py` (main line 94). The change keeps the row type unchanged.

## Columns (unchanged)

`org_id`, `org_name`, `msp_id`, `source`, `request_status`, `error`

The column order follows `dataclasses.asdict`, as `model.py` line 106 states.

## Status Values

| Value | Meaning | Origin |
| - | - | - |
| `success` | The organization read finished. | Existing |
| `partial` | The organization read finished with a missing source. | Existing |
| `failed` | A read or a listing call failed. | Existing |
| `unavailable` | A source was not available. | Existing |
| `skipped` | The report sent no listing call for the MSP source. | New in this change |

## Skipped Row

| Column | Value |
| - | - |
| `org_id` | `Missing` |
| `org_name` | `MSP` followed by the MSP id, with one space between them |
| `msp_id` | The MSP id |
| `source` | `msp` |
| `request_status` | `skipped` |
| `error` | The reason text from `msp-listing-right.md` |

## Rules

- The report writes one skipped row for each MSP id (D5).
- The skipped rows come first in the status file. The discovery failures start the list at `operation.py` line 534. The organization rows follow at line 567.
- A skipped row keeps the same field order as every other status row.

## Consumers

- The console summary counts `success` and `partial` as usable organizations. It counts `failed` and `unavailable` as failures.
- The console summary counts `skipped` in neither group. It excludes `skipped` from the "Organizations discovered" count (FR-008).
