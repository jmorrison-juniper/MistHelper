# Smoke test command line contract

The read-only smoke test runs with this command, from the repository root.

```text
.venv\Scripts\python.exe -m scripts.netcool_runbook_smoke
```

The smoke test sends GET requests only. This file is the single source for the options, the exit codes, the SMK rules, the paging rules, and the code layout. The data model in `design/data-model.md` gives the entity view of the same results.

## 1. Options

The command accepts these options. No option accepts a token value (FR-032).

| Option | Default | Rule |
| --- | --- | --- |
| `--env-file PATH` | None | Reads only the names in section 2 with `dotenv_values`. Does not change the process environment. The path must resolve outside the repository root, or it must be exactly `<root>/.env`. A path that does not exist gives exit code 2. |
| `--org-id UUID` | None | Organization identifier. Checked as a UUID. Source order is in section 2. |
| `--site-id UUID` | None | Site identifier for SMK-08. When absent, SMK-08 reads the first site of the organization. Checked as a UUID. |
| `--runbook PATH` | `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` | The path must resolve under the repository root. A path that does not exist gives exit code 2 when this option is given. The default path that does not exist gives SKIP for each check that needs the runbook. |
| `--openapi PATH` | `documentation/mist-api-openapi31json.json` | The path must resolve under the repository root. A path that does not exist or cannot be read gives exit code 2. |
| `--window-minutes N` | `60` | Integer of 1 or more. Length of the collection window. |
| `--delay-minutes N` | `2` | Integer of 0 or more. Less than `--window-minutes`. End lag of the collection window. |
| `--max-pages N` | `3` | Integer of 1 or more. Page ceiling for each paged query. |
| `--max-requests N` | `60` | Integer of 1 or more. Request budget of the run. |
| `--max-retries N` | `2` | Integer from 0 to 2. Retries for an HTTP 5xx response and for a connection failure. Section 7 gives the waits. |
| `--call-timeout SECONDS` | `30` | Integer of 1 or more. The client waits at most this many seconds for each SDK call. Section 6 gives the rules. |
| `--output PATH` | `test-artifacts/netcool-runbook-smoke/<UTC timestamp>.json` | The path must resolve under `test-artifacts/` of the repository root. The timestamp has the form `YYYYMMDDTHHMMSSZ`, because a colon is not valid in a Windows file name. |

Relative paths start at the repository root. The run checks each option before the first request. The first failed check gives exit code 2.

The repository root is the folder that holds `scripts`. The package finds it with `Path(__file__).resolve().parents[2]` in `scripts/netcool_runbook_smoke/__main__.py`. Each path violation gives exit code 2, and the run prints the cause. Tests cover a `..` traversal for each path option.

## 2. Environment variables and source order

The smoke test reads these names. An empty value counts as not set.

| Setting | Names, in lookup order | Default |
| --- | --- | --- |
| Token | `MIST_API_TOKEN`, then `MIST_APITOKEN` | None. Missing token gives exit code 2. |
| Regional host | `MIST_HOST` | `api.mist.com` |
| Organization | `--org-id`, then `MIST_ORG_ID`, then `org_id`, then `ORG_ID` | None. Missing organization gives exit code 2. |

Source rules:

- For each name, the process environment wins over the same name in the env file.
- The env file wins over the default value.
- The smoke test checks the token conflict after the lookup. If `MIST_API_TOKEN` and `MIST_APITOKEN` both have values and the values differ, the run gives exit code 2.
- The smoke test never prints, logs, or writes a token value.

Host rules:

- The host must be a bare host name, with no scheme and no slash.
- The host must be one of the `servers` host names of the OpenAPI file. The smoke test reads this list from the OpenAPI file with `OpenApiIndex.server_hosts()`.
- A host outside the list gives exit code 2.

Organization and site rules:

- A value must be a UUID in the form 8-4-4-4-12 hexadecimal digits. Letter case does not matter.
- The smoke test converts each UUID to lowercase after the check.

The approved origin of a run is `https://{api_host}`. The placeholder `{api_host}` is the regional host of this section.

## 3. Exit codes

The run ends with one outcome class. The exit code matches the outcome class.

| Exit code | Outcome class | Trigger |
| --- | --- | --- |
| 0 | `Pass` | No check has the status `FAIL`, and no run stop applies. At least one check ran. WARN, INFO, and SKIP results are allowed. |
| 1 | `Check failure` | One or more checks have the status `FAIL`, or no check ran, and no run stop applies. |
| 2 | `Configuration error` | A token is missing or conflicting. An organization identifier or a site identifier is not a UUID. The host is not in the server list. A path option is outside its allowed root. An env file path does not exist. An explicit `--runbook` or `--openapi` file cannot be read. A default OpenAPI file cannot be read. HTTP 401 rejects the token at login or on any request. A connection failure occurs during token validation. SMK-03 gives FAIL when the token does not grant the organization. The evidence file cannot be written, and no internal error occurs. |
| 3 | `Rate-limit stop` | A final HTTP 429 response. Or `request_limit` minus `requests` is fewer than two times the request budget (`--max-requests`). Or the second Timeout in one run. |
| 4 | `Budget stop` | The request budget is spent before the next request. |
| 5 | `Unsafe paging stop` | A `next` value has a foreign origin, or a page repeats. |
| 6 | `Internal error` | An unexpected exception occurs. The run logs it with a traceback, writes the evidence record when it can, and prints the cause. |

The rules for the exit codes are:

- The first run stop ends the run. Later checks do not run.
- A run stop has priority over a check failure.
- The page ceiling is not a run stop. It gives WARN for the query, and the run continues.
- SKIP does not change the exit code.
- A run that writes evidence before exit gives the same exit code as its outcome class.
- An internal error keeps exit code 6, even when the evidence write also fails. The run prints both causes. An evidence write failure alone gives exit code 2.

## 4. Console output

The console prints ASCII text only. The run prints one line for each check, then the summary, then the outcome, then the evidence line. Each run prints the summary line and the outcome line, including a run that stops before SMK-01. Each check line has this form: check identifier, status, title, colon, and detail.

```text
SMK-01 PASS Configuration: token present, host in the server list, organization ID valid.
SMK-02 PASS Runbook structure: all headings found, each path has a GET operation.
SMK-03 PASS Token and organization access: role read, organization org-1 in the privileges.
SMK-04 PASS Hourly request budget: 1200 of 5000 requests used, 3800 remaining.
SMK-05 PASS Definition catalogs: 6 catalogs not empty, all runbook names found.
SMK-06 WARN Organization search: zero records for alarms in the collection window.
SMK-07 INFO Organization count: alarms, device events, and system events equal. Mist Edge events have no total.
SMK-08 PASS Site scope: 4 site searches returned HTTP 200 for site-1.
SMK-09 PASS Filters and limits: type filter returned only the filter types, limit 1000 gave HTTP 200.
SMK-10 PASS Inventory and webhooks: 6 calls returned HTTP 200.
Checks examined: 10. Passed: 8. Warnings: 1. Info: 1. Failed: 0. Skipped: 0. Requests sent: 33 of 60.
Outcome: Pass (exit code 0).
Evidence: test-artifacts/netcool-runbook-smoke/20261125T143000Z.json
```

The summary line has this form. Checks examined counts the checks that ran with the status PASS, WARN, INFO, or FAIL. Each skipped check has its own count, and each skipped check prints its cause. Requests sent counts every request, including the token validation request of section 6.

```text
Checks examined: N. Passed: P. Warnings: W. Info: I. Failed: F. Skipped: S. Requests sent: R of B.
Outcome: <class> (exit code <n>).
Evidence: <path of the evidence record>
```

The value B is the accepted `--max-requests` value, or 60 when the run accepts no value. A run that stops before SMK-01 prints zero in each count, and its outcome is `Configuration error` with exit code 2. When the run writes no evidence record, the evidence line reads `Evidence: not written`.

The printed detail uses the redaction rules of `contracts/evidence.md`, section 7. The organization identifier prints as `org-1`, and the site identifier prints as `site-1`.

## 5. Checks

Each check runs in the order below. A check that runs after a run stop gets the status SKIP, and its detail gives the cause, for example `not run: rate-limit stop`.

| Check | Title | Requests | Class |
| --- | --- | --- | --- |
| SMK-01 | Configuration | 0 | Identity |
| SMK-02 | Runbook structure | 0 | Identity |
| SMK-03 | Token and organization access | 1 | Identity |
| SMK-04 | Hourly request budget | 1 | Identity |
| SMK-05 | Definition catalogs | 6 | Catalog |
| SMK-06 | Organization search | 4 up to 4 times `--max-pages` | Search |
| SMK-07 | Organization count | 4 | Search |
| SMK-08 | Site scope | 4, or 5 when `--site-id` is absent | Scope |
| SMK-09 | Filters and limits | 6 | Scope |
| SMK-10 | Inventory and webhooks | 6 | Scope |

Common rules for each request:

- The smoke test reads the HTTP status before it reads the body.
- Each request that takes a `limit` parameter sends `limit=1000`, except the one SMK-09 probe with `limit=5000` (section 5.9). The requests of SMK-03, SMK-04, and SMK-05 take no `limit` parameter.
- Each request that takes the `start` and `end` parameters sends the collection window. The window has `start` equal to the current time minus `--window-minutes`, and `end` equal to the current time minus `--delay-minutes`. Both values are epoch seconds in UTC.
- The inventory count, the Mist Edge list, the webhook list, and the site list take no `start` or `end` parameter in the OpenAPI file.

### 5.1 SMK-01 Configuration

- Checks the token, the host, the organization identifier, the site identifier, and the file paths of section 1.
- The check gives PASS when each value passes its rule.
- A failed rule gives FAIL and exit code 2. The run stops before any request.

### 5.2 SMK-02 Runbook structure

- Checks each required heading of `contracts/runbook-structure.md`.
- Checks that each Appendix A path has a GET operation in the OpenAPI file. The check uses `OpenApiIndex.has_get`.
- Checks that each Appendix B table holds at least one name.
- Checks that the set of hosts in section 5.5 equals the set of `servers` hosts of the OpenAPI file.
- The check gives FAIL for a missing heading, a path without a GET operation, or an empty Appendix B table.
- The check gives FAIL for a host set that does not match.
- The detail names each missing value.
- A default runbook path that does not exist gives SKIP with the cause `runbook not found`.

### 5.3 SMK-03 Token and organization access

- Requests `GET /api/v1/self`.
- The status must be 200. A 403 gives FAIL. A 401 gives exit code 2.
- The check looks for a privilege with the scope `org` and the `org_id` value of the organization. The OpenAPI file names the field `org_id` in each privilege. The live run confirms the field.
- A privilege entry without an `org_id` field, and without the scope `msp`, does not grant the organization. The check gives WARN with the detail `organization scope not confirmed` for that entry.
- The check records the role name in the detail.
- The check gives PASS when the privilege with the scope `org` has the role `read`. Any other role gives WARN with the role name, because a production collector must use a read-only token.
- When no privilege with the scope `org` matches, and a privilege with the scope `msp` exists, the check gives WARN. The detail is `organization access can come from an MSP privilege, so the role for the organization is unknown`. The run continues.
- When no entry grants the organization, the check gives FAIL, and the run stops with exit code 2. The detail states that the token does not grant the organization.

### 5.4 SMK-04 Hourly request budget

- Requests `GET /api/v1/self/usage`.
- The body must hold integers for `requests` and `request_limit`, and a number for `seconds`. The OpenAPI file gives these types.
- A usage request fails when its HTTP status is not 200, or when the body lacks one of these values.
- A failed usage request gives WARN with the detail `the hourly usage was not readable`. The run continues.
- An HTTP 401 or a final HTTP 429 keeps its exit code from section 3.
- Each run makes one usage request.
- When `request_limit` minus `requests` is fewer than two times the request budget (`--max-requests`), the check gives FAIL and the run stops with exit code 3.
- The check compares `request_limit` with 5000, the value that the HTTP 429 description of the OpenAPI file names. A different value gives WARN with both values.
- The detail gives the remaining requests and the value of `seconds`.

### 5.5 SMK-05 Definition catalogs

- Requests six catalogs: `/api/v1/const/alarm_defs`, `/api/v1/const/device_events`, `/api/v1/const/mxedge_events`, `/api/v1/const/system_events`, `/api/v1/const/ap_led_status`, and `/api/v1/const/webhook_topics`.
- Each catalog must return status 200 and a top-level JSON array with at least one item. An empty catalog gives FAIL.
- Each name of an Appendix B table must match the `key` of an item in the catalog for that table. The mapping is in `contracts/runbook-structure.md`, section 8.
- A name that the catalog does not hold gives FAIL. The detail names the missing value.
- The evidence record holds each catalog in full, except the `example` member of each item.
- The `for_org` member of each webhook topic item gives the topic scope. The runbook takes the scope from the live catalog.
- Without the runbook, each Appendix B comparison gives SKIP with the cause `runbook not found`. The catalog requests still run.

### 5.6 SMK-06 Organization search

- Requests the organization search of four families: alarms, device events, Mist Edge events, and system events.
- Each query follows the `next` value up to `--max-pages` pages, as section 6 defines.
- The Mist Edge request sends `start` and `end`. The check compares the echoed values with the sent values (observation `q2`).
- The alarm search accepts a `site_id` parameter. This check does not send it.
- Each page must return status 200 and a `results` list. The top-level JSON array is not accepted for a search page.
- The identifier fields of each family come from the runbook. When a query returns records, each identifier field must appear in at least one record of the family. A field that appears in no record gives FAIL.
- Zero records give WARN. The detail states that zero records do not prove that no event exists.
- A page ceiling with a `next` value still present gives WARN with the stop reason `PageCeiling`.
- Mist Edge search responses have no `total` value. The check does not require one.
- The check records observation `q8`: the distinct values of the enumerated fields of the records that it read. For alarms, these are the values of `status` (schema `alarm_status`, values `open` and `resolved`), `severity`, `group`, and the true and false counts of `acked`. The live run on 2026-11-26 found that the alarm records carried no `status` field. For device events, the values of `ev_type`. For Mist Edge events, the values of `severity`. The check records values only, never identifiers, and the values pass the redaction rules of `evidence.md`, section 7.

### 5.7 SMK-07 Organization count

- Requests the count endpoint of four families with `distinct=type`: alarms, device events, Mist Edge events, and system events.
- The OpenAPI file lists `type` as a value of the `distinct` parameter for the device event and Mist Edge event counts. It lists no values for the alarm and system event counts, so the live run confirms `type` for those families (observation `q5`).
- Each count request sends `limit=1000`, and each count must return status 200 and a `results` list.
- The families with a `total` value are alarms, device events, and system events. For each of these families, the check compares the `total` of the first search page with the sum of the `count` values. Both values use the same collection window.
- Equal values give PASS for that family. A different value gives WARN with both values.
- The device event comparison runs only when the device event search read all its pages. When the search did not read all its pages, the device event part gives SKIP with the cause `device event search incomplete`.
- Mist Edge events have no `total` value in the search response. The Mist Edge part gives INFO, and the detail gives the reason.
- Device event searches in SMK-06 send no `device_type`, so the default `ap` applies (observation `q1`).
- The check status follows the roll-up rule of `design/data-model.md`, section 11.

### 5.8 SMK-08 Site scope

- When `--site-id` is absent, the check requests `GET /api/v1/orgs/{org_id}/sites` with `limit=1000`. The first site of the returned list is the site for this check. An empty list gives SKIP with the cause `no site in organization`.
- Requests one page of each site search with `limit=1000`: alarms, device events, Mist Edge events, and system events.
- Each request must return status 200 and a `results` list.
- Zero records give WARN, as in SMK-06.

### 5.9 SMK-09 Filters and limits

The check sends six requests. Each request reads one page, and no request follows a `next` value.

1. Device event search with `type` set to the first two keys of the device event catalog from SMK-05, separated by a comma with no space. The request sends the collection window and `limit=1000`.
2. Device event search with `limit=5000`, and with the collection window. This is the only request with a limit above 1000. It is the one exception to the `limit` rule of section 5, and the owner can remove it in the review. The OpenAPI file gives no maximum for `limit` on this operation, so the request observes the page size behavior (observation `q3`).
3. Device event search with `device_type=switch`, the collection window, and `limit=1000`. The check records the distinct `type` values of the page.
4. Device event search with `device_type=gateway`, the collection window, and `limit=1000`. The check records the distinct `type` values of the page.
5. Mist Edge event search with `duration=1h`, without `start` or `end`, and with `limit=1000`. The check records the `start` and `end` values of the response.
6. Mist Edge event search with no `start`, `end`, or `duration`, and with `limit=1000`. The check records the `start` and `end` values of the response. This answers observation `q2`.

The status of request 1 decides the check status.

- The check gives PASS when request 1 returns HTTP 200 with at least one record.
- Each returned `type` must be one of the two keys.
- Zero records give WARN, because the filter is not proven.
- A returned `type` outside the two keys gives FAIL. So does a status other than 200 for request 1.

Requests 2 to 6 are probes. A probe adds INFO observations to the evidence record, and no probe lowers the check status. The FAIL rule of section 7 for an HTTP 4xx response does not apply to a probe. Observation `q3` records one of these values for request 2.

- `accepted`: HTTP 200, and the echoed `limit` is 5000.
- `reduced`: HTTP 200, and either the echoed `limit` is below 5000, or the page has a `next` value and fewer records than requested.
- `rejected`: HTTP 400 or HTTP 422.
- `not_observed`: any other status. The record keeps the status code.

### 5.10 SMK-10 Inventory and webhooks

The check sends six requests.

1. `GET /api/v1/orgs/{org_id}/inventory/count` with `type=ap`, `distinct=model`, and `limit=1000`.
2. `GET /api/v1/orgs/{org_id}/inventory/count` with `type=switch`, `distinct=model`, and `limit=1000`.
3. `GET /api/v1/orgs/{org_id}/inventory/count` with `type=gateway`, `distinct=model`, and `limit=1000`.

The `distinct` values of this endpoint are `model`, `status`, `site_id`, `sku`, and `version`. None of them is a device type, so the check selects each device type with `type`. The device count of a type is the sum of the `count` values of its results. The `total` value is the number of distinct result buckets, not the number of devices.

4. `GET /api/v1/orgs/{org_id}/mxedges` with `limit=1000`, one page. The response is a top-level JSON array. The check records the item count and the field names. Zero items give INFO, because an organization can have no Mist Edge devices.
5. `GET /api/v1/orgs/{org_id}/stats/devices` with `type=ap`, the collection window, and `limit=1000`, one page. The response is a top-level JSON array. The check records the item count and whether `last_trouble` appears in any item. The OpenAPI file does not describe the item fields, so the live run answers observation `q6`. Zero items give WARN.
6. `GET /api/v1/orgs/{org_id}/webhooks` with `limit=1000`, one page. The response is a top-level JSON array. The check records the item count, the topic names, and the number of enabled and disabled webhooks. The check never records a webhook URL, a webhook name, or a secret. Zero items give INFO.

Each request must return status 200. A status other than 200 gives FAIL for that request, except a 401, which gives exit code 2.

## 6. Request budget, paging, and run time

GET is the only method of the smoke test. The counted requests never exceed the request budget (SC-005).

The budget rules are these.

- The budget is `--max-requests`. The default is 60.
- A request is one client call or one client retry. The client uses the budget unit before the call or the retry starts.
- The token validation request of the SDK counts as one request. It is the only login request that the budget counts. The SDK sends it once, when the client creates the session with the token. The SDK sets a timeout of 30 seconds for this request (`mistapi/__api_session.py`, line 576). When the request fails with another error, such as a timeout, the session can have no token. The first request then gets HTTP 401, which gives exit code 2.
- The client never calls `APISession.login()`, because `login()` sends a second GET to `/api/v1/self`. The implementation verifies in the SDK source that `mist_get` works without `login()`.
- The client never reads the private `_session` attribute of the SDK.
- The SDK retries an HTTP 429 response up to three times inside one client call. The client cannot count those retries, so the evidence record holds `sdk_retry_possible: true`.
- When the `Retry-After` header holds integer seconds, the SDK sleeps that long. Otherwise, the SDK sleeps 5, 10, or 20 seconds. The sleep does not use budget units.
- The SDK call has no timeout (`mistapi/__api_request.py`, line 277). The client runs each SDK call in a daemon worker thread. The client waits at most `--call-timeout` seconds for the result. The abandoned thread is a daemon thread, so it cannot block the exit.
- The client sends no request when the budget is spent. The client returns an error of the class `BudgetExhausted`, and the run ends with exit code 4.

Run time and size of a run:

- A full run without retries makes 32 to 41 client calls when `--max-pages` is 3. With the token validation request, the run sends 33 to 42 requests.
- The count rises with each retry and with a larger page ceiling.
- A typical run takes 1 to 3 minutes.
- The worst case is about 33 minutes at the default budget and the default call timeout. It is 60 requests at 30 seconds each, plus at most 2.5 seconds for each retry.

Paging rules:

- An absolute `next` value must use the scheme `https`, the approved host, and the port 443 or no port.
- A relative `next` value must start with `/api/v1/`. It must not hold a `..` segment or a backslash, and it must not start with `//`.
- Any other `next` value stops the run with exit code 5 (`ForeignOrigin`). No request uses that value.
- A page repeats when an earlier page of the same query returned its `next` value.
- A page also repeats when its `results` value has the same SHA-256 hash as an earlier page of the same query. The hash is SHA-256 of the canonical JSON. Canonical JSON is UTF-8 JSON with sorted keys and no spaces between tokens.
- A repeated page stops the run with exit code 5 (`RepeatedPage`).
- When the page count reaches `--max-pages` and a `next` value remains, the query is incomplete. The stop reason is `PageCeiling`, and the check gives WARN.
- The run keeps the `next` values and the page hashes in memory only.
- Observation `q4` holds the form of the first `next` value that a search page returns, and whether that value holds `search_after`. It holds `none` when no search page returns a `next` value. The answer is `null` when the run reads no search page.

## 7. HTTP status handling

The client applies these rules to each response.

| Condition | Client action | Check result | Run |
| --- | --- | --- | --- |
| HTTP 200 with a valid JSON body | Completed | Per check | Continues |
| HTTP 401 at login or on any request | Run stop | Not applicable | Exit code 2 |
| Connection failure during token validation at login | Run stop | Not applicable | Exit code 2 |
| Other HTTP 4xx, such as 400, 403, or 404 | No retry | FAIL | Continues |
| HTTP 429 | The SDK retries three times, then the client records `Throttled` | FAIL | Exit code 3 |
| HTTP 5xx | Retry at most `--max-retries` times, waiting 1 second, then 2 seconds, plus jitter up to 0.5 second | FAIL after the last attempt | Continues |
| Connection failure (SDK status `None`, data `{}`) | Retry at most `--max-retries` times, with the same wait | FAIL with `ConnectionError` after the last attempt | Continues |
| Timeout | No retry. The client waits at most `--call-timeout` seconds for each SDK call. | FAIL with `Timeout` | Continues. The second Timeout in one run stops the run with exit code 3. |
| Malformed JSON | No retry | FAIL with `MalformedJson`. Never zero records. | Continues |
| Empty body | No retry | FAIL with `EmptyBody` | Continues |
| Search page without `results` | No retry | FAIL with `MissingResults`. Never an empty success. | Continues |

The rules below apply to all responses.

- The session constructor raises `ValueError` for HTTP 401, and it raises `ConnectionError` for a connection failure during token validation. The client maps both cases to exit code 2.
- The SDK does not raise an exception for an HTTP error status. The client reads `status_code` first, and then it reads `data`.
- The SDK sets `data` to an empty object when the body is not valid JSON. The SDK keeps the body text in `raw_data`. The client reads `raw_data` to tell an empty body from a malformed body.
- The client never logs, prints, or writes `raw_data`.
- The client records a `Retry-After` value only when it is an integer number of seconds. For another form, the client records the string `not numeric`.
- Observation `q7` holds the names of the response headers of the run. The `rate_limit_header_present` answer is true when a header name contains `ratelimit` or `rate-limit`, ignoring case.
- For each HTTP 4xx or 5xx response, the evidence record keeps at most 200 characters of the redacted error text.
- The client exposes one HTTP method, GET. The client has no method for POST, PUT, PATCH, or DELETE.

## 8. Logging, redaction, and output

- Each module that acts creates its logger with `structlog.get_logger(__name__)`.
- Each action writes an `info` line before it, and a `debug` line after it. The `debug` line gives the result, such as a count or a status. An action is a request, a file write, or a data transform.
- Each log call uses a `%s` message template and positional values. For example, `logger.info("GET %s started", path_label)`. Extra context uses a keyword argument.
- Do not format the message before the call. Do not use an f-string, a `format` method, or the `%` operator for the message.
- Each `except` block calls `logger.exception`, which records the full traceback. The `%s` template names the check identifier, the path label, and the error class.
- The path label uses `{org_id}` and `{site_id}` placeholders.
- `__main__.py` configures structlog once. It sets `structlog.stdlib.BoundLogger` as the wrapper class, and it adds the processor `structlog.stdlib.PositionalArgumentsFormatter()`. The key-value renderer writes to stderr. A processor replaces the token value with `[redacted]`, and it removes UUID, MAC address, and email patterns from each log line.
- The run sets the standard library logger `mistapi` to WARNING.
- The token value never appears in a log line, a console line, or an evidence record.
- The redaction rules of `contracts/evidence.md`, section 7, apply to each log line and each console line.
- The organization identifier prints as `org-1`, and the site identifier prints as `site-1`.
- The console output and the logs use ASCII only.

## 9. Evidence record and exit

- The run writes the evidence record before it exits, when the output path is valid.
- When the output path is not valid, the run writes no evidence record. It prints the cause and exits with code 2.
- A run that stops before SMK-01 also writes a record when the output path is valid. The layout of that record is in `contracts/evidence.md`, sections 1 and 3.
- When the evidence write fails, the run prints the cause in ASCII. The exit code follows the rules of section 3.
- When an unexpected exception occurs, the run exits with code 6. The run logs the exception with its traceback, writes the evidence record when it can, and prints the cause.
- The evidence record holds no token and no identifier. The schema is in `contracts/evidence.md`.

## 10. Code layout and tests

The package and its tests use these layouts. Each folder holds five children or fewer. The count excludes `__init__.py`, as the repository guard `tests/guardrails/test_move_module_guidance.py` does.

```text
scripts/netcool_runbook_smoke/
+-- __init__.py
+-- __main__.py
+-- client.py
+-- command.py
+-- documents.py
+-- checks/
    +-- __init__.py
    +-- identity.py
    +-- catalogs.py
    +-- searches.py
    +-- scope.py
    +-- support.py
```

- `documents.py` holds `RunbookClaims`, `OpenApiIndex`, `MarkdownTables`, `EvidenceRedactor`, and `EvidenceWriter`. The package has no `claims.py` module and no `evidence.py` module.
- `__main__.py` holds `SmokeSettings`, `SettingsLoader`, `IdentityRules`, `CheckSequence`, and `SmokeCommand`.
- `client.py` holds `CallRecord`, `PageSet`, `CallGovernor`, `PageWalker`, and `ReadOnlyMistClient`.
- `command.py` holds `TracebackFreeFormatter`, `StandardLogging`, `LogSetup`, `EnvFileReader`, and `RunReport`.
- `checks/__init__.py` holds `CheckStatus`, `CheckResult`, `CheckContext`, `StopRun`, and `EvidenceBuilder`.
- `checks/support.py` holds `SessionOpener` and `RequestTrail`.

```text
tests/unit/scripts/netcool_runbook_smoke/
+-- test_netcool_smoke_client.py
+-- test_netcool_smoke_documents.py
+-- test_netcool_smoke_checks.py
+-- test_netcool_smoke_command.py
+-- test_netcool_runbook_document.py
```

- The test folder has no `__init__.py`. It holds these five files and no other file.
- Each test writes its files under `tmp_path`.
- Only `test_netcool_smoke_client.py` imports `mistapi` at module scope. That module covers HTTP 4xx, HTTP 5xx, timeout, connection error, malformed JSON, and empty body.
- The tests use a fake session object for each Mist response. No test uses a real token or the network.
- The gates for these files are in `design/quickstart.md`, section 4.
