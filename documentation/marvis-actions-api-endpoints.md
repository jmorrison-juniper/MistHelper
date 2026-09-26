# Marvis Actions API endpoints (menu 270)

This report lists each Mist API endpoint that menu 270 calls. Menu 270 exports the
Marvis Actions of an organization, and it resolves open actions in bulk. Use this
report as an example when you build a similar tool. Issue #3299 tracks the feature.

The examples use placeholder values. Replace `<org_id>`, `<API token>`, and
`<row_key>` with your own values. A value such as `<uuid>` or `<mac>` in a response
example replaces a real identifier.

Caution: three of the five endpoints are `labs` endpoints, so a Mist release can
change them without notice and stop your script. The OpenAPI document of Mist does
not describe the `labs` endpoints, and `mistapi` 0.64.0 holds no method for them. If
a request returns HTTP 404 or a changed response shape, compare the request with the
Mist UI again. MistHelper confirmed each endpoint against the Mist UI version
`admin2.21.1765-hotfix` on 2026-09-23.

No documented endpoint can replace a `labs` endpoint. The section
[Why no documented endpoint can replace the labs endpoints](#why-no-documented-endpoint-can-replace-the-labs-endpoints)
compares each documented endpoint that looks similar, such as the alarm endpoints.

## Summary

| Step | Method | Path | Purpose | Modes | Changes Mist data |
| - | - | - | - | - | - |
| 1 | GET | `/api/v1/labs/orgs/{org_id}/suggestion` | Read the Marvis Actions list, one page at a time. | 1, 2, 3, 4 | No |
| 2 | GET | `/api/v1/labs/suggestions_schema` | Read the topic names and the recommended actions. | 1, 2, 3, 4 | No |
| 3 | GET | `/api/v1/orgs/{org_id}/sites` | Read the site names. | 1, 2, 3, 4 | No |
| 4 | GET | `/api/v1/orgs/{org_id}/alarms/search` | Read the Marvis alarms, and add the alarm values to each exported action. | 1, 2, 4 | No |
| 5 | PUT | `/api/v1/labs/orgs/{org_id}/suggestions` | Resolve one action. | 3 | Yes |
| 6 | GET | `/api/v1/labs/orgs/{org_id}/suggestion` | Read the list again to verify each resolve. | 3 | No |

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

No `search` endpoint serves the Marvis Actions list. The alarm search is not a
replacement, because its rows hold no `row_key` value. Modes 1, 2, and 4 read the
alarm search only to add eight alarm columns to each exported action. See
[Step 4](#step-4-read-the-marvis-alarms).

The `marvis_configs` search is not a replacement either, because it reads a
different object. See
[Endpoints that menu 270 does not call](#endpoints-that-menu-270-does-not-call).
For the full comparison, see
[Why no documented endpoint can replace the labs endpoints](#why-no-documented-endpoint-can-replace-the-labs-endpoints).

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

## Step 4. Read the Marvis alarms

`GET /api/v1/orgs/{org_id}/alarms/search`

Modes 1, 2, and 4 send this search one time for each export. The search occurs
after the filter prompts and before the write. Mode 3 does not send it. The
OpenAPI document of Mist describes this endpoint, and MistHelper calls it through
the SDK. Issue #3339 added this step.

Mist keeps a Marvis alarm for many Marvis Actions. The alarm holds its own status,
its resolved time, and its acknowledge values. MistHelper copies eight alarm
values into the row of each exported action. You then read one file instead of
two lists.

### Query parameters for the alarm search

| Name | Value that MistHelper sends | Purpose |
| - | - | - |
| `group` | `marvis` | Return the Marvis alarms only. The groups `certificate_expiry`, `infrastructure`, and `security` hold no Marvis Action. |
| `start` | Epoch seconds, as text | The start of the search window. |
| `end` | Epoch seconds, as text | The end of the search window. MistHelper sends the time of the run. |
| `limit` | `1000` | The number of alarms on each page. The default of the API is 100. |

MistHelper builds the search window from three rules.

1. The window starts one day before the oldest `start_time` of the exported
   actions.
2. The start is never earlier than 400 days before the end. A live test on
   2026-09-24 proved that width.
3. The window is at least one day wide.

The Marvis Actions list holds `start_time` in epoch milliseconds. The alarm search
reads epoch seconds. MistHelper divides each action time by 1,000 before it
builds the window.

Caution: a request without `start` and `end` can miss an old alarm. The search
then reads a short default window, and the alarm columns of the old action stay
empty.

### Example request for the alarm search

```text
curl.exe -s -H "Authorization: Token <API token>" "https://api.mist.com/api/v1/orgs/<org_id>/alarms/search?group=marvis&start=<epoch seconds>&end=<epoch seconds>&limit=1000"
```

The same request through `mistapi`:

```python
response = mistapi.api.v1.orgs.alarms.searchOrgAlarms(  # Read the first page.
    apisession, org_id, group="marvis", start=str(start), end=str(end), limit=1000
)
next_page = mistapi.get_next(apisession, response)  # Follow the next link, or get None without a link.
```

### Response of the alarm search

```json
{
  "results": [
    {
      "id": "<uuid>",
      "org_id": "<uuid>",
      "site_id": "<uuid>",
      "group": "marvis",
      "type": "switch_offline",
      "severity": "critical",
      "status": "resolved",
      "count": 1,
      "timestamp": 1790196720,
      "last_seen": 1790197526,
      "resolved_time": 1790198345,
      "entity_macs": ["<mac>"],
      "impacted_entities": [
        {
          "entity_mac": "<mac>",
          "entity_name": "<switch name>",
          "entity_type": "switch"
        }
      ]
    }
  ],
  "start": 1755903503.0,
  "end": 1790463503.0,
  "limit": 1000,
  "total": 33
}
```

The alarm times hold whole epoch seconds. The `start` value and the `end` value of
the response hold decimal epoch seconds. If more alarms exist than one page holds,
the body also holds a `next` link with a `search_after` value. Do not build that
value yourself. Follow the link.

### Paging rule for the alarm search

MistHelper stops the read when the first of these conditions is true.

1. A page holds no `next` link.
2. A page holds no alarm.
3. A page holds a `next` link that the read already followed.
4. The read reached 100 pages.

After condition 3 or condition 4, MistHelper logs one warning line. The join then
holds the alarms of the pages that MistHelper read, so some alarm cells can stay
empty by mistake.

A page fails when it returns no HTTP answer, a status that is not 200, or a body
without a `results` list. If a page fails, MistHelper discards every alarm row.
The export continues, and it writes every action with empty alarm columns. One
warning line names the reason, and the portal still marks the run as completed.

MistHelper keeps only the rows whose `group` is `marvis`. The example `next` link
of the API reference holds no `group` value, so a next page can hold other groups.

### How MistHelper joins an alarm to an action

1. MistHelper matches the alarm `action_id` to the action `uuid`.
2. If no alarm matches, MistHelper matches the alarm `id` to the action `uuid`.
3. If two alarms hold one key, the alarm with the larger `last_seen` value wins.

The join does not use the topic names, because the alarm types use other names.
For example, the topic `switch/sw_offline` joins to the alarm type
`switch_offline`, and the topic `ap/ap_disconnect` joins to `ap_offline`. See
[The schema and the alarm definitions](#the-schema-and-the-alarm-definitions) for
each topic and the alarm types with a similar name.

A live test on 2026-09-24 read 112 actions and 33 Marvis alarms. The alarm `id`
equaled the action `uuid` for 31 actions. No alarm held an `action_id` value. 81
actions had no alarm, and 79 of them started before the oldest alarm that the
search returned. Mist does not document how long it keeps an alarm, so an old
action can have no alarm.

### The alarm columns

| Column | Alarm field | Value |
| - | - | - |
| `alarm_id` | `id` | The alarm UUID. |
| `alarm_type` | `type` | The alarm type, for example `switch_offline`. |
| `alarm_status` | `status` | The alarm status, for example `open` or `resolved`. |
| `alarm_resolved_time_iso` | `resolved_time` | The resolve time as ISO 8601 UTC text, in whole seconds. |
| `alarm_acked` | `acked` | `True` when an operator acknowledged the alarm. |
| `alarm_acked_time_iso` | `acked_time` | The acknowledge time as ISO 8601 UTC text, in whole seconds. |
| `alarm_ack_admin_name` | `ack_admin_name` | The name of the administrator who acknowledged the alarm. |
| `alarm_note` | `note` | The note that the administrator wrote with the acknowledge. |

The eight columns come after `exported_at`, so the first 43 columns keep their
positions. If an action has no alarm, the eight cells stay empty. The live
organization held no acknowledged alarm, so the last four columns stayed empty on
every row.

### The count lines of the join

After the join, the run shows two lines in the SSH session and in the portal.

```text
Marvis alarm join: 31 of 112 exported actions have a Marvis alarm. 81 have no alarm.
Marvis alarms in the search window without an action in the list: 2
```

The second line counts the alarms whose two keys name no action of the list. Such
an alarm can be newer than the list read.

A later live run on 2026-09-24 at 23:55Z proved this case. The list then held
114 actions, and two of them were the actions of the two newer alarms. All 33
alarms joined an action, and the second count line showed 0.

### The limits of an acknowledge step

Menu 270 reads the acknowledge values of each alarm, but it does not acknowledge
an alarm. Issue #3357 tracks that change as phase 2 of issue #3339. A person must
review that change before it merges. Read these limits before you plan an
acknowledge script.

- An acknowledge changes Mist data for every engineer who reads the alarm.

- The research did not test if a resolve changes the alarm, or if an acknowledge
  changes the action.

- The `ack_all` request has no group filter, so it also acknowledges the alarms of
  the groups `certificate_expiry`, `infrastructure`, and `security`.

- The organization API has no path that removes the acknowledge of one alarm. To
  undo one acknowledge, send `unack` with a list that holds one alarm ID. The site
  API has a path for one alarm: `POST /api/v1/sites/{site_id}/alarms/{alarm_id}/unack`,
  with the SDK function `unackSiteAlarm`.

- The bundled API document limits one `ack` batch or one `unack` batch to 1,000
  alarm IDs. The text of the `ack_all` operation and the `unack_all` operation
  states the limit. The schema of the body states no limit.

Warning: do not send `ack_all` from a script, because it will acknowledge every
alarm of the organization. No request can restore the acknowledge state that each
alarm held before.

## Step 5. Resolve one action

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
the rows that show No in that column. If Mist returns a status key that this table
does not hold, MistHelper counts the action as closed. Mode 4 then exports the
action and prints a caution line that names the key. Compare those actions with the
Mist UI.

## Permissions

The Mist UI shows the status controls to a user with the permission
`canUpdateMarvisActionsStatus`. The organization roles admin, write, and helpdesk
hold that permission.

The research used a token with the organization admin role for every request in
this report. The research did not test a token with a lower role.

## Request budget

| Mode | Requests for one run |
| - | - |
| 1, 2, or 4 | One list read for each 1,000 rows, one schema read, one site read for each 1,000 sites, and one alarm search for each 1,000 Marvis alarms. |
| 3 | The list read, the schema read, and the site read of mode 1, one PUT for each action, and one more list read for each 1,000 rows. Mode 3 sends no alarm search. |

All users of MistHelper share one Mist token. Mist allows about 5,000 requests each
hour for one token. The setting `MARVIS_RESOLVE_MAX_ACTIONS` in `.env` limits one
mode 3 run to 500 actions by default. If more open actions match the filter, the run
resolves the oldest actions first. The SDK `mistapi` retries an HTTP 429 answer, and
MistHelper waits between two PUT requests.

## Endpoints that menu 270 does not call

| Method | Path | Reason | Changes Mist data |
| - | - | - | - |
| GET | `/api/v1/labs/orgs/{org_id}/suggestions?query=get_suggestion` | The plural path returns 100 rows at most, and it does not page. | No |
| POST | `/api/v1/orgs/{org_id}/alarms/{alarm_id}/ack` | It acknowledges one alarm. See [The limits of an acknowledge step](#the-limits-of-an-acknowledge-step). | Yes |
| POST | `/api/v1/orgs/{org_id}/alarms/ack` | It acknowledges a list of alarms. | Yes |
| POST | `/api/v1/orgs/{org_id}/alarms/ack_all` | It acknowledges every alarm of the organization, in every alarm group. | Yes |
| POST | `/api/v1/orgs/{org_id}/alarms/unack` | It removes the acknowledge of a list of alarms. | Yes |
| POST | `/api/v1/orgs/{org_id}/alarms/unack_all` | It removes the acknowledge of every alarm of the organization. | Yes |
| POST | `/api/v1/labs/sites/{site_id}/suggestions/fix` | It starts a Marvis self-drive fix, which changes the device configuration. | Yes |
| POST | `/api/v1/orgs/{org_id}/tickets` | It opens a support ticket for an RMA. | Yes |
| POST | `/api/v1/labs/orgs/{org_id}/jcloud/request_virtualassistant_url` | It opens a Marvis chat session. | Yes |
| GET | `/api/v1/labs/orgs/{org_id}/suggestion?query=time_series` | It returns a trend of counts, not the rows. | No |
| GET | `/api/v1/labs/orgs/{org_id}/suggestion?query=group_by_category_symptom` | It returns counts. Menu 270 counts the rows that it already holds. | No |
| GET | `/api/v1/labs/orgs/{org_id}/suggestion_detail/{id}/suggestion_id` | It returns one detail record. The list already holds the fields that the export needs. | No |
| GET | `/api/v1/msps/{msp_id}/suggestion/count` | The public document describes it, but it returns the counts of an MSP only. See [The MSP count](#the-msp-count). | No |
| GET | `/api/v1/orgs/{org_id}/alarms/count` | It counts the alarms by one field, and it returns no rows. | No |
| GET | `/api/v1/const/alarm_defs` | It lists the alarm types. It holds no topic key and no advice. See [The schema and the alarm definitions](#the-schema-and-the-alarm-definitions). | No |
| POST | `/api/v1/sites/{site_id}/alarms/{alarm_id}/unack` | It removes the acknowledge of one alarm of one site. | Yes |
| POST | `/api/v1/orgs/{org_id}/alarmtemplates/suppress` | It suppresses every alarm of a scope for up to 180 days. It names no action. See [The resolve and the alarm acknowledge](#the-resolve-and-the-alarm-acknowledge). | Yes |
| GET | `/api/v1/orgs/{org_id}/troubleshoot` | It returns the results of a Marvis diagnosis, not the actions. See [The troubleshoot endpoint](#the-troubleshoot-endpoint). | No |
| GET | `/api/v1/orgs/{org_id}/devices/events/search` | It returns device events without a status or a key. See [The device events](#the-device-events). | No |
| PUT | `/api/v1/orgs/{org_id}/setting` | It changes the automatic operations of Marvis. It cannot close an action. See [The Marvis settings](#the-marvis-settings). | Yes |
| GET | `/api/v1/sites/{site_id}/marvis_configs/search` | It reads Marvis Config Actions, which are not Marvis Actions. See [The Marvis Config Actions](#the-marvis-config-actions). | No |
| GET | `/api/v1/sites/{site_id}/marvis_configs/count` | It counts Marvis Config Actions by one field. | No |
| DELETE | `/api/v1/sites/{site_id}/marvis_configs/{id}` | It deletes one Marvis Config Action. | Yes |
| POST | `/api/v1/sites/{site_id}/marvis_configs/{id}/feedback` | It marks one Marvis Config Action as invalid. It cannot resolve a Marvis Action. | Yes |

Warning: a call to the self-drive endpoint can change the configuration of a live
device and stop client traffic. Do not call that endpoint from a script.

The section
[Why no documented endpoint can replace the labs endpoints](#why-no-documented-endpoint-can-replace-the-labs-endpoints)
compares the documented endpoints of this table with the `labs` endpoints.

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

## Why no documented endpoint can replace the labs endpoints

Menu 270 calls three `labs` endpoints. The research compared each one with every
documented endpoint that looks similar. No documented endpoint can replace a `labs`
endpoint. Issue #3368 holds the research. Each request of the research was a GET
request, so no request changed Mist data.

The SDK column of each table names the function under `mistapi.api.v1`. The
research used `mistapi` 0.64.0, the bundled OpenAPI document of release 2607.1.1,
and live reads of the lab organization on 2026-09-25. See
[Sources for the Marvis Actions endpoints](#sources-for-the-marvis-actions-endpoints).

### The three functions that menu 270 needs

| Function | `labs` endpoint | What menu 270 reads or changes |
| - | - | - |
| The list | `GET /api/v1/labs/orgs/{org_id}/suggestion` | Every action, open and closed, with `uuid`, `row_key`, `status`, `label`, `comment`, the topic, the details, and the times. |
| The schema | `GET /api/v1/labs/suggestions_schema` | The display name, the recommended action, and the detection text of each topic. |
| The resolve | `PUT /api/v1/labs/orgs/{org_id}/suggestions` | The status of one action, with a resolution code and a comment. |

A replacement must meet three conditions.

1. It returns the same objects. The list returns every action, open and closed.
2. It uses the same key. The resolve names the `row_key` of a list row.
3. It changes the same status. The Open tab of the Mist UI selects each action by
   its status.

The alarm endpoints fail each of the three conditions. Every other documented
endpoint fails one of the conditions or more.

### Summary of the documented endpoints

| Documented endpoint | SDK function | Nearest `labs` function | Why it cannot replace the `labs` function |
| - | - | - | - |
| `GET /api/v1/orgs/{org_id}/alarms/search` | `orgs.alarms.searchOrgAlarms` | The list | Only 33 of 114 actions had an alarm. No alarm holds `row_key`. The search has no status filter. See [The list and the alarm search](#the-list-and-the-alarm-search). |
| `GET /api/v1/orgs/{org_id}/alarms/count` | `orgs.alarms.countOrgAlarms` | The list | It returns counts, not rows. It has no group filter. See [The search cannot select the open alarms](#the-search-cannot-select-the-open-alarms). |
| `GET /api/v1/sites/{site_id}/alarms/search` and `GET /api/v1/sites/{site_id}/alarms/count` | `sites.alarms.searchSiteAlarms` and `sites.alarms.countSiteAlarms` | The list | The same limits as the organization paths, for one site only. A full export then needs one request for each site. |
| `GET /api/v1/const/alarm_defs` | `const.alarm_defs.listAlarmDefinitions` | The schema | It holds no advice and no topic key. Eight topics have no Marvis alarm type with a similar name. See [The schema and the alarm definitions](#the-schema-and-the-alarm-definitions). |
| `POST /api/v1/orgs/{org_id}/alarms/{alarm_id}/ack` | `orgs.alarms.ackOrgAlarm` | The resolve | It records an acknowledge on the alarm, not a new action status. Its body holds a note, not a resolution code. See [The resolve and the alarm acknowledge](#the-resolve-and-the-alarm-acknowledge). |
| `POST /api/v1/orgs/{org_id}/alarms/ack` | `orgs.alarms.ackOrgMultipleAlarms` | The resolve | The same reason as the row above, for a list of alarm IDs. |
| `POST /api/v1/orgs/{org_id}/alarms/ack_all` | `orgs.alarms.ackOrgAllAlarms` | The resolve | It acknowledges every alarm of every group. It has no filter. |
| `POST /api/v1/sites/{site_id}/alarms/{alarm_id}/ack`, `POST /api/v1/sites/{site_id}/alarms/ack`, and `POST /api/v1/sites/{site_id}/alarms/ack_all` | `sites.alarms.ackSiteAlarm`, `sites.alarms.AckSiteMultipleAlarms`, and `sites.alarms.ackSiteAllAlarms` | The resolve | The same reasons as the organization paths, for one site. The name `AckSiteMultipleAlarms` starts with a capital A in the document and in the SDK. |
| `POST /api/v1/orgs/{org_id}/alarmtemplates/suppress` | `orgs.alarmtemplates.suppressOrgAlarm` | The resolve | It stops new alarms for a scope. Its body names no alarm, no alarm type, and no action. |
| `GET /api/v1/msps/{msp_id}/suggestion/count` | `msps.suggestion.countMspsMarvisActions` | The list | It returns counts for the organizations of one MSP. It returns no row. See [The MSP count](#the-msp-count). |
| `GET /api/v1/orgs/{org_id}/troubleshoot` | `orgs.troubleshoot.troubleshootOrg` | The list | It returns a diagnosis of the last 7 days at most. It names no action. See [The troubleshoot endpoint](#the-troubleshoot-endpoint). |
| `GET /api/v1/orgs/{org_id}/devices/events/search` | `orgs.devices.searchOrgDeviceEvents` | The list | It returns device events. An event holds no status and no action key. See [The device events](#the-device-events). |
| `GET /api/v1/orgs/{org_id}/insights/{metric}` and the other SLE paths | `orgs.insights.getOrgSle` | The list | It returns SLE values, not actions. See [The other documented Marvis endpoints](#the-other-documented-marvis-endpoints). |
| `GET /api/v1/orgs/{org_id}/marvisclients/events/search` and the three other operations of the tag "Orgs Clients - Marvis" | `orgs.marvisclients.searchOrgMarvisClientEvents` | The list | It returns the events of the Marvis Client app, not actions. See [The other documented Marvis endpoints](#the-other-documented-marvis-endpoints). |
| `GET /api/v1/sites/{site_id}/marvis_configs/search` and the three other paths of the family | The four functions of `sites.marvis_configs` | The list and the resolve | It reads Marvis Config Actions, which are a different object. See [The Marvis Config Actions](#the-marvis-config-actions). |
| `PUT /api/v1/orgs/{org_id}/setting` | `orgs.setting.updateOrgSettings` | The resolve | It changes the automatic operations of Marvis. It cannot close an action. See [The Marvis settings](#the-marvis-settings). |
| `POST /api/v1/orgs/{org_id}/webhooks` with the topic `alarms` | `orgs.webhooks.createOrgWebhook` | The list | It sends new alarm events only. The documented payload holds no status and no action key. See [The webhooks](#the-webhooks). |

### The list and the alarm search

The alarm search is the documented endpoint that is nearest to the list. Mist
creates a Marvis alarm for some Marvis Actions. An action and its alarm name the
same problem at the same site. The five parts below show why the alarm search cannot
replace the list.

#### Only some actions have an alarm

On 2026-09-25, the list held 114 actions. A search of the Marvis alarms over 400
days returned 33 alarms. Each alarm joined one action, because the alarm `id`
equaled the action `uuid`. Of the 114 actions, 81 had no alarm.

| Topic | Actions | Actions with an alarm | Alarm type |
| - | - | - | - |
| `ap/ap_disconnect` | 66 | 9 | `ap_offline` |
| `switch/sw_offline` | 30 | 19 | `switch_offline` |
| `gateway/bad_wan_link` | 6 | 0 | None |
| `switch/port_flap` | 3 | 2 | `port_flap` |
| `ap/site_radar_channel_punishment` | 2 | 0 | None |
| `application/reachability_failure` | 2 | 2 | `minis_application_reachability_failure` |
| `connectivity/dhcp_failure` | 2 | 1 | `minis_dhcp_failure` |
| `gateway/non_compliant` | 2 | 0 | None |
| `gateway/vpn_path_down` | 1 | 0 | None |
| Total | 114 | 33 | |

Mist does not document the period that it keeps an alarm. The oldest alarm was 50.2
days old, and the oldest action was 84.5 days old. Of the 81 actions without an
alarm, 79 started before the oldest alarm. The other two are one `ap/ap_disconnect`
action and one `ap/site_radar_channel_punishment` action. A new action can therefore
have no alarm.

Three more searches read the other alarm groups over the same window. They returned
656 `infrastructure` alarms, 190 `security` alarms, and 0 `certificate_expiry`
alarms. No alarm of these groups held an `id` or an `action_id` that equals an
action `uuid`.

#### No alarm holds the key of the resolve

The Mist UI sends the `row_key` of the action in the resolve body. No live alarm
holds `row_key`, and no example in the alarm definitions holds it. The alarm `id`
equals the action `uuid`, but the research did not send a resolve with `uuid`. A
script must therefore read the list to find the `row_key` of an action.

#### The two status models are different

| Item | Marvis Action | Marvis alarm |
| - | - | - |
| Status values | `open`, `inprogress`, `reoccured`, `resolved`, `validated`, `marvis_self_driven`, and `expired action` | `open` and `resolved` |
| Who closes the object | Marvis, or a user with the resolve | Mist. The document describes no request that sets the alarm `status`. |
| Record of the operator | `label` (the resolution code) and `comment` | `acked`, `acked_time`, `ack_admin_name`, and `note` |
| Change request | `PUT /api/v1/labs/orgs/{org_id}/suggestions` | The acknowledge requests. The document does not state that an acknowledge changes `status`. |
| Close time | `resolve_time` and `validation_time` | `resolved_time` |

On 2026-09-25, each of the 33 pairs held the action status `validated` and the
alarm status `resolved`. In 30 pairs, both close times existed. In each of these
pairs, the alarm `resolved_time` and the action `validation_time` differ by one
second or less. The two close times agree, so Marvis closes the two objects at the
same time. The research cannot tell if a resolve by a user also closes the alarm.
The organization held no open action for that test.

#### The alarm fields do not hold the action fields

| Action field in the list | Alarm field | Difference |
| - | - | - |
| `uuid` | `id` | The same value when an alarm exists. |
| `row_key` | None | The resolve needs this key. |
| `category` and `symptom` | `type` | The alarm types use other names. See [Each topic and the alarm types](#each-topic-and-the-alarm-types). |
| `status` | `status` | The action has seven values. The alarm has two values. |
| `label` | None | The alarm holds no resolution code. |
| `comment` | `note` | The note belongs to an acknowledge, not to a resolve. |
| `assignee` | None | The alarm holds no owner. |
| `severity` | `severity` | The action holds a number, for example 60. The alarm holds `critical` or `warn`. |
| `details.impacted_tuple` | `impacted_entities` | Both name the impacted devices. An alarm entity holds no start time and no end time. |
| `start_time` and `end_time` | `timestamp` and `last_seen` | The action uses epoch milliseconds. The alarm uses epoch seconds. |
| `resolve_time` and `validation_time` | `resolved_time` | The alarm holds one close time. |
| `suggestion` | None | The alarm holds no advice code. |
| `self_drivable` and `self_driven` | None | The alarm holds no self-drive value. |
| `zendesk_ticket` and the RMA fields | None | The alarm holds no support case. |

The live alarms and the alarm schema do not agree either.

| Group of fields | Fields |
| - | - |
| Live fields that the schema does not describe (7) | `connected_switch_macs`, `entity_ids`, `entity_macs`, `impacted_ap_count`, `impacted_entities`, `impacted_entity_count`, and `port_ids` |
| Schema fields that no live alarm held (11) | `ack_admin_id`, `ack_admin_name`, `acked`, `acked_time`, `aps`, `bssids`, `gateways`, `hostnames`, `note`, `ssids`, and `switches` |

No live alarm held the field `acked`. The organization held no acknowledged alarm,
so the research cannot tell if Mist adds the field after an acknowledge.

Caution: a script that reads `acked` without a default value can stop with an error
at the first live alarm. Read each alarm field with a default value.

#### The search cannot select the open alarms

The alarm search has no `status` filter. The documented filters are `site_id`,
`group`, `severity`, `type`, `ack_admin_name`, `acked`, `start`, `end`, and
`duration`. A script must read every alarm and select the open alarms itself.

`GET /api/v1/orgs/{org_id}/alarms/count` counts the alarms for each value of one
field, which the `distinct` parameter names. It has no group filter and no status
filter. On 2026-09-25, `distinct=group` returned 656 `infrastructure` alarms, 190
`security` alarms, and 33 `marvis` alarms. The site count
`GET /api/v1/sites/{site_id}/alarms/count` accepts the filters `group`, `type`,
`severity`, `acked`, and `ack_admin_name`, but it counts one site only. A count
cannot give the rows that an export or a resolve needs.

### The schema and the alarm definitions

`GET /api/v1/const/alarm_defs` lists each alarm type that Mist can create. It is
the documented endpoint that is nearest to the schema. The SDK function is
`const.alarm_defs.listAlarmDefinitions`.

| Item | The schema (`labs`) | The alarm definitions (documented) |
| - | - | - |
| Entries | 35 topics | 248 alarm types. 35 types belong to the group `marvis`. |
| Other entries | None | 213 types: `infrastructure` 157, `security` 36, and `certificate_expiry` 20. |
| Key of one entry | `category` and `symptom` | `key` |
| Categories | 8: `ap`, `application`, `client`, `connectivity`, `gateway`, `layer_1`, `security`, and `switch` | 5 values of `marvis_suggestion_category`: `ap`, `application`, `connectivity`, `gateway`, and `switch` |
| Fields of one entry | 18 | 8 live fields. The document describes 7 fields, without `default_enabled`. |
| Advice | `recommended_action`, `detection_logic`, `detection_scope`, and `ask_marvis_query` | None |
| Automatic operation | `auto_operation_capable`, `auto_operation_flag`, and `default_auto_operation_permission` | None |
| Severity | None. The list row holds a number. | 31 types hold `critical`, and 4 types hold `warn`. |
| Link to the other object | None | No field names a topic. `marvis_suggestion_category` names a category only. The `example` names a topic in a sample payload. |

These are the 18 fields of a schema entry.

- The keys and the names: `action`, `category`, `display_name`, `icon`, and `symptom`.
- The advice: `ask_marvis_query`, `detection_logic`, `detection_scope`, and `recommended_action`.
- The automatic operation: `auto_action_permission_modal_disabled`, `auto_operation_capable`, `auto_operation_flag`, and `default_auto_operation_permission`.
- The display of the Mist UI: `columns`, `org_column_mappings`, `prefixes_for_display_data`, `server_column_mappings`, and `site_column_mappings`.

The 8 fields of an alarm definition are `default_enabled`, `display`, `example`,
`fields`, `group`, `key`, `marvis_suggestion_category`, and `severity`. The four
`warn` types are `ap_loop_by_duplicate_tunnels`, `ap_loop_by_duplicate_wlan_paths`,
`ap_loop_by_switch_port_flap`, and `port_flap`. The type
`intermittent_wan_connectivity` holds no `default_enabled` value. Each other Marvis
type holds `true`.

Nine topics hold `auto_operation_capable` with the value `true`. No alarm definition
holds a field for an automatic operation. See [The Marvis settings](#the-marvis-settings).

#### Each topic and the alarm types

The API gives no map from a topic to an alarm type. This table compares the 35
topics with the 35 Marvis alarm types in three ways.

- The column "Similar name" compares the names only.
- The column "Named in an example" lists each alarm type whose `example` names the
  topic in `details.category` and `details.symptom`. Two examples hold `details` as
  JSON text, and the column reads that text too. The mark "(text)" shows these two
  examples. See
  [The examples in the alarm definitions](#the-examples-in-the-alarm-definitions).
- The column "Live join" gives the join of 2026-09-25.

The values of the column "Live join" have these meanings.

- Yes: at least one action joined an alarm. The numbers give the actions with an
  alarm and all the actions of the topic.
- No alarm: at least one action started after the oldest alarm, but no action had
  an alarm.
- Too old: each action of the topic started before the oldest alarm.
- No data: the organization held no action of the topic.

| Topic | Display name in the schema | Similar name | Named in an example | Live join |
| - | - | - | - | - |
| `ap/ap_disconnect` | Offline | `ap_offline` | `ap_offline`, `ap_offline_isp_site_down` | Yes, 9 of 66 |
| `ap/ap_loop` | AP Loop Detected | `ap_loop_by_duplicate_tunnels`, `ap_loop_by_duplicate_wlan_paths`, `ap_loop_by_switch_port_flap` | `ap_loop_by_duplicate_tunnels`, `ap_loop_by_duplicate_wlan_paths` | No data |
| `ap/headroom_insufficient` | Dynamic Capacity Optimization | `insufficient_capacity` | None | No data |
| `ap/health_check` | Health Check Failed | `health_check_failed` | `health_check_failed` | No data |
| `ap/insufficient_coverage` | Insufficient Coverage | `insufficient_coverage` | `insufficient_coverage` | No data |
| `ap/mxedge_failure` | Mist Edge Anomaly | None | None | No data |
| `ap/non_compliant` | Non-compliant | `non_compliant` | `non_compliant` | No data |
| `ap/site_down_isp_issue` | ISP Offline | `ap_offline_isp_site_down` | None | No data |
| `ap/site_radar_channel_punishment` | DFS Optimization | None | None | No alarm, 0 of 2 |
| `application/reachability_failure` | Reachability Failure | `minis_application_reachability_failure` | `minis_application_reachability_failure` (text) | Yes, 2 of 2 |
| `client/persistently_failing` | Persistently Failing Clients | None | None | No data |
| `connectivity/arp_failure` | ARP Failure | `arp_failure`, `minis_arp_failure` | `arp_failure`, `minis_arp_failure` | No data |
| `connectivity/auth_failure` | Authentication Failure | `authentication_failure` | `authentication_failure` | No data |
| `connectivity/dhcp_failure` | DHCP Failure | `dhcp_failure`, `minis_dhcp_failure` | `dhcp_failure`, `minis_dhcp_failure` | Yes, 1 of 2 |
| `connectivity/dns_failure` | DNS Failure | `dns_failure`, `minis_dns_failure` | `dns_failure`, `minis_dns_failure` | No data |
| `gateway/bad_wan_link` | Intermittent WAN Connectivity | `bad_wan_uplink` | `intermittent_wan_connectivity` | Too old, 0 of 6 |
| `gateway/gw_mtu_mismatch` | MTU Mismatch | `gw_mtu_mismatch` | `gw_mtu_mismatch` | No data |
| `gateway/gw_negotiation_incomplete` | Negotiation Incomplete | `gw_negotiation_mismatch` | None | No data |
| `gateway/intermittent_wan_connectivity` | Bad WAN Uplink | `intermittent_wan_connectivity` | `bad_wan_uplink` | No data |
| `gateway/non_compliant` | Non-compliant | `gw_non_compliant` | `gw_non_compliant` | Too old, 0 of 2 |
| `gateway/vpn_path_down` | VPN Path Down | `vpn_path_down` | `vpn_path_down` (text) | Too old, 0 of 1 |
| `layer_1/bad_cable` | Bad Cable | `ap_bad_cable`, `bad_cable`, `gw_bad_cable` | `ap_bad_cable`, `bad_cable`, `gw_bad_cable` | No data |
| `layer_1/bad_fiber_optics` | Bad Fiber Optics | None | None | No data |
| `security` with an empty symptom | Empty | None | None | No data |
| `switch/high_cpu` | High CPU | `sw_high_cpu_usage` | None | No data |
| `switch/misconfig_port` | Misconfigured Port | None | None | No data |
| `switch/missing_vlan` | Missing VLAN | `missing_vlan` | `missing_vlan` | No data |
| `switch/mtu_mismatch` | MTU Mismatch | `sw_mtu_mismatch` | `sw_mtu_mismatch` | No data |
| `switch/negotiation_incomplete` | Negotiation Incomplete | `sw_negotiation_incomplete` | `sw_negotiation_incomplete` | No data |
| `switch/port_flap` | Network Port Flap | `port_flap` | `port_flap` | Yes, 2 of 3 |
| `switch/port_stuck` | Port Stuck | `port_stuck` | `port_stuck` | No data |
| `switch/rogue_dhcp_server` | Rogue DHCP Server Detected | None | None | No data |
| `switch/stp_loop` | Loop Detected | `switch_stp_loop` | None | No data |
| `switch/sw_offline` | Switch Offline | `switch_offline` | `switch_offline` | Yes, 19 of 30 |
| `switch/traffic_anomaly` | Traffic Anomaly | None | None | No data |

Eight topics have no Marvis alarm type with a similar name. For three of them, the
group `infrastructure` holds a type with a similar name.

| Topic | Type with a similar name in the group `infrastructure` |
| - | - |
| `ap/mxedge_failure` | The 24 `mist_edge_*` types, for example `mist_edge_disconnected` |
| `layer_1/bad_fiber_optics` | `sw_bad_optics` |
| `switch/rogue_dhcp_server` | `sw_rogue_dhcp_server_detected` |
| `ap/site_radar_channel_punishment`, `client/persistently_failing`, `switch/misconfig_port`, `switch/traffic_anomaly`, and the `security` topic | None in any group |

The `infrastructure` types are not Marvis alarms, and menu 270 searches the group
`marvis` only. In the live organization, no `infrastructure` alarm joined an action.

The table also shows these differences.

- The categories `client`, `layer_1`, and `security` hold no alarm definition. The
  three alarm types for a bad cable use the categories `ap`, `gateway`, and
  `switch`. Each of their examples names the topic `layer_1/bad_cable`. So
  `marvis_suggestion_category` does not always equal the category of the topic.

- One Marvis alarm type has no topic with a similar name. It is
  `wan_device_problem`, with the display name "Device Problem". Its example names
  `device_health/device_problem`, and the schema holds no such topic.

- Five topics have two or three alarm types with a similar name. They are
  `ap/ap_loop`, `connectivity/arp_failure`, `connectivity/dhcp_failure`,
  `connectivity/dns_failure`, and `layer_1/bad_cable`. The name does not tell which
  type Mist creates for one action. For `connectivity/dhcp_failure`, the live join
  found `minis_dhcp_failure`, not `dhcp_failure`.

- The similar name and the example do not agree for `ap/site_down_isp_issue`. The
  name is similar to `ap_offline_isp_site_down`, but the example of that type names
  `ap/ap_disconnect`.

- Five pairs occur in the live join. They are `ap/ap_disconnect` with `ap_offline`,
  `switch/sw_offline` with `switch_offline`, `switch/port_flap` with `port_flap`,
  `application/reachability_failure` with `minis_application_reachability_failure`,
  and `connectivity/dhcp_failure` with `minis_dhcp_failure`.

The two WAN topics have no clear answer. The sources do not agree for
`gateway/bad_wan_link`.

| Source | Alarm type for `gateway/bad_wan_link` |
| - | - |
| The symptom key `bad_wan_link`, compared with the keys of the alarm types | `bad_wan_uplink` |
| The Mist UI name "Bad WAN Uplink", compared with the display names of the alarm types | `bad_wan_uplink` |
| The schema display name "Intermittent WAN Connectivity", compared with the display names of the alarm types | `intermittent_wan_connectivity` |
| The `details.symptom` of the examples | `intermittent_wan_connectivity` |
| The live join | No pair. Each of the 6 actions started before the oldest alarm. |

The example of `intermittent_wan_connectivity` also holds the `type` value
`bad_wan_uplink`, so the same example holds the two names. Do not map the WAN topics
to an alarm type by name. Use the join of the alarm `id` and the action `uuid`.

#### The examples in the alarm definitions

The document describes `example` as a "Sample alarm payload returned for this alarm
type". Each of the 35 Marvis types holds an example. The examples hold fields that
no live alarm holds.

| Field | Examples that hold it | Live alarms that hold it |
| - | - | - |
| `category` | 34 of 35 | 0 of 33 |
| `details` | 34 of 35 | 0 of 33 |
| `details.symptom` | 32 of 35 as an object field. Two more examples hold it in JSON text. | 0 of 33 |
| `suggestion` | 30 of 35 | 0 of 33 |
| `action_id` | 15 of 35 | 0 of 33 |
| `row_key` | 0 of 35 | 0 of 33 |

The documented webhook payload `webhook_alarm_event` does not describe these fields
either. The research found no payload that holds them. The research did not test a
webhook delivery.

The examples also hold errors. In 13 of the 35 examples, the `type` value differs
from the `key` of the definition. In 7 of them, only the letter case differs, for
example `MISSING_VLAN`. The other 6 hold another name. For example, the example of
`switch_offline` holds `sw_offline`, and the example of `dhcp_failure` holds
`psk_failure`.

The top-level `category` of 7 examples differs from the `marvis_suggestion_category`
of the definition. For example, the example of `gw_non_compliant` holds
`device_health`, but the definition holds `gateway`. The example of
`switch_stp_loop` holds no `category`.

Five examples name a topic that the schema does not hold. They are
`switch/ap_loop`, `ap/insufficient_capacity`, `gateway/negotiation_mismatch`,
`device_health/device_problem`, and `switch/high_cpu_usage`.

Two examples hold `details` as JSON text, not as an object. They are the examples of
`minis_application_reachability_failure` and `vpn_path_down`. The text of each names
a schema topic: `application/reachability_failure` and `gateway/vpn_path_down`. A
script that reads `details` as an object finds no topic in these two examples. The
example of `switch_stp_loop` holds no `details`, so it names no topic.

In total, 29 examples name a schema topic, 5 name a topic that the schema does not
hold, and 1 names no topic. The examples name 22 of the 35 topics. The other 13
topics have no example.

The examples give the best map that Mist publishes from an alarm type to a topic.
But a sample can hold wrong values, and no live alarm holds these fields. Do not use
the examples as a map in a script. To find the alarm of an action, join the alarm
`id` to the action `uuid`. That join needs the list, so it does not remove the need
for the `labs` list. See
[How MistHelper joins an alarm to an action](#how-misthelper-joins-an-alarm-to-an-action).

### The resolve and the alarm acknowledge

| Item | The resolve (`labs`) | The alarm acknowledge (documented) |
| - | - | - |
| Path | `PUT /api/v1/labs/orgs/{org_id}/suggestions` | `POST /api/v1/orgs/{org_id}/alarms/{alarm_id}/ack`, `POST /api/v1/orgs/{org_id}/alarms/ack`, or `POST /api/v1/orgs/{org_id}/alarms/ack_all` |
| SDK function | None | `orgs.alarms.ackOrgAlarm`, `orgs.alarms.ackOrgMultipleAlarms`, or `orgs.alarms.ackOrgAllAlarms` |
| Target | One action, by `row_key` | One alarm by `alarm_id`, a list in `alarm_ids`, or every alarm |
| Body | `row_key`, `status`, `label`, `comment`, and `resolve_time` | `note`. The list request also requires `alarm_ids`. |
| Record | The action `status`, `label`, and `comment` | The alarm `acked`, `acked_time`, `ack_admin_name`, and `note` |
| Resolution code | `label`, with four values. See [Resolution codes](#resolution-codes). | None |
| Effect on the Open tab | The action leaves the Open tab. | Not known. The research did not test it. |
| Undo | The same PUT with the `status` value `open`. See [Undo a resolve](#undo-a-resolve). | `POST /api/v1/orgs/{org_id}/alarms/unack` with a list, or the site path for one alarm |
| Batch limit | One action for each request | Up to 1,000 alarm IDs in one list request. The text of the `ack_all` operation states the limit. |
| Reach | Every action | Only the actions that have an alarm. 81 of 114 actions had no alarm. |

The document describes no request that sets the alarm `status`. The research did
not test if an acknowledge changes the action, or if a resolve changes the alarm.
Issue #3357 tracks that test as phase 2 of issue #3339. See
[The limits of an acknowledge step](#the-limits-of-an-acknowledge-step).

Four other requests in the document change data near the alarms. None of them can
resolve an action.

| Request | SDK function | What it changes | Why it cannot resolve an action |
| - | - | - | - |
| `POST /api/v1/orgs/{org_id}/alarmtemplates/suppress` | `orgs.alarmtemplates.suppressOrgAlarm` | It stops the alarm service for the organization, for site groups, or for sites. | The body holds `scope`, `applies`, `duration`, and `scheduled_time`. It names no alarm type, no alarm, and no action. |
| `DELETE /api/v1/orgs/{org_id}/alarmtemplates/suppress` | `orgs.alarmtemplates.unsuppressOrgSuppressedAlarms` | It removes a suppression. | It changes no action. |
| `POST /api/v1/orgs/{org_id}/alarmtemplates` and `PUT /api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id}` | `orgs.alarmtemplates.createOrgAlarmTemplate` and `orgs.alarmtemplates.updateOrgAlarmTemplate` | The `rules` map sets `enabled` and `delivery` for each alarm type. | A rule controls future alarms. It does not close an action. |
| `POST /api/v1/sites/{site_id}/marvis_configs/{id}/feedback` | `sites.marvis_configs.submitSiteMarvisConfigFeedback` | It marks one Marvis Config Action as invalid. | It changes a different object. See [The Marvis Config Actions](#the-marvis-config-actions). |

The default `duration` of a suppression is 3,600 seconds, and the maximum is
15,552,000 seconds (180 days). A `duration` of 0 removes the suppression. The
`scheduled_time` can start the suppression up to 7 days later.

Warning: a suppression will stop every alarm of its scope, not only the Marvis
alarms. The operators then get no alarm for a real outage for up to 180 days. Do not
use a suppression to clear the Marvis Actions.

### The MSP count

`GET /api/v1/msps/{msp_id}/suggestion/count` is the only documented path with
`suggestion` in its name. Its OpenAPI tag is "MSPs Marvis", and it is the only
operation of that tag. The SDK function is `msps.suggestion.countMspsMarvisActions`.

| Item | The list (`labs`) | The MSP count (documented) |
| - | - | - |
| Scope | One organization | Every organization of one MSP |
| Parameters | `query`, `resolve_wcid`, `limit`, `page`, and four filters | `distinct` (`org_id` or `status`, default `org_id`) and `limit` (default 100) |
| Response | One row for each action | `distinct`, `limit`, `results`, and `total`. Each result holds a `count`. |
| Key for the resolve | `row_key` | None |
| Topic filter | `category` and `symptom` | None |
| Status filter | `status` | None |

The research did not call this endpoint. The lab organization belongs to no MSP,
and the token holds the organization admin role only. The document describes counts
only, so the endpoint cannot give the rows that an export or a resolve needs. An MSP
can use it to count the actions of each organization. The MSP must then read the
list of each organization.

### The troubleshoot endpoint

`GET /api/v1/orgs/{org_id}/troubleshoot` is the only operation of the OpenAPI tag
"Orgs Marvis". The SDK function is `orgs.troubleshoot.troubleshootOrg`.

| Item | The list (`labs`) | The troubleshoot endpoint (documented) |
| - | - | - |
| Content | The Marvis Actions of the organization | A Marvis diagnosis for a site, a device, or a client |
| Time range | Each action that Mist keeps. The oldest action was 84.5 days old. | The last 7 days at most |
| Parameters | `query`, `resolve_wcid`, `limit`, `page`, and four filters | `mac`, `site_id`, `start`, `end`, and `type` (`wan`, `wired`, or `wireless`) |
| Status and key | `status` and `row_key` | None |
| License | No document states a license. | The document states that the endpoint requires a Marvis subscription. |

On 2026-09-25, the research asked for a diagnosis of the site with the most
actions. The window covered 6 days. The answer for `wired` held 0 results, the
answer for `wan` held 0 results, and the answer for `wireless` held 1 result,
"Weak Signal". In the same window, 3 actions started at that site: 2 `sw_offline`
actions and 1 `ap_disconnect` action. The diagnosis named none of them.

### The device events

`GET /api/v1/orgs/{org_id}/devices/events/search` returns the raw events of the
devices. The SDK function is `orgs.devices.searchOrgDeviceEvents`. The default
`device_type` is `ap`. For a switch or a gateway, send `device_type=switch` or
`device_type=gateway`.

The research read the events of the switch of the newest `sw_offline` action. The
window started 10 minutes before the `start_time` of the action, and it ended 10
minutes after the `end_time`. The search returned 32 events.

| Event type | Count |
| - | - |
| `SW_PORT_DOWN` | 9 |
| `SW_PORT_UP` | 9 |
| `SW_LACP_MEMBER_DOWN` | 3 |
| `SW_LACP_MEMBER_UP` | 3 |
| `SW_STP_TOPO_CHANGED` | 2 |
| `SW_LACPD_TIMEOUT` | 2 |
| `SW_LACPD_TIMEOUT_CLEARED` | 2 |
| `SW_DISCONNECTED` | 1 |
| `SW_CONNECTED` | 1 |

The 16 fields of an event are `chassis_mac`, `count`, `device_type`, `ext_ip`,
`first_seen`, `has_pcap`, `mac`, `model`, `org_id`, `pcap_url`, `port_id`,
`site_id`, `text`, `timestamp`, `type`, and `version`. No field holds a status, a
topic, or an action key. The events show what the device reported, not the action
of Marvis. An engineer can quote the events as evidence in a resolve comment. A
script cannot use them to find or to resolve an action.

### The other documented Marvis endpoints

| Family | Paths | SDK functions | Why it cannot replace a `labs` function |
| - | - | - | - |
| SLE | `GET /api/v1/orgs/{org_id}/insights/{metric}`, `GET /api/v1/orgs/{org_id}/insights/sites-sle`, and `GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary` | `orgs.insights.getOrgSle`, `orgs.insights.getOrgSitesSle`, and `sites.sle.getSiteSleClassifierDetails` | It returns the values of each service level and its classifiers, not actions. |
| Marvis Client | `GET /api/v1/orgs/{org_id}/marvisclients/events/search`, `GET /api/v1/orgs/{org_id}/marvisclients/events/count`, `GET /api/v1/orgs/{org_id}/insights/marvisclient/{marvisclient_id}/marvisclient-metrics`, and `DELETE /api/v1/orgs/{org_id}/stats/marvisclients` | `orgs.marvisclients.searchOrgMarvisClientEvents`, `orgs.marvisclients.countOrgMarvisClientEvents`, `orgs.insights.getOrgMarvisClientInsights`, and `orgs.stats.deleteOrgMarvisClient` | These four operations of the OpenAPI tag "Orgs Clients - Marvis" read the events and the metrics of the Marvis Client app on the client devices. The DELETE removes one Marvis Client. None of them reads or changes an action. |
| Settings | `GET` and `PUT` on `/api/v1/orgs/{org_id}/setting` and on `/api/v1/sites/{site_id}/setting` | `orgs.setting.getOrgSettings`, `orgs.setting.updateOrgSettings`, `sites.setting.getSiteSetting`, and `sites.setting.updateSiteSettings` | It controls the Marvis features. It holds no action. See [The Marvis settings](#the-marvis-settings). |
| Webhooks | `POST /api/v1/orgs/{org_id}/webhooks` with the topic `alarms` | `orgs.webhooks.createOrgWebhook` | It sends new alarm events to a receiver. See [The webhooks](#the-webhooks). |

#### The Marvis settings

| Item | The document | The live organization |
| - | - | - |
| `org_setting.marvis` | `disable_proactive_monitoring` and `self_driving`, with `wan`, `wired`, and `wireless`. Each domain holds `enabled`. The schema sets `additionalProperties` to false, so it permits no other field. | Only `auto_operations`, with 9 flags. Each flag holds `true`. Neither documented field is present. |
| `site_setting.marvis` | `auto_operations` with 9 flags | `null` on the site with the most actions |

The 9 live flags equal the 9 `auto_operation_flag` values of the schema. The
document describes its own 9 flag names for the site setting. Only 3 names occur in
both lists: `ap_non_compliant`, `gateway_non_compliant`, and `switch_port_stuck`.
So the document does not describe the setting that the live organization uses.

With a flag, Marvis can act on a topic without an operator. A flag cannot close an
action, and it holds no action key. [The self-drive fields](#the-self-drive-fields)
describes the live flags and their history.

Warning: a PUT to the organization setting will change the Marvis behavior for every
site. A wrong `marvis` object can stop the automatic operations, or start them on
live devices. Do not send a settings PUT to change the Marvis Actions.

#### The webhooks

The document describes 30 webhook topics. It also holds `webhook_delivery_topic`,
which lists the 5 topics that report delivery results. On 2026-09-25, the live
`GET /api/v1/const/webhook_topics` returned 31 topics. The live list adds
`filtered-asset-rssi` and `vbeacon`, and it does not hold `site-sle`. No topic in
the two lists holds the word Marvis or the word suggestion.

The nearest topic is `alarms`. The documented payload `webhook_alarm_event` holds
`aps`, `bssids`, `count`, `event_id`, `for_site`, `id`, `last_seen`, `node`,
`org_id`, `site_id`, `ssids`, `timestamp`, `type`, and `update`. It holds no
`status`, no `group`, and no action key. A webhook sends only the new events, so it
cannot give the actions that exist before the webhook. The research did not create
a webhook.

### When to check again

A later Mist release can change this answer. Check again when one of these events
occurs.

- The OpenAPI document of Mist adds a path with `suggestion` or `/labs/` in its
  name.
- A `mistapi` release adds a function for a Marvis Actions path.
- The alarm search adds a `status` filter, or a live alarm holds `row_key`.
- The Mist UI sends the resolve to a path outside `labs`.

This command prints each path of the bundled document that holds `suggestion` or
`/labs/`. Run it from the repository root.

```powershell
python -c "import json; spec = json.load(open('documentation/mist-api-openapi31json.json', encoding='utf-8')); print(sorted(path for path in spec['paths'] if 'suggestion' in path or '/labs/' in path))"
```

With release 2607.1.1, the command printed one path.

```text
['/api/v1/msps/{msp_id}/suggestion/count']
```

If the command prints a new path, compare the path with the three conditions in
[The three functions that menu 270 needs](#the-three-functions-that-menu-270-needs).

### Sources for the Marvis Actions endpoints

MistHelper checked these sources on 2026-09-24 and on 2026-09-25.

| Source | Version | Result |
| - | - | - |
| The bundled `documentation/mist-api-openapi31json.json` | Release 2607.1.1, 756 paths | The four operations of the Marvis Config family and the MSP count path. No list path, schema path, or resolve path for Marvis Actions. |
| The `master` branch of `mistsys/mist_openapi`, commit `0613a22acd` of 2026-09-18 | Release 2609.1.0, 762 paths | The same four operations of the Marvis Config family. No list path, schema path, or resolve path for Marvis Actions. |
| `mistapi` 0.64.0 installed in this worktree | Uploaded on 2026-09-15 | The four functions of the Marvis Config family and `msps.suggestion.countMspsMarvisActions`. No function for a `labs` path. |
| The online index `https://www.juniper.net/documentation/us/en/software/mist/api/llms.txt` | Read on 2026-09-25 | 1,266 API pages. No page names `labs`. |
| Live GET requests to the lab organization | 2026-09-24 and 2026-09-25 | The live facts of this report. No request changed Mist data. |

The only Marvis Actions path in the public document is the MSP count path. Menu 270
therefore keeps its direct calls to the `labs` paths. The Caution at the top of this
report stays correct.

## Where MistHelper keeps the results

| File | SQLite table | ArangoDB collection | Primary key | Content |
| - | - | - | - | - |
| `data/OrgMarvisActions.csv` | `OrgMarvisActions` | `listOrgMarvisActions` | `uuid` | One row for each action, with 43 action columns and 8 alarm columns. Modes 1, 2, and 4 write it. |
| `data/OrgMarvisActionsResolveResults.csv` | `OrgMarvisActionsResolveResults` | `resolveOrgMarvisActions` | `result_id` | One row for each action that a mode 3 run touched. |

The default format writes the CSV file. The `--output-format sqlite` flag writes
the SQLite table in `data/mist_data.db` and writes no CSV file. When ArangoDB
answers, each run also writes the ArangoDB collection.

The `result_id` joins the action `uuid` and the `resolve_time` of the run, so each
run adds new rows. The database document of an action holds the full raw row, the
readable columns, and the eight alarm columns.

A SQLite table from a release before issue #3339 holds 43 columns. The next
SQLite write adds the eight alarm columns to the table. Pull request #3351 added
that step.

## Where the code lives

| Endpoint | MistHelper method | File |
| - | - | - |
| List | `MarvisActionsClient.list_actions` | `src/marvis/actions/client.py` |
| Schema | `MarvisActionsClient.read_schema` | `src/marvis/actions/client.py` |
| Sites | `MarvisActionsClient.read_site_names` | `src/marvis/actions/client.py` |
| Alarm search | `MarvisActionsClient.search_marvis_alarms` | `src/marvis/actions/client.py` |
| Alarm join | `MarvisAlarmJoin.apply` | `src/marvis/actions/alarms.py` |
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
