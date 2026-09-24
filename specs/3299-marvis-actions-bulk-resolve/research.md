# Research: Marvis Actions export and bulk resolve

**Issue**: #3299 | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

This file records the evidence behind each design decision. The agent read the Mist
UI bundle and made read-only API requests. No request in this research changed Mist
data.

## Sources

| Source | What it proves |
| - | - |
| Mist UI bundle `admin2.21.1765-hotfix`, chunk 490, read 2026-09-23 | The paths, the query parameters, the resolve body, the codes, the status names, and the topic names that the Mist UI uses |
| Live GET requests to the lab organization on 2026-09-23 and 2026-09-24 | The response shape, the paging, and the key fields |
| `documentation/mist-api-openapi31yaml.yaml` | No `labs` path is documented. The only Marvis Actions path is the MSP count. |
| `mistapi` 0.64.0 in the worktree `.venv` | No method exists for the `labs` paths. `countMspsMarvisActions` exists for the MSP count. |

## R1. The list endpoint

**Decision**: Read `GET /api/v1/labs/orgs/{org_id}/suggestion` with
`query=get_suggestion`, `resolve_wcid=true`, `limit`, and `page`.

**Evidence**:

- The Mist UI Marvis Actions page sends this request.
- The response is `{"results": [...], "page": 1, "limit": 50, "total": 112}`.
- The first page number is 1. Three pages of 50 returned 50, 50, and 12 rows, with no
  row on two pages.
- The server does not cap `limit` at 1000. A request with `limit=5000` returned all
  112 rows and echoed `limit` 5000. The operation still pages, because a large
  organization can hold more rows than one response should carry.
- The server accepts the filters `category`, `symptom`, `status` (one value), and
  `active`. The operation reads every row and filters in memory, because the topic
  table needs the count of every topic.

**Paging rule**: Stop when a page is empty. When `total` is a number, stop when the
count of rows read reaches `total`. When `total` is absent, stop when a page holds
fewer rows than the `limit` that the response states. Stop after 100 pages in every
case.

**Alternatives rejected**:

- `GET /api/v1/labs/orgs/{org_id}/suggestions?query=get_suggestion` (plural path).
  It returns at most 100 rows and does not page.
- `GET /api/v1/orgs/{org_id}/alarms/search?group=marvis`. This is the older alarm
  view. It does not carry the `row_key` that the resolve request needs.

## R2. The schema endpoint

**Decision**: Read `GET /api/v1/labs/suggestions_schema` for the recommended action
text. Keep a built-in catalog of the category names and the subcategory names.

**Evidence**:

- The response is `{"data": [...]}` with 35 entries. Each entry holds `category`,
  `symptom`, `display_name`, `recommended_action`, `detection_logic`, and other
  fields.
- The Mist UI list does not read `display_name`. It uses its own name map. Two
  schema names differ from the UI names: the schema calls `bad_wan_link`
  "Intermittent WAN Connectivity" and calls `intermittent_wan_connectivity` "Bad WAN
  Uplink". The UI calls `bad_wan_link` "Bad WAN Uplink".
- The operation therefore uses the UI names from its built-in catalog first. It uses
  the schema name only for a topic that the catalog does not hold.

**Category names from the UI**: `ap` Wireless, `application` Data
Center/Application, `client` Clients, `connectivity` Connectivity, `gateway` WAN,
`layer_1` Layer 1, `security` Security, and `switch` Wired.

## R3. The resolve endpoint

**Decision**: Send one `PUT /api/v1/labs/orgs/{org_id}/suggestions` request for each
action, one at a time.

**Evidence**: The Mist UI "Resolve" dialog builds one body and loops over the checked
rows with `await`. Each request carries:

```json
{
  "row_key": "<row_key of the action>",
  "status": "resolved",
  "label": "suggested",
  "comment": "",
  "resolve_time": 1790222367274
}
```

- `resolve_time` is epoch milliseconds, and the dialog sets it one time for the batch.
- The dialog also adds `suggestion_id: a.id`. Live rows hold no `id` field, so the
  value is `undefined`, and the browser drops it from the JSON text. The operation
  therefore does not send `suggestion_id`.
- The RMA flow and the AP upgrade flow send the same body with `label` `suggested`
  and an empty comment. The RMA flow runs 10 requests in parallel. The operation
  sends one request at a time. One request for each action is the documented UI
  behavior, and a sequential loop is easy to stop.

**Alternatives rejected**: A batch body with many row keys. No UI flow sends one, so a
guess could fail or could change the wrong rows.

## R4. The resolution codes

| Code (`label`) | Text in the Mist UI | Comment |
| - | - | - |
| `suggested` | Solved using the Mist suggested action | Optional |
| `nonsuggested` | Solved using another method (please comment below) | Required |
| `known` | A known issue and should be ignored in the future | Optional |
| `invalid` | Incorrectly listed as an issue | Optional |

The UI dialog preselects `suggested`. The operation does the same, and it accepts the
word `other` for `nonsuggested`, because the user asked for "some sort of other
category".

## R5. The status values

| Status | Text in the Mist UI | Open tab | Resolve target |
| - | - | - | - |
| `open` | Open | Yes | Yes |
| `inprogress` | In Progress | Yes | Yes |
| `reoccured` | Reoccurred | Yes | Yes |
| `resolved` | Resolved By User | No | No |
| `validated` | AI Validated | No | No |
| `marvis_self_driven` | Marvis Self Driven | No | No |
| `expired action` | Expired Action | No | No |

The API spells `reoccured` with one `r`. The code must use that spelling.

## R6. Recoverability

**Decision**: Use the signal word Caution for the resolve, not Warning.

**Evidence**: The UI status cell shows read-only text for `reoccured`, `validated`,
and `marvis_self_driven`. For every other status it shows a dropdown with Open, In
Progress, and Resolved, minus the current status. A user-resolved action therefore
returns to Open with one click. The bulk Status button offers the same three values
for checked rows. The UI permission is `canUpdateMarvisActionsStatus`, which the
admin, write, and helpdesk organization roles hold.

## R7. The keys

**Decision**: `uuid` is the natural key of an action. `row_key` addresses the resolve
request.

**Evidence**:

- The `uuid` field is present and unique on all 112 live rows.
- For 108 of the 112 rows, `uuid` equals `uuid3(NAMESPACE_X500, row_key)`. The key is
  therefore stable across reads. The other 4 rows use a different input, and their
  `uuid` is still unique.
- The `row_key` field holds `&` and `/`, so it is not a valid ArangoDB `_key`.
- The `unique_key` field repeats across rows, so it is not a key.
- The `suggestion_id` field is present on only 64 of 112 rows.

A row that holds no `uuid` receives `uuid3(NAMESPACE_X500, row_key)`, so it never
receives a random key.

## R8. The site names

**Decision**: Read the site list one time through `mistapi.api.v1.orgs.sites.listOrgSites`
and `mistapi.get_all`.

**Evidence**: Most rows carry only `site_id`. Gateway rows also carry `site_name` in
`details.impacted_tuple`. A NOC report needs the site name. One request for each run
costs little.

## R9. The operations portal

**Evidence**: `web_portal/services/operation.py`.

- The portal runs only the `safe` and `interactive_safe` classes.
- The browser sends one answer for each control, in control order, and a blank
  answer for an empty control. An operation that asks fewer questions leaves the
  rest in the queue, and the queue discards them. An operation that asks more
  questions reads an end-of-input, and `safe_input` returns the default.
- The portal marks a run as failed when a log line holds "could not", "failed to",
  or "error fetching". It reports a missing input when a line holds "no value
  provided". A run with no file completes only when a line explains the empty
  result.
- The operation must therefore never log "could not" or "failed to" on a normal
  path. It uses "returned no data" for a fallback.
- The Stop button writes `stop_loop.txt`, and `ConfigUtils.check_stop_signal`
  consumes it.

**Decision**: The prompt order is fixed: mode, category, subcategory, resolution code,
comment, and confirmation. The portal row holds six controls in that order.

## R10. The request budget

- The report modes cost one schema read, one list read for each 1,000 rows, and one
  site list read for each 1,000 sites.
- A resolve run adds one write for each target and one more list read at the end.
- Every agent shares one Mist token of about 5,000 requests each hour. The cap of 500
  writes for each run keeps one run inside that budget.
- `mistapi` retries HTTP 429 by itself. `AdaptivePacer` waits between writes.

## R11. Out of scope

| Endpoint | Why the feature does not call it |
| - | - |
| `POST /api/v1/labs/sites/{site_id}/suggestions/fix` | It starts a Marvis self-drive fix, which changes device configuration. |
| `POST /api/v1/orgs/{org_id}/tickets` | It opens an RMA support ticket. |
| `POST /api/v1/labs/orgs/{org_id}/jcloud/request_virtualassistant_url` | It opens a Marvis chat session. |
| `GET /api/v1/labs/orgs/{org_id}/suggestion?query=time_series` | It returns a count trend, not the rows. |
| `GET /api/v1/labs/orgs/{org_id}/suggestion?query=group_by_category_symptom` | It returns counts. The operation counts the rows it already holds. |
| `GET /api/v1/labs/orgs/{org_id}/suggestion_detail/{id}/suggestion_id` | It returns one detail record. The list already carries the fields the report needs. |
| `GET /api/v1/msps/{msp_id}/suggestion/count` | It is documented, but it returns MSP counts only. |

The endpoint report names each of these, so a NOC engineer knows they exist.
