# Research for feature 4934: NOC runbook for the Juniper Mist to IBM Netcool alarm integration

This document records decisions D1 to D15 for the plan. Each decision gives its rationale, its alternatives, and its sources. Each fact that the live smoke run must confirm carries the mark `Pending live verification`. Each fact that only the Netcool administrator can confirm carries the mark `Pending Netcool administrator confirmation`. Each fact that only Mist can confirm carries the mark `Open, confirm with Mist`.

The runbook takes the mark of each fact from spec FR-003. A fact marked `Pending live verification` becomes `Verified (live)` after the live run, or it leaves the runbook. A fact marked `Pending Netcool administrator confirmation` becomes `Proposal`. A fact marked `Open, confirm with Mist` becomes `Open decision`.

## Source types

Each citation names its original source. This document uses these source types.

- A repository path with line numbers, relative to the repository root.
- An OpenAPI pointer. It names the file `documentation/mist-api-openapi31json.json`, the path or the schema name, and the operationId when one exists.
- An SDK pointer. It names the module under the `mistapi` package, the SDK version 0.64.1, and the line numbers.
- A vendor documentation URL.
- `Verified (live) on 2026-11-26`. A read-only run of the smoke test shows the fact.
- `Design decision of this feature`. A decision or a proposal is the only source, and no repository file states it.
- `Not verified (design assumption)`. An unverified reference is the only source, and no repository file or OpenAPI pointer states the fact.

## Source conflicts and gaps

The table lists each conflict between sources and each fact that no source gives. The owner resolves each conflict before the runbook states the fact.

| Number | Topic | Sources | Effect on this plan |
| --- | --- | --- | --- |
| C1 | Organization alarm search site filter | The OpenAPI file, operationId `searchOrgAlarms` at `/api/v1/orgs/{org_id}/alarms/search`, has the query filter `site_id`. It also has the query parameter `ack_admin_name`. | Resolved by the OpenAPI file. D2 keeps the organization search as the default. |
| C2 | Mist Edge event time parameters | The OpenAPI file, operationIds `searchOrgMistEdgeEvents` and `searchSiteMistEdgeEvents`, lists `start`, `end`, and `duration` for the organization and the site search. | Resolved by the OpenAPI file. D8 uses these parameters. Live question 2 checks the echoed collection window. |
| C3 | Organization webhook topics | The vendor webhook page `https://www.mist.com/documentation/webhooks/` limits organization webhooks to audit and device events. The repository page `documentation/api/orgs/POST_orgs_org_id_webhooks.md` line 11 lists more organization topics. Source for the further topics: Not verified (design assumption). | Resolved. D12 takes the scope from the live catalog, using the `for_org` member of each topic item. |
| C4 | Branch type | AGENTS.md allows `docs`. The constitution, `.specify/memory/constitution.md`, lists `fix`, `feat`, and `chore` only. | Resolved. The branch is `feat/4934-mist-netcool-runbook`. See the plan. |
| G1 | Paths that the first source review did not give | `countOrgInventory` at `/api/v1/orgs/{org_id}/inventory/count` and `listOrgMxEdges` at `/api/v1/orgs/{org_id}/mxedges`. The OpenAPI file holds both paths (checked 2026-11-25). | D14 checks both paths in the OpenAPI file. **Verified (live) on 2026-11-26**: the paths `/api/v1/orgs/{org_id}/inventory/count` and `/api/v1/orgs/{org_id}/mxedges` returned HTTP 200 in run 1 and in run 2 (SMK-10). |
| G2 | SDK timeout | The SDK 0.64.1 sets no timeout on its API GET calls (`mistapi/__api_request.py` lines 277, 298 to 300, 322 to 324, and 343). The SDK sets a timeout of 30 seconds only for the token validation in `_get_api_token_data` (`mistapi/__api_session.py` line 576). | D13 gives the mechanism: a daemon worker thread that waits at most `--call-timeout` seconds (default 30). |
| G3 | Session counting | No source checked states whether `APISession` exposes a `requests.Session`. | The client never reads the private `_session` attribute of the SDK. It records `sdk_retry_possible: true` (D5 and D13). |

## D1. Collection model

**Decision**: The baseline polls the four organization search families through REST. A hybrid design is an enhancement. The hybrid design adds webhooks for low latency and polling for reconciliation and replay. The owner approves the enhancement before any build.

**Rationale**:

The NOC proposal sets the baseline as polling every five minutes. Source: Design decision of this feature.

The vendor page states that webhooks push real-time events to a provided URL (https://www.mist.com/documentation/webhooks/). The model is therefore one-way.

The NOC requirement states that a fire-and-forget webhook does not meet the delivery requirement. Source: Design decision of this feature. The receiver needs durable delivery, retry, replay, or reconciliation. The vendor webhook pages give no webhook retry rule (https://www.mist.com/documentation/webhooks/ and https://www.mist.com/documentation/custom-http-headers-authentication-for-webhooks/).

**Alternatives considered**: A webhook-only feed, rejected because no retry rule is documented (https://www.mist.com/documentation/webhooks/). A hybrid baseline, rejected because the enhancement needs change approval (spec Clarifications, Q2, and FR-018).

**Sources**: The vendor URLs of this decision, Design decision of this feature for the NOC requirement, and spec FR-006, FR-017, and FR-018.

**Open, confirm with Mist**: The statement that Mist does not redeliver a failed POST is Not verified (design assumption). The vendor pages do not state redelivery. The runbook states this only after Mist confirms it.

## D2. Organization scope by default

**Decision**: Use the organization endpoints by default. Use the site endpoints for three cases only. The cases are the per-site statistics loop of menu 307, the investigation of one site, and a site filter that the organization search lacks. The organization alarm search can filter by `site_id`, and it also has the query parameter `ack_admin_name`. The device event, Mist Edge event, and system event searches of the organization have no `site_id` query parameter.

**Rationale**:

One organization search call covers all sites (OpenAPI pointer `searchOrgAlarms`, path `/api/v1/orgs/{org_id}/alarms/search`).

The menu 307 code calls the statistics endpoint once for each site (`src/operations/exporting/ap_warning_report/client.py` lines 116 to 133). Its call count grows with the site count (the call sites in `src/operations/exporting/ap_warning_report/client.py` lines 96 to 126 and 183 to 193).

The OpenAPI file, `documentation/mist-api-openapi31json.json`, shows that the GET operation `searchOrgAlarms` has the query parameters `site_id` and `ack_admin_name`. Conflict C1 is resolved by that file.

**Alternatives considered**: Site-level polling for every site, rejected because the call count grows with the site count (`src/operations/exporting/ap_warning_report/client.py` lines 116 to 133). Organization alarm search with one `site_id` filter for each site, rejected for the baseline because it repeats each call for each site.

**Sources**: `src/operations/exporting/ap_warning_report/client.py` lines 96 to 133 and 183 to 193, the OpenAPI pointer `searchOrgAlarms`, and the OpenAPI file, documentation/mist-api-openapi31json.json. The OpenAPI file has the `site_id` and `ack_admin_name` parameters of the organization alarm search. Conflict C1 is resolved by that file.

**Not observed in the live runs**: Whether the organization alarm search with a `site_id` filter returns the same alarms as the site search for one site. Neither run sent the filtered organization search. SMK-08 records the site search, and it returned HTTP 200 for each family in both runs. In run 2, the site search returned zero alarm records for the first site, and the organization alarm search returned alarm records. The two results were not compared.

## D3. Collection window

**Decision**: End each collection window 2 minutes before the current time. Overlap successive collection windows by 5 minutes. Both values are proposals until the live run measures the search delay.

**Rationale**:

The NOC proposal states that the search index can lag. Source: Not verified (design assumption). A collection window must end in the past, and successive collection windows must overlap.

No source checked gives an indexing delay or clock-skew guidance. The archived API pages (https://www.mist.com/documentation/mist-api-introduction/ and https://www.mist.com/documentation/mist-api-architecture/) do not discuss search.

The timestamps use UTC. Source: Design decision of this feature. The alarm item carries `timestamp` as a number of epoch seconds (OpenAPI pointer `components/schemas/alarm`, property `timestamp`). The device event item and the organization system event item carry a numeric `timestamp` (OpenAPI pointers `components/schemas/device_event` and `components/schemas/org_system_event`).

The menu 307 code uses a 3,600-second history window that ends at its cutoff (`src/operations/exporting/ap_warning_report/client.py` lines 145, 188 to 189, and 258). This is an existing precedent for a fixed history window.

**Alternatives considered**: A collection window that ends at the current time, rejected by the NOC proposal. A longer lag, rejected because no source gives a value that supports it.

**Sources**: Not verified (design assumption) for the search lag, and Design decision of this feature for the UTC statement. The menu 307 client, `src/operations/exporting/ap_warning_report/client.py` lines 145, 188 to 189, and 258. The OpenAPI pointers `components/schemas/alarm`, `components/schemas/device_event`, and `components/schemas/org_system_event`. Spec FR-007, FR-008, and Assumptions.

**Verified (live) on 2026-11-26** for the unit: `start` and `end` are epoch seconds. The echoed windows of 3600 seconds and 86400 seconds equal one hour and one day, in both runs. **Not observed in the live runs** for the search delay. Neither run compared each event time with the first search result that holds the event. The planning value of 2 minutes stays. Source for this measure: Design decision of this feature.

## D4. Pagination

**Decision**: Send `limit=1000` on each paged request. Follow a `next` value only when it passes the origin check. End the query when a page repeats, with the stop reason `RepeatedPage`. End each query at the page ceiling of 3 pages in the smoke test, with the stop reason `PageCeiling`. Mark a query that ends at the page ceiling as incomplete.

A production collector treats an incomplete collection as failed. It never clears an alarm from an incomplete collection.

**Rationale**:

The owner rule to pass `limit=1000` on Mist calls has this source: Design decision of this feature. The repository default page size is also 1000 (`.github/copilot-instructions.md` line 350).

The specification states no maximum for `limit` (OpenAPI pointer `components/parameters/limit`, which has `minimum` 0 and no `maximum`).

The search families take `search_after` as their only paging input (OpenAPI pointer `components/parameters/search_after`).

The SDK helper `get_all` has no iteration limit (`mistapi/__pagination.py` lines 39 to 74). It returns an empty list when the body holds an error (`mistapi/__pagination.py` lines 55 and 65 to 74).

A relative `next` resolves against the approved origin. An absolute `next` needs a check of its scheme, host, and path (spec FR-036).

The run tracks each continuation that it used, and it ends the query with the stop reason `RepeatedPage` on a cycle (spec FR-037).

A short page does not prove completion unless the endpoint contract supports that inference. Source: Design decision of this feature.

**Alternatives considered**: The SDK helper `get_all`, rejected because it has no ceiling and it hides an error body as an empty list (`mistapi/__pagination.py` lines 39 to 74). A page size of 5000, rejected because no source shows that the value is valid. SMK-09 records its behavior.

**Sources**: The OpenAPI pointers `components/parameters/limit` and `components/parameters/search_after`. The SDK pointer `mistapi/__pagination.py` lines 39 to 74. Design decision of this feature for the owner rule and the paging rules. Spec FR-009, FR-033, FR-035, FR-036, and FR-037.

**Verified (live) on 2026-11-26** for the form of `next`. Run 1 returned no `next` link. Run 2 returned a relative `next` link that carries `search_after`, on the device event search, which reached the page ceiling. Both runs show the behavior at `limit=5000`. The API reduced the limit to 1000 and returned HTTP 200 (SMK-09). **Verified (live) on 2026-11-26** for the `total` field of the alarm and system event searches, which equals the count endpoint in both runs (SMK-07). The device event total equals the count endpoint in run 1. In run 2, the device event search was incomplete, so SMK-07 skipped the comparison. SMK-07 gives no comparison for the Mist Edge search in either run, because the family table has no total for it.

## D5. Rate limits and the request budget

**Decision**: The token limit is 5,000 requests for each hour, with an hourly reset. The run ends with the rate-limit stop when `request_limit` minus `requests` is fewer than two times the request budget. The default request budget is 60 requests for each run.

For a poll every 5 minutes, the collector uses the formula R_hour = 12 times C, plus O. The value C is the sum, over the four families, of the page calls and the count calls in one cycle. The value O is the other calls in the hour.

**Rationale**:

The quota is 5,000 requests for each hour, with an hourly reset (https://www.mist.com/documentation/mist-api-introduction/, section Rate Limit). The HTTP 429 description names the 5,000 calls for each API token (OpenAPI pointer `components/responses/HTTP429`).

Rate limiting follows the individual organization token (https://www.mist.com/documentation/org-api-token/). User tokens of one account share one limit. Source: Not verified (design assumption).

The usage response gives `requests`, `request_limit`, and `seconds` (OpenAPI pointer `components/schemas/api_usage`).

The call formula in `src/operations/exporting/ap_warning_report/client.py` (lines 96 to 126 and 183 to 193) puts one menu 307 run near 3,144 calls. That is about 63 percent of the threshold. Other jobs that use the same token count against it.

The SDK retries HTTP 429 up to three times. It sleeps for the `Retry-After` value in seconds. Without that header, it sleeps for 5 times 2 to the power of the attempt number. The SDK pointer is `mistapi/__api_request.py` lines 186 to 201 and 229 to 241.

**Alternatives considered**: No budget, rejected because the hourly quota is shared. A per-run budget only, rejected because the hourly limit is the constraint.

**Sources**: The vendor pages https://www.mist.com/documentation/mist-api-introduction/ (section Rate Limit) and https://www.mist.com/documentation/org-api-token/. The OpenAPI pointers `components/responses/HTTP429` and `components/schemas/api_usage`. The repository file `src/operations/exporting/ap_warning_report/client.py` lines 96 to 126 and 183 to 193. The SDK pointer `mistapi/__api_request.py` lines 186 to 201 and 229 to 241. Spec FR-034, FR-038, SMK-04, and Clarifications, Q4.

**Not observed in the live runs** for the unit of `Retry-After`. No response in either run carried the header. The SDK code gives seconds (`mistapi/__api_request.py` lines 186 to 201). No vendor page checked gives the unit. **Not observed in the live runs** for the scope of the usage counter. The count fell from 11 used to 2 used between the two runs. No source checked names the scope of the usage counter. **Verified (live) on 2026-11-26** for the response header names. Run 1 returned 26 names, and run 2 returned 27 names. No name is a rate-limit header, and the OpenAPI file defines no rate-limit response header.

**Implementation check**: None. The client never reads the private `_session` attribute of the SDK (gap G3).

## D6. Tokens

**Decision**: Use one organization API token for each organization for polling. Give the token read-only privileges. Use a separate token for the AP Warning report only when it uses much of the hourly limit. The owner decides that case in Section 15 of the runbook.

**Rationale**:

The token types are user and organization (https://www.mist.com/documentation/org-api-token/). An organization token has scoped privileges (OpenAPI pointer `getSelf`, path `/api/v1/self`, property `privileges` with its `scope` member).

A user token shares the account limit. Source: Not verified (design assumption). It can block the portal login. Source: Not verified (design assumption).

The privilege role enum of `/api/v1/self` lists `admin`, `helpdesk`, `installer`, `read`, and `write` (OpenAPI pointer `getSelf`, path `/api/v1/self`, property `privileges` with its `role` member).

Source for the Helpdesk role of the read-only alarm token: Not verified (design assumption). The vendor administrator-roles page describes Helpdesk and Observer as read-only (https://www.mist.com/documentation/administrator-roles/). The vendor token page names no role for API tokens (https://www.mist.com/documentation/org-api-token/).

Read the token from the approved environment or the credential store. Redact complete secret values at the logging boundary (AGENTS.md, section Secrets).

**Alternatives considered**: A user token, rejected because its calls count against the account limit. A write-capable token, rejected because the smoke test records WARN for any role other than `read` (SMK-03), and polling needs only read access.

**Sources**: The vendor pages https://www.mist.com/documentation/org-api-token/, https://www.mist.com/documentation/administrator-roles/, and https://www.mist.com/documentation/mist-api-introduction/ (section Rate Limit). The OpenAPI pointer `getSelf` (path `/api/v1/self`). AGENTS.md (section Secrets). Not verified (design assumption) for the user token statements. Spec SMK-03, FR-032, and FR-044.

**Verified (live) on 2026-11-26** for the role name. The organization token carries the role `admin` in both runs. SMK-03 gives WARN, because a production collector must use a read-only token. **Not observed in the live runs** for an Observer role on API tokens. The token role is `admin`, so the runs did not test an Observer token. No vendor page checked names an Observer role for API tokens (https://www.mist.com/documentation/org-api-token/).

## D7. Device event volume

**Decision**: Send `device_type=ap` in each organization device event search. Use the server-side `type` filter with a comma-separated allowlist. The allowlist holds no spaces, brackets, or quotes. Before the owner approves the allowlist, use `countOrgDeviceEvents` with `distinct=type` to list the event types.

**Rationale**:

The organization device event search has the default `device_type` value `ap` (OpenAPI pointer `searchOrgDeviceEvents`, path `/api/v1/orgs/{org_id}/devices/events/search`). The SDK sends `device_type` only when the caller passes it (an inference from the SDK pointer `mistapi/api/v1/orgs/devices.py` line 259).

The count endpoint lists `type` in its `distinct` enum (OpenAPI pointer `countOrgDeviceEvents`, path `/api/v1/orgs/{org_id}/devices/events/count`). The `type` filter takes several comma-separated values (the description of the `type` parameter of `searchOrgDeviceEvents` in the OpenAPI file).

The NOC proposal reports thousands of device events in one 5-minute collection window. Source: Not verified (design assumption). The NOC proposal asks for an allowlist. It forbids spaces, brackets, and quotes in a `type` filter (Design decision of this feature, and spec FR-010).

The menu 307 code requests every event type and selects the types in code (`src/operations/exporting/ap_warning_report/client.py` lines 183 to 193, and `src/operations/exporting/ap_warning_report/codes.py` lines 178 to 183).

**Alternatives considered**: Selection in code only, rejected because it transfers thousands of records for each collection window (`src/operations/exporting/ap_warning_report/client.py` lines 183 to 193). No `device_type` value, rejected because an explicit value does not depend on the server default.

**Sources**: The repository files `src/operations/exporting/ap_warning_report/client.py` lines 183 to 193 and `src/operations/exporting/ap_warning_report/codes.py` lines 178 to 183. The OpenAPI pointers `searchOrgDeviceEvents` and `countOrgDeviceEvents`. The SDK pointer `mistapi/api/v1/orgs/devices.py` line 259. Not verified (design assumption) for the event volume, and Design decision of this feature for the allowlist. Spec FR-010 and SMK-09.

**Verified (live) on 2026-11-26** for the default device type. The search does not return only AP events when `device_type` is absent. Run 1 returned the types `ap` and `gateway`. Run 2 returned the types `ap`, `gateway`, and `switch`. In run 2, the `device_type=gateway` search returned three event types, and the `device_type=switch` search returned five event types (SMK-09). Run 1 returned no switch record. **Not observed in the live runs** for the event count of each type in one collection window. The evidence keeps no count for each type.

## D8. Mist Edge events

**Decision**: Use the organization Mist Edge event search with its `start`, `end`, and `duration` parameters. Treat a zero Mist Edge result as normal only when the organization Mist Edge device list holds no device. Read that list with `listOrgMxEdges` (SMK-10).

**Rationale**:

The OpenAPI file gives the GET operations `searchOrgMistEdgeEvents` and `searchSiteMistEdgeEvents` the query parameters `start`, `end`, and `duration`, so conflict C2 is resolved by that file. The response of `searchOrgMistEdgeEvents` has no `total` property, so SMK-07 has no comparison for Mist Edge events.

The OpenAPI file gives `duration` the default value `1d` for each search family.

No source checked states the behavior of an organization without Mist Edge events. The inference that such an organization sends no `mxedge-events` message is Not verified (design assumption). A silent `mxedge-events` topic cannot be checked in the portal. Source: Not verified (design assumption).

**Alternatives considered**: Treat every zero result as a failure, rejected because a zero result is normal for an organization without Mist Edge devices. SMK-06 records WARN for it. Use no time parameter, rejected because no source checked states the default collection window.

**Sources**: The OpenAPI pointers `searchOrgMistEdgeEvents`, `searchSiteMistEdgeEvents`, and `components/schemas/mxedge_event`, Not verified (design assumption) for the inference and the silent-topic statement, and spec SMK-06, SMK-09, and SMK-10. The OpenAPI file, documentation/mist-api-openapi31json.json, has the parameters `start`, `end`, and `duration` of the Mist Edge search.

**Verified (live) on 2026-11-26** for the collection window. Without a time parameter, the Mist Edge search echoes a window of 86400 seconds. With `duration=1h`, it echoes a window of 3600 seconds. Both runs show the same windows (SMK-09). **Verified (live) on 2026-11-26** for the path `/api/v1/orgs/{org_id}/mxedges` (gap G1). The request returned HTTP 200 in both runs (SMK-10).

## D9. System events

**Decision**: Use the organization system event search (`searchOrgSystemEvents`) for the feed. Use `/api/v1/const/system_events` (`listSystemEventsDefinitions`) as the catalog of system event types. The meaning of each type waits for the live catalog.

**Rationale**:

The catalog items have the required fields `display` and `key` (OpenAPI pointer `components/schemas/const_event`).

The organization system event item has seven fields: `change_cat`, `metadata`, `org_id`, `scope`, `site_id`, `timestamp`, and `type` (OpenAPI pointer `components/schemas/org_system_event`).

The site system search response refers to the device event schema, which differs from the organization response (OpenAPI pointer `/api/v1/sites/{site_id}/events/system/search`, response 200, which refers to `response_device_events_search`).

No source checked defines "system events" as a Mist object. The audit log is a different source of administrator activity. Source: Not verified (design assumption). The system event definitions are a gap. Source: Design decision of this feature.

**Alternatives considered**: The audit log, rejected because it records logins and administrator activity, not system events. Source: Design decision of this feature.

**Sources**: The OpenAPI pointers `components/schemas/org_system_event`, `components/schemas/const_event`, and `/api/v1/sites/{site_id}/events/system/search`. Not verified (design assumption) for the audit log. Design decision of this feature for the system event gap. Spec FR-040, SMK-05, and SMK-06.

**Verified (live) on 2026-11-26** for the catalog names and sizes (SMK-05). The six catalogs returned HTTP 200 in both runs. The sizes are: `alarm_defs` 248 entries, `device_events` 387 entries, `mxedge_events` 40 entries, `system_events` 18 entries, `ap_led_status` 37 entries, and `webhook_topics` 31 entries. Each system event entry carries the fields `display`, `group`, and `key`. **Not observed in the live runs** for the meaning of each type. The catalogs give a display text for each type. **Not observed in the live runs** for the cause of a zero result. Neither run tested an organization without system events.

## D10. AP Warning report (menu 307)

**Decision**: Keep menu 307 as a separate source of rows. It is not equivalent to the organization alarm and device event feeds. Its rows come from the `last_trouble` field of the AP site statistics. It uses a 15-minute trouble window and a 14-rule recovery classifier.

Each run costs `T = S + 4 + 2C` requests when each list takes one page. The value S is the number of sites, and the value C is the number of candidate APs. The owner decides whether to retain or retire the report (Section 15).

**Rationale**:

The module reads `last_trouble` through the site statistics endpoint (`src/operations/exporting/ap_warning_report/client.py` lines 124 to 126, and `src/operations/exporting/ap_warning_report/rows.py` lines 47 to 59).

The module sends no alarm search (`documentation/menu-api/safe.md` lines 1323 to 1354, the generated endpoint map of menu 307).

The warning rule is in `src/operations/exporting/ap_warning_report/rows.py` (lines 47 to 54 and 107 to 113) and `src/operations/exporting/ap_warning_report/codes.py` (lines 16, 18 to 31, and 47 to 61). The recovery rules are in `src/operations/exporting/ap_warning_report/codes.py` (lines 146 to 278). The request formula is in `src/operations/exporting/ap_warning_report/client.py` (lines 96 to 126 and 183 to 193).

The inference that the report is not equivalent to the alarm and event searches is Not verified (design assumption).

The unattended run needs an organization. The `--org` option or the `org_id` setting provides it (`MistHelper.py` lines 7809 and 7840 to 7846, and `src/foundation/runtime/config/config_utils.py` lines 190 to 209).

**Alternatives considered**: Replace the per-site reads with the organization statistics endpoint. The earlier design chose that endpoint, but the code does not use it (`specs/numbered/0/0/1/2/1/3/3/0/4590-ap-warning-report/design/research.md` line 5, and `src/operations/exporting/ap_warning_report/client.py` lines 124 to 126).

**Risks** in the menu 307 code are these. The event search echo check is risk 1 (`src/operations/exporting/ap_warning_report/client.py` lines 166 to 167). A silent end to paging is risk 2 (`client.py` lines 33 to 35). Untimed trouble codes that qualify are risk 3 (`rows.py` line 111). The 10-page cap is risk 9 (`client.py` lines 160, 174 to 175, and 179). The `last_trouble` field, documented as a switch field, is risk 8 (`documentation/api/sites/GET_sites_site_id_stats_devices.md` lines 1101 and 3769).

**Sources**: The repository files under `src/operations/exporting/ap_warning_report/` (`client.py`, `rows.py`, `codes.py`, and `operation.py`), `MistHelper.py`, `documentation/menu-api/safe.md`, `documentation/ap-warning-report.md`, `documentation/noc-runbooks/AP_WARNING_REPORT_MENU_307.md`, `specs/numbered/0/0/1/2/1/3/3/0/4590-ap-warning-report/design/research.md`, and spec FR-005 (question 2).

**Verified (live) on 2026-11-26** for the field `last_trouble` in the organization AP statistics. No AP statistics item carries the field in either run. **Not observed in the live runs** for the `last_trouble` values on site AP records. The menu 307 code reads site statistics, and the live runs read organization statistics only. **Verified (live) on 2026-11-26** for the echo of the Mist Edge event search. The search echoes the requested start and end in both runs (SMK-09). **Not observed in the live runs** for the echo of the device event search. **Verified (live) on 2026-11-26** for the count. The organization statistics endpoint and the inventory count of AP devices give the same count in both runs (SMK-10). **Not observed in the live runs** for the match of the AP records between the two endpoints. The runs compared counts only.

## D11. Netcool mapping

**Decision**: Mark the IBM facts as `Verified (vendor documentation)`. The facts are the severity values 0 to 5 and the type values 1, 2, and 13. Deduplication uses `Identifier` with `Tally` and `LastOccurrence`. The standard automations are `generic_clear`, `delete_clears`, and `expire`.

The Netcool administrator selects the receiver. The field rules and the severity map are proposals.

**Rationale**:

The IBM alerts.status table page lists the columns, the severity values from 0 Clear to 5 Critical, and the type values (https://www.ibm.com/docs/en/netcoolomnibus/8.1.0?topic=tables-alertsstatus-table). Deduplication is described at https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/install/concept/omn_con_os_alertprocessing.html. The standard automations are described at https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/admin/reference/omn_adm_sql_standardnetomautomatns.html.

The Mist alarm severity values are `critical`, `info`, and `warn` (OpenAPI pointer `searchOrgAlarms`, parameter `severity`). Device events use `notice` and `warn` (OpenAPI pointer `components/schemas/device_event`, property `ev_type`). Mist Edge events use `normal`, `critical`, `high`, and `warning` (OpenAPI pointer `components/schemas/mxedge_event`, property `severity`).

A map from these values to Netcool severities is a proposal.

The probe HTTP interface is disabled by default, and it does not check credentials by default (https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/probegtwy/task/omn_prb_remotelymanage.html). The ObjectServer HTTP interface is disabled by default. It uses basic HTTP authentication (https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/api/task/omn_api_enableinterfaces.html and https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/api/reference/omn_api_http_httpinterface.html). The Netcool administrator selects the receiver (spec Clarifications, Q3).

Caution: The probe HTTP interface permits any user credentials by default, which can let an unknown client send events. Enable authentication and TLS before the feed sends events.

**Gaps**: The fields that `generic_clear` matches between a problem and a resolution are not stated (https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/admin/reference/omn_adm_sql_standardnetomautomatns.html). The `Identifier` example includes `@Type`. That example gives a problem and its resolution different identifiers, and IBM does not state it (https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/probegtwy/concept/omn_prb_howuniqueidsconstruct.html, an inference). The ExpireTime defaults come from a table summary, not from a quote (https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/install/task/omn_con_ext_settingeventstoexpireauto.html). The vendor index has no page for the Probe for Message Bus (https://www.ibm.com/docs/en/netcoolomnibus/8.1.0?topic=probes-probe-message-bus returned the index page, not a topic).

**Alternatives considered**: The Probe for Message Bus, rejected because the vendor index has no topic for it (https://www.ibm.com/docs/en/netcoolomnibus/8.1.0?topic=probes-probe-message-bus). A direct insert into `alerts.status`, rejected because no vendor page checked states that a POST inserts rows into that table (https://www.ibm.com/docs/en/SSSHTQ_8.1.0/omnibus/wip/api/reference/omn_api_http_httpinterface.html).

**Sources**: The IBM pages that this decision names, the OpenAPI pointers for the Mist severity values, and spec FR-016, FR-017, and Clarifications, Q3.

**Pending Netcool administrator confirmation**: Every Netcool item in this decision. The live smoke run cannot test Netcool.

## D12. Webhooks

**Decision**: Take the webhook topics from the live catalog (`/api/v1/const/webhook_topics`), and take the topic scope from the `for_org` member of each catalog item. SMK-05 and SMK-10 record the catalog and the organization webhooks. The runbook gives the signature headers and the verification steps.

Source IP addresses appear only as a proposal. The owner confirms them before a firewall change. The smoke test creates, changes, and pings no webhook (FR-030).

**Rationale**:

The vendor example lists ten topic keys. The page does not state that the list is complete (`documentation/api/constants/GET_const_webhook_topics.md` lines 64 to 109).

The topic keys use hyphens. The webhook keys in the OpenAPI file use underscores (OpenAPI pointer, `webhooks` section, keys `device_events` and `mxedge_events`, with the topic values `device-events` and `mxedge-events`). The repository page `documentation/api/orgs/POST_orgs_org_id_webhooks.md` line 11 names `device_events` and `mxedge_events` with underscores.

The organization topics differ between sources (conflict C3).

The repository page `documentation/api/orgs/POST_orgs_org_id_webhooks.md` lines 144 to 149 names the headers `X-Mist-Signature-v2` and `X-Mist-Signature`. The header `X-Mist-Signature-v2` equals HMAC-SHA256 of the body with the secret, and the header `X-Mist-Signature` equals HMAC-SHA1, as stated in the repository page `documentation/api/orgs/POST_orgs_org_id_webhooks.md` line 149. The vendor archive does not say how Mist sends or uses the secret (https://www.mist.com/documentation/webhooks/).

The receiver prefers the v2 header for a new receiver. The receiver verifies the signature over the raw body. The encoding, hex or base64, is not stated. Source: Design decision of this feature.

The archived page https://www.mist.com/documentation/ports-enable-firewall/ gives the source IP groups for each region. The Global 01 group is 54.193.71.17 and 54.215.237.20. The extraction of that table assigned each IP group to a region by column order. Each group needs a check against the current vendor documentation before a firewall rule changes.

**Alternatives considered**: A fixed topic list in the runbook, rejected because the live catalog is the source. Source IP addresses copied from the archived table, rejected because the region assignment by column order is not verified.

**Sources**: The vendor pages https://www.mist.com/documentation/webhooks/ and https://www.mist.com/documentation/ports-enable-firewall/ (archived). The repository files `documentation/api/orgs/POST_orgs_org_id_webhooks.md` lines 11 and 144 to 149, and `documentation/api/constants/GET_const_webhook_topics.md` lines 64 to 109. The OpenAPI pointer for the `webhooks` section. Design decision of this feature for the receiver rules. Spec FR-030 and SMK-05.

**Verified (live) on 2026-11-26** for the topic list. The catalog `webhook_topics` returned 31 topics in both runs (SMK-05). Each topic carries the field `key`. The field `for_org` is true for 11 topics, and absent for 20 topics. The field `has_delivery_results` is true for 5 topics, and absent for 26 topics. The field `allows_single_event_per_message` is true for 3 topics, and absent for 28 topics. The field `internal` appears in some topics. **Verified (live) on 2026-11-26** that the organization webhook request returned HTTP 200 in both runs (SMK-10). The count, the topics, and the enabled flags of the organization webhooks are organization data, so this document does not record them.

**Open, confirm with Mist**: The encoding of the signature. The retry rule (D1). The source IP addresses for each region.

## D13. Smoke test design

**Decision**: Build a command-line smoke test in `scripts/netcool_runbook_smoke/`. The client uses `mistapi.APISession` for GET calls only. The client reads `status_code` before it reads `data`. The client never reads the private `_session` attribute of the SDK. The evidence record holds `sdk_retry_possible: true`, because the SDK can retry inside one client call.

A rejected token (HTTP 401) stops the run with exit code 2. HTTP 403 fails one check. The options, the checks SMK-01 to SMK-10, and the exit codes 0 to 6 follow spec FR-045 and `design/contracts/smoke-cli.md`.

**Rationale**:

The SDK does not raise an exception for an HTTP 4xx or 5xx response. It returns the status code (SDK pointer `mistapi/__api_request.py` lines 228 to 249).

An empty list can hide a rejected request (`mistapi/__pagination.py` lines 55 and 65 to 74). The data of an `APIResponse` is `{}` when no response exists (`mistapi/__api_response.py` lines 46 to 48).

The session raises `ValueError` on HTTP 401, and `ConnectionError` on a connection failure, during token validation (`mistapi/__api_session.py` lines 592 to 618).

The SDK logs HTTP 400 and above at error level. It logs the response body only at debug level (`mistapi/__api_response.py` lines 60 to 64).

**Gap G2, timeout**: The SDK sets no timeout on its API GET calls. The call `self._session.get(url)` in `mistapi/__api_request.py` line 277 has no timeout. The token validation request in `_get_api_token_data` has a timeout of 30 seconds (`mistapi/__api_session.py` line 576).

The spec requires a timeout check for the API calls. No source checked gives a documented timeout setting. The client runs each SDK call in a daemon worker thread and waits at most `--call-timeout` seconds (default 30) for the result. The abandoned thread is a daemon thread, so it cannot block the exit. The `mistapi` package exports `arun`, which runs a synchronous function in a worker thread (`mistapi/__init__.py` lines 48 to 85), and the design uses the same mechanism.

**Timeout rule**: A timeout does not retry. The first timeout fails the smoke check with the error `Timeout`. The second timeout in one run ends the run with the rate-limit stop (exit code 3). The cause of a timeout can be an SDK sleep on HTTP 429, or a network fault. The rule bounds the wait for stalled calls to about 60 seconds.

**Budget rule**: The login token validation (one GET) counts as one request. Each client call and each client retry counts as one request, including each timeout. The client never reads the private `_session` attribute of the SDK. The SDK can retry HTTP 429 at most three times inside one call. The client cannot count those retries, so the evidence records `sdk_retry_possible: true`. SMK-04 ends the run with the rate-limit stop when the remaining requests of the hour are fewer than two times the request budget.

**Assumption A1**: A connection failure during token validation maps to exit code 2. The coordinator accepted this mapping. Source: Design decision of this feature. The regional host belongs to the configuration, and spec FR-045 states the mapping.

**Alternatives considered**: A direct HTTP library, rejected because the constitution forbids direct HTTP when a mistapi method exists. The `get_all` helper, rejected for the reasons in D4.

**Sources**: The SDK 0.64.1 pointers `mistapi/__api_request.py`, `mistapi/__api_response.py`, `mistapi/__api_session.py`, `mistapi/__pagination.py`, and `mistapi/__init__.py`. `MistHelper.py` lines 2811 and 2817 (the regional host default). Design decision of this feature for the decisions of this section. Spec FR-030 to FR-048.

**Pending implementation check**: The timeout mechanism (gap G2).

**Verified (live) on 2026-11-26** for each check result. The table gives the status of each check in run 1 and run 2. The outcome is Pass, with exit code 0, in both runs.

| Check | Run 1 status | Run 2 status |
| - | - | - |
| SMK-01 | PASS | PASS |
| SMK-02 | SKIP | SKIP |
| SMK-03 | WARN | WARN |
| SMK-04 | PASS | PASS |
| SMK-05 | SKIP | SKIP |
| SMK-06 | WARN | WARN |
| SMK-07 | INFO | SKIP |
| SMK-08 | WARN | WARN |
| SMK-09 | WARN | WARN |
| SMK-10 | PASS | PASS |

**Verified (live) on 2026-11-26** for the response header names. Run 1 returned 26 names, and run 2 returned 27 names. No response carried `Retry-After` in either run, and no name is a rate-limit header.

## D14. Offline document test

**Decision**: `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py` reads the runbook and the specification with no token and no network access. The test checks four items.

First, each of the 25 operations in the specification section "Mist API Operations" has a GET operation at its path in the OpenAPI file. Its SDK module defines a function with its name.

Second, each Mist API path in the runbook has a GET operation in the OpenAPI file. The paths in code spans, code blocks, and tables count too. Third, the headings of FR-002 exist in order. Fourth, the runbook holds no UUID, MAC address, email address, or token pattern (spec FR-051).

The test prints the line number and the kind of each match, and it never prints the value. It writes the number of paths, headings, and lines scanned that it examined. It fails when it cannot read a file.

**Rationale**:

The guard `tests/guardrails/test_mistapi_spec_modules.py` checks only the last pair of each spec file, as tracked in Issue #4935.

The guard reads a line `- **operationId**: <id>` and a line `- **mistapi SDK module**: <module>` (`tests/guardrails/test_mistapi_spec_modules.py`, lines 71 to 73).

The precedent `scripts/verify_ssr_commands.py` raises an error for zero items and for a missing input.

The test quality ratchet requires a Mist API test module to cover the HTTP and failure cases. It applies when the module imports `mistapi` at module scope (`.github/copilot-instructions.md`, section "Test quality ratchet", and `.github/test-quality-config.toml` line 66).

**Design choice**: The test reads each SDK module as source with the `ast` module. The test then needs no module-scope import of `mistapi`, and it runs offline.

**Alternatives considered**: The existing guard alone, rejected because it checks two operations only. A module-scope import of `mistapi`, rejected because it adds the case requirements of the ratchet to an offline test.

**Sources**: `tests/guardrails/test_mistapi_spec_modules.py` (lines 71 to 73), `scripts/verify_ssr_commands.py`, `.github/copilot-instructions.md` (section "Test quality ratchet"), `.github/test-quality-config.toml` (line 66), Issue #4935, and spec FR-049 to FR-054.

**Live verification**: None. The test checks the paths and the function names in the repository files, including `countOrgInventory` and `listOrgMxEdges` (gap G1).

## D15. Naming and STE rules

**Decision**: Use full descriptive names, for example `for device in devices`. Use one term for each concept. Use the term "site" for a Mist site, and never "store" for a site. Use the term "collection window", and never "time window". Name only the approved products and the generic role terms.

Use the placeholders that spec FR-024 lists. Write all prose in Simplified Technical English. Run `ste-linter` in both modes. Use ASCII only.

**Rationale**:

The repository gate runs the linter with the repository configuration and a score floor of 80 (`.github/copilot-instructions.md`, section "Local gates", row STE, and the key `min_score` in `.ste-linter.toml`).

The licensed dictionary mode checks word choice. The no-dictionary mode checks structure only (the comments at the top of `.ste-linter.toml`).

The devtools version can differ between local and CI runs. Source: Not verified (design assumption). The plan therefore runs both modes with margin.

The repository forbids semicolons, contractions, Latin abbreviations, and phrasal verbs in prose (AGENTS.md, section Writing style, line 50, and `documentation/ASD-STE100_writing-guide.md`).

Use straight quotes and two hyphens for a dash. Source: Design decision of this feature.

The NOC proposal forbids naming other companies and products, and it asks for the term "site". The existing runbooks in `documentation/noc-runbooks/` show term drift, such as gateway, router, and box. Source of the first fact: Design decision of this feature. Source of the second fact: `documentation/noc-runbooks/`.

**Alternatives considered**: The term "store", rejected by the NOC proposal. Source: Design decision of this feature.

**Sources**: `documentation/noc-runbooks/` (existing runbooks, term drift). `.ste-linter.toml`, `.github/copilot-instructions.md` (section "Local gates"), AGENTS.md (section Writing style, line 50), and `documentation/ASD-STE100_writing-guide.md`. Design decision of this feature for the naming rules. Spec FR-021 to FR-025.

**Live verification**: None. The repository gates check the naming and STE rules.
