# Feature Specification: WebSockets tab in the Operations portal

**Feature Branch**: `feat/3551-websocket-tab`

**Created**: 2026-09-29

**Status**: Draft

**Issue**: #3551

**Input**: The user description follows.

```text
Use the Juniper Mist skills to build a new tab for the operations portal for websockets. Build out a page where we can execute and view and/or interact with ALL of the websockets the Mist API provides us the capability to. Use the relevant Juniper skills to accomplish this task.
```

## Background

The Mist API sends live data on WebSocket channels. A client opens one connection, sends a subscribe message for each channel, and then receives each message that Mist publishes on that channel. A second kind of stream starts with a REST command to a device, such as a ping from a switch. The device then sends its output back on a WebSocket channel.

The CLI has 22 WebSocket menus, 102 through 123. The Operations portal hides all of them, because it runs only the `safe` and `interactive_safe` categories. An operator who must watch live data or run a device command from a browser must use the Mist dashboard today.

These sources set the scope:

- The `juniper-mist-automation` skill gives the WebSocket channel list.
- The `juniper-mist-wired`, `juniper-mist-wan`, and `juniper-mist-wireless` skills give the device utilities.
- The `juniper-mist-location` skill gives the location data.
- The `mistapi` package, version 0.64, gives the channel classes and the device utilities.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watch a live channel stream (Priority: P1)

An operator opens the `WebSockets` tab. The operator chooses a channel, such as the device statistics of one site. The operator chooses the site from a list and starts the stream. The page shows each message as it arrives, in a readable form. The operator can pause the view, clear it, filter it, download it, and stop the stream.

**Why this priority**: A live channel is the base of every other story. It has no effect on the network, so it is the safest first value.

**Independent Test**: Start a site device statistics stream against a fake Mist server. Confirm that the page shows the messages, and that each control works.

**Acceptance Scenarios**:

1. **Given** the portal holds a Mist session, **When** the operator opens the `WebSockets` tab, **Then** the page lists every channel in the catalog, grouped by scope.
2. **Given** a site channel and a site, **When** the operator starts the stream, **Then** the card shows the state `subscribed`. The card then shows each message with its time and channel.
3. **Given** a live stream, **When** the operator pauses the view, **Then** no new message appears in the view. The message count continues to increase. When the operator selects resume, the view shows the held messages.
4. **Given** a stream is live, **When** the operator types a filter text, **Then** the view shows only the messages that contain the text.
5. **Given** a stream is live, **When** the operator selects download, **Then** the browser saves the session messages as a JSON Lines file.
6. **Given** a stream is live, **When** the operator stops it, **Then** the server closes the Mist connection and the card shows the state `stopped`.
7. **Given** a location channel, **When** the operator chooses a site, **Then** the page lists the maps of that site. The stream cannot start until the operator chooses a map.

---

### User Story 2 - Run a read-only device utility (Priority: P1)

An operator chooses a site and a device. The page shows only the utilities that the device family supports. The operator runs a ping from a switch to a host. The page shows each output line as the device sends it, and it states when the command finished.

**Why this priority**: Device utilities are the main reason for the CLI WebSocket menus. The read-only utilities change nothing on the device.

**Independent Test**: Run a ping against a fake Mist server that answers the REST command and sends output lines. Confirm that the card shows every line and the final state.

**Acceptance Scenarios**:

1. **Given** the operator chose an access point, **When** the utility list loads, **Then** it shows the utilities for the AP family only.
2. **Given** a host name with a bad format, **When** the operator runs the ping, **Then** the page shows the reason. The server sends no request to Mist.
3. **Given** a valid ping, **When** the device sends output, **Then** the card shows each line in order and ends in the state `finished`.
4. **Given** the device sends no output, **When** the time limit of the utility ends, **Then** the card ends in the state `timed out` and states the reason.

---

### User Story 3 - Run a remote packet capture (Priority: P2)

An operator starts a packet capture on an access point, a switch, a gateway, or a Mist Edge. The operator sets a duration, a packet count, a packet length, and an optional capture filter. The page shows a summary line for each packet. The operator can stop the capture early.

**Why this priority**: A capture proves what a device sends and receives. It changes no configuration, but it uses device resources and it can hold client data, so it follows the channel streams and the read-only utilities.

**Independent Test**: Start a capture against a fake Mist server that sends packet records. Confirm the summaries, the early stop, and the download.

**Acceptance Scenarios**:

1. **Given** a duration above the limit, **When** the operator starts the capture, **Then** the page shows the limit. The server sends no request.
2. **Given** a live capture, **When** a packet record arrives, **Then** the card shows its time, source, destination, protocol, and length. The card shows only the fields that the record holds.
3. **Given** a live capture, **When** the operator stops it early, **Then** the server tells Mist to stop the capture and closes the connection.

---

### User Story 4 - Manage several sessions (Priority: P2)

An operator runs more than one session at the same time. The page shows every live session, also the sessions that another browser tab started. The server enforces a session limit, stops a session that no browser reads, and closes every connection when the portal stops.

**Why this priority**: A WebSocket connection stays open until something closes it. Without limits, forgotten sessions use memory and connections for hours.

**Independent Test**: Start sessions to the limit, start one more, and read the refusal. Stop reading one session and confirm that the server stops it after the idle time.

**Acceptance Scenarios**:

1. **Given** the maximum count of live sessions, **When** an operator starts one more, **Then** the page shows the limit. It also shows the names of the live sessions.
2. **Given** a live session that no browser reads, **When** the idle time ends, **Then** the server stops the session and records the reason.
3. **Given** a live session, **When** the operator reloads the page, **Then** the page lists the session again, and the operator can reopen its view.
4. **Given** live sessions, **When** the portal stops, **Then** the server closes every Mist connection.

---

### User Story 5 - Run a utility that changes device state (Priority: P3)

The portal owner turns on the change flag in the environment file. An operator then runs bounce port, cable test, DHCP release, or clear sessions. The page asks the operator to type the device name before it sends the command.

**Why this priority**: These commands interrupt traffic on a live port or a live client. The portal has no user login, so the commands stay locked until the owner turns them on.

**Independent Test**: With the flag off, confirm that the server refuses each command. With the flag on, confirm that a wrong confirmation is refused and a correct one runs.

**Acceptance Scenarios**:

1. **Given** the change flag is off, **When** the page loads, **Then** each state-changing utility shows a lock and the name of the flag.
2. **Given** the change flag is off, **When** a request for a state-changing utility arrives, **Then** the server refuses it. The server sends nothing to Mist.
3. **Given** the change flag is on, **When** the operator types a text that is not the device name, **Then** the server refuses the command.
4. **Given** the change flag is on and a correct confirmation, **When** the operator runs the command, **Then** the card shows the output. The portal log records the command, the device, and the site.

---

### User Story 6 - Use the remote shell (Priority: P3)

The portal owner turns on the shell flag. An operator opens a remote shell on a switch or an SRX gateway. The operator types the device name to confirm. The operator sends command lines and control keys, reads the output, and closes the shell.

**Why this priority**: The shell gives full command line access to a device. It is the most powerful stream, so it is last and locked by default.

**Independent Test**: With the flag off, confirm the refusal. With the flag on, open a shell against a fake server, send a line, read the output, and close the shell.

**Acceptance Scenarios**:

1. **Given** the shell flag is off, **When** the page loads, **Then** the shell shows a lock and the name of the flag.
2. **Given** the shell flag is on and the confirmation is correct, **When** the operator sends `show version`, **Then** the card shows the device output.
3. **Given** an open shell, **When** the operator selects the interrupt key, **Then** the server sends the interrupt character to the device.
4. **Given** an open shell, **When** the operator closes it, **Then** the server closes the connection and the portal log records the close.

---

### Edge Cases

- The portal holds no Mist session or no organization. The page states the reason and disables every start control.
- A site holds no map, no asset, or no SDK client. The picker states that the list is empty and why.
- Mist refuses a subscription, or the token lacks the privilege. The session ends in the state `failed`, and the card states the reason.
- The Mist connection closes before the operator stops it. The card states the close reason. A channel stream tries to connect again a limited number of times.
- A channel sends more messages than the view can show. The server keeps the newest messages, drops the oldest, and counts the drops. The card shows the count.
- One message is very large. The server keeps a shortened copy and marks it as shortened.
- The operator closes the browser tab. The server stops the session after the idle time.
- The operator stops a session while it still connects. The server cancels the connection and ends the session in the state `stopped`.
- A request names an unknown catalog key, a raw channel path, or an identifier with a bad format. The server refuses the request and sends nothing to Mist.
- Two operators start the same channel. The server treats them as two sessions, and both count toward the limit.
- The device family of a device is unknown. The page offers no utility and states why.

## Requirements *(mandatory)*

### Functional Requirements

**Page and catalog**

- **FR-001**: The portal MUST add a `WebSockets` item to the navigation bar. The item MUST open the WebSockets page.
- **FR-002**: The page MUST list every channel in the catalog. It MUST group the channels by scope: organization, site, location, and diagnostics. Each entry MUST show a plain description and the identifiers that it needs.
- **FR-003**: The page MUST list every device utility that sends output on a WebSocket. The device families are AP, EX switch, SRX gateway, SSR router, and Mist Edge. Each entry MUST show its parameters and its safety class.
- **FR-004**: The server MUST hold the catalog in one place. The page MUST read the catalog from the server and MUST NOT hold a channel path of its own.

**Channel streams**

- **FR-005**: An operator MUST be able to start a channel stream from a catalog entry and the identifiers that it needs. The page MUST fill the pickers for sites, maps, devices, assets, and SDK clients from the Mist API.
- **FR-006**: The server MUST build each channel path from a catalog key and checked identifiers. The server MUST refuse a raw path, an unknown key, and an identifier with a bad format.
- **FR-007**: The server MUST open each Mist connection with the portal credentials and the WebSocket host of the organization cloud region. The browser MUST NOT receive the API token or a Mist WebSocket address.
- **FR-008**: The page MUST show each message no later than 2 seconds after the server receives it. The page MUST decode the nested data string of a message into readable JSON, and it MUST show the receive time and the channel.
- **FR-009**: An operator MUST be able to pause, resume, clear, and filter the view. The operator MUST also be able to download the messages as JSON Lines and stop the session.
- **FR-010**: Each session card MUST show the session state, the message count, the message rate, and the count of dropped messages.

**Device utilities**

- **FR-011**: An operator MUST be able to choose a device at a site. The page MUST offer only the utilities that the device family supports.
- **FR-012**: The server MUST check every utility parameter before it sends a request to Mist. The checks cover host names and addresses, count ranges, port names, MAC addresses, network names, and fixed choices.
- **FR-013**: The page MUST show each output line in order as it arrives. It MUST state when the command finished, failed, or timed out.
- **FR-014**: A utility session MUST end when the device finishes. It MUST also end when no output arrives for the time limit, or at the maximum duration.

**Packet captures**

- **FR-015**: An operator MUST be able to start a remote capture with a duration, a packet count, a packet length, and an optional capture filter. The server MUST enforce a fixed range for each number.
- **FR-016**: The page MUST show a summary of each packet record. When the operator stops a capture early, the server MUST tell Mist to stop the capture.

**State-changing utilities and the remote shell**

- **FR-017**: The utilities that change device state MUST stay locked while the change flag is off. The flag is off by default. While the flag is on, each run MUST need the operator to type the device name.
- **FR-018**: The remote shell MUST stay locked while the shell flag is off. The flag is off by default. While the flag is on, the shell MUST need the operator to type the device name. The operator MUST be able to send a line, send the interrupt, tab, space, and `q` keys, read the output, and close the shell.
- **FR-019**: The portal log MUST record each run of a state-changing utility and each shell open and close. Each record MUST name the device and the site. The log MUST NOT record a secret or the text that the operator sends to a shell.

**Limits and life cycle**

- **FR-020**: The server MUST limit the count of live sessions. The default limit is 5. When the limit is reached, the server MUST refuse a new session and state the reason.
- **FR-021**: The server MUST stop a session that no browser read for the idle time. The default idle time is 120 seconds.
- **FR-022**: The server MUST limit the memory of each session. The default limit is 500 messages or 8 MB, whichever comes first. The server MUST drop the oldest messages first and count the drops.
- **FR-023**: The server MUST stop a channel stream at its maximum life. The default is 30 minutes. The card MUST state why the session stopped.
- **FR-024**: The page MUST list the live sessions after a reload, so that an operator can reopen a session.
- **FR-025**: The server MUST close every Mist connection when the portal stops.
- **FR-026**: The page MUST read new messages with short requests. No page request may hold a server thread for more than 5 seconds.

**Errors and text**

- **FR-027**: When Mist refuses a subscription or closes a connection, the card MUST state the reason in plain words. The session MUST end in the state `failed`.
- **FR-028**: When the portal holds no Mist session or no organization, the page MUST state the reason and MUST disable every start control.
- **FR-029**: All page text, error text, and log text MUST follow Simplified Technical English. Log text MUST use ASCII characters only.
- **FR-030**: Every control on the page MUST carry a stable test identifier.

### Key Entities

- **Channel definition**: One catalog entry for a subscribe channel. It holds a key, a scope, a name, a description, a path pattern, and the identifiers that the path needs.
- **Utility definition**: One catalog entry for a device utility. It holds a key, the device families that support it, a name, and a description. It also holds the parameters with their checks, a safety class, and the time limits. The safety class is read, capture, change, or shell.
- **Stream session**: One live connection that an operator started. It holds an identifier, the catalog key, the target identifiers, a state, the start time, the last read time, the counters, and the message buffer.
- **Stream message**: One message in a session buffer. It holds a sequence number, the receive time, the channel, the decoded content, the size, and a mark when the server shortened it.
- **Picker option**: One row in a picker list, such as a site, a map, a device, an asset, or an SDK client. It holds an identifier, a label, and for a device, its family.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator starts a site channel stream with 4 selections or fewer after the page opens.
- **SC-002**: The page shows a message no later than 2 seconds after the server receives it, for 95 percent of the messages.
- **SC-003**: The catalog holds 100 percent of the 18 channels and 100 percent of the streaming device utilities in `mistapi` 0.64. An automated test proves the count.
- **SC-004**: With 5 live sessions at 10 messages each second, other portal pages still answer in less than 1 second for 95 percent of the requests.
- **SC-005**: With 5 full sessions, the session buffers use 40 MB or less in total.
- **SC-006**: No response to the page holds the API token or a Mist WebSocket address. An automated test proves it.
- **SC-007**: After a browser tab closes, no Mist connection of that tab stays open for more than 3 minutes.
- **SC-008**: No state-changing utility and no shell runs while its flag is off. An automated test proves it.

## Assumptions

- The portal keeps its current access control. It serves private networks only and has no user login. For this reason, the state-changing utilities and the remote shell are locked by default.
- The portal API token has the privilege for the streams. A token without the privilege gets a refusal, and the page shows it.
- A channel sends data only when the organization uses the feature. For example, the location channels need maps and BLE, and the Mist Edge channels need a Mist Edge. An empty stream is a valid result, and the card states that no message arrived yet.
- The device commands that send no WebSocket output are out of scope. These are clear MAC table, clear learned MAC, clear BPDU error, clear 802.1X sessions, and clear policy hit count. The Operations tab is the place for REST-only commands.
- The CLI WebSocket menus 102 through 123 stay the same.
- The container runs the portal in one process, so one process holds every session.
- The portal uses the `mistapi` package for the Mist connection, the regional host, and the device utilities.
