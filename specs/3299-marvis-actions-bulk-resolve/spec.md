# Feature Specification: Marvis Actions export and bulk resolve

**Feature Branch**: `feat/3299-marvis-actions-bulk-resolve`

**Created**: 2026-09-24

**Status**: Approved for implementation

**Issue**: #3299

**Input**: User description (voice transcript, cleaned): "Create a new numbered menu
option for Marvis Actions. It must mark Marvis Actions as resolved in bulk. For
example, an AP was offline, and we fixed it with a port bounce, with the Marvis
suggested action, or it was a false issue. We must send the resolution back to the
API to clear the action. We must do this in bulk, and by topic, so the option shows
a menu of the topics that we want to act on. The option must also make a pure
report dump of the Marvis Actions list to CSV and to the database. It must filter
by category or by subcategory. The operations portal must run the option. Create a
standalone report in the data folder. The report lists every API endpoint that the
feature uses, so the NOC team has an example. Support a comment for the resolution
code that means another method."

## Clarifications

### Session 2026-09-24

The user runs this work in autopilot mode, so the agent answered each question
from the repository evidence and recorded the reason.

- Q: Which statuses can a bulk resolve target? -> A: `open`, `inprogress`, and
  `reoccured` only. These statuses fill the Open tab of the Mist UI. A closed
  action never receives a request.
- Q: Can one filter answer select more than one category or subcategory? -> A: Yes
  on the command line, with a comma-separated list. The operations portal offers
  one choice for each control, because a choice control holds one value.
- Q: Which typed confirmation protects the resolve? -> A: `RESOLVE <count>`, where
  the count is the number of targets. A portal user submits every answer before
  the preview, so a fixed word cannot prove that the user saw the target set. The
  count can.
- Q: Which safety class does menu 270 take? -> A: `interactive_safe`. The portal
  runs only `safe` and `interactive_safe` rows, and the user requires the portal.
  The resolve writes a recoverable status, and it needs the typed count.
- Q: Does a resolve run also write a fresh copy of the report? -> A: No. It writes
  the result file. The engineer runs mode 1 again for a fresh report, so one run
  never replaces the report file without a request.
- Q: How does the portal handle the missing preview? -> A: The engineer runs mode 2
  first and reads the open count in the log. Then the engineer runs mode 3 with
  that count.

## Definitions

- **Marvis Action**: One Mist record that names one network problem that Marvis
  found, such as an AP that is offline. The Mist UI calls the list "Marvis Actions".
  The API calls one record a "suggestion". This document calls one record an
  *action*.
- **Category**: The Mist `category` field of an action, such as `ap` (Wireless) or
  `switch` (Wired). The user calls it the super category.
- **Subcategory**: The Mist `symptom` field of an action, such as `ap_disconnect`
  (AP Offline). The user calls it the subcategory.
- **Topic**: One category and subcategory pair, such as `switch/sw_offline` (Wired /
  Switch Offline). One subcategory key can occur in two categories. For example,
  `non_compliant` occurs under `ap` and under `gateway`. A topic therefore always
  holds both keys.
- **Open action**: An action whose status is `open`, `inprogress`, or `reoccured`.
  These three statuses fill the Open tab of the Mist UI. The API spells `reoccured`
  with one `r`.
- **Resolution code**: The Mist `label` field that a resolve request sends. The four
  codes are `suggested`, `nonsuggested`, `known`, and `invalid`.
- **Operations portal**: The Flask operations web application on port 8055.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export the Marvis Actions list as a report (Priority: P1)

A NOC engineer must share the current Marvis Actions of an organization with a
shift lead. The engineer opens MistHelper, selects menu 270, and presses Enter at
each prompt. The operation reads every action from the Mist API, shows a count for
each topic, and writes `OrgMarvisActions.csv` under `data/`. It writes the same
rows to the configured database backend. The engineer opens the CSV file in a
spreadsheet. Each row names the site, the device, the category, the subcategory,
the status, the resolution code, the comment, and the times.

**Why this priority**: The report is the lowest-risk value, and every other story
reads the same list. It changes nothing in the Mist cloud.

**Independent Test**: Run `python MistHelper.py --menu 270` and press Enter at each
prompt. Confirm that the console shows the topic table. Confirm that the CSV file
holds one data row for each action that the API returned.

**Acceptance Scenarios**:

1. **Given** an organization with 112 actions, **When** the engineer runs mode 1
   with no filter, **Then** `OrgMarvisActions.csv` holds 112 data rows and one
   header row.
2. **Given** the polyglot database backend, **When** the engineer runs mode 1 two
   times, **Then** the database holds each action one time. The upsert key is the
   Mist `uuid` field.
3. **Given** an organization with no actions, **When** the engineer runs mode 1,
   **Then** the operation states that no action exists and writes no file.
4. **Given** an API error on the list request, **When** the engineer runs mode 1,
   **Then** the operation states the HTTP status. It writes no file and changes
   nothing.
5. **Given** mode 2, **When** the engineer runs it, **Then** the file holds only the
   open actions.

---

### User Story 2 - Filter the report by category or by subcategory (Priority: P2)

A Wired team lead wants only the switch problems. The engineer runs menu 270 and
reads a numbered category table with an action count and an open count for each
category. The engineer enters the number for Wired. The operation then shows a
numbered subcategory table for Wired only. The engineer presses Enter to keep every
Wired subcategory, or enters the number for Switch Offline only. The file then
holds only the actions of the chosen topics.

**Why this priority**: Filters make the report usable for one team, and the resolve
story depends on the same filter to choose its targets.

**Independent Test**: Run mode 1, enter one category number, and enter one
subcategory number. Confirm that every data row in the CSV file holds that category
and that subcategory.

**Acceptance Scenarios**:

1. **Given** the category prompt, **When** the engineer enters `switch`, the number
   of the Wired row, or `all`, **Then** the operation accepts each form.
2. **Given** the subcategory prompt, **When** the engineer enters `sw_offline` or
   `switch/sw_offline`, **Then** the operation selects the Wired / Switch Offline
   topic.
3. **Given** a list of tokens such as `ap,switch`, **When** the engineer enters it,
   **Then** the operation selects both categories.
4. **Given** an answer that matches no category, such as `swich`, **When** the
   engineer enters it, **Then** the operation names the answer. It writes no file,
   changes nothing, and returns to the menu.
5. **Given** a known category that holds no action now, **When** the engineer
   selects it, **Then** the operation states that no action matches the filter. It
   writes no file.

---

### User Story 3 - Mark the open actions of chosen topics as resolved (Priority: P3)

An engineer bounced 12 switch ports to clear 12 Port Stuck actions. The actions stay
open in Mist until someone resolves them. The engineer runs menu 270 in mode 3,
selects Wired and Port Stuck, and reads a preview of the 12 open actions. The
engineer selects the resolution code "Solved using the Mist suggested action",
leaves the comment empty, and types `RESOLVE 12`. The operation sends one resolve
request for each action. It records the result of each request in
`OrgMarvisActionsResolveResults.csv`, reads the list again, and states how many
actions now show a closed status.

**Why this priority**: This is the only story that changes Mist data. It depends on
the list from User Story 1 and the filter from User Story 2.

**Independent Test**: With a mocked session, run mode 3 on 3 open actions and type
`RESOLVE 3`. Confirm 3 resolve requests with the exact request body, and a result
file with 3 rows.

**Acceptance Scenarios**:

1. **Given** 12 open actions in the chosen topics, **When** the engineer types
   `RESOLVE 12`, **Then** the operation sends 12 resolve requests and writes 12
   result rows.
2. **Given** the same preview, **When** the engineer types `RESOLVE 11`, `resolve
   12`, `YES`, or nothing, **Then** the operation sends no request and states that
   no action changed.
3. **Given** the code "Solved using another method", **When** the engineer leaves
   the comment empty, **Then** the operation sends no request and states that this
   code needs a comment.
4. **Given** the code "Solved using another method" and the comment "Replaced the
   PoE injector", **When** the engineer confirms, **Then** each request carries
   `label` `nonsuggested` and that comment.
5. **Given** a request that fails with HTTP 403, **When** the run finishes, **Then**
   the result file marks that row as an error. That row holds the HTTP status. The
   other rows show their own result. The summary names the error count.
6. **Given** a Stop request from the operations portal during the run, **When** the
   operation reaches the next action, **Then** it sends no other request. It
   writes the partial result file.
7. **Given** a closed action in the chosen topics, **When** the engineer runs
   mode 3, **Then** the operation never sends a request for it. An AI Validated
   action is one type of closed action.
8. **Given** no open action in the organization, **When** the engineer runs mode 3,
   **Then** the operation states that no open action exists. It asks no other
   question.

---

### User Story 4 - Run all three modes from the operations portal (Priority: P4)

An engineer without a shell session opens the operations portal on port 8055. The
engineer finds "Marvis Actions" in the operation list. The engineer selects the
mode, the category, the subcategory, the resolution code, the comment, and the
confirmation. Then the engineer clicks Run. The log panel streams the topic table
and the result. The Results panel previews the CSV file.

**Why this priority**: The portal widens the audience. The command line already
works, so this story adds reach, not capability.

**Independent Test**: With Playwright, select menu 270 in the portal, run mode 1,
and confirm the Completed status and the `OrgMarvisActions.csv` preview.

**Acceptance Scenarios**:

1. **Given** the operations portal, **When** the engineer opens the operation list,
   **Then** menu 270 appears under the "Marvis Actions" heading.
2. **Given** mode 1 and the default answers, **When** the engineer clicks Run,
   **Then** the run completes and the Results panel lists `OrgMarvisActions.csv`.
3. **Given** mode 3, one or more targets, and an empty confirmation, **When** the
   engineer clicks Run, **Then** the run reports a missing required input. It
   changes nothing.
4. **Given** mode 3 and a confirmation count that does not match the target count,
   **When** the engineer clicks Run, **Then** the run fails. It states the expected
   answer and changes nothing.

---

### User Story 5 - Give the NOC team an API endpoint report (Priority: P5)

A NOC engineer wants to build a similar tool. The engineer opens
`data/Marvis_Actions_API_Endpoints_Report.md` and reads each endpoint that menu 270
calls. For each endpoint, the report gives the method, the path, the query
parameters, the request body, the response shape, the permission, and one example.
A tracked copy is at `documentation/marvis-actions-api-endpoints.md`.

**Why this priority**: The report is documentation. It carries no runtime risk.

**Independent Test**: Open the report and confirm that it names every endpoint that
the code calls, and that each example uses a placeholder identifier.

**Acceptance Scenarios**:

1. **Given** the report, **When** the engineer reads it, **Then** it lists the
   schema read, the list read, the site list read, and the resolve write.
2. **Given** the report, **When** the engineer reads the resolve section, **Then**
   it states the four resolution codes and the comment rule. It also states how
   to undo a resolve.

---

### Edge Cases

- **No `uuid` on a row.** The operation derives the same kind of key that Mist uses
  for most rows: a version 3 UUID of the `row_key` in the X.500 namespace. The row
  therefore never receives a random key, and a second run does not duplicate it.
- **A page that repeats rows.** The operation removes a duplicate `uuid`, so a list
  that shifts during paging does not duplicate a row.
- **A list that never ends.** A page guard stops the paging after 100 pages, and the
  operation states that the list is incomplete.
- **A page read that fails after an earlier page succeeded.** The operation discards
  the partial list, states the HTTP status, writes no file, and changes nothing. A
  partial list could hide an action from the report or from the resolve targets.
- **An unexpected response shape.** If the list response holds no `results` list, the
  operation stops, names the shape problem, and changes nothing. The labs endpoints
  are not documented, so Mist can change them.
- **An unknown category or subcategory in live data.** The operation shows it in the
  table with its key as the name, and the filter accepts it.
- **A schema read that fails.** The operation uses its built-in topic names and
  continues. The recommended action column stays empty.
- **A site list read that fails.** The site name column stays empty, and the report
  continues.
- **More open targets than the cap.** The operation resolves the oldest actions up to
  `MARVIS_RESOLVE_MAX_ACTIONS` (default 500) and states the cap. The confirmation
  count equals the capped count.
- **A comment longer than 1,000 characters.** The operation refuses it and sends no
  request.
- **An action with no `row_key`.** The operation skips it, records the reason, and
  sends no request for it.
- **An HTTP 429 answer.** The `mistapi` session retries it. The adaptive pacer also
  waits between requests.
- **A resolve that Mist accepts, but the list still shows an open status.** The
  result row reads `sent_unverified`, and the summary tells the engineer to check the
  action in the Mist portal.
- **A portal user who submits every answer before the preview.** The count in
  `RESOLVE <count>` forces a report run first, and it refuses the run when the count
  changed.

## Requirements *(mandatory)*

### Functional Requirements

**Menu and safety class**

- **FR-001**: The system MUST add menu operation 270, the next free number, and MUST
  NOT renumber an existing operation.
- **FR-002**: The system MUST register 270 as `interactive_safe`, so the operations
  portal can run it. The registry row MUST state why the resolve mode still counts
  as safe. The resolve writes an action status only. An engineer can recover that
  status in the Mist UI. The resolve also needs a typed confirmation that no
  automated pass can produce.
- **FR-003**: The first prompt MUST ask for the mode: 1 exports every action, 2
  exports the open actions, and 3 resolves the open actions. The default MUST be 1.

**Reading the list**

- **FR-004**: The system MUST read every action of the organization through
  `GET /api/v1/labs/orgs/{org_id}/suggestion` with `query=get_suggestion`,
  `resolve_wcid=true`, `limit=1000`, and a page number, until the last page.
- **FR-005**: The system MUST stop the paging after 100 pages and MUST state that the
  list is incomplete when it stops for that reason.
- **FR-006**: The system MUST read the topic names from
  `GET /api/v1/labs/suggestions_schema`, and it MUST fall back to a built-in catalog
  when that read returns no data.
- **FR-007**: The system MUST read the site names of the organization through the
  `mistapi` method `listOrgSites`.

**Filters**

- **FR-008**: The system MUST show a numbered category table with the category key,
  the category name, the action count, and the open count.
- **FR-009**: The system MUST show a numbered subcategory table that holds only the
  topics inside the selected categories.
- **FR-010**: Each filter prompt MUST accept `all`, a table number, a category key, a
  subcategory key, or a `category/subcategory` pair. It MUST also accept a
  comma-separated list of these forms. A blank answer MUST mean `all`, because the
  prompt default supplies that value. If the operator presses Ctrl+C at a filter
  prompt, the prompt returns an empty answer. The filter then MUST select no action,
  so the run stops.
- **FR-011**: The system MUST refuse the whole run when one token matches nothing,
  and it MUST name the token.
- **FR-012**: In modes 2 and 3, the tables MUST list only the topics that hold an open
  action.

**Report export**

- **FR-013**: Modes 1 and 2 MUST write `OrgMarvisActions.csv` through
  `DataExporter.write_with_format_selection` with the endpoint name
  `listOrgMarvisActions`.
- **FR-014**: The primary key strategy for `listOrgMarvisActions` MUST be
  `natural_pk` on `uuid`, and it MUST exist before the code writes a row.
- **FR-015**: The CSV file MUST hold one fixed column set, so every run writes the
  same header. Nested fields MUST appear as JSON text.
- **FR-016**: The database backend MUST receive the full nested action plus the
  readable fields, so a query can read any Mist field.
- **FR-017**: The system MUST write no file when no action matches, and it MUST say
  so.

**Bulk resolve**

- **FR-018**: Mode 3 MUST target only open actions inside the selected topics.
- **FR-019**: Mode 3 MUST show a preview of every target before any prompt for the
  resolution code.
- **FR-020**: Mode 3 MUST offer the four resolution codes, and the default MUST be
  `suggested`. The word `other` MUST mean `nonsuggested`.
- **FR-021**: The code `nonsuggested` MUST require a comment that is not empty.
  Every code MUST accept a comment. A comment MUST NOT exceed 1,000 characters.
- **FR-022**: Mode 3 MUST require the typed answer `RESOLVE <count>`, where the count
  is the number of targets. The comparison MUST be exact after the system trims the
  answer and joins repeated spaces. Any other answer MUST send no request.
- **FR-023**: The system MUST send one
  `PUT /api/v1/labs/orgs/{org_id}/suggestions` request for each target, one at a
  time, with the body `row_key`, `status` `resolved`, `label`, `comment`, and
  `resolve_time`. The body MUST match the body that the Mist UI sends.
- **FR-024**: The system MUST pace the requests with `AdaptivePacer`.
- **FR-025**: The system MUST check the stop signal before each request.
- **FR-026**: The system MUST resolve at most `MARVIS_RESOLVE_MAX_ACTIONS` actions in
  one run, oldest first. The default MUST be 500.
- **FR-027**: The system MUST record one result row for each target, with the HTTP
  status, the outcome, and the error text.
- **FR-028**: After the requests, the system MUST read the list again and record the
  status that Mist reports for each target.
- **FR-029**: The system MUST write the result rows to
  `OrgMarvisActionsResolveResults.csv` with the endpoint name
  `resolveOrgMarvisActions`, `natural_pk` on `result_id`.
- **FR-030**: When any request fails, the summary MUST name the failure count at the
  ERROR level.

**Operations portal**

- **FR-031**: The operations portal MUST list menu 270 under the "Marvis Actions"
  heading.
- **FR-032**: The portal row MUST hold six controls in prompt order: mode, category,
  subcategory, resolution code, comment, and confirmation.
- **FR-033**: A portal run with a missing required answer MUST fail with a clear
  reason, and a refused run MUST change nothing.

**Documentation**

- **FR-034**: The system MUST ship `data/Marvis_Actions_API_Endpoints_Report.md` and
  the tracked copy `documentation/marvis-actions-api-endpoints.md`.
- **FR-035**: The README, the menu reference, the category table in
  `.github/copilot-instructions.md`, and `deploy/.env.example` MUST name the new
  operation and the new setting.

**Safety and secrets**

- **FR-036**: The system MUST NOT write an API token or a password into a log line, a
  console line, or an export file.
- **FR-037**: The system MUST NOT call the Marvis self-drive endpoint, the RMA ticket
  endpoint, or any endpoint that changes device configuration.

### Key Entities

- **Marvis Action**: One Mist action record. Its natural key is `uuid`. The resolve
  request addresses it by `row_key`. It carries the category, the subcategory, the
  status, the severity, the impacted entities, the times in epoch milliseconds, the
  resolution code, and the comment.
- **Topic**: One category and subcategory pair, with a readable name for each key, an
  action count, and an open count.
- **Resolution code**: One of four Mist `label` values, with the text that the Mist UI
  shows for it.
- **Resolve result**: One row for each target of a resolve run. It holds the
  `result_id`, the action `uuid`, the topic, the site, and the entity. It also holds
  the previous status, the code, the comment, and the resolve time. Last, it holds
  the HTTP status, the outcome, the error text, and the status that Mist reported
  after the run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer exports every Marvis Action of an organization with one
  menu choice and three Enter key presses.
- **SC-002**: A mode 1 run on 112 actions costs 3 API requests: one schema read, one
  list page, and one site list page.
- **SC-003**: A second export of the same actions adds no duplicate row to the
  database.
- **SC-004**: An engineer resolves every open action of one topic in one run,
  instead of one click for each action in the Mist UI.
- **SC-005**: No request leaves MistHelper unless the typed answer equals
  `RESOLVE <count>` for the current target count.
- **SC-006**: Every mode runs from the operations portal, and a refused portal run
  changes nothing.
- **SC-007**: Automated tests cover the paging, the page guard, the token parser, and
  the open filter. They also cover the confirmation refusal, the comment rule, the
  cap, and the stop signal. Last, they cover the request body, the failure path, and
  the portal row. Coverage on the new package is 80 percent or more.
- **SC-008**: Every repository quality gate passes.

## Assumptions

- The next free menu number is 270, because 269 is the highest number in use.
- The org list endpoint and the resolve endpoint are `labs` endpoints. The Mist API
  documentation does not list them, and `mistapi` 0.64 holds no method for them.
  The evidence is the Mist UI bundle `admin2.21.1765-hotfix`, read on 2026-09-23,
  and live read-only requests on the same day. The operation therefore calls them
  through the `mistapi` session methods `mist_get` and `mist_put`. This obeys the
  constitution rule, because no `mistapi` method exists for these paths.
- The only documented Marvis Actions endpoint is the MSP count
  `GET /api/v1/msps/{msp_id}/suggestion/count`. It returns counts only, so the
  feature does not use it. The endpoint report names it.
- The resolve is recoverable. The Mist UI offers a status dropdown with Open, In
  Progress, and Resolved for a user-resolved action, and a bulk Status button for
  checked rows. The feature therefore uses the signal word Caution, not Warning.
- The token needs an organization role that can write Marvis Actions. The Mist UI
  grants this to the admin, write, and helpdesk roles.
- On 2026-09-23 the lab organization held 112 actions and 0 open actions. A live
  resolve therefore reaches the no-target message only. Mocked tests prove the write
  path. The feature must not resolve a closed action to create a test.
- The Mist UI resolves one action with each request, in sequence. The feature does
  the same, and it does not guess at a batch request body.
- The organization comes from the shared helper, which reads the application
  context, the cache, the environment, the `.env` file, or a prompt, in that order.
