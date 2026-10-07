# Data Model: Menu 209 HTTP Error Handling

This feature adds no database schema. It defines transient response and result
states for the existing menu 209 workflow.

## Entity: Native Beacon Response

Represents the value returned by
`mistapi.api.v1.sites.beacons.getSiteBeacon`.

| Field | Type | Required | Rules |
| - | - | - | - |
| `status_code` | integer or other value | No | Accept integer 200-299. Fail every other integer. Continue for absent or non-integer values. |
| `url` | string or unavailable | No | Read only for an integer failure. Use `the requested path` when absent. |
| `data` | dictionary, list, `None`, or other value | No | Read only after successful or compatibility classification. |

### Validation

1. Inspect `status_code` before `data`.
2. Treat an integer status from 200 through 299 as success.
3. Treat every other integer status as failure.
4. Preserve current payload handling when the status is absent or non-integer.
5. Do not inspect the body to classify the response.

## Entity: HTTP Failure Signal

Represents the status-only operator failure from a failed response.

| Field | Type | Required | Rules |
| - | - | - | - |
| `status_code` | integer | Yes | Must be outside 200-299. |
| `url` | string | Yes | Use the response URL or the canonical fallback. |
| `operator_line` | string | Yes | Must equal `! Error fetching site beacon detail: HTTP <status> from <url>`. |

### Validation

1. Do not access or serialize the payload.
2. Do not access or log `data["detail"]`.
3. Do not include headers, request metadata, session data, tokens, or
   authorization data.

## Entity: Beacon Payload

Represents successful data that can enter the existing normalizer.

| Shape | Result |
| - | - |
| Dictionary | One normalized row |
| List | Existing dictionary-row filtering |
| `None` | Empty successful result |
| Unsupported value | Existing empty-result fallback |

### Validation

The payload can enter normalization only for integer 2xx, absent, or
non-integer status.

## Entity: Operation Result

Represents the visible outcome of menu 209.

| State | Entry condition | Export behavior | Operator behavior |
| - | - | - | - |
| `failed_http` | Integer status is outside 200-299 | No exporter call | Emit the exact status and URL line |
| `failed_exception` | SDK or runtime raises an exception | No exporter call | Preserve existing error handling |
| `successful_export` | Successful payload normalizes to one or more rows | Use existing exporter | Preserve current success message |
| `successful_no_data` | Successful payload normalizes to no rows | No exporter call | Preserve current no-data message |

## Entity: Export Artifact

Represents the unchanged successful output.

| Field | Value |
| - | - |
| Filename | `SiteBeacon_<site_id>_<beacon_id>.csv` |
| API function name | `getSiteBeacon` |
| Primary-key strategy | Natural key |
| Primary key | `id` |
| Output boundary | Existing `DataExporter.write_with_format_selection` path |

## Relationships

- One native beacon response produces one operation result.
- A failed HTTP response produces one HTTP failure signal.
- A successful native response can produce one beacon payload.
- A successful non-empty payload can produce one export artifact.
- A failed result or successful no-data result produces no export artifact.

## State Transitions

```text
SDK call
  |
  +-- raises RuntimeError containing 429 --> adaptive delay --> retry or failed_exception
  |
  +-- raises another exception ----------> failed_exception
  |
  +-- returns response
        |
        +-- integer status outside 2xx --> failed_http
        |
        +-- integer 2xx -----------------> read payload --> normalize
        |
        +-- absent or non-integer status -> read payload --> normalize
                                                   |
                                                   +-- rows --> successful_export
                                                   |
                                                   +-- empty -> successful_no_data
```

The `failed_http` transition must occur before payload access and
normalization.
