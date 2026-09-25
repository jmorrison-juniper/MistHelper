# Research: Menu 270 joins each Marvis Action to its Marvis alarm

**Feature**: `3339-marvis-alarm-join` | **Issue**: #3339

**Spec**: [spec.md](./spec.md) | **Parent research**: [3299 research](../3299-marvis-actions-bulk-resolve/research.md)

This file records the evidence for each design decision. Each item names its
source, so a reviewer can repeat the check.

## Sources

| Source | What it gives |
| - | - |
| `documentation/api/orgs/GET_orgs_org_id_alarms_search.md` | The query values and the alarm fields of the organization alarm search. |
| `mistapi` 0.64.0, installed in the local virtual environment and in `misthelper-app` | The signatures of `searchOrgAlarms` and `get_next`. |
| `src/marvis/actions/client.py` at `origin/main` 0e84cb7c | The page checks and the guard of the Marvis Actions list read. |
| `src/marvis/actions/operation.py` at 0e84cb7c | The export step and the output of each mode. |
| `web_portal/services/operation.py` at 0e84cb7c | The words that make the portal mark a run as failed. |
| A live read-only test on 2026-09-24 at about 20:00Z | The alarm rows and the action rows of the lab organization. |

## R1. The join key

The live test read 112 actions from the Marvis Actions list and 33 alarms from
the alarm search. Each alarm held a unique `id`.

| Check | Result |
| - | - |
| Alarm `id` equals an action `uuid` | 31 alarms |
| Alarm `action_id` equals an action `uuid` | 0 alarms. No alarm held an `action_id` key. |
| One action with two alarms | 0 actions |
| Action status to alarm status | `validated` to `resolved` for 31 of 31 pairs |

The 31 pairs covered five alarm types.

| Action topic | Alarm type | Pairs |
| - | - | - |
| `switch/sw_offline` | `switch_offline` | 18 |
| `ap/ap_disconnect` | `ap_offline` | 8 |
| `switch/port_flap` | `port_flap` | 2 |
| `application/reachability_failure` | `minis_application_reachability_failure` | 2 |
| `connectivity/dhcp_failure` | `minis_dhcp_failure` | 1 |

The issue states that the definition examples of the `minis_*` types hold an
`action_id` that differs from the `id`. The live rows held no `action_id`.

Decision: build two maps. Match the `action_id` map first, then the `id` map. A
row of the future can then join through either key. The topic names and the
alarm type names differ, so the join does not use them.

## R2. The time units and the search window

The alarm search reads `start` and `end` as epoch seconds. The alarm fields
`timestamp`, `last_seen`, `resolved_time`, and `acked_time` also hold epoch
seconds. The Marvis Actions list holds epoch milliseconds in `start_time`.

The live test sent these windows. Each window ended at the time of the test.

| Window | HTTP status | Alarms |
| - | - | - |
| 7 days | 200 | 3 |
| 30 days | 200 | 23 |
| 200 days | 200 | 33 |
| 400 days | 200 | 33 |
| From one day before the oldest action start | 200 | 33 |

The API echoed `start` and `end` as floating point numbers, such as
`1782935503.0`. The oldest alarm `timestamp` was 2026-08-06T01:59:46Z. The oldest
action `start_time` was 2026-07-02T19:51:43Z. For 31 of 31 pairs, the alarm
`timestamp` equals the action start. For 0 of 31 pairs, the alarm
`resolved_time` equals the action end.

Decision: start the window one day before the oldest exported action. Stop at
400 days, because the live test proved that width. A window of one day or less
is not useful, so the window is at least one day wide. Send each value as whole
seconds in text, because the SDK types `start` and `end` as text.

## R3. The paging of the alarm search

The SDK function `searchOrgAlarms` sends page 1. A page holds up to `limit`
rows. If more rows exist, the body holds a `next` link with a `search_after`
value. The API reference states that the client must not build that value.

`mistapi.get_next(session, response)` reads `response.next`. It returns `None`
when the response holds no link. Otherwise, it calls `session.mist_get` with the
link. `mistapi.get_all` is not safe for this read. It raises an error on a page
that fails, and it loops without end on a repeated link.

The example `next` link of the API reference holds no `group` value.

Decision: read page 1 with `searchOrgAlarms` and `limit=1000`. Read each next
page with `get_next`. Stop at a page without a link, at an empty page, at a
repeated link, or at 100 pages. Keep only the rows with the group `marvis`,
because a next page can lose the group filter.

## R4. The alarm fields of the live organization

| Field | Alarms that hold it |
| - | - |
| `id`, `type`, `status`, `group`, `severity`, `timestamp`, `last_seen`, `count`, `site_id`, `org_id`, `impacted_entities` | 33 of 33 |
| `resolved_time` | 29 of 33 |
| `acked`, `acked_time`, `ack_admin_name`, `note`, `action_id` | 0 of 33 |

The statuses were `resolved` for 32 alarms and `open` for 1 alarm. The alarm
`severity` holds text, such as `critical`. The action `severity` holds a number,
so the two values do not compare.

Decision: copy eight fields. The acknowledge fields stay empty on the lab
organization. They fill when an operator acknowledges an alarm. Phase 2 needs
them to show the acknowledge state of each alarm.

## R5. The rows that did not join

81 actions had no alarm. 79 of them started before the oldest alarm. Two started
inside the alarm range. Their topics were `ap/site_radar_channel_punishment` and
`ap/ap_disconnect`.

Two alarms had no action. Both started on 2026-09-24 at about 19:14Z, less than
one hour before the test. One was `switch_offline` with the status `open`. One
was `ap_offline` with the status `resolved`.

Decision: log both counts. The first count shows the engineer how many empty
cells to expect. The second count shows the alarms that the list does not show
yet. The log states the count only, because the cause of each case is not proven.

## R6. The columns and the record shape

`MarvisActionRecord` is a frozen dataclass with 43 fields, and its field order
is the CSV column order. The builder fills each field from one raw row. The alarm
values come from a second read, after the filter step.

Decision: append eight fields after `exported_at`, each with an empty default.
The builder does not change. The join returns a new record through
`dataclasses.replace`. The database document receives the same eight values, so
the three stores hold one shape.

The two time columns take the `_iso` suffix. Six other time columns use that
suffix, and each holds ISO text. The new reader `MarvisFieldReader.iso_seconds`
turns epoch seconds into ISO text. It reuses the checks of `iso`, which reject a
value of 0 or less and a year outside the range of `datetime`.

## R7. The module placement

The package docstring names four modules. `model.py` holds five classes, and
`operation.py` holds six classes. A new class in either module breaks the
five-item rule further.

Decision: add the fifth module `alarms.py` with two classes, `MarvisAlarmIndex`
and `MarvisAlarmJoin`. Put the search in `MarvisActionsClient`, because the
client docstring states that one class holds every Mist API call of the feature.
Reuse `MarvisListResult` for the search result.

## R8. The portal failure words

`HANDLED_ERROR_MARKERS` in `web_portal/services/operation.py` holds `error
fetching`, `failed to`, and `could not`. The portal reads every log line of a
run. If one line holds a marker, the portal marks the run as failed, even when
the run wrote its file.

Decision: the warning line for a refused alarm search states "The Marvis alarm
search returned no usable result." It holds no marker. A unit test checks each
new log line against the three markers.

## R9. The SQLite writer

Before pull request #3351, the SQLite writer never added a column to an old
table. A write of 51 columns to a table of 43 columns failed on every insert,
and the writer still returned True. Issue #3350 records the defect.

Decision: this feature starts after the merge of #3351 on 2026-09-24 at 22:27Z.
The live test reads the SQLite table after a mode 1 run, and it confirms the
eight new columns.

## R10. The request budget

A mode 1 run sends one schema read, one list read for each 1,000 actions, and one
site read for each 1,000 sites. The join adds one alarm search for each 1,000
alarms. On the lab organization, the join adds one request.

## Alternatives that were rejected

| Alternative | Why it was rejected |
| - | - |
| Join by topic and impacted device. | The topic names and the alarm type names differ, and one device can hold two problems. The `id` key matched 31 of 31 pairs. |
| One alarm read for each action. | 112 actions would send 112 requests instead of 1. |
| `mistapi.get_all` for the paging. | It raises an error on a page that fails, and it loops without end on a repeated link. |
| A separate file `OrgMarvisAlarms.csv`. | The engineer must then join two files for each audit. |
| A window of the last 7 days. | It returned 3 of 33 alarms. |
| Stop the export when the alarm search fails. | The report worked before this feature, and the alarm columns are optional. |
| Acknowledge the alarms in phase 1. | An acknowledge writes to Mist, so it needs a human review and its own issue. |
