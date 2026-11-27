# Feature Specification: EX Transceiver Master Report

**Feature Branch**: `feat/4773-ex-transceiver-master-report`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4773: Add one master transceiver report after EX hardware collection. Preserve every independent native XML and JSON file. Add an optional portal checkbox and a CLI menu operation for the master CSV. Support XML-only, JSON-only, and both-format collection without duplicate rows.

## Clarifications

### Session 2026-11-26

- Q: Which CLI menu number holds the new operation? → A: Menu 310. Menu 310 is free on `main`, and no open pull request uses it.
- Q: Does the new report change menu 309? → A: No. Menu 309 keeps its native files, its hardware CSV report, and its master XML. Menu 310 runs the same collection and writes only the transceiver master CSV.
- Q: What is a transceiver item? → A: A reply item whose name is `Xcvr`, one space, and an identifier. The element type does not decide the match, because the live element type is not verified.
- Q: How does the report read the module type? → A: It reads the `description` text, trims it, and collapses repeated spaces. It uses no lookup table, because a lookup table would invent names.
- Q: Which source does a switch use when both XML and JSON replies are valid? → A: The XML reply. The JSON reply stays as a native file and adds no rows.
- Q: Does a valid JSON reply replace a failed XML reply in a both-format run? → A: No. The switch gets one outcome row that names the failed format. The JSON file stays as a native file.
- Q: What does the report write when a collected switch holds no transceiver item? → A: One no-transceiver row for that switch. A silent absence would hide a collected switch.
- Q: Is the portal checkbox on by default? → A: No. With the checkbox off, every existing output stays unchanged.
- Q: Where does the portal write the file? → A: `hardware/transceiver-master.csv` in the run folder. The file joins the manifest and the ZIP archive, and the batch download route serves it.
- Q: Where does the CLI write the file? → A: `data/ExTransceiverMaster_<UTC time>.csv`. The name never overwrites an earlier file.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Write one transceiver master CSV from the CLI (Priority: P1)

An operator chooses menu 310 with an organization token. The menu finds the connected EX switches and shows the counts. The operator types the confirmation phrase. The menu collects each switch and writes one CSV file. The file holds one row for each transceiver.

**Why this priority**: The CLI is the main path for a junior engineer who needs one file for a whole organization. The file replaces a manual search of each switch.

**Independent Test**: Use a mocked organization with connected EX switches, one offline switch, one non-EX device, and one virtual chassis. Run menu 310 and confirm. The CSV holds the transceiver rows of each connected switch and no row for an excluded device.

**Acceptance Scenarios**:

1. **Given** an organization token and connected EX switches, **When** the operator confirms menu 310, **Then** one CSV file holds one row per transceiver.
2. **Given** an offline switch and a non-EX device, **When** the menu builds targets, **Then** the CSV omits both and the menu counts each reason.
3. **Given** a virtual chassis, **When** the run ends, **Then** each member transceiver has its own row and its own module location.
4. **Given** the operator types a wrong phrase, ends input, or presses Ctrl+C, **When** the prompt ends, **Then** no shell opens and no file is written.

---

### User Story 2 - Get the master CSV from the portal (Priority: P1)

An operator opens the Multi Site action and selects the EX hardware action. The operator selects the optional transceiver master CSV checkbox. The preview shows the choice. After the run, the operator downloads the CSV from the run results. The checkbox is off by default.

**Why this priority**: The portal is the second front end for the operations center. Its CSV must match the CLI output for the same switch data.

**Independent Test**: Use fake batch services with one completed switch. Change the checkbox and confirm that the preview becomes invalid. Run with the checkbox on and confirm the file, the manifest entry, the ZIP member, and the download.

**Acceptance Scenarios**:

1. **Given** the EX hardware action is selected, **When** the page shows its choices, **Then** the transceiver checkbox is unchecked and has test identifier `ws-batch-hardware-transceiver-csv`.
2. **Given** a preview exists, **When** the operator changes the checkbox, **Then** the preview becomes invalid, and start stays disabled until a new preview exists.
3. **Given** a completed run with the checkbox on, **When** the operator requests the transceiver download, **Then** the response holds the CSV file of that run.

---

### User Story 3 - Collect XML, JSON, or both without duplicate rows (Priority: P1)

An operator chooses XML, JSON, or both. The native files stay separate for each format. The transceiver rows match for the same switch data, whichever format the operator chose. A both-format run uses the XML reply for rows and adds no duplicate rows from JSON.

**Why this priority**: Equal rows across formats protect the report. A duplicate row would double the count of transceivers.

**Independent Test**: Use one synthetic switch in three runs: XML only, JSON only, and both. Compare the transceiver rows. Ignore the source column and the run time.

**Acceptance Scenarios**:

1. **Given** the same switch data in XML and in JSON, **When** the report compiles each format, **Then** the transceiver rows are equal.
2. **Given** a switch with valid XML and JSON replies, **When** the report compiles, **Then** the rows come from XML only.
3. **Given** a both-format run with an invalid XML reply, **When** the report compiles, **Then** the switch gets one outcome row naming the failed format.

---

### User Story 4 - Keep partial results and spreadsheet safety visible (Priority: P2)

An operator runs an organization in which one switch fails and one organization cannot be read. The report keeps every attempted switch. Each row states its status. The summary shows the counts. A text value that starts with a formula character cannot run as a formula in a spreadsheet.

**Why this priority**: A missing row hides a fault. A spreadsheet formula can run device text.

**Independent Test**: Use mocked results with one collected switch, one failed switch, one skipped switch, one canceled switch, and one unread organization. Confirm one outcome row for each unsuccessful target and one row for the unread organization. Confirm that a description starting with an equals sign gets an apostrophe.

**Acceptance Scenarios**:

1. **Given** a switch that did not collect, **When** the report compiles, **Then** one outcome row shows its status and a plain reason.
2. **Given** an organization that Mist could not read, **When** the report compiles, **Then** one outcome row shows the organization with empty switch columns.
3. **Given** a description that starts with a formula character, **When** the report writes the cell, **Then** the cell starts with an apostrophe.

### Edge Cases

- A transceiver item has no description, no part number, and no serial number. The row keeps empty cells and invents no value.
- Two switches share one hostname. The rows keep separate device identifiers.
- Two transceiver items under one device share one name. The existing numbered suffix keeps the item paths distinct.
- A reply is truncated, malformed, or holds a credential. The switch gets one failed outcome row with the existing plain reason.
- A JSON reply holds a non-finite number. The reply fails, and no row is invented.
- No connected EX switch exists. No file is written, and the menu prints the existing sentence.
- The operator presses Ctrl+C after some switches collect. The collected switches keep their rows, and the other switches get canceled outcome rows.
- The report would exceed the 64 MiB limit. No file is written, and the menu says so in one sentence.
- A description holds non-ASCII text. The CSV keeps UTF-8 text. Log lines stay ASCII.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST add CLI menu 310 that collects EX switch transceivers and writes one transceiver master CSV.
- **FR-002**: The Multi Site hardware action MUST offer an optional transceiver master CSV checkbox. The checkbox MUST be off by default.
- **FR-003**: Both front ends MUST reuse the existing fixed read-only commands. The feature MUST NOT add or change a device command.
- **FR-004**: Both front ends MUST keep the typed confirmation, the connected-only filter, and the offline exclusion of menu 309.
- **FR-005**: The CLI MUST let the operator choose XML, JSON, or both before confirmation. The confirmation MUST show each command that runs.
- **FR-006**: The feature MUST keep each native file unchanged. It MUST NOT rewrite, merge, or delete a native file.
- **FR-007**: The report MUST write one transceiver row for each transceiver item of each collected switch.
- **FR-008**: Each transceiver row MUST hold the switch hostname, module type, serial number, model number, part number, and module location when present.
- **FR-009**: Rows MUST use the natural key org_id, device_id, and item_path. Duplicate hostnames and virtual-chassis members MUST stay distinct.
- **FR-010**: The report MUST NOT invent a value. An absent source value MUST stay an empty cell.
- **FR-011**: A switch with a valid XML reply MUST use that reply for rows. A JSON reply for the same switch MUST add no rows.
- **FR-012**: A switch with only a valid JSON reply MUST produce the same transceiver rows as the same data in XML.
- **FR-013**: A collected switch with no transceiver item MUST produce one no-transceiver row.
- **FR-014**: A target that did not collect MUST produce one outcome row with its status and a plain reason.
- **FR-015**: An organization that Mist could not read MUST produce one outcome row with empty switch columns.
- **FR-016**: The CLI summary and the file MUST show partial results with counts for collected, failed, skipped, and canceled targets.
- **FR-017**: Every text cell MUST pass the spreadsheet formula guard before the file is written.
- **FR-018**: The file MUST be UTF-8 CSV with one header row. It MUST pass the file check before publication.
- **FR-019**: The CLI MUST write the file under the data folder with a UTC time in its name. It MUST NOT overwrite an earlier file.
- **FR-020**: The portal MUST publish the file in the run folder with the other outputs. The file MUST appear in the manifest and in the ZIP archive.
- **FR-021**: The portal MUST bind the checkbox value to each preview. A change to the checkbox MUST invalidate the preview.
- **FR-022**: The checkbox MUST carry the stable test identifier `ws-batch-hardware-transceiver-csv`.
- **FR-023**: The portal MUST serve the file through the batch download route with the format value `transceiver-csv`.
- **FR-024**: Each new action MUST log an info line before it and a debug line after it. Log lines MUST be ASCII and MUST hold no secret.
- **FR-025**: Product output MUST stay under the data folder. Failure screenshots and traces MUST stay under the test-artifacts folder.
- **FR-026**: Each CLI prompt MUST treat end of input and an interrupt as a cancel. A cancel MUST open no shell and write no file.
- **FR-027**: Menu 310 MUST register with category `resource_intensive`, destructive set to false, and supports_fast set to false.
- **FR-028**: The primary key strategy `ExTransceiverMaster` MUST exist before menu 310 runs.
- **FR-029**: Menu 309 output MUST stay unchanged, including the native files, the hardware CSV report, and the master XML.
- **FR-030**: With the checkbox off, the portal MUST keep every existing output unchanged. No existing default may change.
- **FR-031**: Test fixtures and examples MUST use synthetic values only. No real device name, serial number, token, or address may appear.

### Key Entities *(include if feature involves data)*

- **Transceiver row**: One installed transceiver of one collected switch. Its natural key is org_id, device_id, and item_path.
- **Outcome row**: One target or one unread organization that produced no valid reply. It holds a collection status and a plain reason.
- **No-transceiver row**: One collected switch that holds no transceiver item.
- **Native file**: One saved XML or JSON reply. The report reads a native file and never changes it.
- **Run folder**: The portal folder of one run under `data/websocket-streams/`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature names these existing mistapi REST methods: `getSelf`, `listMspOrgs`, `listOrgSites`, `listSiteDevices`, and `listSiteDevicesStats`. It adds no REST call.
- The shell path uses the existing owned WebSocket transport for `ex.createShellSession`. The utility trigger builds the matching path `/api/v1/sites/{site_id}/devices/{device_id}/shell`. This feature does not change that transport.
- Contract evidence stays with the existing tests in `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py` and `tests/guardrails/test_websocket_transport_constitution.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a mocked run with the same data in XML, JSON, and both formats, transceiver rows match in every column except source_format and report_run_utc.
- **SC-002**: In a mocked run with duplicate hostnames, duplicate serial numbers, and one virtual chassis, each physical transceiver produces exactly one row.
- **SC-003**: In a mocked run, every attempted target and every unread organization appears in the file with at least one row.
- **SC-004**: The formula guard tests find zero text cells that start with an unguarded formula character.
- **SC-005**: With the portal checkbox off, a mocked run writes no transceiver file. Each other output matches the earlier release for the same input and a fixed run time.
- **SC-006**: The browser test confirms the stable identifier, the unchecked default, and the preview invalidation after a checkbox change.
- **SC-007**: In an authorized read-only live run on the lab organization, CSV serial numbers equal the serial numbers in the saved replies.
- **SC-008**: Every local gate in the T-LOCAL-GATES task of `tasks.md` passes with its expected result.

## Assumptions

- Live transceiver items appear as `Xcvr` items in the same chassis tree that the synthetic fixtures model. Live confirmation is pending, as listed in `design/research.md`.
- The fixed `detail` option of the existing command works on the lab software release. The risk is recorded in `design/research.md`.
- The existing limits apply: 1000 targets per batch, 1 MiB per saved reply, and 64 MiB of output per run.
- The status value `connected` marks a switch that can run. The existing filter uses that value.
- The CSV headers use the names in `design/contracts/transceiver-csv.md`.

## Out of Scope

- A lookup table that maps part numbers to marketing names.
- A preview table for the transceiver CSV in the portal. The operator downloads the file.
- Any change to the menu 309 output, the master XML, or the SFP merge menu 100.
- Any change to the owned WebSocket transport or to the shell contract.
- A browser sign-in and a narrower shell unlock, which issue #4939 tracks.
- Repair of the two test-quality findings that issue #4783 tracks.
- Any change to `src/operations/exporting/export/data_exporter.py`, which open draft pull request #4813 changes.
