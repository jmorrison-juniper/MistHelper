# Marvis Actions API endpoints (menu 270)

This report lists each Mist API endpoint that menu 270 calls. Menu 270 exports the
Marvis Actions of an organization, and it resolves open actions in bulk. Use this
report as an example when you build a similar tool. Issue #3299 tracks the feature.

The examples use placeholder values. Replace `<org_id>`, `<API token>`, and
`<row_key>` with your own values. A value such as `<uuid>` or `<mac>` in a response
example replaces a real identifier.

Caution: three of the four endpoints are `labs` endpoints, so a Mist release can
change them without notice and stop your script. The OpenAPI document of Mist does
not describe the `labs` endpoints, and `mistapi` 0.64.0 holds no method for them. If
a request returns HTTP 404 or a changed response shape, compare the request with the
Mist UI again. MistHelper confirmed each endpoint against the Mist UI version
`admin2.21.1765-hotfix` on 2026-09-23.

## Summary

| Step | Method | Path | Purpose | Modes | Changes Mist data |
| - | - | - | - | - | - |
| 1 | GET | `/api/v1/labs/orgs/{org_id}/suggestion` | Read the Marvis Actions list, one page at a time. | 1, 2, 3, 4 | No |
| 2 | GET | `/api/v1/labs/suggestions_schema` | Read the topic names and the recommended actions. | 1, 2, 3, 4 | No |
| 3 | GET | `/api/v1/orgs/{org_id}/sites` | Read the site names. | 1, 2, 3, 4 | No |
| 4 | PUT | `/api/v1/labs/orgs/{org_id}/suggestions` | Resolve one action. | 3 | Yes |
| 5 | GET | `/api/v1/labs/orgs/{org_id}/suggestion` | Read the list again to verify each resolve. | 3 | No |

The list path ends in `suggestion`. The resolve path ends in `suggestions`. Do not
mix the two paths.

The menu has four modes.

- Mode 1 exports every action.
- Mode 2 exports the open actions only.
- Mode 3 resolves the open actions that the filter selects.
- Mode 4 exports the closed actions only. Issue #3342 added this mode.

A closed action holds a status that the Open tab of the Mist UI does not show. See
[Status values](#status-values). The columns `status_name`, `label_name`, `comment`,
`resolve_time_iso`, and `validation_time_iso` show how and when each action closed.
Mode 4 sends the same GET requests as mode 1, and it changes no Mist data.

No `search` endpoint serves the Marvis Actions list. The older alarm search is not
a replacement, because its rows hold no `row_key`. The `marvis_configs` search is
not a replacement either, because it reads a different object. See
[Endpoints that menu 270 does not call](#endpoints-that-menu-270-does-not-call).

## Common request values

| Item | Value |
| - | - |
| Base URL | `https://<MIST_HOST>`. The `MIST_HOST` value in `.env` sets the host, for example `api.mist.com`. |
| Authentication | The header `Authorization: Token <API token>`. |
| Content type | `application/json` for the PUT body. |
| Organization | The organization UUID. The Mist portal URL shows it after `org_id=`. |
| Role | The research used an organization token with the admin role. See [Permissions](#permissions). |

Warning: a person who reads your API token can change your organization with it. Do
not write a token into a report, a ticket, a chat message, or a log file. If a token
becomes visible, revoke it in the Mist portal.

The `curl` examples use one line, because PowerShell and the Windows command prompt
do not read the `\` line break of a Linux shell. On Windows, type `curl.exe`. In
Windows PowerShell 5.1, `curl` is a name for `Invoke-WebRequest`, which reads other
options.

## Step 1. Read the Marvis Actions list

`GET /api/v1/labs/orgs/{org_id}/suggestion`

### Query parameters for the list

| Name | Value that MistHelper sends | Purpose |
| - | - | - |
| `query` | `get_suggestion` | Return the action rows. Other values return counts or a trend. |
| `resolve_wcid` | `true` | Return the names of the impacted wireless clients. |
| `limit` | `1000` | The number of rows on each page. `MIST_PAGE_LIMIT` in `.env` sets the value. |
| `page` | `1` for the first page | The page number. MistHelper adds 1 for each next page. |

The server also accepts the filters `category`, `symptom`, `status` (one value), and
`active`. MistHelper does not send them. MistHelper reads every row and filters in
memory, because the topic tables show the count of every topic.

### Example request for the list

```text
curl.exe -s -H "Authorization: Token <API token>" "https://api.mist.com/api/v1/labs/orgs/<org_id>/suggestion?query=get_suggestion&resolve_wcid=true&limit=1000&page=1"
```

### Response of the list

```json
{
  "results": [
    {
      "uuid": "<uuid>",
      "row_key": "<row_key>",
      "suggestion_id": "swoff-291",
      "org_id": "<uuid>",
      "site_id": "<uuid>",
      "category": "switch",
      "symptom": "sw_offline",
      "suggestion": "check_switch_offline",
      "impact_scope": "switch",
      "status": "validated",
      "severity": 60,
      "label": null,
      "comment": null,
      "assignee": null,
      "entity_type": "switch",
      "entity_id": "<mac>",
      "details": {
        "disconnect_reason": "unreachability",
        "event_type": "switch_disconnect",
        "impacted_tuple": [
          {
            "entity_id": "<uuid>_209339051780",
            "entity_mac": "<mac>",
            "entity_name": "<switch name>",
            "start_time": 1790196720000,
            "end_time": 1790197526000
          }
        ]
      },
      "start_time": 1790196720000,
      "end_time": 1790197526000,
      "suggestion_time": 1790197730575,
      "resolve_time": 1790200156317,
      "validation_time": 1790200156317,
      "reoccur_time": null,
      "duration": 806,
      "reoccur_count": null,
      "batch_count": 1,
      "self_drivable": false,
      "self_driven": null,
      "zendesk_ticket": null
    }
  ],
  "page": 1,
  "limit": 1000,
  "total": 112
}
```

The example row is shorter than a live row. A live row also holds display fields
and evidence fields, such as `evidence`, `prefix`, `unique_key`, and the RMA fields.
The value `total` counts every action in the organization. It is not the count of
rows on the page.

### Paging rule for the list

MistHelper stops the read when the first of these conditions is true.

1. A page holds no row.
2. The count of rows read reaches `total`.
3. The response holds no `total`, and a page holds fewer rows than the `limit` that
   the response states.
4. The read reached 100 pages. MistHelper then logs a warning that the list can be
   incomplete.

If a page returns a status that is not 200, MistHelper discards the whole list. It
writes no file, and it resolves no action. A partial list must not reach an export
or a resolve.

### Fields that MistHelper reads from each row

| Field | Meaning | Example |
| - | - | - |
| `uuid` | The stable key of the action. MistHelper uses it as the primary key. | `<uuid>` |
| `row_key` | The key that the resolve request names. The text holds `&` and `/`. Send it exactly as the list returns it. | `<row_key>` |
| `suggestion_id` | The ID that the Mist UI shows. Some rows do not hold it. | `swoff-291` |
| `org_id`, `site_id` | The organization and the site of the action. | `<uuid>` |
| `category` | The super category key. | `switch` |
| `symptom` | The subcategory key. | `sw_offline` |
| `suggestion` | The Mist code of the advice. | `check_switch_offline` |
| `impact_scope` | The scope of the impact. | `switch` |
| `status` | The status key. See [Status values](#status-values). | `validated` |
| `severity` | The severity number. | `60` |
| `label` | The resolution code of a resolved action. | `suggested` |
| `comment` | The comment of the last resolve. | `null` |
| `assignee` | The person who owns the action. | `null` |
| `entity_type`, `entity_id` | The kind and the identifier of the impacted entity. | `switch`, `<mac>` |
| `details.impacted_tuple` | One object for each impacted device or port. Each object holds names, MAC addresses, and ports. | A list |
| `start_time`, `end_time`, `suggestion_time`, `resolve_time`, `validation_time`, `reoccur_time` | Times in epoch milliseconds. | `1790196720000` |
| `duration` | The length of the problem in seconds. | `806` |
| `reoccur_count`, `batch_count` | The count of repeats and the count of grouped entities. | `1` |
| `self_drivable`, `self_driven` | Two flags of the Marvis self-drive feature. No Mist document defines them. See [The self-drive fields](#the-self-drive-fields). | `false` |
| `zendesk_ticket` | The link to the support case. | `null` |

Do not use `unique_key` as a key. The value repeats across rows. Do not use
`suggestion_id` as a key, because some rows do not hold it. The research found
`uuid` on all 112 rows of the lab organization.

### The self-drive fields

No Mist document defines the fields `self_drivable` and `self_driven`. The OpenAPI
document of Mist does not describe the `labs` rows. The topic schema describes each
topic, but it does not describe the fields of a row.

Do not use `self_driven` alone as proof that Marvis fixed the problem. Two signals
can show a change by Marvis, and each signal misses the rows that the other signal
finds.

| Signal | Rows in the lab organization on 2026-09-24 | What the rows hold |
| - | - | - |
| `self_driven` is `True` | 8 | Six `bad_wan_link` rows and two `non_compliant` rows of the `gateway` category. Each row holds the status `validated`. In each row, the `resolve_time` is equal to the `validation_time`. |
| The status is `marvis_self_driven` | 1 | One `site_radar_channel_punishment` row. The row holds no `self_driven` value, no `resolve_time`, and no `validation_time`. |

To find each action that Marvis can have changed, read both signals. Keep a row if
`self_driven` is `True` or if `status` is `marvis_self_driven`.

`self_drivable` is `True` on 10 rows. The 10 rows belong to three topics:
`bad_wan_link`, the `gateway` topic `non_compliant`, and
`site_radar_channel_punishment`. Each of the three topics has a flag in the org
setting `marvis.auto_operations`.

A live read on 2026-09-24 tested the settings as a cause. The read sent GET
requests only.

- The org setting `marvis.auto_operations` held nine flags, and each flag held `true`.

- The org audit log holds two changes to that setting since 2026-01-01. The change
  of 2026-04-23 added `gateway_bad_wan_link` and `ap_site_radar_channel_punishment`
  with the value `true`. `gateway_non_compliant` held `true` before that change. The
  change of 2026-09-24 added `switch_missing_vlan` and `switch_stp_loop`.

- The site settings of the two sites that hold these rows held no `marvis` value.

The flags of the three topics held `true` before the oldest action started on
2026-07-02. The settings therefore do not explain the difference between the
signals. The two `site_radar_channel_punishment` rows hold no `self_driven` value,
but the eight `gateway` rows hold `True`. Issue #3340 holds the evidence.

## Step 2. Read the topic schema

`GET /api/v1/labs/suggestions_schema`

This request takes no query parameter. The path names no organization.

### Example request for the schema

```text
curl.exe -s -H "Authorization: Token <API token>" "https://api.mist.com/api/v1/labs/suggestions_schema"
```

### Response of the schema

The response holds one entry for each topic. The request returned 35 entries on
2026-09-24.

```json
{
  "data": [
    {
      "category": "client",
      "symptom": "persistently_failing",
      "display_name": "Persistently Failing Clients",
      "recommended_action": "<the advice text>",
      "detection_logic": "<how Marvis finds the problem>",
      "detection_scope": "<what Marvis examines>",
      "columns": ["site", "clients", "details", "date", "status"],
      "icon": "act-symptom-placeholder"
    }
  ]
}
```

MistHelper copies `recommended_action` into the CSV column of the same name.
MistHelper uses `display_name` only for a topic that its built-in catalog does not
hold, because two schema names do not match the Mist UI names. The schema swaps the
names of `bad_wan_link` and `intermittent_wan_connectivity`. The Mist UI calls
`bad_wan_link` "Bad WAN Uplink", and the schema calls it "Intermittent WAN
Connectivity".

If this read fails, the export continues. The `recommended_action` column stays
empty, and the log states the HTTP status.

## Step 3. Read the site names

`GET /api/v1/orgs/{org_id}/sites?limit=1000`

The OpenAPI document of Mist describes this endpoint. MistHelper calls it through
the SDK.

```python
response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000)  # Read the first page.
sites = mistapi.get_all(mist_session=apisession, response=response)  # Read each next page.
```

MistHelper reads `id` and `name` from each site, and it fills the `site_name`
column. If this read fails, the export continues. The `site_name` column stays
empty, and the log states the HTTP status.

## Step 4. Resolve one action

`PUT /api/v1/labs/orgs/{org_id}/suggestions`

Caution: a wrong filter can resolve the wrong actions, and those actions then leave
the Open tab of every engineer. This request changes the status of an action in the
Mist portal. You can set a resolved action back to Open. See
[Undo a resolve](#undo-a-resolve).

MistHelper sends one request for each action, one at a time. The Resolve dialog of
the Mist UI does the same. No flow of the Mist UI sends a batch body, so MistHelper
does not guess one.

### Request body for the resolve

| Field | Type | Value |
| - | - | - |
| `row_key` | Text | The `row_key` of the action, exactly as the list returns it. |
| `status` | Text | `resolved` |
| `label` | Text | The resolution code. See [Resolution codes](#resolution-codes). |
| `comment` | Text | The comment of the engineer. It can be empty, except for the code `nonsuggested`. |
| `resolve_time` | Whole number | The time of the run in epoch milliseconds. All requests of one run send the same value. |

Do not send `suggestion_id`. The code of the Mist UI names that field, but the live
rows hold no `id` value, so the browser drops the field. MistHelper sends the same
body that the browser sends.

```json
{
  "row_key": "<row_key>",
  "status": "resolved",
  "label": "nonsuggested",
  "comment": "Bounced port ge-0/0/12 on the access switch. The AP is online again.",
  "resolve_time": 1790222367274
}
```

### Resolution codes

| Number in menu 270 | Code (`label`) | Text in the Mist UI | Comment |
| - | - | - | - |
| 1 | `suggested` | Solved using the Mist suggested action | Optional |
| 2 | `nonsuggested` | Solved using another method (please comment below) | Required |
| 3 | `known` | A known issue and should be ignored in the future | Optional |
| 4 | `invalid` | Incorrectly listed as an issue | Optional |

The Mist UI requires a comment for the code `nonsuggested`. Menu 270 applies the
same rule before it sends a request. Menu 270 also accepts the word `other` for code
2, and it sends `nonsuggested` in the body.

### Example request for the resolve

Write the body into the file `resolve_body.json`, then send the file. A body file
prevents a quote error in the Windows shells.

```text
curl.exe -s -X PUT -H "Authorization: Token <API token>" -H "Content-Type: application/json" -d "@resolve_body.json" "https://api.mist.com/api/v1/labs/orgs/<org_id>/suggestions"
```

The same request through `mistapi`:

```python
response = apisession.mist_put(f"/api/v1/labs/orgs/{org_id}/suggestions", body=body)  # One PUT for one action.
accepted = isinstance(response.status_code, int) and 200 <= response.status_code < 300  # Any 2xx status.
```

### Response of the resolve

MistHelper treats each 2xx status as accepted, and it does not read the response
body. For any other status, MistHelper records the status and the first 300
characters of the error body in the results file. If no HTTP answer arrives,
`mistapi` returns no status, and MistHelper records the outcome `error`.

The research did not send a live resolve request, because the lab organization held
no open action. Read the results file of the first live run to confirm the response.

### Verify each resolve

After the last request, MistHelper waits 2 seconds and reads the list again. Then it
compares the status of each accepted action.

| Outcome | Meaning |
| - | - |
| `resolved` | Mist accepted the request, and the new list read shows a closed status. |
| `sent_unverified` | Mist accepted the request, but the new read shows an open status or no status, or the read failed. Examine the action in the Mist portal. |
| `error` | Mist refused the request, or no HTTP answer arrived. The row holds the HTTP status and the error text. |
| `not_sent` | The stop signal arrived before this request. |
| `skipped` | The action holds no `row_key`, so no request can address it. |

### Undo a resolve

To set a resolved action back to Open, send the same PUT request with this body.

```json
{
  "row_key": "<row_key>",
  "status": "open"
}
```

Menu 270 does not send this request. The status list of the Mist UI sends the same
path with the new status. The Mist UI offers Open, In Progress, and Resolved,
without the current status. The Mist UI shows the status as text that you cannot
change after Marvis sets AI Validated, Reoccurred, or Marvis Self Driven.

## Status values

| Status | Text in the Mist UI | Open tab | Menu 270 can resolve it |
| - | - | - | - |
| `open` | Open | Yes | Yes |
| `inprogress` | In Progress | Yes | Yes |
| `reoccured` | Reoccurred | Yes | Yes |
| `resolved` | Resolved By User | No | No |
| `validated` | AI Validated | No | No |
| `marvis_self_driven` | Marvis Self Driven | No | No |
| `expired action` | Expired Action | No | No |

The API writes `reoccured` with one `r`. Use that exact text in a filter.

Mode 2 and mode 3 keep the rows that show Yes in the Open tab column. Mode 4 keeps
the rows that show No. If Mist returns a status key that this table does not hold,
MistHelper counts the action as closed. Mode 4 then exports the action and prints a
caution line that names the key. Compare those actions with the Mist UI.

## Permissions

The Mist UI shows the status controls to a user with the permission
`canUpdateMarvisActionsStatus`. The organization roles admin, write, and helpdesk
hold that permission.

The research used a token with the organization admin role for every request in
this report. The research did not test a token with a lower role.

## Request budget

| Mode | Requests for one run |
| - | - |
| 1, 2, or 4 | One list read for each 1,000 rows, one schema read, and one site read for each 1,000 sites. |
| 3 | The reads of mode 1, one PUT for each action, and one more list read for each 1,000 rows. |

All users of MistHelper share one Mist token. Mist allows about 5,000 requests each
hour for one token. The setting `MARVIS_RESOLVE_MAX_ACTIONS` in `.env` limits one
mode 3 run to 500 actions by default. If more open actions match the filter, the run
resolves the oldest actions first. The SDK `mistapi` retries an HTTP 429 answer, and
MistHelper waits between two PUT requests.

## Endpoints that menu 270 does not call

| Method | Path | Reason | Changes Mist data |
| - | - | - | - |
| GET | `/api/v1/labs/orgs/{org_id}/suggestions?query=get_suggestion` | The plural path returns 100 rows at most, and it does not page. | No |
| GET | `/api/v1/orgs/{org_id}/alarms/search?group=marvis` | The older alarm view. Its rows hold no `row_key`, so a resolve cannot use them. | No |
| POST | `/api/v1/labs/sites/{site_id}/suggestions/fix` | It starts a Marvis self-drive fix, which changes the device configuration. | Yes |
| POST | `/api/v1/orgs/{org_id}/tickets` | It opens a support ticket for an RMA. | Yes |
| POST | `/api/v1/labs/orgs/{org_id}/jcloud/request_virtualassistant_url` | It opens a Marvis chat session. | Yes |
| GET | `/api/v1/labs/orgs/{org_id}/suggestion?query=time_series` | It returns a trend of counts, not the rows. | No |
| GET | `/api/v1/labs/orgs/{org_id}/suggestion?query=group_by_category_symptom` | It returns counts. Menu 270 counts the rows that it already holds. | No |
| GET | `/api/v1/labs/orgs/{org_id}/suggestion_detail/{id}/suggestion_id` | It returns one detail record. The list already holds the fields that the export needs. | No |
| GET | `/api/v1/msps/{msp_id}/suggestion/count` | The public document describes it, but it returns the counts of an MSP only. | No |
| GET | `/api/v1/sites/{site_id}/marvis_configs/search` | It reads Marvis Config Actions, which are not Marvis Actions. See [The Marvis Config Actions](#the-marvis-config-actions). | No |
| GET | `/api/v1/sites/{site_id}/marvis_configs/count` | It counts Marvis Config Actions by one field. | No |
| DELETE | `/api/v1/sites/{site_id}/marvis_configs/{id}` | It deletes one Marvis Config Action. | Yes |
| POST | `/api/v1/sites/{site_id}/marvis_configs/{id}/feedback` | It marks one Marvis Config Action as invalid. It cannot resolve a Marvis Action. | Yes |

Warning: a call to the self-drive endpoint can change the configuration of a live
device and stop client traffic. Do not call that endpoint from a script.

### The Marvis Config Actions

The Mist API holds a second family with "Marvis" and "action" in its names. The
OpenAPI tag of the family is "Sites Marvis Configs". The family does not serve the
Marvis Actions of menu 270.

| Operation | Method | Path | SDK function in `mistapi.api.v1.sites.marvis_configs` |
| - | - | - | - |
| Search | GET | `/api/v1/sites/{site_id}/marvis_configs/search` | `searchSiteMarvisConfigActions` |
| Count | GET | `/api/v1/sites/{site_id}/marvis_configs/count` | `countSiteMarvisConfigActions` |
| Delete | DELETE | `/api/v1/sites/{site_id}/marvis_configs/{id}` | `deleteSiteMarvisConfigAction` |
| Feedback | POST | `/api/v1/sites/{site_id}/marvis_configs/{id}/feedback` | `submitSiteMarvisConfigFeedback` |

The OpenAPI document added the family in release 2605.1.0. The SDK `mistapi` added
the four functions in 0.63.0.

A Marvis Action is one problem that Marvis found. A Marvis Config Action is the
record of one configuration change on a switch port. This table shows the
differences.

| Item | Marvis Action | Marvis Config Action |
| - | - | - |
| Scope | One organization | One site |
| Key | `row_key` | `id` |
| Status | `open`, `resolved`, `validated`, and the other values in [Status values](#status-values) | No status field |
| Change | A PUT with a resolution code | A DELETE, or a feedback POST with the `type` value `invalid` |
| Example content | The topic `sw_offline` | The `op` value `disable_port` with the `reason` value `rogue_dhcp_server_detected` |

The schema `marvis_config_action` holds the fields `admin_id`, `id`, `mac`, `op`,
`org_id`, `port_id`, `reason`, `site_id`, `src`, `timestamp`, `type`, and `vlan_ids`.
The document gives the `op` examples `disable_port`, `enable_port`, `update_mtu`,
and `add_vlans_to_port`. The feedback body holds `type` and `note`.

Warning: a DELETE call removes the record of a Marvis change, and no endpoint can
restore the record. A feedback POST changes the record in the Mist cloud. Do not
call either operation from a script. The document does not tell if a DELETE also
changes the port.

#### Live read of the Marvis Config Actions

On 2026-09-24, MistHelper read the search endpoint and the count endpoint with GET
requests only.

- Both endpoints returned HTTP 200 on all 144 sites of the organization. Each answer held 0 records.
- Each answer covered one hour. The window started one hour before the request and ended at the request.
- The window stayed at one hour for `duration=1d`, `duration=30d`, `start` alone, and `start` with `end`. The research sent `start` and `end` in seconds and in milliseconds, on 3 sites.

A read therefore cannot show a Marvis Config Action from before the last hour. In
three places, the live answers do not agree with the OpenAPI document.

| Item | OpenAPI document | Live answer |
| - | - | - |
| Default window | `duration` default `1d` | One hour |
| Default `limit` | 100 | 10 |
| Type of `start` and `end` in the answer | Integer epoch seconds | Decimal epoch seconds |

#### Sources for the Marvis Actions endpoints

MistHelper checked three sources on 2026-09-24.

| Source | Version | Result |
| - | - | - |
| The bundled `documentation/mist-api-openapi31json.json` | Release 2607.1.1, 756 paths | The four operations of the family. No list path, schema path, or resolve path for Marvis Actions. |
| The `master` branch of `mistsys/mist_openapi`, commit `0613a22acd` of 2026-09-18 | Release 2609.1.0, 762 paths | The same four operations. No list path, schema path, or resolve path for Marvis Actions. |
| `mistapi` 0.64.0 on PyPI, the newest release | Uploaded on 2026-09-15 | The same four functions. No function for a `labs` path. |

The only Marvis Actions path in the public document is the MSP count path. Menu 270
therefore keeps its direct calls to the `labs` paths. The Caution at the top of this
report stays correct.

## Where MistHelper keeps the results

| File | SQLite table | ArangoDB collection | Primary key | Content |
| - | - | - | - | - |
| `data/OrgMarvisActions.csv` | `OrgMarvisActions` | `listOrgMarvisActions` | `uuid` | One row for each action. Modes 1, 2, and 4 write it. |
| `data/OrgMarvisActionsResolveResults.csv` | `OrgMarvisActionsResolveResults` | `resolveOrgMarvisActions` | `result_id` | One row for each action that a mode 3 run touched. |

The default format writes the CSV file. The `--output-format sqlite` flag writes
the SQLite table in `data/mist_data.db` and writes no CSV file. When ArangoDB
answers, each run also writes the ArangoDB collection.

The `result_id` joins the action `uuid` and the `resolve_time` of the run, so each
run adds new rows. The database document of an action holds the full raw row and
the readable columns.

## Where the code lives

| Endpoint | MistHelper method | File |
| - | - | - |
| List | `MarvisActionsClient.list_actions` | `src/marvis/actions/client.py` |
| Schema | `MarvisActionsClient.read_schema` | `src/marvis/actions/client.py` |
| Sites | `MarvisActionsClient.read_site_names` | `src/marvis/actions/client.py` |
| Resolve | `MarvisActionsClient.resolve_action` | `src/marvis/actions/client.py` |
| Verify | `MarvisBulkResolver.verify` | `src/marvis/actions/operation.py` |

## Example script that only reads

This script counts the open actions of each topic. It sends GET requests only. The
`.env` file must hold `MIST_HOST` and `MIST_APITOKEN`.

```python
"""Count the open Marvis Actions of each topic. This script sends GET requests only."""

import collections  # The Counter class counts the topics.

import mistapi  # The Mist API SDK.

OPEN_STATUSES = {"open", "inprogress", "reoccured"}  # The API writes "reoccured" with one r.
PAGE_LIMIT = 1000  # The number of rows on each page.
MAX_PAGES = 100  # The same page guard as MistHelper.
ORG_ID = "<org_id>"  # Replace with your organization UUID.

apisession = mistapi.APISession(env_file=".env")  # Read MIST_HOST and MIST_APITOKEN from the file.
apisession.login()  # Confirm the token before the first read.
counts: collections.Counter[str] = collections.Counter()  # The open count of each topic.
rows_read = 0  # The total counts every row, so count every row.
for page in range(1, MAX_PAGES + 1):  # The first page is page 1.
    response = apisession.mist_get(  # Read one page of the list.
        f"/api/v1/labs/orgs/{ORG_ID}/suggestion",
        query={"query": "get_suggestion", "resolve_wcid": "true", "limit": str(PAGE_LIMIT), "page": str(page)},
    )
    if response.status_code != 200:  # A failed page makes every count wrong.
        raise SystemExit(f"The list read returned HTTP {response.status_code}.")  # Stop and name the status.
    results = response.data["results"]  # The action rows of this page.
    rows_read += len(results)  # Add the rows of this page.
    counts.update(  # Count the open actions of this page.
        f"{row.get('category')}/{row.get('symptom')}" for row in results if row.get("status") in OPEN_STATUSES
    )
    total = response.data.get("total")  # The count of every action in the organization.
    if not results or (total is not None and rows_read >= total):  # The last page.
        break  # No more rows exist.
    if total is None and len(results) < PAGE_LIMIT:  # Without a total, a short page is the last page.
        break  # No more rows exist.
for topic, count in counts.most_common():  # The largest topic first.
    print(f"{topic}: {count} open")  # One line for each topic.
print(f"Read {rows_read} actions. {sum(counts.values())} are open.")  # The summary line.
```
