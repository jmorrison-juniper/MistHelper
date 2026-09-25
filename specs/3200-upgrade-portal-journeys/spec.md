# Feature Specification: Upgrade portal journey harness and multi-site parity

**Feature Branch**: `test/3200-upgrade-portal-journeys`

**Created**: 2026-09-23

**Status**: Draft

**Issue**: #3200

**Input**: User description: "Create an end-to-end testing harness for the
upgrade capture portal. Create a user journey for every scenario that an
operator uses the portal for. Focus on the multi-site mode. Prove 100 percent
feature parity between the single-site mode and the multi-site mode. Each mode
must support every operation for a single device family (AP only, switch only,
gateway only) and for mixed families, and each journey must go all the way to
the end of the upgrade process. Use a real browser (Playwright). Take a
screenshot at every step and review it. Use the server log and the script log
for troubleshooting. Do performance testing too."

## Background

The upgrade capture portal listens on port 8056. Its code is in
`src/upgrade_portal/`. The portal has two modes. The single-site mode upgrades
one site in one run. The multi-site mode upgrades many sites of one
organization in one multi-site operation.

No browser test drives a mode to the end of an upgrade today. The browser suite
in `tests/e2e/upgrade_portal/` uses fixed stand-ins. The stand-ins hold two
sites and three devices, and each upgrade status stays at `running`. The
stand-in launcher of the single-site mode drives no device.

The multi-site browser test answers the status API call inside the browser. The
shipped status API route therefore does not answer that call. The current
fixtures also replace the shipped organization service and the shipped device
service with fixed answers.

The rehearsal harness of issue #1992 drives the shipped run driver with a
driven clock against a stand-in cloud. It proves the settle rules and the stop
rules below the browser. It opens no page.

The multi-site mode offers fewer pages and fewer controls than the single-site
mode. This feature measures that difference in a parity matrix. Each gap gets
its own GitHub issue.

## User Scenarios & Testing *(mandatory)*

This document uses one term for each concept.

- The **operator** is the person that a journey plays. The **engineer** is the
  person who runs the harness and reads its artifacts.

- A **journey** is one scripted operator path through the portal, from its
  start page to its end condition. A **happy-path journey** is a journey with
  no fault.

- A **step** is one operator action in a journey and the checks that follow
  it.

- A **harness run** is one execution of a selected set of journeys.

- The **journey server** is the portal process that the harness starts. It
  runs the shipped routes and the shipped services. The **server log** is the
  log file of the journey server.

- The **runner** is the test process that drives the browser. The **runner
  log** is the log file of the runner.

- The **cloud boundary** is the point where shipped code calls the `mistapi`
  package. That package is the Mist SDK.

- The **simulated cloud** answers each call at the cloud boundary. No call
  leaves the process of the journey server.

- A **fleet** is the set of organizations, sites, devices, versions, and
  clients that the simulated cloud holds. The harness has two fleets, the
  default fleet and the large fleet.

- The **journey clock** is the one time source of the run driver and the
  simulated cloud. It moves faster than the wall clock.

- The **journey control** is the test-only channel that sets faults, moves the
  journey clock, and ends sessions and site locks.

- A **run** is one single-site upgrade run.

- A **multi-site operation** is the aggregate operation of spec 2200. Each
  **child** of the operation is one child job.

- A **write** is one call that asks the cloud to upgrade firmware.

- A **device family** is AP, switch, or gateway. A **family combination** is
  one of the seven sets of one or more device families.

- A **gateway class** is Junos or SSR. The shipped gateway classifier decides
  the class of each gateway.

- The **end of the upgrade** is the last condition of a happy-path journey.
  FR-051 and FR-052 define it for each mode.

- A **capability** is one thing that an operator can do in a mode.

- The **parity matrix** is the table that shows each capability, its status in
  each mode, and the journeys that prove the status.

- A **gap** is a capability that the two modes do not have in the same form.

- The **artifacts** are the screenshots, logs, timings, and records that a
  journey leaves.

- The **report** is the one JSON file of a harness run. The **index page** is
  the one HTML page of a harness run.

- A **budget** is the time limit for one class of page or API call.

---

### User Story 1 - Drive a multi-site upgrade to the end for each family combination (Priority: P1)

An engineer starts a harness run with the default fleet. For each of the seven
family combinations, one journey opens a browser and signs in. The journey
selects the organization, the multi-site mode, and the sites. It sets the
version of each family and the upgrade options, types `CONFIRM`, and starts
the operation. The journey clock then moves each simulated device through the
upgrade, and the progress page shows each child until the operation completes.

**Why this priority**: The multi-site mode has the least proof today. No
browser test gets a multi-site operation to its completed status. A defect in
this mode reaches many sites at the same time.

**Independent Test**: Run the seven multi-site happy-path journeys alone. Each
journey gets to the end of the upgrade in less than 3 minutes. The simulated
cloud records one write for each child.

**Acceptance Scenarios**:

1. **Given** the AP family alone, **When** the journey confirms the operation,
   **Then** the plan holds one organization AP child for the selected sites.
   The simulated cloud receives one organization write. The write names only
   those sites and only access points.

2. **Given** the switch family alone, **When** the journey confirms, **Then**
   the plan holds one site child for each selected site with a switch.

3. **Given** the gateway family and the two gateway classes, **When** the
   journey confirms, **Then** the plan holds site children for the Junos
   gateways. The plan holds the organization SSR route for the SSR gateways.
   The pages use the word gateway and do not ask for a class.

4. **Given** a selected site that holds a Mist Edge device, **When** the
   journey reads the plan, **Then** no child holds the Mist Edge device. The
   simulated cloud receives no write for it.

5. **Given** each of the seven family combinations, **When** the journey clock
   moves each device through the upgrade, **Then** each child shows its
   completed status. The operation status reads `completed`.

6. **Given** an active operation, **When** the journey refreshes the page or
   waits for the poll, **Then** the page shows the status of each child. That
   status agrees with the simulated cloud, and no refresh sends a write.

7. **Given** the upgrade options of the journey, **When** the simulated cloud
   receives each write, **Then** each write body holds the selected value of
   each option. The options are the strategy, the canary phases, the reboot
   choice, and the reboot-at interval. They also include the Junos file
   action, the force choice, the maximum failure percentage, and the start
   time.

8. **Given** a journey that starts at the sign-in page, **When** it completes
   the form, **Then** its browser session gets to the end of the upgrade. The
   harness gives that browser no session cookie before the sign-in.

---

### User Story 2 - Drive a single-site upgrade to the end for each family combination (Priority: P1)

An engineer runs the single-site happy-path journeys. Each journey signs in
and selects the organization, the single-site mode, and one site. It runs the
pre-check capture, selects a version for each device, and sets the upgrade
options. It reads the warning list, types `CONFIRM`, and starts the run. The
journey clock drives the cascade through the gateway, switch, access point,
and client phases, and the shipped settle gate decides each phase. The portal
then runs the post-check capture, and the journey opens the comparison.

**Why this priority**: The single-site mode is the reference for the parity
matrix. No browser test gets a single-site run to `complete` today, because
the stand-in launcher drives no device. The parity matrix needs a proven
reference.

**Independent Test**: Run the seven single-site happy-path journeys alone.
Each run gets to `complete`. The comparison shows the version before and the
version after for each upgraded device.

**Acceptance Scenarios**:

1. **Given** one site and one family combination, **When** the journey runs
   the pre-check capture, **Then** the capture page shows the verified badge.
   The device table and the client tables agree with the fleet.

2. **Given** the options page, **When** the journey selects a version for each
   device and sets each applicable option, **Then** the confirmation page
   shows each selection. The page also shows the warning list and the call
   count.

3. **Given** the typed word `CONFIRM`, **When** the journey starts the run,
   **Then** the phases settle in the sequence gateways, switches, access
   points, clients. A phase with no device of its family shows `skipped`.

4. **Given** a device that reconnects with the new version, **When** the
   journey reads the progress page, **Then** the device shows as waiting.
   After the shipped settle wait ends on the journey clock, the device shows
   as settled.

5. **Given** a settled client phase, **When** the run continues, **Then** the
   portal starts the post-check capture with no operator action. The run
   status becomes `complete`.

6. **Given** a complete run, **When** the journey opens the comparison,
   **Then** the device table marks each upgraded device as changed. Each
   changed row names the version before and the version after. The client
   table shows the scripted client changes.

7. **Given** the site with the two gateway classes, **When** the journey
   confirms a gateway run, **Then** the page shows the warning for mixed
   gateway classes. The simulated cloud receives the SSR write at the
   organization scope.

8. **Given** the site with a Mist Edge device, **When** the journey opens the
   inventory page, **Then** the page marks that device as unsupported. The run
   holds no target for it.

9. **Given** the upgrade options of the journey, **When** the simulated cloud
   receives each write, **Then** each write body holds the selected value of
   each option.

---

### User Story 3 - Publish the parity matrix and one GitHub issue for each gap (Priority: P1)

An engineer reads the parity matrix after a harness run. The matrix shows each
capability of the two modes. For each capability, the matrix shows the status
in each mode and the result for each family combination that applies. It also
shows the journeys that prove the result. Each gap names one GitHub issue.

**Why this priority**: The user asks for proof of full parity between the two
modes. Without the matrix, a gap stays hidden until an operator meets it on a
production site.

**Independent Test**: Run the harness and open the matrix. Compare the rows
with the capability inventory of this spec and with the controls of the
shipped templates. Each row shows a status for each mode, one or more
journeys, and one issue for each gap.

**Acceptance Scenarios**:

1. **Given** a finished harness run, **When** the engineer opens the matrix,
   **Then** each capability of the inventory shows its status in each mode.
   Each row also shows the identifiers of the journeys that prove the status.

2. **Given** a capability that the two modes do not have in the same form,
   **When** the harness writes the matrix, **Then** the row shows `gap`. The
   row names one GitHub issue.

3. **Given** a gap with an open issue, **When** its gap journey runs, **Then**
   the journey reports the gap and the issue number. The journey does not
   report a pass.

4. **Given** a gap that a change closes, **When** its gap journey passes,
   **Then** the harness reports the row as out of date. The harness run fails
   until the matrix shows `parity` for that row.

5. **Given** each `data-testid` control in the shipped templates of a mode,
   **When** the harness examines the inventory, **Then** each control maps to
   one capability. The harness reports each control that maps to no
   capability.

6. **Given** the matrix, **When** the engineer reads its summary, **Then** the
   summary shows the parity percentage of the two modes.

---

### User Story 4 - Prove the safety rules under faults (Priority: P2)

An engineer runs the safety journeys in each mode. The simulated cloud gives
one write an uncertain answer, rejects one write, or loses a site lock between
two child writes. A journey starts two times, starts from a second tab, uses
the back control, and sends a recorded request again. A second operator tries
to use a locked site and to control the work of the first operator. A session
expires before the start, and a browser write goes without its CSRF token.

**Why this priority**: These journeys prove the safety rules of spec 2200 and
spec 1823 in a browser. They depend on the happy-path journeys of user story 1
and user story 2.

**Independent Test**: Run the safety journeys alone. The simulated cloud
records one write, and no more, for each planned write and each claimed child.
Each refused action shows a plain message and sends no write.

**Acceptance Scenarios**:

1. **Given** a child write with no answer, **When** the operation continues,
   **Then** the child shows an unknown status. The operation shows
   `attention_required`. The simulated cloud records one write for that child,
   also after each refresh that follows.

2. **Given** a single-site write with no answer, **When** the run continues,
   **Then** the run shows the unknown result and offers the reconciliation.
   The simulated cloud records one write for it.

3. **Given** a rejected write for one child, **When** the operation continues,
   **Then** the other children keep their own status. The operation shows
   `partial`.

4. **Given** a site lock that expires between two child writes, **When** the
   submission continues, **Then** the portal sends no write for the remaining
   children. Those children show `not_submitted`.

5. **Given** the confirmation page, **When** the journey selects the start
   control two times fast, **Then** the portal starts only one operation or
   run.

6. **Given** a started operation or run, **When** the journey starts it again
   from a second tab, **Then** the portal refuses the repeat. The portal also
   refuses a start after the back control. Each refusal shows a plain message.

7. **Given** a recorded start request, **When** the journey sends it again with
   the same confirmation value, **Then** the portal refuses it with status 409.
   The portal sends no write.

8. **Given** a site that operator A locks, **When** operator B tries to start
   work there, **Then** the portal refuses and names the holder. The refusal
   occurs in each mode. A single-site run of operator A also blocks a
   multi-site operation of operator B that includes the site.

9. **Given** work that operator A owns, **When** operator B tries to stop,
   cancel, retry, or reschedule it, **Then** the portal refuses. The portal
   sends no cloud call for it.

10. **Given** a session that expires on the confirmation page, **When** the
    journey starts the upgrade, **Then** the portal asks for a new sign-in.
    The portal sends no write. The journey must confirm again after the new
    sign-in.

11. **Given** a browser write without a correct CSRF token, **When** the
    journey sends it, **Then** the portal refuses it. The portal sends no cloud
    call.

12. **Given** an operator address on a reserved domain, **When** the journey
    starts the upgrade, **Then** the portal refuses the write and names the
    cure. The refusal occurs in each mode.

13. **Given** a seeded defect, **When** the safety journeys run against the
    seeded code, **Then** one or more journeys fail for each defect. There are
    three seeded defects. The first sends a second write for one child. The
    second sends a gateway write through the organization AP route. The third
    drops one upgrade option before the write.

---

### User Story 5 - Prove the device faults and the recovery controls (Priority: P2)

An engineer runs the device fault journeys in each mode. One device fails with
a reported cause. One device does not reconnect. One device reconnects with a
different version. The journeys then use the recovery controls: cancel, stop,
retry, reschedule, and reconciliation. If a mode has no control for a fault,
the journey records a gap.

**Why this priority**: The fault pages tell an operator what to do at the worst
moment. The rehearsal of issue #1992 proves the rules below the browser. No
journey proves the pages.

**Independent Test**: Run the fault journeys alone. Each journey gets to its end
condition. Each page shows the outcome that the shipped rules give. The report
names each gap row.

**Acceptance Scenarios**:

1. **Given** a device that fails with a reported cause, **When** the journey
   reads the progress page, **Then** the single-site page shows the failure
   alert. The alert names the device and the cause. The multi-site page shows
   the error of the child.

2. **Given** a device that does not reconnect, **When** the journey clock gets
   to the settle deadline, **Then** the run marks it as not returned. The run
   gets to a terminal status in the time budget of the journey. The matrix
   records what the multi-site page shows.

3. **Given** a device that reconnects with a different version, **When** the
   journey reads the progress page, **Then** the single-site page shows the
   version mismatch. The matrix records what the multi-site page shows.

4. **Given** an active multi-site operation, **When** the journey types
   `CANCEL` and cancels it, **Then** the portal sends one cancel call for each
   submitted child. A child with no cancel route gets no call. The page shows
   the result of each child.

5. **Given** a cancellation result, **When** the journey reads it, **Then** the
   page does not claim that a device went back to its earlier firmware.

6. **Given** a single-site run with a future start time, **When** the journey
   cancels the run, **Then** the run shows `cancelled`. The simulated cloud
   receives no write.

7. **Given** a single-site run in mid-cascade, **When** the journey types
   `STOP` and stops the run, **Then** the stop page shows three outcome lists.
   The lists name the cancelled devices, the devices that write firmware now,
   and the devices with no cancel route. The message says that each device
   that writes firmware completes its write.

8. **Given** a failed single-site run, **When** the journey uses retry,
   **Then** the new run keeps the saved options and versions. The new run holds
   only the devices that failed or did not complete.

9. **Given** a single-site run that did not start, **When** the journey
   reschedules it, **Then** the page shows the new start time. The simulated
   cloud receives no write before that time on the journey clock.

10. **Given** a stopped run with an uncertain device status, **When** the
    journey sends the reconciliation, **Then** the page shows the result from
    the simulated cloud. The journey types the confirmation of the
    reconciliation first.

11. **Given** a recovery control that only the single-site mode has, **When**
    its gap journey runs, **Then** the journey records the gap and the issue.

---

### User Story 6 - Examine and troubleshoot a harness run from its artifacts (Priority: P2)

After a harness run, the engineer opens the index page. The page shows each
journey, each step, each screenshot, and the checks of each step. For a failed
step, the page shows the console errors, the page errors, the failed requests,
and the HTTP errors. It also shows the lines of the server log and the runner
log for that step. The engineer examines each screenshot and records a
verdict, and each defect gets its own GitHub issue.

**Why this priority**: A failed journey without clear artifacts costs hours.
The user asks for a screenshot at each step and for an examination of each
screenshot.

**Independent Test**: Run one journey with a seeded page error. Open the index
page. Find the failed step, its screenshot, its console error, and its lines
in the server log in less than 2 minutes.

**Acceptance Scenarios**:

1. **Given** a finished harness run, **When** the engineer opens the index
   page, **Then** each journey shows its steps in sequence. Each step shows its
   screenshot, its URL, its time, and its check result.

2. **Given** an unexpected error in a step, **When** the step ends, **Then** the
   step fails, and the artifacts name the error. An error is a console error, a
   page error, a failed request, or an HTTP status of 400 or more.

3. **Given** a failed step, **When** the engineer opens it, **Then** the index
   page shows the server log and the runner log of that step. The page also
   shows a link to the browser trace of the journey.

4. **Given** each screenshot, **When** the automatic screenshot checks run,
   **Then** the harness flags raw template text. It also flags the text
   `None`, `undefined`, `NaN`, or `[object Object]`. It flags an empty main
   region, an unexpected error banner, and a sideways scroll of the page body.

5. **Given** a harness run, **When** the engineer examines each screenshot,
   **Then** the inspection record holds a verdict for each screenshot. It holds
   an issue number for each defect.

6. **Given** the report, **When** a tool reads it, **Then** the tool finds each
   journey, step, timing, and write count. The report also holds each budget
   result and each parity result. The report is one JSON file with a schema
   version.

7. **Given** each text artifact of a harness run, **When** the harness scans
   it, **Then** the scan finds no credential value.

---

### User Story 7 - Measure the performance at the default scale and at a large scale (Priority: P3)

The engineer runs the harness with the default fleet and with the large fleet.
The large fleet holds about 150 sites and about 3,000 devices. The harness
records the server time and the browser timing of each page and each API
call. It also records the number of simulated cloud calls for each. The
performance report ranks the slowest pages and the slowest API calls and
compares each value with its budget.

**Why this priority**: Performance does not block the parity proof. But a large
organization is the target of the multi-site mode. A slow status poll at that
scale can hide the progress of a live operation.

**Independent Test**: Run the large-fleet multi-site journey alone. The report
names the 10 slowest pages and the 10 slowest API calls. Each entry shows the
server time at the 95th percentile and a budget result.

**Acceptance Scenarios**:

1. **Given** each journey, **When** a page opens or an API call answers,
   **Then** the harness records the server time and the browser timing. It also
   records the count of simulated cloud calls.

2. **Given** the large fleet, **When** the multi-site journey selects all sites
   and all device families, **Then** the journey gets to the end of the
   upgrade. The journey takes less than 10 minutes.

3. **Given** the large fleet, **When** the single-site journey runs at the
   largest site, **Then** the journey gets to the end of the upgrade. The
   journey takes less than 10 minutes.

4. **Given** the report, **When** the engineer reads it, **Then** it ranks the
   10 slowest pages and the 10 slowest API calls for each fleet. Each entry
   shows the 50th percentile, the 95th percentile, the maximum, and the sample
   count.

5. **Given** a value that is more than its budget, **When** the harness writes
   the report, **Then** the budget result shows `breach`. The result names one
   GitHub issue.

6. **Given** an earlier report, **When** the harness writes a new report,
   **Then** the new report shows the change of each 95th percentile value.

---

### User Story 8 - Prove the cross-cutting operator journeys (Priority: P3)

The engineer runs the journeys that surround the upgrade. These journeys
include the sign-in, the sign-out, a change of organization, and a change of
mode. They also include the navigation menu, the history, the comparison, the
error pages, basic accessibility, and a narrow viewport. Two more journeys
include a capture with no upgrade and a lock takeover after the cooldown.

**Why this priority**: Most of these paths have a browser test today with fixed
stand-ins. The journeys add the frame around a full upgrade. They also prove
that the state stays correct across pages.

**Independent Test**: Run the cross-cutting journeys alone. Each journey
passes. Each page passes the navigation checks and the accessibility checks.

**Acceptance Scenarios**:

1. **Given** the sign-in page, **When** the journey signs in with the stand-in
   browser token, **Then** the portal shows the organization. No page, file,
   or log holds the token value.

2. **Given** a provider account with a second factor, **When** the journey
   types the address, the password, and the code, **Then** the organization
   list shows.

3. **Given** a signed-in operator, **When** the journey signs out, **Then** each
   page after that asks for a new sign-in. The back control shows no protected
   data.

4. **Given** sites and options for organization A, **When** the journey selects
   organization B, **Then** the portal shows no site, option, or operation of
   organization A. A start with the earlier confirmation fails.

5. **Given** selected sites in the multi-site mode, **When** the journey
   selects the single-site mode, **Then** the portal removes the selected
   targets. The change in the other direction also removes the selected
   targets.

6. **Given** each page after the sign-in, **When** the harness examines the
   header, **Then** the Sites, History, and Compare links show. The theme
   control and the sign-out control also show, and each link opens its page.

7. **Given** the sign-in page, **When** the harness examines the header,
   **Then** the page shows no navigation link and no sign-out control.

8. **Given** completed runs and completed operations, **When** the journey opens
   the history page, **Then** each entry shows its status, operator, account,
   and age. Each entry shows a link to its captures and its comparison.

9. **Given** two post-check captures of one run, **When** the journey opens the
   comparison, **Then** the newest post-check is the default. The journey can
   select the earlier one, and each download holds each row of the page.

10. **Given** an error page, **When** the journey opens it, **Then** the portal
    shows a plain message, the correct HTTP status, and a way back. The error
    pages come from an unknown path, a page with no selected context, and an
    operation of a different owner. No page shows a stack trace.

11. **Given** each page of each journey, **When** the accessibility checks run,
    **Then** the page has one main heading. Each form control has a label. Each
    button and each link has an accessible name. No status uses color as its
    only sign.

12. **Given** each typed confirmation, **When** the journey uses the keyboard
    alone, **Then** the journey can type the word and start the action.

13. **Given** a viewport 390 pixels wide, **When** a happy-path journey runs in
    each mode, **Then** each control that the journey uses can scroll into
    view. The page body does not scroll sideways outside a table scroll area.

14. **Given** a site, **When** the journey runs a capture at the extra tier and
    downloads it, **Then** the file holds each row of the page.

15. **Given** an abandoned session that holds a site lock, **When** the
    cooldown ends, **Then** a second operator must type `CONFIRM` to take over
    the site. The journey control marks the session as abandoned and ends the
    cooldown. Before the cooldown ends, the first owner can type `continue` to
    restore the run.

---

### Edge Cases

- The shipped code makes a cloud call that the simulated cloud does not answer.
  The existing traps refuse the call, and the journey fails with the name of
  the call.

- The browser asks for a host other than the journey server. The browser
  refuses the request, and the step records a failed request.

- The journey server stops during a journey. The harness fails that journey,
  keeps the server log, and starts a new journey server for the next journey.

- A step waits for a page condition that does not occur. The step fails at its
  time limit. It keeps a screenshot and the last lines of the server log.

- A journey server from an earlier harness run still holds a port. The harness
  stops only a server that its own owner record names. It then takes a
  different free port.

- The journey clock goes past a phase deadline while the browser shows a
  different page. The next page shows the status that the shipped rules gave.

- The operator refreshes the progress page during the cascade. The portal sends
  no new write, because the stored record decides the next action.

- A session expires while the progress page polls. The poll answers with a
  sign-in request, and the run continues on the server.

- No selected site holds a device of the selected family. The portal refuses
  the plan or shows an empty plan, and it sends no write.

- The only gateway at a selected site is a Mist Edge device. The plan holds no
  gateway child for that site.

- The uncertain answer occurs on the organization AP child. The AP child stays
  unknown, and each site child keeps its own status.

- A capture runs while a status poll repeats. The poll stays in its budget.

- A screenshot does not save. The step records the problem, and the journey
  fails.

- Two harness runs start at the same time on one workstation. Each harness run
  uses its own run identifier, port, artifact directory, and fleet.

- A journey with the large fleet takes more time than its budget. The report
  shows a breach for that journey.

- A page computes an age from a server time. The browser date follows the
  journey clock, so the page shows a correct age.

- A gap journey passes because a change added the capability. The harness fails
  the run until the matrix shows `parity` for that row.

## Requirements *(mandatory)*

### Functional Requirements

#### The journey server

- **FR-001**: The harness MUST start its own journey server for each harness
  run. The journey server MUST listen on `127.0.0.1` only.

- **FR-002**: The journey server MUST run the shipped portal routes, the shipped
  templates, and the shipped browser scripts with no change.

- **FR-003**: The journey server MUST run the shipped `RunDriver`, settle gate,
  stop path, capture collector, and reconciliation service of
  `src/upgrade_portal/`.

- **FR-004**: The journey server MUST run the shipped services of
  `src/firmware/aggregate_upgrade_service.py`,
  `src/firmware/org_upgrade_service.py`, and `src/firmware/upgrade_service.py`.
  It MUST NOT replace these services with a stand-in. The report MUST show the
  SDK call name of each write, so a reader can see which shipped service made
  it.

- **FR-005**: The journey server MUST replace only four things. They are the
  cloud boundary, the record stores, the time source, and the registration of
  test operators.

- **FR-006**: The journey server MUST reuse the isolated resources, the record
  stores, and the traps of `tests/support/upgrade_portal_e2e/`. It MUST follow
  the server pattern of `tests/e2e/upgrade_portal/conftest.py`.

- **FR-007**: The harness MUST NOT stop, change, or answer a request between
  the browser and the journey server. The shipped routes answer each page and
  each API call.

- **FR-008**: The journey server MUST write each file that a shipped path
  writes into the directory of the harness run.

- **FR-009**: The journey server MUST write one log line for each request. The
  line holds the journey identifier, the step identifier, and the method. It
  also holds the path, the status, and the server time.

- **FR-010**: The journey server MUST set `ORG_UPGRADE_WRITES_ENABLED` to
  `True` in its own process only. It MUST change no production setting.

- **FR-011**: If the journey server stops during a journey, the harness MUST
  fail that journey and keep the server log. The harness MUST then start a new
  journey server for the next journey.

#### The simulated cloud

- **FR-012**: The simulated cloud MUST answer each call that the shipped code
  makes at the cloud boundary. Each answer MUST have the shape of the live
  cloud answer, as the rules of `src/upgrade_portal/app/seam_shapes.py` state.

- **FR-013**: The simulated cloud MUST reuse the attachment points, the fleet
  script, and the stand-in cloud of `tests/support/rehearsal/` where they
  apply. It MUST hold no copy of a settle rule, a phase sequence, or a stop
  rule.

- **FR-014**: The simulated cloud MUST accept a write, record it, and keep it
  inside the process of the journey server. The rehearsal stand-in refuses a
  write, but a journey must get to the end of the upgrade.

- **FR-015**: The simulated cloud MUST examine each write body against the
  documented request shape of the Mist API. It MUST answer status 400 for a
  body that breaks the shape.

- **FR-016**: The simulated cloud MUST record each call. The record holds the
  call name, the scope, the identifiers, and a copy of the body with no
  credential. It also holds the answer, the time on the journey clock, and the
  step.

- **FR-017**: The simulated cloud MUST answer the reads of the capture
  collector from the same device data as the upgrade reads. A post-check
  capture then shows the new versions and the scripted client changes.

- **FR-018**: The simulated cloud MUST answer the device event search with the
  device type that the caller gives, and it MUST answer in pages. These rules
  are FR-009 and FR-010 of spec 1992.

- **FR-019**: The simulated cloud MUST answer the account read. The progress
  page then shows the Mist account label from the cloud boundary.

#### The fleets

- **FR-020**: The default fleet MUST hold the organizations and the sites of
  this table.

| Organization | Site | Access points | Switches | Junos gateways | SSR gateways | Mist Edge devices |
| - | - | - | - | - | - | - |
| First | Site 1 | 3 | 2 | 1 | 0 | 0 |
| First | Site 2 | 3 | 2 | 0 | 1 | 0 |
| First | Site 3 | 3 | 2 | 1 | 0 | 0 |
| First | Site 4 | 3 | 2 | 1 | 1 | 1 |
| Second | Site 5 | 1 | 1 | 1 | 0 | 0 |

- **FR-021**: In the default fleet, 4 wireless clients MUST connect to each
  access point, and 3 wired clients MUST connect to each switch. Each site
  MUST hold 1 guest client.

- **FR-022**: Each device family MUST have two or more models. Each model MUST
  offer the version that runs now and two or more newer versions.

- **FR-023**: After the upgrade, one wireless client of each site MUST move to
  a different access point. One wired client of each site MUST NOT reconnect.

- **FR-024**: The large fleet MUST hold one organization with about 150 sites
  and about 3,000 devices. Each site holds about 12 access points, 6 switches,
  and 2 gateways. The large fleet holds the two gateway classes and 5 Mist
  Edge devices.

- **FR-025**: The large fleet MUST also hold one large site with 200 devices
  and 2,000 clients.

- **FR-026**: The simulated cloud MUST give each organization, site, and device
  a fake identifier. No identifier names a live Mist tenant.

#### The simulated devices

- **FR-027**: After an accepted write, each simulated device MUST move through
  the statuses accepted, downloading, rebooting, and reconnected. Each move
  occurs at a scripted interval on the journey clock.

- **FR-028**: While a device reboots, the simulated cloud MUST report the
  device as offline and its clients as disconnected.

- **FR-029**: When a device reconnects, the simulated cloud MUST report a
  reconnect event, a smaller uptime, and the new version. The clients of the
  device reconnect, except for the scripted changes.

- **FR-030**: The journey control MUST let a journey give one device a
  different outcome. The outcomes are a failure with a reported cause, no
  reconnection, and a reconnection with a different version.

- **FR-031**: The journey control MUST let a journey give one write a different
  answer. The answers are an acceptance, a rejection with a status of 400 or
  more, and an uncertain answer.

- **FR-032**: For an uncertain answer, the simulated cloud MUST apply the write.
  The caller MUST receive no answer.

- **FR-033**: A device with a start time or a reboot-at interval MUST wait for
  that time on the journey clock.

- **FR-034**: The upgrade status reads MUST report the status of each device in
  the shape of the live cloud. This rule applies to the organization job, the
  site job, and the SSR job.

- **FR-035**: A cancel call MUST cancel each device that did not start to write
  firmware. It MUST report each device that writes firmware now as a device
  that continues.

#### The journey clock and the journey control

- **FR-036**: The run driver and the simulated cloud MUST read one journey
  clock. The journey clock MUST reuse the driven clock of
  `tests/support/rehearsal/`. It MUST fill the four time seats of the run
  driver that spec 1992 names.

- **FR-037**: The journey clock MUST move faster than the wall clock by a set
  multiple. The default multiple MUST let a happy-path journey get to the end
  of the upgrade in less than 3 minutes.

- **FR-038**: The journey control MUST let a journey move the journey clock
  forward by a set interval at once. The journey clock MUST NOT move
  backwards.

- **FR-039**: The date that the browser reads MUST follow the journey clock.
  The browser timers MUST keep the pace of the wall clock.

- **FR-040**: The site locks and the operator sessions MUST keep the wall
  clock. The journey control MUST let a journey end a session or a site lock at
  once. It MUST also let a journey mark a session as abandoned.

- **FR-041**: The journey control MUST change only the simulated cloud, the
  journey clock, and the test sessions and site locks. It MUST NOT change a
  shipped rule.

#### The journeys

- **FR-042**: The harness MUST drive a browser through Playwright. Each journey
  MUST use its own browser context.

- **FR-043**: A journey MUST be a sequence of named steps. Each step does one
  operator action and then checks the page.

- **FR-044**: A step MUST find each control through its `data-testid` value.
  The values follow the contract in
  `specs/1823-upgrade-capture-portal/contracts/ui-testids.md`.

- **FR-045**: A step MUST wait for a page condition. A step MUST NOT wait for a
  fixed interval of wall-clock time.

- **FR-046**: Each step MUST have a time limit. If the step takes more time
  than its limit, the step fails and keeps its artifacts.

- **FR-047**: Each journey MUST make the runs and the operations that it uses.
  No journey reads a run or an operation of a different journey.

- **FR-048**: One or more happy-path journeys in each mode MUST start at the
  sign-in page and complete the sign-in form. The other journeys can start from
  a session that the journey server registers at its start.

- **FR-049**: The harness MUST let the engineer select journeys by identifier,
  user story, mode, family combination, and fleet. It MUST also offer a smoke
  set for a quick check. The smoke set holds `M-ASG` and `S-ASG`.

- **FR-050**: The journeys MUST open each of these pages: `/select/org`,
  `/select/mode`, `/select/site`, the inventory page, and the capture page.
  They MUST also open the pages below `/runs/` and `/upgrade/org/`, and the
  pages `/history` and `/compare`.

- **FR-051**: A single-site journey gets to the end of the upgrade when the run
  status is `complete`. The post-check capture MUST show its verified badge.
  The comparison MUST show the new version of each upgraded device.

- **FR-052**: A multi-site journey gets to the end of the upgrade when the
  operation status is `completed` and each child shows a terminal status.

#### The journey catalog

- **FR-053**: The harness MUST hold one happy-path journey for each mode and
  each family combination. The catalog below names the 14 journeys.

- **FR-054**: The happy-path journeys MUST include the two gateway classes, a
  site with the two classes, and a site with a Mist Edge device.

- **FR-055**: The harness MUST hold one fault journey for each fault of the
  catalog in each mode. If a mode has no control for the fault, the journey
  records a gap.

- **FR-056**: The harness MUST hold the cross-cutting journeys of the catalog.

- **FR-057**: The harness MUST hold the two large-fleet journeys of the
  catalog.

| Identifier | Journey | Modes |
| - | - | - |
| `M-A`, `M-S`, `M-G`, `M-AS`, `M-AG`, `M-SG`, `M-ASG` | Happy path for AP, switch, gateway, and each mixed combination | Multi-site |
| `S-A`, `S-S`, `S-G`, `S-AS`, `S-AG`, `S-SG`, `S-ASG` | Happy path for the same seven combinations | Single-site |
| `F-UNCERTAIN` | A write with an uncertain answer | Each mode |
| `F-PARTIAL` | A rejected write, and a site lock that expires between two writes | Each mode |
| `F-DOUBLE` | Two fast starts, a start from a second tab, and a start after the back control | Each mode |
| `F-REPLAY` | A recorded start request that the journey sends again | Each mode |
| `F-LOCK` | A lock conflict with a second operator, in one mode and across the two modes | Each mode |
| `F-OWNER` | Control actions from an operator who does not own the work | Each mode |
| `F-SESSION` | A session that expires before the start and during a poll | Each mode |
| `F-CSRF` | A browser write without a correct CSRF token | Each mode |
| `F-ADDRESS` | A write from an operator address on a reserved domain | Each mode |
| `F-FAILED` | A device that fails with a reported cause | Each mode |
| `F-LOST` | A device that does not reconnect | Each mode |
| `F-MISMATCH` | A device that reconnects with a different version | Each mode |
| `F-CANCEL` | A cancellation | Each mode |
| `F-STOP` | A stop in the middle of the upgrade | Each mode |
| `F-RETRY` | A retry of the failed devices | Each mode |
| `F-RESCHEDULE` | A new start time before the start | Each mode |
| `F-RECONCILE` | A reconciliation of an uncertain status | Each mode |
| `X-SIGNIN-TOKEN` | A sign-in with a browser token | Shared |
| `X-SIGNIN-PROVIDER` | A sign-in with a provider account and a second factor | Shared |
| `X-SIGNOUT` | A sign-out | Shared |
| `X-ORG` | A change of organization | Each mode |
| `X-MODE` | A change of mode | Each mode |
| `X-NAV` | The navigation menu on each page | Each mode |
| `X-HISTORY` | The history page | Each mode |
| `X-COMPARE` | The comparison page | Each mode |
| `X-ERRORS` | The error pages | Each mode |
| `X-ACCESS` | Basic accessibility | Each mode |
| `X-NARROW` | A narrow viewport | Each mode |
| `X-CAPTURE` | A capture with no upgrade | Each mode |
| `X-TAKEOVER` | A lock takeover after the cooldown | Each mode |
| `P-LARGE-M` | The large-fleet journey with all sites and all families | Multi-site |
| `P-LARGE-S` | The large-fleet journey at the largest site | Single-site |

A journey that runs in each mode adds the suffix `-S` or `-M` to its
identifier. An example is `F-STOP-M`.

#### The artifacts

- **FR-058**: Each step MUST record one full-page screenshot after its checks.
  A failed step MUST also record a screenshot at the moment of the problem.

- **FR-059**: Each step MUST record its console errors, its page errors, and its
  failed requests. It MUST also record each response with an HTTP status of 400
  or more.

- **FR-060**: Each journey MUST name the errors and the HTTP statuses that it
  expects. Each other error MUST fail the step.

- **FR-061**: Each step MUST record its start time and its end time on the wall
  clock and on the journey clock.

- **FR-062**: Each journey MUST keep an excerpt of the server log and of the
  runner log. The excerpt holds the lines of the requests of that journey.

- **FR-063**: A failed journey MUST keep a browser trace.

- **FR-064**: Each harness run MUST write one report and one index page into
  `data/test-artifacts/upgrade-portal-journeys/<harness-run-identifier>/`.

- **FR-065**: The report MUST follow a documented schema with a version number.

- **FR-066**: The harness MUST run the automatic screenshot checks of user
  story 6 on the page of each step.

- **FR-067**: The feature MUST keep an inspection record. The record holds a
  verdict for each screenshot, a note, and the issue number of each defect.

- **FR-068**: Each defect that the journeys find MUST get one GitHub issue. The
  issue names the journey, the step, the screenshot, and the log lines. One
  defect gets one issue, also when several journeys find it.

- **FR-069**: The harness MUST write only ASCII characters to its logs.

#### The parity matrix

- **FR-070**: The feature MUST keep a capability inventory for the two modes.
  The inventory starts from the baseline table below.

- **FR-071**: The harness MUST compare the inventory with the `data-testid`
  controls of the shipped templates of each mode. It MUST report each control
  that maps to no capability.

- **FR-072**: For each capability, the matrix MUST show the status in each
  mode and the result for each family combination that applies. It MUST also
  show the journeys that prove the result and the verdict.

- **FR-073**: A status in a mode MUST be `proven`, `partial`, `missing`, or
  `defect`. A verdict MUST be `parity` or `gap`.

- **FR-074**: The harness MUST make each status from the journey results of the
  harness run. The feature keeps only the issue number of each gap by hand.

- **FR-075**: A gap journey MUST report the gap and its issue number, and it
  MUST NOT report a pass. If a gap journey passes, the harness MUST fail the
  run and report the row as out of date.

- **FR-076**: The matrix MUST show the parity percentage. The percentage is the
  number of `parity` rows divided by the number of rows.

- **FR-077**: The feature MUST publish the matrix as Markdown in the feature
  directory and in the directory of each harness run.

- **FR-078**: Each gap MUST have one GitHub issue. The issue names the
  capability, the mode, the family combinations, and the gap journey.

- **FR-079**: The matrix MUST show the sign-in, the sign-out, and the theme
  control in one shared group. Each shared row has one status, because these
  controls come before the mode selection or apply to the whole portal.

The baseline below comes from the shipped templates and routes on 2026-09-23.
The status `present` means that the mode offers the control. The status
`partial` means that the mode offers a smaller form of it. The status `missing`
means that the mode offers no control. The journeys replace each baseline
status with a status of FR-073.

| Identifier | Capability | Single-site | Multi-site |
| - | - | - | - |
| C01 | Select the organization and the mode | `present` | `present` |
| C02 | Select one site or several sites | `present` | `present` |
| C03 | Show the inventory with the firmware mismatch mark and the unsupported mark | `present` | `partial` |
| C04 | Select all, one, or more device families | `present` | `present` |
| C05 | Classify each gateway as Junos or SSR and use the route of its class | `present` | `present` |
| C06 | Keep each Mist Edge device out of the plan | `present` | `present` |
| C07 | Hold a site lock, name the holder, release the lock, and take over after the cooldown | `present` | `partial` |
| C08 | Run the pre-check capture at the standard tier and the extra tier, with a download | `present` | `missing` |
| C09 | Refuse the start until a verified pre-check exists | `present` | `missing` |
| C10 | Select a version for each device from the available versions | `present` | `partial` |
| C11 | Select the strategy: canary, big bang, RRM, or serial | `present` | `present` |
| C12 | Set the canary phases | `present` | `present` |
| C13 | Select the reboot after the write | `present` | `present` |
| C14 | Set the reboot-at interval | `present` | `present` |
| C15 | Select the Junos file action | `present` | `present` |
| C16 | Force the write when a device runs the selected version | `present` | `present` |
| C17 | Select the stable version | `present` | `missing` |
| C18 | Set the P2P choice, the P2P cluster size, and the P2P parallelism | `present` | `missing` |
| C19 | Set the RRM node sequence, the slow ramp, the first batch, and the maximum batch | `present` | `missing` |
| C20 | Select the mesh upgrade | `present` | `missing` |
| C21 | Select the SSR channel | `present` | `missing` |
| C22 | Set the maximum failures and the maximum failure percentage | `present` | `partial` |
| C23 | Set the start time | `present` | `present` |
| C24 | Show the warning list for mixed gateway classes and for a version that runs now | `present` | `missing` |
| C25 | Show the confirmation summary with the scope, the versions, the options, and the call count | `present` | `partial` |
| C26 | Type `CONFIRM` before the start | `present` | `present` |
| C27 | Show the Mist account label before the write | `present` | `missing` |
| C28 | Run the cascade of gateways, switches, access points, and clients with the settle gate | `present` | `missing` |
| C29 | Show the status and the version check of each device | `present` | `partial` |
| C30 | Refresh the progress page by the automatic poll and by the refresh control | `present` | `present` |
| C31 | Show the age of the last update and the stale-run badge | `present` | `missing` |
| C32 | Show the failure alert with the device and the reported cause | `present` | `partial` |
| C33 | Show the operator address on the progress page | `present` | `missing` |
| C34 | Stop with the typed word `STOP` and show the three outcome lists | `present` | `partial` |
| C35 | Cancel work that did not get to the cloud | `present` | `missing` |
| C36 | Retry the failed devices with the saved options | `present` | `missing` |
| C37 | Set a new start time for work that did not start | `present` | `missing` |
| C38 | Reconcile an uncertain status with a typed confirmation | `present` | `missing` |
| C39 | Run the post-check capture with no operator action | `present` | `missing` |
| C40 | Compare the pre-check and the post-check, with the statistics and the downloads | `present` | `missing` |
| C41 | Show the work on the history page with its status, operator, account, and links | `present` | `missing` |
| C42 | Retry, cancel, or clear several runs from the history page | `present` | `missing` |
| C43 | Show the audit rows of each action | `present` | `missing` |
| C44 | Send one write for each planned write or child, and refuse a replay | `present` | `present` |
| C45 | Keep an uncertain write unknown and do not send it again | `present` | `present` |
| C46 | Keep each result visible after a partial submission | `present` | `present` |
| C47 | Check the owner before each control action | `present` | `present` |
| C48 | Check the CSRF token of each browser write | `present` | `present` |
| C49 | Refuse a write from an operator address on a reserved domain | `present` | `present` |
| C50 | Refuse a write after the session expires | `present` | `present` |
| C51 | Show the navigation menu on each page | `present` | `present` |
| C52 | Pass the basic accessibility checks on each page | `present` | `present` |
| C53 | Show each control at a narrow viewport | `present` | `present` |
| C54 | Show a plain error page with a way back | `present` | `present` |

#### Dependencies and compatibility

- **FR-080**: The harness MUST add no runtime dependency to the portal. It MUST
  use the test tools that the repository holds today.

- **FR-081**: The harness MUST run on Windows 11 and on Linux. It MUST make
  each path with the path tools of the platform.

- **FR-082**: The harness MUST NOT replace the rehearsal harness of issue #1992
  or the existing browser tests.

### Safety Requirements

- **SR-001**: A journey MUST NOT send a write, a cancel, or a read to the live
  Mist cloud.

- **SR-002**: The harness MUST keep three guards against a live call, and each
  guard MUST work alone. The simulated cloud answers each call at the cloud
  boundary. The harness refuses each connection that does not go to
  `127.0.0.1`. The process of the journey server holds no credential.

- **SR-003**: The harness MUST use no API token, no password of a live account,
  and no production store. The environment of the journey server MUST hold no
  credential variable.

- **SR-004**: If the shipped code makes a call that the simulated cloud does
  not answer, the existing traps MUST refuse the call. The journey MUST then
  fail with the name of the call.

- **SR-005**: The simulated cloud MUST record one write, and no more, for each
  planned write of a run. The same rule applies to each claimed child of a
  multi-site operation. A second write for the same planned write or child MUST
  fail the journey.

- **SR-006**: After an uncertain answer, the portal MUST send no second write
  for that planned write or child. The status MUST stay unknown until a read
  reconciles it.

- **SR-007**: The portal MUST refuse each browser write that has no correct
  CSRF token. The refusal MUST send no cloud call.

- **SR-008**: The portal MUST check the owner before each control action on a
  run or an operation.

- **SR-009**: The portal MUST check a live site lock for each selected site
  before each write.

- **SR-010**: A journey MUST NOT treat the acceptance of a write as the end of
  the upgrade. The completed status MUST show only after the simulated devices
  reconnect with the new version.

- **SR-011**: A cancellation result MUST NOT claim that a device went back to
  its earlier firmware.

- **SR-012**: The harness MUST NOT replace or weaken a shipped guard. The typed
  confirmation check, the reserved-address check, and the CSRF check stay in
  the shipped code path. The owner check, the lock check, and the replay check
  also stay there.

- **SR-013**: The journey control MUST exist only in the process of the
  journey server. It MUST open only behind the gate variable of the existing
  browser suite. A production start of the portal MUST NOT load it.

- **SR-014**: The harness MUST scan each text artifact and the page text of
  each step for the stand-in credential values. The scan MUST find no match.

- **SR-015**: The harness MUST write only below
  `data/test-artifacts/upgrade-portal-journeys/` and the temporary directory
  of the operating system. It MUST change no production record.

- **SR-016**: The harness MUST start no container.

- **SR-017**: The browser of each journey MUST refuse each request to a host
  other than the journey server.

### Performance Requirements

- **PR-001**: The harness MUST record the server time of each page and each API
  call of each journey. The source is the request log line of FR-009.

- **PR-002**: The harness MUST record the browser timing of each page. The
  timing holds the time to the first byte, the time to the DOM content event,
  and the time to the load event.

- **PR-003**: The harness MUST record the browser timing of each API call that
  a page script makes.

- **PR-004**: The harness MUST record the count of simulated cloud calls for
  each page and each API call.

- **PR-005**: The harness MUST measure the status polls of the two modes while
  a run or an operation is active. It MUST also measure them while a capture
  runs.

- **PR-006**: The performance report MUST rank the 10 slowest pages and the 10
  slowest API calls for each fleet. The rank uses the server time at the 95th
  percentile.

- **PR-007**: Each ranked entry MUST show the 50th percentile, the 95th
  percentile, the maximum, and the sample count.

- **PR-008**: The report MUST compare each value with the budget of this
  table.

| Measure | Default fleet | Large fleet |
| - | - | - |
| Server time of a page, 95th percentile | 1 second | 3 seconds |
| Server time of an API call, 95th percentile | 0.5 seconds | 2 seconds |
| Server time of a status poll, 95th percentile | 0.5 seconds | 1 second |
| Browser time to the DOM content event, 95th percentile | 2 seconds | 5 seconds |
| Wall-clock time of a happy-path journey | 3 minutes | 10 minutes |
| Wall-clock time of a full harness run | 60 minutes | No budget |

- **PR-009**: The plan can set a separate budget for one named call. The report
  MUST then show the cause of that budget.

- **PR-010**: If a value is more than its budget, the report MUST show
  `breach` and name one GitHub issue.

- **PR-011**: If a report from an earlier harness run exists, the new report
  MUST show the change of each 95th percentile value.

- **PR-012**: The harness MUST measure with the timing data that the browser
  and the server log give. The measurement MUST add no wait to a request.

### Key Entities

- **Harness run**: One execution of a set of journeys. It holds the run
  identifier, the fleet, the journey list, the start time, the end time, the
  report, and the index page.

- **Journey**: One scripted operator path. It holds the identifier, the user
  story, the mode, the family combination, and the fault. It also holds the
  steps, the expected errors, the result, and the capabilities that it proves.

- **Step**: One operator action and its checks. It holds the name, the sequence
  number, the URL, the times, and the times on the journey clock. It also holds
  the screenshot, the errors, the responses, and the result.

- **Journey server**: The portal process of one harness run. It holds the port,
  the run identifier, the server log, and the owner record.

- **Simulated cloud**: The answers at the cloud boundary. It holds the fleet,
  the status of each device, and the call record.

- **Fleet**: The organizations, sites, devices, models, versions, and clients.
  The default fleet and the large fleet are the two fleets.

- **Device script**: The plan of one device in a journey. It holds the outcome,
  the interval of each status move, the version after, and the client changes.

- **Call record**: One call at the cloud boundary. It holds the call name, the
  scope, the identifiers, the body copy, and the answer. It also holds the time
  on the journey clock and the step.

- **Journey clock**: The one time source of the run driver and the simulated
  cloud. It holds the time, the multiple of the wall clock, and each move.

- **Journey control**: The test-only channel of the journey server. It sets the
  device outcomes and the write answers. It also moves the clock and ends
  sessions and site locks.

- **Artifacts**: The screenshots, the log excerpts, the browser trace, and the
  step records of a journey.

- **Report**: The JSON file of one harness run, with a schema version.

- **Index page**: The HTML page of one harness run. It holds a link to each
  journey, each step, each screenshot, and each log excerpt.

- **Inspection record**: The verdict for each screenshot, with a note and the
  issue number of each defect.

- **Capability**: One thing that an operator can do in a mode. It holds the
  identifier, the name, the status in each mode, and the family combinations
  that apply. It also holds the journeys that prove it.

- **Parity matrix**: The table of all capabilities. It holds the verdict of each
  row and the parity percentage.

- **Performance sample**: One measure of one page or one API call. It holds the
  path, the method, the server time, and the browser timing. It also holds the
  count of cloud calls, the journey, and the step.

- **Budget**: The limit for one class of measure and one fleet. It holds the
  limit, the result, and the issue number of a breach.

- **Defect issue**: The GitHub issue for one defect or one gap.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a developer workstation, each of the 14 happy-path journeys
  gets to the end of the upgrade in less than 3 wall-clock minutes.

- **SC-002**: At the default fleet, 7 of 7 family combinations get to the end of
  the upgrade in each mode.

- **SC-003**: In each harness run, zero connections leave the workstation. Each
  trap counter reads zero at the end of each journey.

- **SC-004**: In each journey, the simulated cloud records one write, and no
  more, for each planned write and each claimed child. The double submission
  journeys and the replay journeys give the same count.

- **SC-005**: Each step of each journey has one screenshot. Each screenshot has
  a verdict in the inspection record before the feature closes.

- **SC-006**: The parity matrix includes 100 percent of the capabilities of the
  inventory. The inventory check finds zero controls that map to no capability.

- **SC-007**: Each gap and each defect names one GitHub issue. Zero defects have
  no issue.

- **SC-008**: When each gap issue closes, the parity percentage reads 100. Zero
  gap journeys then stay in the catalog.

- **SC-009**: The performance report names the 10 slowest pages and the 10
  slowest API calls for each fleet. Each budget result reads `pass`, or
  `breach` with an issue number.

- **SC-010**: A full harness run at the default fleet completes in less than 60
  minutes on a developer workstation.

- **SC-011**: Each large-fleet journey gets to the end of the upgrade in less
  than 10 minutes.

- **SC-012**: Zero credential values occur in the text artifacts and in the
  page text of a harness run.

- **SC-013**: Each of the 3 seeded defects makes one or more journeys fail.

- **SC-014**: An engineer who did not write the harness uses the index page. In
  less than 2 minutes, the engineer finds a failed step, its screenshot, and
  its lines in the server log.

- **SC-015**: In 5 consecutive harness runs on the same code, each journey gives
  the same result.

- **SC-016**: Each Markdown file of this feature scores 80 or more with the STE
  linter of the repository.

## Assumptions

- The journey operators use a stand-in address on a reachable domain, as the
  firmware operator of the existing browser suite does. Issue #2615 refuses a
  firmware write from a reserved domain. The harness sends no mail.

- The provider sign-in uses the existing login seam of the sign-in route. The
  seam answers from the simulated cloud and opens no socket.

- The harness uses the Chromium browser of Playwright. Other browsers are out
  of scope.

- The desktop viewport is 1440 by 900 pixels. The narrow viewport is 390 by
  844 pixels. The browser uses the UTC time zone and the `en-US` locale, so
  the screenshots stay stable.

- The journey server can set the browser poll interval to 5 seconds. That value
  is the lowest value that the portal settings accept. A journey can also use
  the refresh control.

- The default multiple of the journey clock is 60. One wall-clock second is
  then one minute on the journey clock. The plan can change the multiple if a
  budget makes it necessary.

- The multi-site mode has no settle gate today. The multi-site end of the
  upgrade therefore uses the status that the simulated cloud reports for each
  child.

- The budgets are first values. The plan can change a budget after the first
  measured harness run, and the plan then records the cause.

- The simulated cloud does not model the batch rules of each strategy. It
  records the options and answers the progress in the shape of the live cloud.

- The harness runs through its own command and a test marker. The default test
  command does not run it. The plan decides when CI runs it.

- The plan can run journeys in parallel with one journey server for each
  worker. A full harness run then stays in its budget.

- The engineer or the implementing agent examines the screenshots and writes
  the inspection record.

- The engineer opens each GitHub issue by hand or with the `gh` tool. The
  harness opens no issue and calls no GitHub service.

- The artifacts stay below `data/`, which Git ignores. The parity matrix and the
  inspection record of the feature stay in the feature directory.

- The harness keeps each earlier harness run directory. The engineer removes old
  directories by hand.

- The capability inventory of this spec is a baseline. The journeys replace
  each baseline status with a proven status.

- Issue #3200 names `/upgrade/...` for the single-site pages. The shipped
  single-site pages are below `/runs/`. This spec uses the shipped paths.

- Spec 2200 names the completed aggregate status `complete`. The shipped code
  writes `completed`. This spec uses the shipped word.

- The new harness code must obey the Five-Item Rule of the constitution. The
  directory `tests/e2e/upgrade_portal/` holds more than five children today.
  The plan must record how the new package enters the tree.

- The existing browser tests stay. A later issue can remove a duplicate test.

## Non-Goals

- Do not send a write, a cancel, or a read to the live Mist cloud. Do not run a
  live upgrade.

- Do not replace the rehearsal harness of issue #1992. It stays the proof of the
  settle rules below the browser.

- Do not add the missing multi-site capabilities in this feature. Each gap gets
  its own issue.

- Do not repair a defect in this feature. Each defect gets its own issue.

- Do not change a shipped route, a shipped template, or a shipped guard to make
  a journey pass.

- Do not model the batch rules of the cloud strategies.

- Do not test a browser other than Chromium. Do not test a mobile layout
  outside the narrow viewport check.

- Do not add a runtime dependency to the portal.

- Do not run the harness against a portal container or a shared server. Use
  only a server that the harness starts.

- Do not measure the latency of the live cloud or the load of many operators at
  the same time.
