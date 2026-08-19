# Feature Specification: Upgrade Pre-Check and Post-Check Portal

**Feature Branch**: `feat/1823-upgrade-capture-portal`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "I need your help to build a tool which can be used for pre-check and post-check before and after the code upgrade. This tool should show before and after code version, wired, wireless clients, Router/switch/APs status"

## User Scenarios & Testing *(mandatory)*

A customer plans a mass firmware upgrade of switches across many sites. A gateway
upgrade effort follows later. Today the operators record the state of a site by
hand before the upgrade. They record it again after the upgrade. They then compare
the two records by eye. This work is slow, and it misses changes.

This feature adds a web portal. The portal records the state of one site before
the upgrade. The portal starts the upgrade. The portal waits until every device
returns. The portal then records the state again and shows the difference.

This document uses one term for each concept:

- A **capture** is one record of the state of one site at one moment.
- A **capture set** holds every capture for one site and one upgrade run.
- An **upgrade job** is one firmware upgrade request for one site.
- A **site lock** gives one person exclusive write access to one site.
- A **comparison result** is the computed difference between two captures.
- A **session owner** is the person who holds a site lock.
- The **settle gate** is the wait that proves a device finished its upgrade.

---

### User Story 1 - Record the state of a site before an upgrade (Priority: P1)

An operator opens the portal, chooses an organization, a site, and a device type.
The operator presses the capture button. The portal collects the state of every
device of that type at that site. The portal collects the wired client list and
the wireless client list. The portal shows the data as tables. The portal saves
the data and offers a file download.

**Why this priority**: This delivers the first half of the customer request. The
operator gets a trustworthy pre-check record without any manual work. This story
has value on its own, because an operator can run it before an upgrade that runs
outside the portal.

**Independent Test**: Choose a site with at least one device. Press the capture
button. Confirm that the tables show every device and every client. Download the
file and confirm that the file holds the same rows.

**Acceptance Scenarios**:

1. **Given** an operator selected an organization, a site, and the device type
   switch, **When** the operator presses the capture button, **Then** the portal
   shows a table of switches with the firmware version, the status, the uptime,
   the model, and the serial number.
2. **Given** the capture finished, **When** the operator reads the client tables,
   **Then** the portal shows every wired client and every wireless client with the
   MAC address, the hostname, the IP address, the VLAN, and the parent device.
3. **Given** the capture finished, **When** the operator presses the download
   control, **Then** the portal returns a file that holds every captured row.
4. **Given** the operator enabled the extra data toggle, **When** the capture
   finishes, **Then** the portal also shows the switch port state, the power over
   Ethernet state, the radio state, the tunnel state, the peer state, and the
   active alarms.
5. **Given** the selected site holds no device of the selected type, **When** the
   capture finishes, **Then** the portal reports an empty result and does not
   report an error.

---

### User Story 2 - Compare the state before and after an upgrade (Priority: P1)

After the upgrade finishes, the operator runs a second capture. The portal then
enables the compare control. The portal shows the two captures as two sorted
tables side by side. The portal marks each row as unchanged, changed, missing, or
added. The portal shows overall statistics. The operator downloads the comparison
as a file.

**Why this priority**: This delivers the second half of the customer request. The
comparison is the artifact that proves the upgrade did no harm. Without it the
operator still compares by eye.

**Independent Test**: Run a capture. Run a second capture without any upgrade.
Confirm that the comparison reports no lost device and no lost client. Then remove
one client from the network and run the second capture again. Confirm that the
comparison marks that client as missing.

**Acceptance Scenarios**:

1. **Given** the first capture and the second capture both saved, **When** the
   operator presses the compare control, **Then** the portal shows both captures
   as two tables that use the same sort order.
2. **Given** a device reports a new firmware version in the second capture,
   **When** the portal builds the comparison, **Then** the portal marks that
   device as changed and shows the old version and the new version.
3. **Given** a client appears in the first capture and not in the second capture,
   **When** the portal builds the comparison, **Then** the portal marks that
   client as missing.
4. **Given** a wireless client attached to a different access point between the
   two captures, **When** the portal builds the comparison, **Then** the portal
   marks that client as moved and names both access points.
5. **Given** the comparison is on screen, **When** the operator presses the
   download control, **Then** the portal returns a file that holds every row of
   both captures and the statistics.
6. **Given** the operator ran the second capture more than one time, **When** the
   operator opens the comparison, **Then** the portal uses the newest second
   capture and lets the operator select an earlier one.

---

### User Story 3 - Start the upgrade and watch every device return (Priority: P2)

The operator selects the upgrade options as radio groups. The operator types
`CONFIRM` in a text box. The portal then enables the begin control. The operator
presses begin. The portal sends the upgrade job. The portal refreshes a status
display every 30 seconds and offers a manual refresh. The portal waits for each
device to reconnect, to reset its uptime, and to report the new firmware version.
The portal then waits 60 more seconds for that device. When every device settles,
the portal shows the new firmware version for each device and prompts for the
second capture. While the upgrade job runs, the operator can stop it. A stop
action cancels every device that has not started yet.

**Why this priority**: This removes the manual watch that costs the operator the
most time. The operator can still run the upgrade outside the portal, so this
story ranks below the two capture stories.

**Independent Test**: Select a site with one device. Type `CONFIRM`. Press begin.
Confirm that the status display updates without a page reload. Confirm that the
portal reports the device as settled only after the firmware version changes and
the extra wait passes.

**Acceptance Scenarios**:

1. **Given** the operator did not type `CONFIRM`, **When** the operator looks at
   the begin control, **Then** the control is disabled.
2. **Given** the operator typed `CONFIRM`, **When** the operator looks at the
   begin control, **Then** the control is enabled.
3. **Given** the first capture did not run, **When** the operator types `CONFIRM`,
   **Then** the begin control stays disabled and the portal explains why.
4. **Given** an upgrade job is running, **When** 30 seconds pass, **Then** the
   status display refreshes without any operator action.
5. **Given** a device reconnected but still reports the old firmware version,
   **When** the portal evaluates the settle gate, **Then** the portal keeps that
   device in the waiting state.
6. **Given** a device failed during the upgrade, **When** the portal detects the
   failure, **Then** the portal raises an alert that names the device and the
   reported reason.
7. **Given** every device of the selected type settled, **When** the portal
   updates the display, **Then** the portal shows the new firmware version for
   each device and prompts for the second capture.
8. **Given** an upgrade job is running and the operator typed `STOP`, **When** the
   operator presses the stop control, **Then** the portal asks the cloud to cancel
   every device that has not started, and names each cancelled device.
9. **Given** a device already writes firmware, **When** the operator stops the
   upgrade job, **Then** the portal lets that device finish and reports it as a
   device that continues.
10. **Given** the cloud offers no cancel action for the selected device type,
    **When** the operator stops the upgrade job, **Then** the portal says that it
    cannot cancel, stops its own polling, and does not claim a cancellation.

---

### User Story 4 - Work on several sites at the same time without collision (Priority: P2)

Several administrators upgrade different sites at the same time. Each person gives
a work email address. The portal combines that email address with a browser
identity to form a session owner. One session owner drives several sites in
several browser tabs at the same time. The portal blocks a different session owner
from starting work on a site that is already locked. Any person can read the state
and the data at any time.

**Why this priority**: The customer runs a mass upgrade across many sites. Two
people who write to one site at the same time corrupt the record. This story
protects the data that the first two stories produce.

**Independent Test**: Open the portal in two browser profiles with two different
email addresses. Start an upgrade on one site from the first profile. Confirm that
the second profile cannot start work on the same site. Confirm that the second
profile can still read the site data.

**Acceptance Scenarios**:

1. **Given** no lock exists for a site, **When** an operator starts a capture on
   that site, **Then** the portal grants the site lock to that session owner.
2. **Given** one session owner holds the lock for a site, **When** a different
   session owner tries to start work on that site, **Then** the portal blocks the
   action and names the current holder and the lock time.
3. **Given** one session owner holds the lock for a site, **When** a different
   person opens the read view of that site, **Then** the portal shows the current
   state and the stored data without any prompt.
4. **Given** one session owner holds locks on two sites, **When** that owner opens
   a third browser tab for a third site, **Then** the portal grants the third lock
   to the same owner.
5. **Given** a session stopped responding, **When** 5 minutes pass, **Then** the
   portal reports the session as abandoned and allows a takeover.
6. **Given** the cooldown ended, **When** a different person requests the site,
   **Then** the portal requires the text `CONFIRM` before it erases the unfinished
   decisions and data.
7. **Given** the original session owner returns before the cooldown ends, **When**
   that owner types `continue`, **Then** the portal restores the unfinished run.

---

### User Story 5 - Authenticate as a managed service provider user (Priority: P3)

An operator chooses the credential mode when the portal opens. The operator keeps
the environment API token, or switches to a managed service provider login. The
login prompts for an email address and a password. The portal reports whether the
login succeeded. In token mode the portal shows the assumed organization. In
provider mode the portal shows a searchable dropdown of the organizations that the
account can reach.

**Why this priority**: Token mode covers the single-organization case and needs no
extra work. Provider mode extends the portal to a partner who manages many
customers. The portal delivers value without provider mode.

**Independent Test**: Open the portal and keep the token mode. Confirm that the
portal names the assumed organization. Restart the portal, choose the provider
login, and confirm that the organization dropdown lists more than one
organization.

**Acceptance Scenarios**:

1. **Given** the portal opened, **When** the operator reads the first screen,
   **Then** the portal offers the token mode and the provider login mode.
2. **Given** the operator kept the token mode, **When** the first screen loads,
   **Then** the portal names the assumed organization and hides the organization
   dropdown.
3. **Given** the operator chose the provider login, **When** the operator supplies
   a valid email address and password, **Then** the portal reports success and
   shows a searchable organization dropdown.
4. **Given** the operator supplied a wrong password, **When** the portal answers,
   **Then** the portal reports the failure and does not show any organization.
5. **Given** any credential mode, **When** the operator reads any screen, any
   file, or any log entry, **Then** no password value and no token value appears.

---

### User Story 6 - Read a comparison from a past upgrade (Priority: P3)

An operator returns the next day, the next week, or the next month. The operator
selects a site and a past upgrade run. The portal shows the stored capture set and
the comparison result. The operator downloads the comparison again.

**Why this priority**: The customer needs evidence after the fact. A support case
or an audit can arrive weeks after the upgrade. The live flow still works without
this story, so it ranks below the live stories.

**Independent Test**: Complete one upgrade run. Close the browser. Open the portal
the next day, select the same site, and confirm that the stored comparison renders
with the same rows and the same statistics.

**Acceptance Scenarios**:

1. **Given** a completed upgrade run exists for a site, **When** the operator
   opens the history view for that site, **Then** the portal lists every stored
   capture set with its date and its device type.
2. **Given** the operator selected a stored capture set, **When** the portal
   renders it, **Then** the portal shows the same tables and the same statistics
   as on the day of the upgrade.
3. **Given** the operator opened a stored capture set, **When** the operator
   presses the download control, **Then** the portal returns the same file
   content as on the day of the upgrade.

---

### Edge Cases

#### Upgrade failures

- **A partial failure.** Some devices upgrade and some devices fail. The portal
  marks each device on its own. The portal never reports the site as successful
  while one device failed.
- **A device never reconnects.** The settle gate for that device reaches the time
  limit. The portal marks the device as not returned. The portal continues to
  report the other devices. The operator can run the second capture without the
  missing device.
- **A device returns on the wrong version.** The device reconnects and reports a
  firmware version that is not the requested version. The portal marks the device
  as a version mismatch, not as a success.
- **The requested version equals the running version.** The firmware version never
  changes, so the settle gate never sees a version change. If the force option is
  off, the portal marks the device as already current and does not wait.
- **An upgrade is already running at the site.** Another person started an upgrade
  outside the portal. The portal detects the running upgrade and warns the
  operator before it sends a new upgrade job.

#### Cascade and timing

- **A gateway upgrade overlaps a switch upgrade.** The cascade forbids this inside
  the portal. If the portal detects an active gateway upgrade while switches are
  still upgrading, the portal holds the downstream gates closed and reports the
  reason.
- **Clock skew.** The clock of the portal host and the clock of the cloud differ.
  The portal detects a reboot from the reported uptime value that decreases. The
  portal never subtracts a cloud timestamp from a local clock value to decide that
  a device rebooted.
- **Stale cloud statistics.** The cloud reports the old firmware version and the
  old uptime for a short time after the reboot. The settle gate requires the
  reconnect event, the uptime reset, and the version change together. The portal
  also ignores a statistics record that is older than the upgrade start time.
- **A very long upgrade.** A large device takes longer than the time limit. The
  portal keeps the device in the waiting state until the limit, then marks it as
  not returned. The operator can extend the wait or continue.

#### Concurrency and sessions

- **Two people request one site at the same time.** Exactly one request wins the
  site lock. The portal never grants the same site lock twice.
- **A browser tab closes during the flow.** The upgrade continues in the cloud.
  The portal keeps the run state on the server. When the operator returns before
  the cooldown ends, the operator types `continue` and resumes.
- **The portal process restarts during an upgrade.** The run state survives the
  restart. The operator resumes the same run and does not send a second upgrade
  job.
- **Two tabs of one owner on one site.** Both tabs show the same state. The portal
  accepts only one begin action and ignores a duplicate.

#### Data volume and shape

- **An organization with thousands of clients.** The portal reads the full client
  list in pages and never truncates it. The tables page in the browser. The
  downloaded file holds every row.
- **A site with a virtual chassis.** Several member switches report under one
  virtual chassis. The capture records each member and the virtual chassis. The
  settle gate waits for every member, not for the first member.
- **An empty site.** The site holds no device of the selected type. The capture
  succeeds with zero rows. The begin control stays disabled.
- **A site with only one device family.** The site has no gateway, or no switch,
  or no access point. The cascade skips the missing gate and opens the next gate.
- **A client with a randomized MAC address.** The client can present a different
  MAC address in the second capture. The comparison marks it as one missing client
  and one added client. The portal states this limit next to the client
  statistics.
- **A client with no hostname.** The comparison matches on the MAC address and
  shows an empty hostname. The portal never drops the row.
- **A device joins or leaves between the two captures.** The comparison marks the
  device as added or missing. This is a result, not an error.

#### Platform and storage

- **A site with both router families.** The site holds one router family and the
  other router family at the same time. The portal detects each model and sends
  each family to its own upgrade path. The portal reports the result for each
  family.
- **The primary database is unreachable.** The capture still completes. The portal
  writes the backup file. The portal tells the operator that the database write
  did not happen.
- **The cloud rejects a request for rate reasons.** The portal delays and retries.
  One rejected call does not fail the whole capture.
- **The credential stops working during a run.** The portal stops the run, reports
  the failure in plain words, and keeps the data that it already collected.

#### Capture ordering

- **The operator repeats the second capture.** The portal stores every run of the
  second capture. The comparison uses the newest run by default.
- **The operator tries the first capture again.** The second capture already
  succeeded. The portal blocks the first capture for that run and explains that
  the original record is protected.

## Clarifications

### Session 2026-08-19

- Q: How long must the portal keep a stored capture set? → A: Keep every capture
  set for an unlimited period. Do not delete a capture set automatically, and do
  not put a capture on a storage path that expires a record. Record the stored
  size of each capture set, so that an operator can watch storage growth.
- Q: Does the portal need a control that stops an upgrade that already runs? →
  A: Yes. Add a stop control that cancels every device that has not started. The
  operator must type `STOP` to enable it. Never interrupt a device that already
  writes firmware, because an interrupted write can leave a device unusable. If
  the cloud offers no cancel action for that device type, say so plainly and do
  not claim a cancellation.

## Requirements *(mandatory)*

### Functional Requirements

#### Portal start and access

- **FR-001**: The system MUST offer a new menu entry that starts the upgrade
  capture portal.
- **FR-002**: The portal MUST listen on a port that is not the port of the
  existing web portal.
- **FR-003**: The portal port MUST be configurable, so that the port does not
  conflict inside a container and does not conflict when several people run the
  portal on one host.
- **FR-004**: The portal MUST print a clickable link to the console when it
  starts.
- **FR-005**: The portal MUST serve several people at the same time without a
  loss of data and without a mixed view between people.

#### Credential mode and organization selection

- **FR-006**: The portal MUST let the operator choose between the environment API
  token and a managed service provider login.
- **FR-007**: If the operator chooses the provider login, the portal MUST prompt
  for an email address and a password. If the account requires a second
  authentication factor, the portal MUST prompt for that factor and MUST retry
  the login with it.
- **FR-008**: The portal MUST report whether the login succeeded or failed.
- **FR-009**: The portal MUST never show, log, or store a password value or a
  token value. The portal MUST refer to a stored credential by its variable name
  only.
- **FR-010**: If the operator keeps the token mode, the portal MUST name the
  assumed organization and MUST hide the organization dropdown.
- **FR-011**: If the operator chooses the provider login, the portal MUST show a
  searchable dropdown of the organizations that the account can reach.

#### Site and device type selection

- **FR-012**: The portal MUST show a searchable dropdown of the sites in the
  selected organization.
- **FR-013**: The portal MUST show a dropdown of device type with the choices
  access point, gateway, and switch.
- **FR-014**: The portal MUST support one site for each run.
- **FR-015**: The selection layer MUST accept a list of sites later, without a
  change to the capture logic or to the comparison logic.

#### Upgrade option selection

- **FR-016**: The portal MUST show the same upgrade options that the existing bulk
  firmware upgrade flow prompts for, for the selected device type.
- **FR-017**: The portal MUST show each option group as a radio group that accepts
  exactly one selection.
- **FR-018**: The portal MUST preselect the same default value that the existing
  bulk firmware upgrade flow uses for each option.
- **FR-019**: If the device type is gateway, the portal MUST detect the router
  model of each device at the site and MUST send each router family to its own
  upgrade path.
- **FR-020**: If one site holds both router families, the portal MUST show the
  option groups for each family and MUST report the result for each family.

#### The first capture

- **FR-021**: The portal MUST offer a capture control that runs the first capture.
- **FR-022**: A capture MUST collect the default data tier. The default tier holds
  the device state and the client lists. The device state holds the firmware
  version, the status, the uptime, the model, and the serial number. The client
  lists hold every wired client and every wireless client with the MAC address,
  the hostname, the IP address, the VLAN, the SSID, the signal strength, and the
  parent access point or switch port.
- **FR-023**: The portal MUST offer a toggle for each run that adds the extra data
  tier. The extra tier holds the switch port state, the power over Ethernet state,
  the radio channel, the radio power, the tunnel state, the peer state, and the
  active alarms.
- **FR-024**: Every capture MUST record a schema version.
- **FR-025**: Every capture MUST record the organization, the site, the device
  type, the capture position in the run, the session owner, the data tier, the
  start time, and the end time.
- **FR-026**: The portal MUST show a completed capture as tables.
- **FR-027**: The portal MUST offer a file download of a completed capture.
- **FR-028**: A capture MUST never drop a device or a client that the cloud
  reports.

#### Storage and retention

- **FR-029**: The portal MUST write every capture to the primary database.
- **FR-030**: The portal MUST write every capture to a backup file.
- **FR-031**: If the primary database is unreachable, the portal MUST still
  complete the capture, MUST write the backup file, and MUST tell the operator
  that the database write did not happen.
- **FR-032**: The portal MUST retain every capture set for an unlimited period.
  The portal MUST NOT delete a capture set automatically, and MUST NOT set an
  expiry time on a stored capture.
- **FR-032a**: The portal MUST NOT store a capture on a storage path that expires
  a record automatically.
- **FR-032b**: The portal MUST record the stored size of each capture set, so
  that an operator can see how storage grows across many sites.

#### Confirmation and upgrade start

- **FR-033**: The portal MUST keep the begin control disabled until the operator
  types the exact text `CONFIRM`.
- **FR-034**: The portal MUST reject any other text, including a different letter
  case.
- **FR-035**: The portal MUST keep the begin control disabled until the first
  capture saved.
- **FR-036**: The portal MUST send the upgrade job only for the devices of the
  selected device type at the selected site.
- **FR-037**: The portal MUST detect an upgrade that already runs at the selected
  site and MUST warn the operator before it sends a new upgrade job.
- **FR-038**: The portal MUST accept only one begin action for each upgrade job,
  even when the operator opens several browser tabs.

#### Stop control

- **FR-038a**: The portal MUST show a stop control while an upgrade job runs.
- **FR-038b**: The portal MUST keep the stop control disabled until the operator
  types the exact text `STOP`. The portal MUST reject any other text, including a
  different letter case.
- **FR-038c**: When the operator confirms the stop action, the portal MUST ask
  the cloud to cancel the upgrade for every device that has not started.
- **FR-038d**: The portal MUST NOT interrupt a device that already writes
  firmware. Interrupting a write can leave the device unusable.
- **FR-038e**: The portal MUST report which devices the stop action cancelled and
  which devices continue, and MUST name each device.
- **FR-038f**: If the cloud does not support a cancel action for the selected
  device type, the portal MUST tell the operator that fact, MUST stop its own
  polling, and MUST NOT claim that it cancelled the upgrade.
- **FR-038g**: After a stop action, the portal MUST allow the second capture, so
  that the operator can compare the part of the fleet that did upgrade.
- **FR-038h**: The portal MUST record every stop action with the session owner,
  the time, and the list of cancelled devices.
- **FR-038i**: Only the session owner that holds the site lock MAY stop that
  upgrade job.

#### Progress display and the settle gate

- **FR-039**: The portal MUST refresh the status display every 30 seconds without
  any operator action.
- **FR-040**: The portal MUST offer a manual refresh control.
- **FR-041**: The portal MUST show the status of each device on its own.
- **FR-042**: The portal MUST poll the device events every 20 seconds and MUST
  wait for the event that reports that the device reconnected to the cloud.
- **FR-043**: After the reconnect event, the portal MUST poll the device
  statistics until the uptime resets and the firmware version changes.
- **FR-044**: After the uptime resets and the firmware version changes, the portal
  MUST wait 60 more seconds before it treats the device as settled.
- **FR-045**: The portal MUST detect a reboot from a reported uptime value that
  decreases, and MUST NOT compare a cloud timestamp against the local clock.
- **FR-046**: The portal MUST ignore a device statistics record that is older than
  the upgrade start time.
- **FR-047**: The portal MUST apply a time limit to the settle gate of each
  device. If the limit passes, the portal MUST mark that device as not returned
  and MUST continue with the other devices.
- **FR-048**: The portal MUST report progress to the operator as each device
  returns.
- **FR-049**: When every device of the selected type settles, the portal MUST show
  the new firmware version for each device.
- **FR-050**: If a device fails during the upgrade or after the upgrade, the
  portal MUST raise an alert that names the device and the reported reason.
- **FR-051**: If a device returns on a firmware version that is not the requested
  version, the portal MUST mark that device as a version mismatch.

#### Cascade order

- **FR-052**: The portal MUST open the switch gate only after the gateway gate
  closes.
- **FR-053**: The portal MUST open the access point gate only after the switch
  gate closes.
- **FR-054**: The portal MUST open the wireless client gate only after the access
  point gate closes.
- **FR-055**: The portal MUST treat the wired clients as released by the switch
  gate.
- **FR-056**: The portal MUST wait 60 seconds more for each access point, so that
  the statistics and the uptime show the fresh boot.
- **FR-057**: The portal MUST NOT open a downstream gate before its upstream gate
  closes.
- **FR-058**: If a site holds no device of one family, the portal MUST skip that
  gate and MUST open the next gate.

#### The second capture

- **FR-059**: After every device settles, the portal MUST prompt for the second
  capture.
- **FR-060**: The second capture MUST use the same data options and the same
  retention as the first capture.
- **FR-061**: The portal MUST let the operator repeat the second capture as many
  times as needed.
- **FR-062**: The portal MUST retain each run of the second capture as a separate
  record.
- **FR-063**: After the second capture succeeds, the portal MUST block the first
  capture for that run, so that the original record stays intact.

#### Comparison

- **FR-064**: After the second capture saves, the portal MUST enable the compare
  control.
- **FR-065**: The portal MUST show the first capture and the second capture as two
  sorted tables side by side.
- **FR-066**: Both tables MUST use the same sort order, so that the operator sees
  which rows are missing and which rows are new.
- **FR-067**: The portal MUST mark each row as unchanged, changed, missing, or
  added.
- **FR-068**: If a wireless client attached to a different access point between
  the two captures, the portal MUST mark that client as moved and MUST name both
  access points.
- **FR-069**: The comparison MUST show overall statistics. The statistics MUST
  hold the device count before and after, the device count for each firmware
  version, the wired client count, the wireless client count, the count of devices
  that changed version, the count of devices that did not change version, the
  count of devices that failed, the count of clients lost, the count of clients
  gained, and the count of clients that moved.
- **FR-070**: The portal MUST offer a file download of the comparison.
- **FR-071**: If the operator repeated the second capture, the comparison MUST use
  the newest run by default and MUST let the operator select an earlier run.

#### Site lock and concurrency

- **FR-072**: The portal MUST prompt for the work email address of the operator
  before it starts any write action.
- **FR-073**: The portal MUST combine the work email address with a browser
  identity to form the session owner.
- **FR-074**: One session owner MUST be able to hold locks on several sites in
  several browser tabs at the same time.
- **FR-075**: The portal MUST hold one site lock for each site.
- **FR-076**: The portal MUST grant a site lock to exactly one session owner, even
  when two requests arrive at the same time.
- **FR-077**: If a site lock exists, the portal MUST block a different session
  owner from a capture, an upgrade start, an unfinished step, or an option change
  on that site.
- **FR-078**: If a session stops responding, the portal MUST start a 5 minute
  cooldown.
- **FR-079**: After the cooldown ends, the portal MUST require the text `CONFIRM`
  from a different operator before it erases the unfinished decisions or data.
- **FR-080**: If the original session owner returns before the cooldown ends, the
  portal MUST restore the run when that owner types `continue`.
- **FR-081**: The portal MUST let any person read the current state and the stored
  data without any typed text.
- **FR-082**: A site lock MUST NOT block a read.
- **FR-083**: The run state MUST live on the server, so that a closed browser tab
  or a restarted portal does not lose the run.

#### History

- **FR-084**: The portal MUST let an operator retrieve a stored capture set by
  site and by date.
- **FR-085**: A stored capture set MUST render with the same tables, the same
  statistics, and the same download content as on the day of the upgrade.

#### Observability

- **FR-086**: The portal MUST log every operation before it starts and after it
  ends.
- **FR-087**: The portal MUST log the session owner with every operation that
  changes state.
- **FR-088**: The portal MUST never write a credential value to a log.

#### Performance

- **FR-089**: The portal MUST collect the device data and the client data in
  parallel.
- **FR-090**: The portal MUST poll several devices in parallel during the settle
  gate.
- **FR-091**: The portal MUST stay responsive to a read request while a capture
  runs or while an upgrade runs.
- **FR-092**: If the cloud rejects a request for rate reasons, the portal MUST
  delay and retry that request, and MUST NOT fail the whole capture.
- **FR-093**: The portal MUST read a long client list in pages and MUST NOT
  truncate it.

#### Appearance

- **FR-094**: The portal MUST use the T-Mobile color scheme with the primary color
  `#E20074`.
- **FR-095**: The theme assets MUST ship with the application, so that version
  control tracks them and the container image holds them.

### Web Interface Contract

The repository requires a user interface section in any specification that
changes a web interface. This subsection states the behavior, not the design.

**Views**: The portal offers five views. The credential view chooses the
credential mode. The selection view chooses the organization, the site, the device
type, and the upgrade options. The capture view runs a capture and shows its
tables. The progress view shows the upgrade status. The comparison view shows the
two captures side by side and the statistics. A history view lists stored capture
sets for one site.

**Critical journeys**: An operator moves from the credential view to the selection
view, then to the capture view, then to the progress view, then back to the
capture view for the second capture, then to the comparison view. An operator can
enter the history view from any point without a lock.

**Assertions**: A test MUST be able to assert that the begin control is disabled
before the text `CONFIRM` is present. A test MUST be able to assert that the
status display changed after 30 seconds. A test MUST be able to assert that the
comparison marks a removed client as missing.

**Stability contract**: Every control that a test drives MUST carry a stable test
identifier that does not change with the layout or the style.

**Artifacts**: A failed interface test MUST produce a screenshot and a trace.

### Key Entities

- **Capture**: One record of the state of one site at one moment, for one device
  type. Holds the device rows, the wired client rows, the wireless client rows, an
  optional extra data tier, a schema version, a data tier marker, a position in
  the run, and a start time and an end time. A capture is never changed after it
  saves.
- **Capture set**: The group of captures for one site and one upgrade run. Holds
  exactly one first capture and one or more second captures. Owns the link to the
  upgrade job and to the session owner.
- **Upgrade job**: One firmware upgrade request for one site and one device type.
  Holds the selected options, the target firmware version, the device list, the
  router family for a gateway run, the start time, the end time, and the outcome
  for each device.
- **Site lock**: The record that gives one session owner exclusive write access to
  one site. Holds the site, the session owner, the grant time, the last activity
  time, and the state. The state is active, in cooldown, or released. A site lock
  never blocks a read.
- **Comparison result**: The computed difference between the first capture and one
  second capture. Holds the row state for each device and each client, the moved
  client pairs, and the overall statistics. A comparison result is reproducible
  from its two captures.
- **Session owner**: The identity that holds a site lock. Holds the work email
  address of the operator and a browser identity. One session owner can hold
  several site locks at the same time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator completes the first capture for a site of 50 devices in
  under 2 minutes.
- **SC-002**: An operator reads the full before-and-after comparison in under 30
  seconds after the compare control is pressed.
- **SC-003**: The portal reports a device as settled within 3 minutes of the
  moment that device reaches a stable state.
- **SC-004**: A capture drops zero devices and zero clients across 20 consecutive
  runs on sites of different sizes.
- **SC-005**: Two operators who work on two different sites at the same time never
  see each other's data and never block each other, across 20 consecutive
  attempts.
- **SC-006**: A second operator who tries to start work on a locked site is
  blocked in 100 percent of attempts.
- **SC-007**: An operator retrieves a comparison from at least 90 days earlier and
  reads the same rows and the same statistics as on the day of the upgrade. No
  stored capture expires on its own at any age.
- **SC-008**: The portal completes a capture for a site with 5,000 clients without
  a failure and without a browser timeout.
- **SC-009**: 100 percent of captures produce a readable backup file, including
  the captures that run while the primary database is unreachable.
- **SC-010**: 100 percent of operations produce a start log entry and an end log
  entry.
- **SC-011**: Zero password values and zero token values appear in any screen, any
  downloaded file, or any log entry, across a full audit of one upgrade run.
- **SC-012**: A junior network operations engineer completes the full flow, from
  the credential view to the comparison view, on the first attempt and without
  help, in at least 90 percent of trials.
- **SC-013**: The manual pre-check and post-check effort for one site decreases
  from 30 minutes to under 5 minutes.
- **SC-014**: The comparison correctly classifies a client that moved to a
  different access point as moved, and not as one lost client and one gained
  client, in at least 95 percent of moves.
- **SC-015**: A stop action reaches the cloud in under 10 seconds, and no device
  that had not started the upgrade at that moment receives new firmware.
- **SC-016**: A stop action never leaves a device unusable, across 20 consecutive
  attempts.

## Assumptions

### Assumptions and defaults

- The operator uses a modern desktop browser. Mobile layout is not a target.
- The operator has network access to the Mist cloud and to the portal host.
- The customer upgrades switches first. The gateway effort follows later.
- The upgrade itself reuses the existing bulk firmware upgrade capability. This
  feature adds the portal, the captures, the settle gate, the lock, and the
  comparison.
- The default settle gate time limit for each device is 60 minutes. An operator
  can continue before the limit passes.
- A capture matches a client by its MAC address. A randomized MAC address can
  therefore appear as one lost client and one gained client.
- The portal treats a site with no device of the selected type as a valid empty
  capture, not as an error.
- The portal keeps the option defaults of the existing bulk firmware upgrade flow,
  so that a result from the portal matches a result from the menu flow.
- A site lock covers the whole site, not one device type. The cascade crosses
  device types, so a partial lock would let a second operator disturb a running
  cascade.
- The portal reuses the existing parallel execution engine, so that the cloud API
  rate limits stay respected.

### Constraints

- The word `capture` already names the packet capture feature in this codebase.
  The locked decision keeps `capture` as the term for this feature. The naming
  must separate the two concepts clearly.
- The upgrade request body of the cloud API already uses the field name `snapshot`
  for the recovery snapshot flag of a Junos device. This feature MUST NOT use the
  word snapshot for the pre-check and post-check record.
- The existing web portal listens on port 8055. A second application in this
  repository uses port 5173 for its development server, port 8000 for its
  interface layer, and port 80 for its production image. The container also uses
  port 2200. The new portal MUST avoid every one of these ports.
- The requester specified a production web server process for the portal, and a
  dedicated port for it.
- The T-Mobile palette exists today only inside the Mermaid documentation
  contracts. The palette defines 12 colors. The primary color is `#E20074`. The
  status colors are `#00C853` for success, `#FFD600` for warning, and `#FF1744`
  for danger. No web style sheet uses these colors yet. The one existing browser
  application in this repository uses an unrelated blue palette.
- The `.gitignore` file and the `.dockerignore` file exclude any path that
  matches `*tmo*`, `*TMO*`, `*t-mobile*`, or `*T-Mobile*`. The `.gitignore` file
  also excludes `*T-MOBILE*`. A theme file that carries the brand name would stay
  untracked and would not enter the container image. This is a constraint on the
  naming, not a chosen solution.
- The environment holds a live production API token. The portal reads it by
  variable name only and never prints its value.
- The primary database can silently accept no write outside a container. The
  existing export path reports success even when the database write does not
  happen, because it returns the file result only. The portal MUST therefore
  verify the database write on its own and MUST report the true outcome.
- This repository holds two schema version conventions that disagree. One uses an
  integer with a forward migration. The other uses a text value with no
  migration. This feature MUST choose one convention and MUST record the choice.
- The current portal blocks a duplicate operation with an in-memory guard. That
  guard works only because the web server runs one worker process. It does not
  survive a restart. The site lock of this feature MUST work across worker
  processes and MUST survive a restart.
- No existing code reads the power over Ethernet state. That data arrives inside
  the port records that the repository already retrieves, but no code reads those
  fields yet.

### Out of scope

- A run across several sites at the same time. The selection layer must accept a
  site list later, but this release supports one site for each run.
- An upgrade of any device family other than access point, gateway, and switch.
- A change to the firmware upgrade options themselves. The portal presents the
  existing options.
- A scheduled or unattended run. An operator drives every run.
- An automatic revert of a failed upgrade.

### Dependencies

- The cloud API supplies the device list, the device statistics, the device
  events, the wired client list, the wireless client list, the port records, the
  alarms, and the firmware upgrade endpoints.
- An interactive login with an email address and a password already exists in the
  command line tool. It already handles a second authentication factor and it
  already lists the organizations of a managed service provider. The portal
  reuses that capability instead of a new login path.
- The primary database and the companion cache run as containers alongside the
  portal.
- The existing multi-backend export path writes the backup file.
- The existing bulk firmware upgrade capability sends the upgrade job.
- The existing parallel execution engine drives the cloud API calls.
