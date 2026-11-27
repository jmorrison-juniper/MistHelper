# Contract: Results File

This contract describes the results file that the resolve run writes. The file is `data\OrgMarvisActionsResolveResults.csv` (row 8). The results writer (row 13) writes it through the shared exporter. Each row describes one target action.

## Columns

The columns follow the field order of the results class (row 11). The file holds 26 columns.

| Position | Column | Meaning |
| - | - | - |
| 1 | `result_id` | The row key. It combines the action key and the run time. |
| 2 | `uuid` | The natural key of the action. |
| 3 | `row_key` | The key that the resolve body names. |
| 4 | `org_id` | The organization of the action. |
| 5 | `site_id` | The site of the action. |
| 6 | `site_name` | The site name for a reader. |
| 7 | `category` | The category key. |
| 8 | `category_name` | The category name for a reader. |
| 9 | `symptom` | The subcategory key. |
| 10 | `symptom_name` | The subcategory name for a reader. |
| 11 | `topic` | The pair key, such as `switch/sw_offline`. |
| 12 | `entity_names` | The names of the impacted devices. |
| 13 | `alarm_id` | The joined Marvis alarm identifier. |
| 14 | `previous_status` | The status before the run. |
| 15 | `resolution_code` | The key of the resolution code that the run sent. |
| 16 | `resolution_name` | The text of the resolution code. |
| 17 | `comment` | The comment that the run sent. |
| 18 | `outcome` | One outcome from the list below. |
| 19 | `http_status` | The HTTP status of the resolve request. Empty when no request went out. |
| 20 | `message` | The reason of the outcome. |
| 21 | `verified_status` | The status from the verify read. |
| 22 | `alarm_ack_outcome` | The result of the optional alarm acknowledge step. |
| 23 | `alarm_ack_http_status` | The HTTP status of the acknowledge request. |
| 24 | `alarm_ack_message` | The reason of the acknowledge result. |
| 25 | `resolve_time` | The run time in epoch milliseconds. |
| 26 | `resolve_time_iso` | The run time as readable text. |

## Outcome Values

The outcome column holds one of these values (row 10): `resolved`, `sent_unverified`, `error`, `not_sent`, or `skipped`. The interim value `sent` (row 9) is replaced by the verify step (row 12).

## Console Summary

The console prints one summary line with the count of each outcome in the order of the list above. A test asserts the format of the line (test 14 in the test set of `tasks.md`).

## Acceptance Reading

The live check reads three columns: `outcome`, `http_status`, and `verified_status`. Acceptance needs an HTTP 2xx status in `http_status`, the outcome `resolved` in `outcome`, and a verified status outside the open statuses (row 18).
