# Evidence record contract

The smoke test writes one evidence record for each run. The record is UTF-8 JSON with sorted keys. The writer stores the record under `test-artifacts/`, and Git ignores that folder. This file defines the keys, the type of each key, an example, and the redaction rules.

The evidence record is an allowlist. The writer copies no HTTP response body, except the definition catalogs of section 5 and the redacted error text of section 7. The writer keeps only the keys of this file.

## 1. Top-level keys

The record has these 14 keys. Each key is always present. A value that the run did not obtain is `null`, or an empty list or object, as the table states.

| Key | Type | Required | Rule |
| --- | --- | --- | --- |
| `schema_version` | string | Yes | Fixed value `1`. |
| `generated_at` | string | Yes | UTC timestamp in ISO 8601 form with the suffix `Z`. |
| `tool` | object | Yes | Section 2. |
| `host` | string | Yes | The regional host of the run, with no scheme. |
| `organization_label` | string | Yes | Fixed value `org-1`. The organization identifier is never written. |
| `settings` | object | Yes | Section 3. Holds no secret. |
| `request_count` | integer | Yes | Requests that the run used, including the token validation request. Zero or more. |
| `request_budget` | integer | Yes | The accepted value of `--max-requests`. One or more. The value is 60 when the run accepts no value. |
| `sdk_retry_possible` | boolean | Yes | Always `true`. The SDK can retry inside one client call, and the client cannot see those retries. |
| `outcome_class` | string | Yes | One of the outcome classes of `contracts/smoke-cli.md`, section 3. |
| `exit_code` | integer | Yes | The exit code of the outcome class, from 0 to 6. |
| `checks` | array of object | Yes | Section 4. Holds ten items, one for each check, in the order SMK-01 to SMK-10. Holds an empty array when the run stops before SMK-01. |
| `catalogs` | object | Yes | Section 5. Holds one key for each catalog of SMK-05. |
| `observations` | object | Yes | Section 6. Holds the answers to the live questions. |

## 2. The `tool` object

| Key | Type | Rule |
| --- | --- | --- |
| `name` | string | Fixed value `netcool_runbook_smoke`. |
| `module` | string | Fixed value `scripts.netcool_runbook_smoke`. |
| `version` | string | The value of `__version__` in `scripts/netcool_runbook_smoke/__init__.py`. The value is `1.0.0`. This version names the smoke tool. It is not the version of the project constitution. The run reads that value, and it does not read `pyproject.toml`. |

## 3. The `settings` object

The `settings` object holds the validated options without any secret. A setting that the run does not accept is `null`.

| Key | Type | Rule |
| --- | --- | --- |
| `call_timeout_seconds` | integer | The value of `--call-timeout`. |
| `window_minutes` | integer | The value of `--window-minutes`. |
| `delay_minutes` | integer | The value of `--delay-minutes`. |
| `max_pages` | integer | The value of `--max-pages`. |
| `max_requests` | integer | The value of `--max-requests`. |
| `max_retries` | integer | The value of `--max-retries`. |
| `site_scope` | string or null | `site-1` when the run used a site, otherwise `null`. The site identifier is never written. |
| `runbook` | string | The runbook path relative to the repository root. |
| `openapi` | string | The OpenAPI path relative to the repository root. |
| `runbook_explicit` | boolean | `true` when the operator gave `--runbook`. |
| `env_file_given` | boolean | `true` when the operator gave `--env-file`. The env file path is never written. |

## 4. The `checks` items

Each item of `checks` has these 12 keys.

| Key | Type | Rule |
| --- | --- | --- |
| `check_id` | string | One of `SMK-01` to `SMK-10`. |
| `title` | string | The title of the check in `contracts/smoke-cli.md`. |
| `status` | string | One of `PASS`, `WARN`, `INFO`, `FAIL`, `SKIP`. |
| `detail` | string | ASCII text of 200 characters or fewer. Redacted under section 7. |
| `request_count` | integer | Requests that the check used. |
| `http_statuses` | array of integer | HTTP status codes in request order. Empty when the check made no request. |
| `record_count` | integer or null | Records read by the check. `null` when the check read no records. |
| `page_count` | integer or null | Pages read by the check. `null` when the check read no pages. |
| `stop_reason` | string or null | One of `PageCeiling`, `ForeignOrigin`, `RepeatedPage`, `BudgetExhausted`, `Throttled`, or `Timeout`. `Timeout` marks the second Timeout in one run. `null` when no stop reason applies. |
| `field_names` | array of string | Names of the response fields that the check confirmed. Never a value. |
| `header_names` | array of string | Names of the response headers. Never a header value. |
| `retry_after_seconds` | array of integer or string | `Retry-After` values in integer seconds. A value in another form is the string `not numeric`. |

## 5. The `catalogs` object

The `catalogs` object has these six keys: `alarm_defs`, `device_events`, `mxedge_events`, `system_events`, `ap_led_status`, and `webhook_topics`. Each key holds an object with these keys.

| Key | Type | Rule |
| --- | --- | --- |
| `status_code` | integer or null | The HTTP status of the catalog request. `null` when no response exists. |
| `item_count` | integer | Number of items in the catalog. Zero or more. |
| `items` | array of object | Each item of the catalog, without its `example` member. Catalog data is generic Mist data. |

## 6. The `observations` object

The keys `q1` to `q8` answer the eight live questions of the API check. Each key answers one question.

- `q1`: Does the device event search return only AP events when `device_type` is absent?
- `q2`: Does the Mist Edge event search echo the `start` and `end` that the request gives? What window does it use when the request gives no time parameter?
- `q3`: What happens when `limit` is larger than 1000?
- `q4`: What is the format of `next`, and does it carry `search_after`?
- `q5`: Do the count endpoints accept `distinct=type` for each family?
- `q6`: Do organization AP statistics carry `last_trouble`?
- `q7`: Which response headers does the service return, and is a rate-limit header present?
- `q8`: Which enumerated values do the alarm, device event, and Mist Edge event records hold? Does the alarm search return resolved alarms? The check reads the field `status` of each alarm record (schema `alarm_status`, values `open` and `resolved`). The live run on 2026-11-26 found that the alarm records carried no `status` field.

Each answer is `null` when the run did not observe it.

| Key | Type | Rule |
| --- | --- | --- |
| `q1_device_type_default` | object | `device_types_seen` (array of string) and `only_ap` (boolean or null), from the device event records of SMK-06. |
| `q2_mist_edge_window` | object | `echoes_start_end` (boolean or null), `with_duration_1h`, and `without_time_parameter`. Each of the last two holds `start` and `end` as integers or `null`. |
| `q3_limit_5000` | object | `outcome` (`accepted`, `reduced`, `rejected`, or `not_observed`), `status_code` (integer or null), and `page_limit` (integer or null). The `outcome` rules are in `contracts/smoke-cli.md`, section 5.9. The `status_code` value is the HTTP status of request 2. The `page_limit` value is the `limit` of the response. |
| `q4_next_form` | object | `form` (`relative`, `absolute`, `none`, or `rejected`) and `carries_search_after` (boolean or null). The rules are in `contracts/smoke-cli.md`, section 6. |
| `q5_distinct_type` | object | One key for each family (`alarms`, `device_events`, `mxedge_events`, `system_events`) with the HTTP status (integer or null). |
| `q6_last_trouble_present` | boolean or null | `true` when `last_trouble` appears in an AP statistics item. |
| `q7_response_headers` | object | `names` (array of string), `rate_limit_header_present` (boolean or null), and `retry_after_seconds` (array of integer or string). |
| `q8_alarm_status_values` | object | `alarms` (object with `status`, `severity`, and `group` as arrays of string, and `acked` as an object with the integer counts `true` and `false`), `device_events` (object with `ev_type` as an array of string), and `mxedge_events` (object with `severity` as an array of string). Each array holds the distinct values of the records that SMK-06 read, in sorted order. The value is `null` for a family that read no records. The record holds values only, never an identifier, and each value passes the redaction rules of section 7. The OpenAPI file lists `open` and `resolved` as the values of the alarm `status`. The alarm item also holds `resolved_time`, an integer in epoch seconds. A `resolved` value in `alarms.status` shows that the alarm search returns resolved alarms. |
| `device_event_types_by_device_type` | object | Keys `switch` and `gateway`. Each holds an array of the distinct device event `type` values of one page. |

## 7. Redaction rules

The redaction rules apply to each string of the record, to each printed line, and to each log line. The `EvidenceRedactor` applies them in this order.

1. The writer replaces each organization identifier with `org-1`.
2. The writer replaces each site identifier with `site-1`.
3. The writer replaces each value of the token source with `[redacted]`. The token source is the value of `MIST_API_TOKEN` or `MIST_APITOKEN`, after the lookup.
4. The writer replaces each string that looks like a UUID, a MAC address, an email address, or a token with `[redacted]`.
5. The writer cuts each `detail` string to 200 characters after the replacements.

The redaction shapes are these.

- A UUID has the form 8-4-4-4-12 hexadecimal digits.
- A MAC address has six pairs of hexadecimal digits separated by colons or hyphens.
- An email address has a local part, an at sign, and a domain.
- A token-like value has one of two shapes. The first shape is the word `Token`, a space, and 20 or more letters or digits. The second shape is a run of 32 or more letters or digits.
- The redactor uses the 32 character threshold, which is stricter than the 40 character threshold of the runbook scan. The reason is that response text needs the stricter threshold. The runbook scan reads only written text.

The record never holds these values:

- A token, a secret, or a header value.
- A webhook URL or a webhook name.
- A device name, a site name, or a serial number.
- A customer identifier. Section 11 of `contracts/runbook-structure.md` defines it.

For each HTTP 4xx or 5xx response, the record keeps at most 200 characters of the redacted error text. The error text is the `detail` value of the error body. The record holds no other response body.

The record keeps the names of the response headers and the integer `Retry-After` values. A `Retry-After` value in another form is the string `not numeric`.

The record never holds a path with a user folder. Each path is relative to the repository root.

## 8. Example record

The example uses placeholder values only. The values are not real. The example has the outcome `Pass`, which matches the console example of `contracts/smoke-cli.md`.

```json
{
  "catalogs": {
    "alarm_defs": {"item_count": 1, "items": [{"display": "Example alarm", "group": "infrastructure", "key": "example-alarm-key", "severity": "warn"}], "status_code": 200},
    "ap_led_status": {"item_count": 1, "items": [{"key": "example-led-key"}], "status_code": 200},
    "device_events": {"item_count": 1, "items": [{"display": "Example device event", "key": "example-device-event-key"}], "status_code": 200},
    "mxedge_events": {"item_count": 1, "items": [{"display": "Example Mist Edge event", "key": "example-mxedge-event-key"}], "status_code": 200},
    "system_events": {"item_count": 1, "items": [{"display": "Example system event", "key": "example-system-event-key"}], "status_code": 200},
    "webhook_topics": {"item_count": 1, "items": [{"for_org": true, "key": "example-webhook-topic"}], "status_code": 200}
  },
  "checks": [
    {"check_id": "SMK-01", "detail": "token present, host in the server list, organization ID valid.", "field_names": [], "header_names": [], "http_statuses": [], "page_count": null, "record_count": null, "request_count": 0, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Configuration"},
    {"check_id": "SMK-02", "detail": "all headings found, each path has a GET operation.", "field_names": [], "header_names": [], "http_statuses": [], "page_count": null, "record_count": null, "request_count": 0, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Runbook structure"},
    {"check_id": "SMK-03", "detail": "role read, organization in the privileges.", "field_names": ["org_id", "role", "scope"], "header_names": ["content-type"], "http_statuses": [200], "page_count": null, "record_count": null, "request_count": 1, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Token and organization access"},
    {"check_id": "SMK-04", "detail": "1200 of 5000 requests used, 3800 remaining.", "field_names": ["request_limit", "requests", "seconds"], "header_names": ["content-type"], "http_statuses": [200], "page_count": null, "record_count": null, "request_count": 1, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Hourly request budget"},
    {"check_id": "SMK-05", "detail": "6 catalogs not empty, all runbook names found.", "field_names": ["display", "key"], "header_names": ["content-type"], "http_statuses": [200, 200, 200, 200, 200, 200], "page_count": null, "record_count": null, "request_count": 6, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Definition catalogs"},
    {"check_id": "SMK-06", "detail": "zero alarm records in the collection window. Other families read records.", "field_names": ["id", "timestamp"], "header_names": ["content-type"], "http_statuses": [200, 200, 200, 200], "page_count": 4, "record_count": 57, "request_count": 4, "retry_after_seconds": [], "status": "WARN", "stop_reason": null, "title": "Organization search"},
    {"check_id": "SMK-07", "detail": "alarms, device events, and system events equal. Mist Edge events have no total.", "field_names": ["count", "results", "total"], "header_names": ["content-type"], "http_statuses": [200, 200, 200, 200], "page_count": null, "record_count": null, "request_count": 4, "retry_after_seconds": [], "status": "INFO", "stop_reason": null, "title": "Organization count"},
    {"check_id": "SMK-08", "detail": "4 site searches returned HTTP 200 for site-1.", "field_names": ["results"], "header_names": ["content-type"], "http_statuses": [200, 200, 200, 200], "page_count": 4, "record_count": 12, "request_count": 4, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Site scope"},
    {"check_id": "SMK-09", "detail": "type filter returned only the filter types, limit 1000 gave HTTP 200.", "field_names": ["limit", "results", "type"], "header_names": ["content-type"], "http_statuses": [200, 200, 200, 200, 200, 200], "page_count": 6, "record_count": 25, "request_count": 6, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Filters and limits"},
    {"check_id": "SMK-10", "detail": "6 calls returned HTTP 200.", "field_names": ["results", "total"], "header_names": ["content-type"], "http_statuses": [200, 200, 200, 200, 200, 200], "page_count": 3, "record_count": 14, "request_count": 6, "retry_after_seconds": [], "status": "PASS", "stop_reason": null, "title": "Inventory and webhooks"}
  ],
  "exit_code": 0,
  "generated_at": "2026-11-25T14:30:00Z",
  "host": "{api_host}",
  "observations": {
    "device_event_types_by_device_type": {"gateway": ["example-device-event-key"], "switch": ["example-device-event-key"]},
    "q1_device_type_default": {"device_types_seen": ["ap"], "only_ap": true},
    "q2_mist_edge_window": {"echoes_start_end": true, "with_duration_1h": {"end": null, "start": null}, "without_time_parameter": {"end": null, "start": null}},
    "q3_limit_5000": {"outcome": "reduced", "page_limit": 1000, "status_code": 200},
    "q4_next_form": {"carries_search_after": true, "form": "relative"},
    "q5_distinct_type": {"alarms": 200, "device_events": 200, "mxedge_events": 200, "system_events": 200},
    "q6_last_trouble_present": true,
    "q7_response_headers": {"names": ["content-type"], "rate_limit_header_present": false, "retry_after_seconds": []},
    "q8_alarm_status_values": {"alarms": {"acked": {"false": 1, "true": 0}, "group": ["example-group"], "severity": ["example-severity"], "status": ["example-status"]}, "device_events": {"ev_type": ["example-device-event-type"]}, "mxedge_events": {"severity": ["example-severity"]}}
  },
  "organization_label": "org-1",
  "outcome_class": "Pass",
  "request_budget": 60,
  "request_count": 33,
  "schema_version": "1",
  "sdk_retry_possible": true,
  "settings": {
    "call_timeout_seconds": 30,
    "delay_minutes": 2,
    "env_file_given": false,
    "max_pages": 3,
    "max_requests": 60,
    "max_retries": 2,
    "openapi": "documentation/mist-api-openapi31json.json",
    "runbook": "documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md",
    "runbook_explicit": false,
    "site_scope": "site-1",
    "window_minutes": 60
  },
  "tool": {"module": "scripts.netcool_runbook_smoke", "name": "netcool_runbook_smoke", "version": "1.0.0"}
}
```

## 9. Committed copies

The evidence record under `test-artifacts/` is local, and Git ignores it. The owner commits the live verification record in runbook section 13. The live verification record has this layout.

- The UTC date of the run, from `generated_at`.
- The tool version, from `tool.version`.
- The request count, from `request_count`.
- A table with the columns `Check`, `Status`, and `Notes`. The table has one row for each check.
- A table with the columns `Question`, `Answer`, and `Evidence`. The table has one row for each of the eight live questions.

The record holds statuses, field names, catalog names, and catalog sizes only. It holds no identifier and no organization data volume (FR-028).
