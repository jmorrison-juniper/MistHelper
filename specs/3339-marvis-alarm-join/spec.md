# Feature Specification: Menu 270 joins each Marvis Action to its Marvis alarm

**Feature Branch**: `feat/3339-marvis-alarm-join`

**Created**: 2026-09-24

**Status**: Approved for implementation

**Issue**: #3339, phase 1 only

**Parent feature**: #3299 and [the menu 270 specification](../3299-marvis-actions-bulk-resolve/spec.md)

**Input**: Issue #3339 asks menu 270 to read the Marvis alarms of the
organization and to join each alarm to its action. The user then said: "Begin
working all that, and get the improvements merged into main."

## Summary

Menu 270 exports the Marvis Actions of one organization. Mist also keeps a
Marvis alarm for many of these actions. The alarm holds its own status, its
resolved time, and its acknowledge values. Before this feature, a NOC engineer
compared the two views by hand.

Phase 1 adds eight alarm columns to each export row. Modes 1, 2, and 4 search
the Marvis alarms one time and join each alarm to its action. The run then writes
the joined rows to the CSV file and to the database. Phase 1 reads only. It sends
no acknowledge request and no other write request to Mist.

Phase 2 is the acknowledge step for the alarm of each resolved action. That step
writes to Mist, so it needs a human review. Issue #3357 holds phase 2.

## Clarifications

### Session 2026-09-24

The user runs this work in autopilot mode. The agent answered each question from
the issue, from the live read-only test of 2026-09-24, and from the local Mist API
reference.

- Q: Which phase does this specification cover? -> A: Phase 1 only. Phase 2
  writes to Mist, so a separate issue holds it.
- Q: Which modes search the alarms? -> A: Modes 1, 2, and 4. Mode 3 searches no
  alarm, because its results file holds no alarm column.
- Q: Which key joins an alarm to an action? -> A: The alarm `action_id` first,
  then the alarm `id`. The key must equal the action `uuid`. The live test joined
  31 alarms through `id` and 0 alarms through `action_id`.
- Q: Which alarm wins when two alarms hold the same key? -> A: The alarm with the
  larger `last_seen` value. If the two values are equal, the first alarm stays.
- Q: What are the names of the two time columns? -> A: `alarm_resolved_time_iso`
  and `alarm_acked_time_iso`. The issue names them without the `_iso` suffix. The
  record holds readable text for each time, and six other time columns use that
  suffix.
- Q: Which time window does the search use? -> A: The window starts one day
  before the oldest start time of the exported actions. It ends at the time of the
  run. The window is never wider than 400 days. If no exported action holds a
  start time, the window covers the last 400 days.
- Q: What happens when the alarm search fails? -> A: The export continues. The
  alarm columns stay empty, and one warning line states the reason.
- Q: Does the join add a prompt? -> A: No. The prompts, the portal controls, and
  their order stay the same.
- Q: Which alarms does the join use? -> A: The Marvis alarms only. The request
  sends `group=marvis`, and the client keeps only the rows that hold that group.

### Answers to the open questions of the issue

| Number | Question | Answer |
| - | - | - |
| 1 | Does a resolve in the Marvis Actions list change the alarm status? | Not tested. The test needs a write, so phase 2 holds it. |
| 2 | Does an acknowledge of the alarm change the action status? | Not tested. The test needs a write, so phase 2 holds it. |
| 3 | Does the search return the alarm of a validated action? | Yes. All 31 joined actions held the status `validated`, and each alarm held `resolved`. |
| 4 | Which alarm time does the search window filter? | Not proven. The alarm `timestamp` equals the action start for 31 of 31 pairs, so the window starts before the oldest action start. |
| 5 | Does the search accept a window that starts at the oldest action? | Yes. A window of 400 days returned HTTP 200. |
| 6 | Does the join rule hold for the `minis_*` types? | Yes. Two `minis_application_reachability_failure` alarms and one `minis_dhcp_failure` alarm joined through `id`. |

The issue states that the list returns rows back to 2026-08-06. The live test
found an older row. The oldest action started at 2026-07-02T19:51:43Z. The oldest
alarm started at 2026-08-06T01:59:46Z.

## Definitions

- **Marvis Action**: One Mist record that names one network problem that Marvis
  found. The parent specification defines the term.
- **Marvis alarm**: One row of the organization alarm search with the group
  `marvis`.
- **Join**: The step that finds the alarm of each exported action and copies
  eight alarm values into the export row of that action.
- **Joined action**: An exported action that has an alarm.
- **Search window**: The start time and the end time that the alarm search
  sends, in epoch seconds.
- **Operations portal**: The Flask operations web application on port 8055.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the alarm of each exported action (Priority: P1)

A NOC engineer audits how the Marvis problems of an organization closed. The
engineer runs mode 1 of menu 270. Each export row shows the action values and
the values of its alarm, so the engineer compares the two views in one row.

**Why this priority**: This story is the request of the issue.

**Independent Test**: Run mode 1 with one action that has an alarm and one
action that has no alarm. Read the rows of the export write.

**Acceptance Scenarios**:

1. **Given** an action with an alarm, **When** the engineer runs mode 1, **Then**
   the row holds the alarm `id`, `type`, and `status`. The row also holds the
   resolved time as ISO text.
2. **Given** an action without an alarm, **When** the engineer runs mode 1,
   **Then** the eight alarm columns of the row are empty.
3. **Given** a mode 1, 2, or 4 run, **When** the run writes, **Then** each store
   holds the eight alarm columns. The stores are the CSV file, the SQLite table,
   and the ArangoDB collection.
4. **Given** a mode 1, 2, or 4 run, **When** the run ends, **Then** Mist received
   no write request.

### User Story 2 - Count the rows that did not join (Priority: P2)

The engineer must know how many actions have no alarm. Mist keeps alarms for a
shorter time than actions, so an old action can have no alarm.

**Why this priority**: A count prevents a wrong conclusion from an empty cell.

**Independent Test**: Run mode 1 on three actions and two alarms. One alarm
names no exported action.

**Acceptance Scenarios**:

1. **Given** a run, **When** the join ends, **Then** the log shows how many
   exported actions have an alarm and how many have no alarm.
2. **Given** an alarm that names no action of the list, **When** the join ends,
   **Then** the log shows the count of those alarms.
3. **Given** an SSH session or a portal run, **When** the join ends, **Then**
   the two count lines appear on the console.

### User Story 3 - Keep the export safe when the alarm search fails (Priority: P2)

The alarm columns add information, but the export must not depend on them. A
refused alarm search must not stop the report.

**Why this priority**: The export worked before this feature. The join must not
add a new way for the export to fail.

**Independent Test**: Make the alarm search return HTTP 403. Read the export
write and the log.

**Acceptance Scenarios**:

1. **Given** an alarm search that returns HTTP 403, **When** the engineer runs
   mode 1, **Then** the run writes every row with empty alarm columns.
2. **Given** that refused search, **When** the run ends, **Then** one warning
   line names the reason, and the completion line is the last line.
3. **Given** that refused search, **When** the portal reads the log, **Then**
   the portal marks the run as completed, not as failed.

### User Story 4 - Keep the resolve mode unchanged (Priority: P3)

Mode 3 resolves the open actions. Its results file holds no alarm column.

**Why this priority**: A resolve run must not spend requests on data that it
does not write.

**Independent Test**: Run mode 3 with one open action. Count the alarm search
calls.

**Acceptance Scenarios**:

1. **Given** a mode 3 run, **When** the run ends, **Then** the run sent no alarm
   search request.

### Edge Cases

- An alarm can hold an `action_id` that differs from its `id`. The `action_id`
  match wins, because the issue names that key first.
- Two alarms can hold the same key. The alarm with the larger `last_seen` value
  wins.
- A row of another alarm group can appear in a page. The client drops it.
- An alarm time can hold a fraction of a second. The ISO text keeps whole
  seconds only.
- The live organization held no `acked` value. The `alarm_acked` column then
  stays empty, not False.
- A next link that repeats, or a search that reaches 100 pages, stops the read.
  One warning line states that the join holds the alarms of the pages that the
  client read.
- A page that fails discards every alarm row. The export continues with empty
  alarm columns.
- An older SQLite table holds 43 columns. The writer adds the eight new columns
  before the write. Pull request #3351 fixed that step for issue #3350.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Modes 1, 2, and 4 MUST search the Marvis alarms one time for each
  export. The search MUST use `searchOrgAlarms` with `group=marvis`, the search
  window, and `limit=1000`. The search MUST occur after the filter prompts and
  before the write.
- **FR-002**: The search window MUST start 86,400 seconds before the oldest
  `start_time` of the exported actions. The start MUST NOT be earlier than 400
  days before the end. The end MUST be the time of the run. The window MUST be at
  least one day wide.
- **FR-003**: The client MUST follow the `next` link of each page. The read ends
  at a page without a link or at an empty page. A repeated link or the guard of
  100 pages MUST stop the read with one warning line.
- **FR-004**: A page fails when it returns no HTTP answer, a status other than
  200, or a body without a results list. If a page fails, the client MUST discard
  every alarm row. The export MUST continue with empty alarm columns. The export
  MUST log one warning line that names the reason.
- **FR-005**: The join MUST match the alarm `action_id` to the action `uuid`
  first. If no alarm matches, the join MUST match the alarm `id`. If two alarms
  hold one key, the alarm with the larger `last_seen` value MUST win.
- **FR-006**: Each export row MUST hold eight new columns after `exported_at`, in
  this order: `alarm_id`, `alarm_type`, `alarm_status`,
  `alarm_resolved_time_iso`, `alarm_acked`, `alarm_acked_time_iso`,
  `alarm_ack_admin_name`, and `alarm_note`.
- **FR-007**: An action without an alarm MUST hold empty text in seven columns
  and an empty flag in `alarm_acked`.
- **FR-008**: The two time columns MUST hold ISO 8601 UTC text with whole
  seconds. The source values are epoch seconds.
- **FR-009**: The CSV file, the SQLite table, and the ArangoDB document MUST hold
  the eight columns.
- **FR-010**: The run MUST log two count lines at the display level. The first
  line states the joined count and the count without an alarm. The second line
  states the count of alarms in the window that name no action of the list.
- **FR-011**: Mode 3 MUST NOT search the alarms.
- **FR-012**: The join MUST NOT send a write request to Mist.
- **FR-013**: The prompts, the portal controls, and their order MUST NOT change.
- **FR-014**: The client MUST keep only the alarm rows with the group `marvis`.
- **FR-015**: No new log line can hold the words `could not`, `failed to`, or
  `error fetching`. The portal marks a run as failed when a line holds one of
  them.
- **FR-016**: The README, the NOC endpoint report, and its data copy MUST
  describe the join. The NOC report MUST name the alarm search, the join key, the
  window, and the columns. It MUST also state the limits of an acknowledge step.

### Key Entities

- **Alarm row**: One raw row of the alarm search. The join reads `id`,
  `action_id`, `type`, `status`, `resolved_time`, `acked`, `acked_time`,
  `ack_admin_name`, `note`, `group`, and `last_seen`.
- **Alarm index**: Two maps of the alarm rows. One map uses the `action_id` key,
  and one map uses the `id` key.
- **Alarm columns**: The eight values that the join copies into one export row.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A live mode 1 run on the lab organization joins each action whose
  `uuid` equals the `id` or the `action_id` of an alarm in the window. A direct
  count of the same data gives the same number.
- **SC-002**: The CSV file, the SQLite table, and the ArangoDB collection hold
  the same alarm values for one joined action.
- **SC-003**: A portal run of mode 1 on port 8055 completes, offers
  `OrgMarvisActions.csv`, and shows the two count lines.
- **SC-004**: An SSH run of mode 4 on port 2200 shows the two count lines.
- **SC-005**: Every menu 270 test passes, and each functional requirement has at
  least one test.
- **SC-006**: A mode 1 run on the lab organization sends one alarm search request
  and zero write requests.

## Assumptions

- Pull request #3351 merged before this feature. Without it, a SQLite write to a
  table of 43 columns fails.
- Mist does not document how long it keeps an alarm. The lab organization held
  no alarm older than 2026-08-06T01:59:46Z, and 79 older actions had no alarm.
- The alarm search returns the alarms of every site of the organization when the
  request sends no `site_id`.
- Menu 270 stays `interactive_safe`. The join reads only, so the safety class
  does not change.
