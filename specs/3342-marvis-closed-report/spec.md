# Feature Specification: Menu 270 mode 4, the closed Marvis Actions report

**Feature Branch**: `feat/3342-marvis-closed-report`

**Created**: 2026-09-24

**Status**: Approved for implementation

**Issue**: #3342

**Parent feature**: #3299 and [the menu 270 specification](../3299-marvis-actions-bulk-resolve/spec.md)

**Input**: User question (voice transcript, cleaned): "Does the menu option also
have the ability to give a report of all closed or resolved Marvis alarms or
actions?" The answer was "partly". Mode 1 exports every action, open and closed.
No mode exports the closed actions only. The user then said: "Begin working all
that, and get the improvements merged into main."

## Clarifications

### Session 2026-09-24

The user runs this work in autopilot mode, so the agent answered each question
from the repository evidence and recorded the reason.

- Q: Does the new mode replace a current mode? -> A: No. Mode 4 is new. Modes 1,
  2, and 3 keep their numbers and their behavior, so a saved answer keeps its
  meaning.
- Q: Which actions are closed? -> A: Every action with the `is_open` value False.
  The code sets `is_open` to True for `open`, `inprogress`, and `reoccured` only.
  A status key that the code does not know counts as closed.
- Q: What do the tables count in mode 4? -> A: The tables show only the topics
  that hold a closed action. A new Closed column shows the closed count of each
  row in every mode. The Actions column and the Open column stay.
- Q: Which file does mode 4 write? -> A: `OrgMarvisActions.csv`, with the same
  database strategy as modes 1 and 2. A second file name makes two tables with
  the same columns, and a reader must then join them.
- Q: Does mode 4 read the org alarms of the `marvis` group? -> A: No. Issue #3339
  tracks that join.
- Q: How does the report show a status key that the code does not know? -> A: The
  `status_name` cell holds the raw key. The run also logs one caution line that
  names each unknown key and its count.

## Definitions

- **Marvis Action**: One Mist record that names one network problem that Marvis
  found. The parent specification defines the term.
- **Open action**: An action with the status `open`, `inprogress`, or
  `reoccured`. These three statuses fill the Open tab of the Mist UI.
- **Closed action**: Every other action. The known closed statuses are
  `resolved`, `validated`, `marvis_self_driven`, and `expired action`.
- **Topic**: One category and subcategory pair, such as `switch/sw_offline`.
- **Operations portal**: The Flask operations web application on port 8055.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export the closed actions (Priority: P1)

A NOC engineer must audit how the Marvis Actions of an organization closed. The
engineer starts menu 270, types `4`, and keeps every topic. The report holds the
closed actions only, so the engineer does not filter the CSV file by hand.

**Why this priority**: This story is the request of the user.

**Independent Test**: Run mode 4 on a mix of open and closed actions. Read the
rows of the export write.

**Acceptance Scenarios**:

1. **Given** an organization with open and closed actions, **When** the engineer
   runs mode 4 with every topic, **Then** each exported row holds `is_open` False.
   No open action appears.
2. **Given** a mode 4 run, **When** the run ends, **Then** Mist received no write
   request, and the log holds no resolve line.
3. **Given** a closed row that an operator resolved, **When** mode 4 exports it,
   **Then** the row keeps its `label`, `label_name`, `comment`, and
   `resolve_time_iso` values.

### User Story 2 - Filter the closed report by topic (Priority: P2)

The engineer wants the closed actions of one topic only, such as Wired / Switch
Offline. The category and subcategory tables show only the topics with a closed
action, and each row shows its closed count.

**Why this priority**: The parent feature filters every mode by topic, and the
same answers must work in mode 4.

**Independent Test**: Run mode 4 with a category key and a subcategory key.

**Acceptance Scenarios**:

1. **Given** mode 4, **When** the tables appear, **Then** a topic without a closed
   action is absent.
2. **Given** any mode, **When** a table appears, **Then** it holds the columns
   Actions, Open, and Closed.
3. **Given** mode 4 and a known category without a closed action, **When** the
   engineer selects that category, **Then** the run logs the stop line. The line
   is "No closed Marvis Actions match the filter. No file was written."

### User Story 3 - Run mode 4 from the operations portal (Priority: P2)

The engineer uses the operations portal instead of SSH. The mode list offers the
closed report as a choice that changes nothing in Mist.

**Why this priority**: The user requires the portal for every mode of menu 270.

**Independent Test**: Select mode 4 in the browser, click Run, and read the
answers that the browser sends.

**Acceptance Scenarios**:

1. **Given** the operations page, **When** the engineer opens the mode list,
   **Then** it offers "4 - Export the closed Marvis Actions (report only)".
2. **Given** mode 4 in the portal, **When** the engineer clicks Run, **Then** the
   browser sends `4` as the first of six answers. The control order does not
   change.
3. **Given** a portal run of mode 4, **When** the run ends, **Then** the portal
   reports a completed run that offers `OrgMarvisActions.csv`.

### User Story 4 - Stop with a clear line (Priority: P3)

The engineer runs mode 4 on an organization that holds no closed action.

**Why this priority**: A clear stop line prevents a false success.

**Independent Test**: Run mode 4 on open actions only.

**Acceptance Scenarios**:

1. **Given** an organization with open actions only, **When** the engineer runs
   mode 4, **Then** the run logs "No closed Marvis Actions exist in this
   organization. No file was written." before the filter prompts.

### Edge Cases

- A status key that the code does not know counts as closed. The `status_name`
  cell shows the raw key, and one caution line names each unknown key.
- An empty status key also counts as closed. The caution line shows it as `''`.
- The SQLite format writes the table `OrgMarvisActions` and no CSV file.
- The database keeps the rows of earlier runs, because each write updates a row
  by its `uuid`. A database reader filters the table on `is_open`.
- A bad mode answer, such as `5`, stops the run before any API call.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mode prompt MUST accept the answer `4`. The prompt text MUST be
  "Enter the mode number (1, 2, 3, or 4) [1]: ".
- **FR-002**: The mode table MUST show the line "4. Export the closed Marvis
  Actions only".
- **FR-003**: Mode 4 MUST export only the actions with the `is_open` value False.
- **FR-004**: Mode 4 MUST NOT send a write request to Mist. It MUST send only the
  three read requests of mode 1.
- **FR-005**: In mode 4, the category table and the subcategory table MUST show
  only the topics that hold at least one closed action.
- **FR-006**: Each table MUST show a Closed column in every mode. The value is the
  Actions count minus the Open count.
- **FR-007**: If the organization holds no closed action, mode 4 MUST stop before
  the filter prompts. The stop line is "No closed Marvis Actions exist in this
  organization. No file was written."
- **FR-008**: If the filter keeps no closed action, mode 4 MUST stop with "No
  closed Marvis Actions match the filter. No file was written."
- **FR-009**: Mode 4 MUST write `OrgMarvisActions.csv` with the columns of mode 1
  and the database strategy `listOrgMarvisActions`.
- **FR-010**: A status key that the code does not know MUST show its raw key in
  the `status_name` column. The export MUST log one caution line that names each
  unknown key and its count.
- **FR-011**: The operations portal MUST offer mode 4 with the label "4 - Export
  the closed Marvis Actions (report only)". The six controls and their order MUST
  NOT change.
- **FR-012**: The refusal of an unknown mode MUST state "Enter 1, 2, 3, or 4."
- **FR-013**: The unattended `--testinteractive` pass MUST still take mode 1.
- **FR-014**: The README and both copies of the NOC endpoint report MUST describe
  mode 4.

### Key Entities

- **Mode**: One of the four answers `1`, `2`, `3`, and `4`. Each mode keeps a set
  of `is_open` values. Mode 1 keeps True and False. Modes 2 and 3 keep True. Mode
  4 keeps False.
- **Topic count row**: One row of a filter table. It holds the key, the name, the
  Actions count, the Open count, and the Closed count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A mode 4 run on the lab organization writes only rows with
  `is_open` False. The row count equals the closed count of a mode 1 run.
- **SC-002**: A mode 4 run sends zero PUT requests. The unit tests count the
  requests, and the live `script.log` holds no resolve line.
- **SC-003**: A portal run of mode 4 on port 8055 completes and offers
  `OrgMarvisActions.csv`.
- **SC-004**: An SSH run of mode 4 on port 2200 shows four mode lines and the
  Closed column.
- **SC-005**: Every menu 270 test passes, and each functional requirement has at
  least one test.

## Assumptions

- The lab organization held 0 open actions and 112 closed actions on 2026-09-24.
  A live mode 4 run therefore equals a live mode 1 run in row count. The unit
  tests prove the split with mixed statuses.
- The CSV file holds the rows of the last run only. The database table keeps the
  rows of earlier runs, as it does for mode 2 today.
- Menu 270 stays `interactive_safe`. Mode 4 reads only, so the safety class does
  not change.
