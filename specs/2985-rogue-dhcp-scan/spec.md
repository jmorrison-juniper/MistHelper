# Feature Specification: Org-wide rogue DHCP server scan

**Feature Branch**: `feat/2985-rogue-dhcp-scan`

**Created**: 2026-09-18

**Status**: Draft

**Issue**: #2985

**Input**: User description: "A new numbered menu option where the user can scan an
entire org for any alarms, events, or Marvis alarms or insights that show a switch
with a DHCP rogue server alarming. Show any current, active, or historical result.
The search goes back 30 days across the org. If any site replies, research all of
those within the site and then at device level. Collect, collocate, and record all
this data. Present it as one result, write it to a CSV file, and save it to a
database. The option must also run from the Mist operations web dashboard, and the
data must be viewable there. This does not go in the capture update portal."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find every rogue DHCP server in the organization (Priority: P1)

A NOC engineer receives a report that clients at an unknown site receive a wrong
IP address. The engineer opens MistHelper, selects the rogue DHCP scan, and picks
the organization. The scan searches the whole organization for the last 30 days.
It returns one table. Each row names a site, a switch, a switch port, the signal
source, and the time. The engineer reads the table and learns which sites hold a
rogue DHCP server, and which sites held one earlier in the month.

**Why this priority**: This is the whole point of the feature. Without the org-wide
answer, the engineer still opens each site by hand. This story alone delivers
value, even with no file output and no web dashboard.

**Independent Test**: Run `python MistHelper.py --menu 269`, select an organization,
and confirm that the console prints the combined table and a count for each source.

**Acceptance Scenarios**:

1. **Given** an organization where one switch reported a rogue DHCP server nine days
   ago, **When** the engineer runs the scan, **Then** the result holds one row that
   names that site, that switch, and that port.
2. **Given** an organization with no rogue DHCP signal in 30 days, **When** the
   engineer runs the scan, **Then** the operation prints a clear "no rogue DHCP
   signal found" message and exits without an error.
3. **Given** a signal that the source still reports open, **When** the engineer runs
   the scan, **Then** the row state reads `active`.
4. **Given** a signal that closed inside the window, **When** the engineer runs the
   scan, **Then** the row state reads `historical`.
5. **Given** one site that returns an API error, **When** the engineer runs the scan,
   **Then** the scan records the failure, continues to the next site, and reports the
   failed site count at the end.

---

### User Story 2 - Keep the result for later work (Priority: P2)

The engineer must attach the finding to a change record and compare it against next
week. The scan writes a CSV file under `data/`, and it writes the same records to
the configured database backend. The engineer opens the CSV file in a spreadsheet
and sends it to the site owner.

**Why this priority**: The scan is useful without a file, but an engineer cannot
share a console table or track a trend. This story adds durability. It depends on
User Story 1 for the records.

**Independent Test**: Run the scan on an organization that holds at least one
signal, then confirm that a CSV file exists under `data/` and that the database
holds the same row count.

**Acceptance Scenarios**:

1. **Given** a scan that collected 12 records, **When** the scan finishes, **Then** a
   CSV file under `data/` holds 12 data rows and one header row.
2. **Given** the SQLite backend, **When** the scan runs twice on the same window,
   **Then** the table holds each record one time, because the primary key strategy
   upserts.
3. **Given** a scan that collected zero records, **When** the scan finishes, **Then**
   the scan writes no empty file and states that it wrote nothing.

---

### User Story 3 - Run and read the scan from the operations web dashboard (Priority: P3)

An engineer who does not hold a shell session opens the Mist operations web
dashboard. The engineer finds the rogue DHCP scan in the operation list, starts it,
and watches the log stream. When the scan finishes, the engineer opens the output
file in the browser preview and reads the same table.

**Why this priority**: This widens the audience. The scan already works from the
command line, so this story adds reach, not core capability. It depends on User
Story 1 and User Story 2.

**Independent Test**: Start the operations web dashboard, select the scan, run it,
and confirm that the log panel fills and the output file appears in the result
panel.

**Acceptance Scenarios**:

1. **Given** the operations web dashboard, **When** the engineer opens the operation
   list, **Then** the rogue DHCP scan appears with a clear description.
2. **Given** the engineer starts the scan, **When** the scan runs, **Then** the log
   panel streams progress lines.
3. **Given** the scan finished, **When** the engineer opens the output file, **Then**
   the preview shows the collected rows.
4. **Given** the upgrade capture portal on port 8056, **When** this feature ships,
   **Then** that portal is unchanged.

---

### Edge Cases

- **An organization with no sites.** The scan reports zero sites and exits cleanly.
- **A site identifier in a result that names no known site.** The scan keeps the
  record and marks the site name `unknown`.
- **A record that names no switch.** The scan keeps the record, because the alarm
  still proves a rogue DHCP server at the site. The device columns stay empty.
- **Two sources that report one event.** The scan merges them into one row and lists
  every source that reported it.
- **An API rate limit response.** The scan waits through the existing adaptive delay
  helper and retries. It does not abandon the scan.
- **A clock skew that puts a timestamp in the future.** The scan keeps the record and
  does not reject it.
- **An organization with more than 200 sites.** The scan queries only the sites that
  the organization-level result named.
- **A very large result.** The scan holds the records in memory and reports the count
  as it collects, so an operator sees progress.
- **A missing Mist API token.** The scan fails with one clear message that names the
  missing setting.

## Requirements *(mandatory)*

### Functional Requirements

**Scope and discovery**

- **FR-001**: The system MUST add one new numbered menu operation. The number MUST be
  the next free number, and it MUST NOT renumber an existing operation.
- **FR-002**: The system MUST register the new operation in `OperationRegistry` with
  the category `safe`, because the operation only reads.
- **FR-003**: The system MUST search a window that ends now and starts 30 days
  earlier. The window length MUST be a named constant with an override.
- **FR-004**: The system MUST search the whole organization, not one site.

**Signal sources**

- **FR-005**: The system MUST search organization alarms for the alarm type
  `sw_rogue_dhcp_server_detected`.
- **FR-006**: The system MUST search organization device events for the event type
  `SW_ROGUE_DHCP_SERVER_DETECTED`.
- **FR-007**: The system MUST search organization device events for the event type
  `SW_CONFIG_CHANGED_BY_MARVIS` and MUST keep a record only when its reason names a
  rogue DHCP server.
- **FR-008**: The system MUST search Marvis config actions for each named site and
  MUST keep a record whose reason equals `rogue_dhcp_server_detected`.
- **FR-009**: The system MUST also accept any record whose type text or detail text
  holds both the word `rogue` and the word `dhcp`, without regard to letter case.
  This rule catches a new Mist type string without a code change.
- **FR-010**: The system MUST reject a record that names a DHCP condition but not a
  rogue server, such as a pool exhaustion record or a DHCP failure record.

**Fan-out order**

- **FR-011**: The system MUST query the organization first.
- **FR-012**: The system MUST read the set of site identifiers from the
  organization-level results.
- **FR-013**: The system MUST query each named site for its own alarms, device
  events, and Marvis config actions.
- **FR-014**: The system MUST NOT query a site that no organization-level result
  named, because a blind fan-out over every site wastes the request budget.
- **FR-015**: The system MUST record the switch identity that each record names,
  including the name, the MAC address, the model, and the port.

**Result shape**

- **FR-016**: The system MUST merge every record into one result set and MUST remove
  a duplicate that two sources report.
- **FR-017**: The system MUST mark each record `active` or `historical`.
- **FR-018**: The system MUST produce the same column set for every source, so one
  table holds an alarm, an event, and a Marvis action together.
- **FR-019**: The system MUST record the first time seen, the last time seen, and the
  occurrence count for each record.
- **FR-020**: The system MUST name every source that reported a merged record.

**Output**

- **FR-021**: The system MUST print one combined table to the console, plus a count
  for each source.
- **FR-022**: The system MUST write the records through the shared export path, so
  the configured backend receives them. The file MUST land under `data/`.
- **FR-023**: The system MUST define a primary key strategy for the new dataset
  before the implementation writes any record.
- **FR-024**: The system MUST write no record when it collected none, and it MUST
  say so.

**Failure handling**

- **FR-025**: The system MUST continue the scan when one site query fails.
- **FR-026**: The system MUST report the count of failed sites at the end.
- **FR-027**: The system MUST log an action before each query and a result summary
  after it.
- **FR-028**: The system MUST report progress during the site fan-out.

**Web dashboard**

- **FR-029**: The system MUST expose the operation in the Mist operations web
  dashboard, so an engineer starts it from a browser.
- **FR-030**: The system MUST let an engineer read the collected records in the
  browser through the existing output file preview.
- **FR-031**: The system MUST leave the upgrade capture portal unchanged.
- **FR-032**: The system MUST run without a console prompt when the web dashboard
  starts it.

**Safety and secrets**

- **FR-033**: The system MUST call read-only endpoints only. It MUST NOT change any
  Mist cloud configuration.
- **FR-034**: The system MUST NOT write an API token or a password into a log file,
  a console line, or an export file.

### Key Entities

- **Rogue DHCP finding**: One rogue DHCP server signal about one switch port at one
  site. It carries the organization identifier, the site identifier, the site name,
  the switch name, the switch MAC address, the switch model, the port identifier, the
  VLAN, the source, the signal type string, the state, the severity, the first time
  seen, the last time seen, the count, the detail text, and the record identifier.
- **Scan window**: The start time and the end time that bound the search. The default
  length is 30 days.
- **Scan summary**: The counts that describe one run. It holds the sites queried, the
  sites that failed, the record count for each source, and the merged record count.
- **Signal source**: The named origin of a record. The values are the organization
  alarm, the site alarm, the organization device event, the site device event, and
  the Marvis config action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer answers "does any switch in this organization report a
  rogue DHCP server" in one operation, instead of opening each site by hand.
- **SC-002**: The scan covers a 30-day window across the whole organization in one
  run.
- **SC-003**: The scan queries a site only when an organization-level result named
  that site, so an organization with 200 sites and 3 affected sites issues site
  queries for 3 sites, not 200.
- **SC-004**: One failed site never ends the run. A run with one failed site still
  reports every record from every other site.
- **SC-005**: The result table holds one row for each distinct finding. Two sources
  that report one event produce one row, not two.
- **SC-006**: A second run over the same window adds no duplicate row to the
  database.
- **SC-007**: An engineer starts the scan from the operations web dashboard and reads
  the result there, without a shell session.
- **SC-008**: Automated tests cover the matcher, the normalizer, the merge, the
  window, the fan-out order, and the failure path. Coverage on the new module is 80
  percent or more.
- **SC-009**: Every repository quality gate passes.

## Assumptions

- The next free menu number is 269, because 268 is the highest number in use. If
  another change takes 269 first, the implementation takes the next free number.
- The Mist operations web dashboard is the Flask application in `web_portal/` on port
  8055. The upgrade capture portal on port 8056 is a separate tree and stays out of
  scope, as the request states.
- The literal type strings come from the Mist catalogs in `data/ConstAlarmDefs.csv`
  and `data/ConstDeviceEvents.csv`, and from the OpenAPI specification in
  `documentation/mist-api-openapi31yaml.yaml`. The keyword rule in FR-009 covers a
  string that Mist adds later.
- The Mist API serves a 30-day lookback for alarm and event searches. If the API
  refuses a window that long for an endpoint, the scan shortens the window for that
  endpoint and reports the shorter window it used.
- The alarm record and the event record already name the switch and the port, so the
  scan reads the device identity from the record. It issues a device query only to
  resolve a name that the record omits.
- The organization selection uses the existing helper, which reads the cached
  organization, then the environment, then prompts.
- The Marvis config action endpoint is site-scoped in the installed SDK. No
  organization-level equivalent exists, so the scan calls it for each named site.
- The existing adaptive delay helper and the existing pagination helper cover rate
  limiting and paging. This feature adds neither.
- An engineer holds a Mist API token that can read alarms, events, and Marvis config
  actions. The feature adds no new credential.
