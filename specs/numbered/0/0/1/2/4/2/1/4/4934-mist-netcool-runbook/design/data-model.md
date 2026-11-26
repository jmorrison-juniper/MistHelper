# Data model for feature 4934

This file defines the entities of the NOC runbook and of the read-only smoke test. The runbook describes the production collector. This feature does not implement the collector, so the collector entities are documentation only.

Each entity lists its fields, the type of each field, whether the field must have a value, and the validation rule. Each Netcool entity is a proposal until the Netcool administrator approves it.

## 1. Entity index

| Entity | Owner | Implemented by this feature | Section |
| --- | --- | --- | --- |
| OrganizationConfig | Integration engineer | No (runbook model) | 2 |
| CollectionWindow | Collector | No (runbook model) | 3 |
| Checkpoint | Collector | No (runbook model) | 4 |
| CollectionResult | Collector | No (runbook model) | 5 |
| NormalizedRecord | Collector | No (runbook model) | 6 |
| NetcoolEvent | Netcool administrator | No (proposal) | 7 |
| SmokeSettings | Smoke test | Yes | 8 |
| CallRecord | Smoke test | Yes | 9 |
| PageSet | Smoke test | Yes | 10 |
| CheckResult | Smoke test | Yes | 11 |
| EvidenceRecord | Smoke test | Yes (schema in `contracts/evidence.md`) | 12 |
| Outcome class | Smoke test | Yes (exit codes in `contracts/smoke-cli.md`) | 13 |

## 2. OrganizationConfig

An OrganizationConfig record describes one Mist organization that the feed reads. The record holds no token value. It names the secret manager entry that holds the token.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| logical_name | string | Yes | Lowercase letters, digits, and hyphens. Forty characters or fewer. Unique in the feed. |
| org_id | UUID string | Yes | Canonical form with lowercase hexadecimal digits. Written only as `{org_id}` in any committed file. |
| api_host | string | Yes | One host from the `servers` list of the OpenAPI file. Bare host name, no scheme and no path. |
| token_secret_ref | string | Yes | Name of the secret manager entry or environment variable. The value is never a token. |
| enabled_endpoint_families | list of enum | Yes | Each value is one of `alarms`, `device_events`, `mxedge_events`, `system_events`. No duplicate values. |
| ap_warning_report | enum | Yes | One of `not_configured`, `enabled`, `disabled`. Default: `not_configured` until the owner decides (runbook section 15). |

Validation rules:

- The feed rejects a record whose `api_host` is not in the OpenAPI `servers` list.
- The feed rejects a record whose `org_id` is not a UUID.
- The feed rejects a record whose `token_secret_ref` contains a value that looks like a token.

State transitions: none. A change to an enabled family or to `ap_warning_report` needs approval from the change approver.

## 3. CollectionWindow

A CollectionWindow is the time range that one poll reads for one organization and one endpoint family.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| org_id | UUID string | Yes | Refers to an OrganizationConfig record. |
| endpoint_family | enum | Yes | One of `alarms`, `device_events`, `mxedge_events`, `system_events`. |
| start_epoch_seconds | integer | Yes | Epoch seconds in UTC. Less than `end_epoch_seconds`. |
| end_epoch_seconds | integer | Yes | Epoch seconds in UTC. Equal to the current time minus the end lag. |
| end_lag_minutes | integer | Yes | Proposal. Default 2. The value is verified by the live run. |
| overlap_minutes | integer | Yes | Proposal. Default 5. The value is verified by the live run. |
| created_at_utc | string | Yes | UTC timestamp in ISO 8601 form, for example `2026-11-25T14:30:00Z`. |

Validation rules:

- The start value is the end value of the previous window minus the overlap.
- A window with a start value equal to or greater than its end value is invalid.
- The window never ends after the current time minus the end lag.

State transitions: `planned` to `running` when the first request starts. `running` to `closed` when the collector records a CollectionResult. `closed` to `replayed` when the operator runs the same bounds again.

## 4. Checkpoint

A Checkpoint is the end time of the last collection window that completed for one organization and one endpoint family. Its natural key is the pair of `org_id` and `endpoint_family`.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| org_id | UUID string | Yes | Part of the natural key. |
| endpoint_family | enum | Yes | Part of the natural key. |
| last_closed_window_end | integer | Yes | Epoch seconds in UTC. Equal to the end value of the successful window. |
| updated_at_utc | string | Yes | UTC timestamp in ISO 8601 form. |
| last_result_state | enum | Yes | One of the nine collection result states in section 5. |

Validation rules:

- Only `SUCCESS_WITH_RECORDS` and `SUCCESS_EMPTY` advance a checkpoint.
- A checkpoint never moves to an earlier time, including during a replay.
- A `PARTIAL_ORGANIZATION` result advances only the checkpoints of the families that succeeded.

State transitions: a successful collection moves the checkpoint forward. A failed collection leaves the checkpoint unchanged. The checkpoint recovery procedure replays the windows after the stored checkpoint.

## 5. CollectionResult

A CollectionResult records the outcome of one collection. Each collection has exactly one of the nine states below. Source of the meanings: Design decision of this feature, for the clarify items.

| State | Meaning | Advances checkpoint |
| --- | --- | --- |
| `SUCCESS_WITH_RECORDS` | Each page returned HTTP 200 with a valid body. The last page had no `next` value. The collection holds one record or more. | Yes |
| `SUCCESS_EMPTY` | The same as `SUCCESS_WITH_RECORDS`, with zero records. | Yes |
| `FAILED_HTTP` | A request ended with an HTTP status other than 200, 401, 403, or 429 after the allowed retries. Also used for a timeout and for a connection failure after the allowed retries. | No |
| `FAILED_AUTH` | HTTP 401 or HTTP 403. | No |
| `FAILED_THROTTLED` | HTTP 429 after the wait for `Retry-After` and at most one more attempt. Also used when the remaining requests of the hour are fewer than the requests of the next poll. | No |
| `FAILED_PARSE` | The body is not valid JSON, is empty, or has no `results` list. | No |
| `FAILED_INCOMPLETE_PAGINATION` | The collection stopped before the last page. The causes are the page ceiling, a foreign `next` origin, a repeated page, or missing pagination metadata. | No |
| `FAILED_DELIVERY` | The collection succeeded, but the delivery to Netcool or to the durable buffer failed. | No |
| `PARTIAL_ORGANIZATION` | One endpoint family or more of an organization failed while others succeeded. | Only for the families that succeeded |

Validation rules:

- No state creates a clear by absence. An empty result does not clear any open alarm.
- A production collector never caps pages silently. The page ceiling is a failure in a collector.
- The collector resets the parse state for each event.
- The production collector retries an HTTP 5xx response, a timeout, and a connection failure at most two times, with exponential backoff and jitter (Proposal).
- The collector reads the pagination metadata `next`, `total`, `limit`, `start`, and `end`.
- A last page without `next` while the record count is less than `total` gives `FAILED_INCOMPLETE_PAGINATION`.
- At the start of a shift, a healthy feed has a SUCCESS state for each organization and family.
- A SUCCESS state is `SUCCESS_WITH_RECORDS` or `SUCCESS_EMPTY`, and it is no older than two poll intervals (Proposal).
- A healthy feed at the start of a shift has a delivery backlog of zero (Proposal).

The smoke test does not emit these states. The smoke test uses the check statuses in section 11 and the outcome classes in section 13.

## 6. NormalizedRecord

A NormalizedRecord holds one Mist record in one common shape. The collector creates it before it creates a Netcool event.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| source_system | string | Yes | Fixed value `mist`. |
| source_endpoint_family | enum | Yes | One of `alarms`, `device_events`, `mxedge_events`, `system_events`. |
| organization_id | UUID string | Yes | Never written to evidence or to a committed file. |
| organization_name | string | No | Empty when the source response does not give it. |
| site_id | UUID string | No | Empty when the source response does not give it. |
| site_name | string | No | Empty when the source response does not give it. |
| device_id | string | No | Empty when the source response does not give it. |
| device_mac | string | No | Lowercase, colon-separated, six pairs of hexadecimal digits. |
| device_name | string | No | Empty when the source response does not give it. |
| device_type | enum | No | One of `ap`, `gateway`, `switch`, `mxedge`, `unknown`. |
| event_id | string | No | The alarm identifier for alarms. Empty for families without an identifier field. |
| event_type | string | Yes | The type key from the source record. |
| alarm_group | string | No | Alarms only. One of the alarm group values of the specification. |
| severity | string | Yes | The source value after the severity table of runbook section 9 (proposal). |
| state | enum | Yes | For alarms, `open` or `resolved`. For other families, `unknown`. |
| source_timestamp | string | Yes | UTC timestamp in ISO 8601 form, converted from the source epoch seconds. |
| collection_timestamp | string | Yes | UTC timestamp in ISO 8601 form, set when the collector reads the record. |
| summary | string | Yes | Text of 255 characters or fewer (proposal). |
| details | object | No | Redacted subset of the source fields. Never holds a token, a webhook URL, or a secret. |
| deduplication_key | string | Yes | Natural key. Section 6.1 gives the shape for each family. |
| correlation_key | string | No | Empty in the baseline. Set only when the correlation enhancement is approved. |
| raw_payload_reference | string | No | A reference to the raw payload in the durable buffer. The payload itself is not copied. |

### 6.1 Deduplication key shapes

The key is a natural key where the source gives one. The shapes below are proposals.

- Alarms: `alarm:{event_id}`. The alarm identifier is a UUID.
- Device events: `device:{device_mac}:{event_type}:{source_timestamp}`. The source has no identifier field.
- Mist Edge events: `mxedge:{mxedge_id}:{event_type}:{source_timestamp}`. The source has no identifier field.
- System events: `system:{org_id}:{site_id}:{event_type}:{source_timestamp}`. The site identifier is empty when the event has no site.

Validation rules:

- Each required field has a value that is not empty.
- Each timestamp field uses UTC.
- The parse state resets for each event (FR-014).

State transitions: `created` to `delivered` when delivery succeeds. `created` to `buffered` when delivery fails, and the record waits for replay.

## 7. NetcoolEvent (proposal)

A NetcoolEvent is one event that the feed sends to a Netcool probe. The field names are proposals. The mark `Verified (vendor documentation)` applies only to the Severity values, the Type values, and the deduplication facts. The receiver is an open decision (runbook section 15).

| Field | Type | Required | Rule (proposal) |
| --- | --- | --- | --- |
| Identifier | string | Yes | Equal to `deduplication_key`. Events deduplicate on this field. |
| Node | string | Yes | `device_name` when present, otherwise `device_mac`, otherwise the logical name of the organization. |
| NodeAlias | string | No | `device_mac` when present. |
| Manager | string | Yes | Fixed value that the Netcool administrator names. |
| Agent | string | Yes | Fixed value that the Netcool administrator names. |
| AlertGroup | string | Yes | `alarm_group` for alarms. The source family for other families. |
| AlertKey | string | Yes | Equal to `Identifier` until the Netcool administrator confirms the clear fields. |
| Severity | integer | Yes | 0 to 5, from the severity table of runbook section 9. |
| Summary | string | Yes | Equal to `summary`. |
| FirstOccurrence | string | Yes | Equal to `source_timestamp` of the first event with this `Identifier`. |
| LastOccurrence | string | Yes | Equal to `source_timestamp` of the latest event with this `Identifier`. |
| Tally | integer | No | Set by Netcool, not by the feed. Increases for each repeated event with the same `Identifier`. The UAT case of runbook section 14 confirms the increase. |
| Type | integer | Yes | 1 for a problem, 2 for a resolution, 13 for information. |
| Class | integer | No | Empty in the baseline. The owner decides the value. |
| Location | string | No | `site_name` when present. |
| ExpireTime | integer | No | Proposal. The value follows the `expire` setting that the Netcool administrator approves. |
| URL | string | No | Never holds a token or a webhook URL. |
| ExtendedAttr | string | No | Key and value pairs from `details`, redacted. |

Validation rules:

- `Severity` is an integer from 0 to 5.
- `Type` is 1, 2, or 13.
- `Identifier` is not empty.

The durable buffer stores each event until the Netcool receiver confirms it. The buffer keeps each event for at least the replay window (proposal: 24 hours).

The UAT cases of FR-017 stop the Netcool receiver and confirm that the buffer holds the events. They restart the receiver and confirm the delivery. They send a duplicate and confirm that `Tally` increases with no new row.

State transitions: a problem event (`Type` 1) becomes a resolution event (`Type` 2) only through an explicit clear. A repeated event with the same `Identifier` increases `Tally` and updates `LastOccurrence`. The absence of a source record never creates a resolution event.

## 8. SmokeSettings

SmokeSettings holds the validated options of one smoke test run. The token value is not a field of this entity. The smoke test reads the token from the environment, and it never copies the token into a field.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| host | string | Yes | Bare host name from the OpenAPI `servers` list. Default `api.mist.com`. |
| org_id | UUID string | Yes | Canonical UUID. From `--org-id`, then the environment, then the env file. |
| site_id | UUID string | No | Canonical UUID. Empty means SMK-08 reads the first site of the organization. |
| runbook_path | path | Yes | Default `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md`. Resolves under the repository root. |
| runbook_explicit | boolean | Yes | True when the operator gave `--runbook`. Controls exit code 2 or SKIP for a missing runbook. |
| openapi_path | path | Yes | Default `documentation/mist-api-openapi31json.json`. Resolves under the repository root. A missing file gives exit code 2. |
| window_minutes | integer | Yes | Default 60. One or more. |
| delay_minutes | integer | Yes | Default 2. Zero or more. Less than `window_minutes`. |
| max_pages | integer | Yes | Default 3. One or more. The page ceiling for each paged query. |
| max_requests | integer | Yes | Default 60. One or more. The request budget. |
| max_retries | integer | Yes | Default 2. From 0 to 2. Retries for HTTP 5xx responses and connection failures. |
| call_timeout_seconds | integer | Yes | Default 30. One or more. The client waits at most this many seconds for each SDK call. |
| output_path | path | Yes | Default `test-artifacts/netcool-runbook-smoke/<UTC timestamp>.json`. Resolves under `test-artifacts/` of the repository root. |
| env_file_given | boolean | Yes | True when the operator gave `--env-file`. The path itself is not stored. |

Validation rules:

- The first failed rule stops the run with exit code 2 before any request.
- `delay_minutes` must be less than `window_minutes`.
- The env file path, when given, resolves outside the repository root, or it is exactly `<root>/.env`. The path is not stored.

State transitions: `parsed` to `validated` when every rule passes. `validated` to `running` when the first check starts.

## 9. CallRecord

A CallRecord holds the result of one client call. Each client call and each client retry consumes one unit of the request budget.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| method | enum | Yes | Always `GET`. Any other value is invalid and is never sent. |
| path_label | string | Yes | Path template with `{org_id}` and `{site_id}` placeholders. Never the real values. |
| query_names | list of string | Yes | Names of the query parameters only. Values are not stored. |
| status_code | integer or null | Yes | The HTTP status. Null when no response exists. |
| error_class | enum | Yes | `None`, `Throttled`, `Timeout`, `BudgetExhausted`, `MalformedJson`, `EmptyBody`, `MissingResults`, `ForeignOrigin`, `RepeatedPage`, `ConnectionError`, `ServerError`, or `Unauthorized`. |
| header_names | list of string | Yes | Names of the response headers only. |
| retry_after_seconds | list of integer or string | Yes | Integer seconds only. A value in another form is the string `not numeric`. Empty when none exists. |
| elapsed_seconds | number | Yes | Time for the call in seconds, rounded to two decimals. |
| attempt | integer | Yes | 1 to 3. The first attempt is 1. |

Validation rules:

- The client reads `status_code` before it reads `data`.
- The client never treats a missing `results` key as an empty success.
- The client never retries an HTTP 429 response. The SDK already retries it three times.
- The client retries an HTTP 5xx response and a connection failure at most `max_retries` times.
- The client never retries a timeout. The second Timeout in one run stops the run with exit code 3.
- The client never retries any other HTTP 4xx response.
- The token validation of the session constructor consumes one unit of the budget. The client never calls `APISession.login()`.

State transitions: `planned` to `sent` when the client uses the budget unit. `sent` to `completed` for status 200 with a valid body. `sent` to `retrying` for HTTP 5xx or a connection failure while `attempt` is below `max_retries` plus 1. `sent` to `failed` for every other result.

## 10. PageSet

A PageSet holds the result of one paged query. The query follows the `next` value of each page. The paging rules are in `contracts/smoke-cli.md`, section 6.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| path_label | string | Yes | Same rule as `CallRecord.path_label`. |
| pages_read | integer | Yes | 0 to `max_pages`. |
| record_count | integer | Yes | Records of all read pages. |
| complete | boolean | Yes | True only when the last read page has no `next` value. |
| stop_reason | enum or null | No | `PageCeiling`, `ForeignOrigin`, `RepeatedPage`, `BudgetExhausted`, `Throttled`, or `Timeout`. `Timeout` marks the second Timeout in one run. Null when `complete` is true. |
| next_form | enum | Yes | `relative`, `absolute`, `none`, or `rejected`. `rejected` marks a `next` value that failed validation. |

Validation rules:

- An absolute `next` value must use the scheme `https`, the approved host, and the port 443 or no port.
- A relative `next` value must start with `/api/v1/`. It must not hold a `..` segment or a backslash, and it must not start with `//`.
- A `next` value that fails these rules gives the stop reason `ForeignOrigin`, and no request uses that value.
- A page repeats when an earlier page of the same query returned its `next` value. The stop reason is `RepeatedPage`.
- A page also repeats when its `results` value has the same SHA-256 hash as an earlier page of the same query. The hash uses the canonical JSON of the `results` value. The stop reason is `RepeatedPage`.
- A page ceiling with a `next` value still present gives `complete` false and the stop reason `PageCeiling`. The check status is WARN, and the run continues.
- The run keeps the `next` values and the page hashes in memory only. The run never writes them to the evidence record.

State transitions: `reading` to `complete` when the last page has no `next`. `reading` to `stopped` for each stop reason.

## 11. CheckResult

A CheckResult holds the result of one smoke check. The check identifiers are SMK-01 to SMK-10.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| check_id | string | Yes | One of `SMK-01` to `SMK-10`. |
| title | string | Yes | The title of the check in `contracts/smoke-cli.md`. |
| status | enum | Yes | One of `PASS`, `WARN`, `INFO`, `FAIL`, `SKIP`. |
| detail | string | Yes | ASCII text of 200 characters or fewer. Redacted. |
| request_count | integer | Yes | Requests that the check used. |
| http_statuses | list of integer | Yes | HTTP status codes in request order. |
| record_count | integer or null | No | Records read by the check. Null when the check reads no records. |
| page_count | integer or null | No | Pages read by the check. Null when the check reads no pages. |
| stop_reason | string or null | No | The stop reason of the paged query, or null. |
| field_names | list of string | Yes | Names of the response fields that the check confirmed. |
| header_names | list of string | Yes | Names of the response headers only. |
| retry_after_seconds | list of integer or string | Yes | Integer seconds only. A value in another form is the string `not numeric`. |

Status meanings:

- `PASS` means the check confirmed its fact.
- `WARN` means the check confirmed its fact with a limit or a risk. Zero records and a page ceiling are WARN results.
- `INFO` means the check recorded an observation without a judgment.
- `FAIL` means the proof of the check failed.
- `SKIP` means the check, or one part of it, did not run. The detail gives the cause.

Roll-up rule: the status of a check is the most severe status of its parts, in this order: `FAIL`, `WARN`, `SKIP`, `INFO`, `PASS`. A skipped part stays visible in the status. An observation that a probe records is not a part, so it does not change the status.

State transitions: `pending` to `running` when the check starts. `running` to one of the five statuses when the check ends.

## 12. EvidenceRecord

`contracts/evidence.md` holds the JSON schema of the evidence record. This entity does not repeat the schema. The smoke test writes the evidence record under `test-artifacts/` before each exit, when the output path is valid. The record is the only output file of the smoke test. The client never reads the private `_session` attribute of the SDK. The evidence record holds `sdk_retry_possible: true`, because the SDK can retry inside one client call.

## 13. Outcome class to exit code map

The smoke test ends with exactly one outcome class. The exit code is the number in the table. The triggers of each class, and the precedence rules, are in `contracts/smoke-cli.md`, section 3.

| Exit code | Outcome class |
| --- | --- |
| 0 | Pass |
| 1 | Check failure |
| 2 | Configuration error |
| 3 | Rate-limit stop |
| 4 | Budget stop |
| 5 | Unsafe paging stop |
| 6 | Internal error |
