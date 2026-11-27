# Data Model: Marvis resolve refusal

## Entities

| Entity | Natural key | Source | Role in this change |
| - | - | - | - |
| Marvis Action | `uuid` (list record). The resolve request names it through `row_key`. | Mist list read | The target of one resolve request. Its state is open or closed. |
| Resolve run | `resolve_time` (epoch milliseconds, one value for each run) | Operator prompts and the clock | Holds the resolution code, the comment, and the time. The cap is `MARVIS_RESOLVE_MAX_ACTIONS`, default 500. |
| Resolve result row | `result_id` = the Marvis Action `uuid`, an underscore, and `resolve_time` | Written to `OrgMarvisActionsResolveResults.csv` | Holds `outcome`, `http_status`, `message`, and `verified_status`. |
| Refusal | Run state, set once for each run | The HTTP status of one resolve request | Holds the status, 401 or 403, and the masked error text of the request that set it. |

## Result outcome states

| From | Event | To | Terminal |
| - | - | - | - |
| Start | The row has no `row_key`. | `skipped` | Yes |
| Start | The stop signal arrived before the request. | `not_sent` | Yes |
| Start | A refusal of 401 or 403 arrived for an earlier request in the run. | `not_sent` | Yes |
| Start | The request gets HTTP 2xx. | `sent`, then the verify read | No |
| Start | The request gets a non-2xx status or no answer. | `error` | Yes |
| `sent` | The verify read shows a closed status. | `resolved` | Yes |
| `sent` | The verify read shows an open status, no status, or the read failed. | `sent_unverified` | Yes |

## Run state transitions

| From | Event | To |
| - | - | - |
| Running | HTTP 401 or HTTP 403 answers a request. | Refused. Later rows become `not_sent`. |
| Running | The stop signal arrives. | Stopped. Later rows become `not_sent`. |
| Running | The last target gets an answer. | Finished. |
| Refused | Any event | Refused. The run sends no request. |

## Natural key rules

- The result key `result_id` stays unique for each Marvis Action and each run.
- The Marvis Action key `uuid` stays the same across runs. The refusal does not change it.
- The request key `row_key` is copied from the list. The request does not change it.

## Unaffected fields

The results columns keep their names and order. The masked error text uses the existing `message` column. No column is added or removed.
