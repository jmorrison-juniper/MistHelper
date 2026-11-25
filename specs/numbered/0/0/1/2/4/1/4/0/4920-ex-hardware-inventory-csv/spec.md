# Feature Specification: EX Hardware Inventory CSV

**Feature Branch**: `feat/4920-ex-hardware-inventory-csv`

**Created**: 2026-11-24

**Status**: Draft

**Input**: Issue #4920: Add one command that finds the scope of the Mist credential, opens a WebSocket shell on every connected EX switch with bounded concurrency, runs `show chassis hardware detail | display xml | no-more`, and compiles every switch reply into one CSV report. The credential can cover one organization or an MSP. Offer the command as a CLI menu and as an action on the Multi Site tab of the WebSockets page.

## Clarifications

### Session 2026-11-24

- Q: What are the default and the range of the concurrency setting, and what happens when the value is not valid? → A: The variable is `PORTAL_WS_HARDWARE_CONCURRENCY`. The default is 3 and the range is 1 through 5. These match the Multi Site batch limits. A bad value falls back to the default with one warning that names the variable. This is the repository idiom for `PORTAL_WS_*` settings. The preview shows the value in use.
- Q: What is the maximum number of targets? → A: The maximum is 1000 targets in one batch, as in every Multi Site batch. The CLI runs one batch for each organization, so the limit applies to each organization. The portal runs one batch for the whole preview, so the limit applies to the whole run. An MSP with more than 1000 EX switches uses the CLI.
- Q: Which registry category does menu 309 use? → A: `resource_intensive`. The unattended sweeps skip it, and its skip reason says that it opens a shell on every connected EX switch. The typed phrase is the consent gate.
- Q: How does each front end write the report? → A: The CLI writes through `DataExporter.write_with_format_selection` and forces the CSV backend. It uses a unique UTC-stamped name and then checks the file. The exporter does not write atomically. The portal publishes the CSV with its atomic artifact writer.
- Q: Which organization does a credential with several organization grants and no MSP grant use? → A: It uses the configured `org_id` when that organization is among the grants. When no `org_id` is set and the grants name one organization, it uses that one. In every other case it stops and tells the operator to set `org_id`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect one CSV for an organization from the CLI (Priority: P1)

An operator who holds an organization token chooses menu 309. The tool finds that the token covers one organization. It lists the connected EX switches of that organization and shows the counts. The operator types the confirmation phrase. The tool collects the hardware inventory of each switch and writes one CSV file. The file holds every hardware item of every switch.

**Why this priority**: This is the core value. The operator gets the hardware of a whole organization in one file. The operator does no manual shell work and merges no per-switch files.

**Independent Test**: Use a mocked organization with several sites, connected EX switches, one offline EX switch, one non-EX device, and one virtual chassis. Run menu 309. Verify that the CSV holds the items of each connected switch and holds no row for the excluded devices.

**Acceptance Scenarios**:

1. **Given** an organization token and connected EX switches at several sites, **When** the operator runs menu 309 and confirms, **Then** one CSV file holds the hardware items of every connected EX switch.
2. **Given** a device that is offline, has unknown status, or is not an EX switch, **When** the tool builds the target list, **Then** the tool excludes the device and shows a count for each reason.
3. **Given** a virtual chassis, **When** the tool builds the target list, **Then** the tool collects it once and the CSV shows each member chassis as separate items.
4. **Given** one switch returns no valid reply, **When** the run ends, **Then** the CSV holds one outcome row for that switch with the reason, and the other switches are not affected.
5. **Given** the operator types a different phrase, ends the input, or interrupts the prompt, **When** the tool asks for confirmation, **Then** no shell opens and no file is written.
6. **Given** the operator sets a database output backend, **When** the run ends, **Then** the rows reach that backend with natural keys and the CSV file still appears.
7. **Given** the unattended `--test` and `--testinteractive` sweeps, **When** they run, **Then** they skip menu 309 and open no shell.
8. **Given** the menu documentation generators, **When** they run, **Then** menu 309 appears in the generated menu reference with its category.

---

### User Story 2 - Find the scope and run for an MSP (Priority: P1)

An operator signs in with an MSP login. The tool reads the profile and finds an MSP grant. It lists every organization that the login can access and finds the connected EX switches of each one. After one confirmation, it collects all switches and writes one CSV. The CSV tells the organizations apart.

**Why this priority**: A managed service provider needs the same report across all customers. Without scope detection, the operator must run the command once for each organization.

**Independent Test**: Use mocked profiles for an organization token, an MSP login, an MSP login whose organization list returns HTTP 403, and a profile that the tool cannot read. Verify the scope decision and the targets for each profile. For the MSP login, mock three organizations and make one of them fail. Verify that the run finishes the other two.

**Acceptance Scenarios**:

1. **Given** an organization token, **When** the tool reads the profile, **Then** it chooses organization scope and uses only the organization of the credential.
2. **Given** an MSP login whose MSP organization list succeeds, **When** the tool reads the profile, **Then** it chooses MSP scope and targets every organization in the list.
3. **Given** a profile with an MSP grant whose organization list returns HTTP 403, **When** the tool decides the scope, **Then** it says so once and continues in organization scope.
4. **Given** a profile that the tool cannot read, **When** the tool decides the scope, **Then** it stops before any shell opens and states the reason.
5. **Given** one organization of an MSP fails during discovery or collection, **When** the run continues, **Then** the CSV holds outcome rows for that failure and complete data for the other organizations.

---

### User Story 3 - Run the same action from the Multi Site tab (Priority: P1)

An operator opens the WebSockets page, selects the Multi Site tab, and selects **Collect EX hardware inventory**. The operator chooses the new output **One combined CSV report**, reviews the preview, and confirms. When the run ends, the operator downloads the one CSV file.

**Why this priority**: The portal is the second front end. Operators who work in a browser need the same result without a terminal.

**Independent Test**: With mocked services and a fake browser, choose the CSV output, preview, start, and download. Verify that the file matches the CLI report for the same mocked organization. Verify that the XML, JSON, and both outputs still behave as before.

**Acceptance Scenarios**:

1. **Given** the hardware action, **When** the operator opens the output choices, **Then** **One combined CSV report** appears together with XML, JSON, and both.
2. **Given** the CSV choice, **When** the run ends, **Then** the run folder holds the CSV file, the manifest lists it, and the page offers it for download.
3. **Given** the CSV choice and an MSP credential, **When** the operator previews the run, **Then** the preview shows the number of organizations, the number of targets, and the confirmation phrase.
4. **Given** the CSV choice, **When** one target fails, **Then** the CSV holds its outcome row and the page shows the same failure.
5. **Given** the existing XML, JSON, and both choices, **When** the operator runs them, **Then** they produce the same files as before this change.

---

### User Story 4 - Limit concurrency with an environment variable (Priority: P2)

An operator sets one environment variable to choose how many switches the tool opens a shell on at the same time. A small value protects a fragile link. A larger value finishes a large organization sooner.

**Why this priority**: Concurrency changes the run time and the load on the cloud. The operator must control it without a code change.

**Independent Test**: With a fake shell that records the number of open shells, run 12 targets with limits of 1, 3, and the maximum. Verify that the peak number of open shells never exceeds the limit. Verify that an unset variable uses the default and that an invalid value stops the run with a clear message.

**Acceptance Scenarios**:

1. **Given** the variable holds a valid value, **When** the run starts, **Then** the tool never holds more open shells than that value.
2. **Given** the variable is not set, **When** the run starts, **Then** the tool uses the default of 3.
3. **Given** the variable holds text that is not a whole number or a number outside the range 1 through 5, **When** the run starts, **Then** the tool uses the default of 3, logs one warning that names the variable, and shows the value in use in the preview.
4. **Given** the CLI and the portal, **When** the variable is set, **Then** both use the same value for this action.

---

### User Story 5 - Trust the report (Priority: P2)

An operator opens the CSV in a spreadsheet and sends it to a colleague. The report must show every attempted switch, hold no credential, and run no formula.

**Why this priority**: The report leaves the tool. A missing switch, a leaked secret, or an executable cell causes real harm.

**Independent Test**: Run mocked collections with a failing switch, a cancelled run, a reply that holds a credential, and a description that starts with `=`. Verify the outcome rows, the partial marker, the rejection of the credential, and the neutralized cell.

**Acceptance Scenarios**:

1. **Given** a run that the operator cancels, **When** it ends, **Then** the report holds the finished switches and an outcome row for each other target, and the console summary and the portal manifest mark the run as partial.
2. **Given** a switch reply that holds a credential, **When** the tool validates it, **Then** the tool saves no row from that reply and records a failed outcome that names no secret value.
3. **Given** a text value that begins with `=`, `+`, `-`, or `@`, **When** the tool writes it, **Then** a spreadsheet does not read it as a formula.
4. **Given** a write failure, **When** the tool saves the report, **Then** no partial file appears under the final name.

### Edge Cases

- The organization has no EX switch, no connected EX switch, or no site.
- The organization has more sites or devices than one Mist page returns.
- A switch goes offline between the preview and its turn.
- A switch accepts the shell but never shows a stable prompt.
- A switch reply is empty, truncated, malformed, larger than the limit, or holds a credential.
- A virtual chassis has several members, or two switches share one host name.
- The token cannot open a shell on a device (HTTP 403 on shell creation). The live test of 2026-11-24 met this case: an organization token with the read-only role got HTTP 403 for each of 15 connected switches. The tool notes the read-only role at step 1 and gives each switch one `failed` outcome row.
- Mist answers HTTP 429 during discovery or while the tool opens a shell.
- The MSP organization list is denied, or it lists an organization whose devices the token cannot read.
- An MSP has more than 1000 connected EX switches in total. The CLI runs each organization as its own batch. The portal refuses the whole preview.
- The operator ends the input or presses Ctrl+C at the prompt or during the run.
- The output folder is not writable, or the report name already exists.
- Two organizations hold devices with the same host name or the same serial number.
- The CLI and the portal run this action at the same time.

## Requirements *(mandatory)*

### Functional Requirements

Scope:

- **FR-001**: One action MUST start the whole workflow. The action is menu 309 in the CLI or one action on the Multi Site tab.
- **FR-002**: Before any request to a device, the tool MUST read the profile of the credential and decide the scope: organization scope or MSP scope. The tool MUST show the credential type, the scope, the organization count, and the target count before it asks for confirmation.
- **FR-003**: The tool MUST choose MSP scope only when the profile holds an MSP grant and the tool can list the organizations of that grant. In every other case, the tool MUST use organization scope.
- **FR-004**: If the tool cannot read the profile, it MUST stop before it opens any shell and MUST state the reason. A refused profile MUST NOT count as "no access" without a message.
- **FR-005**: In organization scope, the tool MUST use only one organization. That organization is the configured `org_id` when the grants include it. When no `org_id` is set and the grants name one organization, it is that one. In every other case, the tool MUST stop and tell the operator to set `org_id`. In MSP scope, the tool MUST use every organization that the login can access: the organizations of the MSP lists and the direct grants, without repeats.
- **FR-006**: If the MSP organization list is denied with HTTP 403 or fails in any other way, the tool MUST say so once and continue in organization scope.
- **FR-007**: A failure in one organization MUST NOT stop the other organizations. The failure MUST appear in the report. An organization that Mist could not read appears as one outcome row with empty site and switch columns.

Targets:

- **FR-008**: A target MUST be a switch of the EX family whose current Mist running status is connected.
- **FR-009**: The preview MUST exclude offline devices, devices with unknown status, and devices of other families. It MUST show a count for each reason.
- **FR-010**: A virtual chassis MUST be one target. Its member chassis MUST appear as separate hardware items.
- **FR-011**: Discovery MUST read every page. It MUST report an access error or a page error separately from an empty result.
- **FR-012**: When the turn of a target comes, the tool MUST check its status again. A switch that is no longer connected MUST get a skipped outcome and not a command failure.
- **FR-013**: The tool MUST refuse a batch with more than 1000 targets. It MUST NOT cut the list. The CLI runs one batch for each organization, so the limit applies to each organization. The portal runs one batch for the whole preview, so the limit applies to the whole run.
- **FR-042**: When a run has no target, the tool MUST write no report and MUST say so.
- **FR-043**: When every grant of the credential has the read-only role, the CLI MUST print one note at step 1 that Mist can refuse a switch shell for that role. The note MUST NOT block the run. A switch that Mist refuses MUST appear as one `failed` outcome row whose detail points to the log.

Collection:

- **FR-014**: The tool MUST run exactly one command on each target: `show chassis hardware detail | display xml | no-more`. The command is fixed. Operator text MUST NOT reach a device.
- **FR-015**: The tool MUST reuse the verified collector of issue #4769. That collector waits for a stable CLI prompt, bounds the capture, removes only verified terminal framing, validates the XML, and rejects a reply that holds a credential.
- **FR-016**: The tool MUST hold at most N shells open at the same time. N comes from the environment variable `PORTAL_WS_HARDWARE_CONCURRENCY`. The default is 3 and the range is 1 through 5. A value outside the range, or text that is not a whole number, MUST give the default and one warning that names the variable. The preview MUST show the value in use.
- **FR-017**: The CLI and the portal MUST read the same variable for this action.
- **FR-018**: When the operator cancels, the tool MUST stop queued targets, close active shells, keep finished data, and give each unfinished target an outcome row. The tool MUST mark the run as partial in the console summary and in the portal manifest.
- **FR-019**: The tool MUST apply the existing per-target time limits. A target that exceeds a limit MUST get a failed outcome. Its partial text MUST NOT enter the report.

Report:

- **FR-020**: A run MUST write exactly one CSV report with one header row. The file uses UTF-8 text.
- **FR-021**: The report MUST hold one row for each hardware item of each switch that returned a valid reply. A hardware item is the chassis, a module, a sub-module, or a deeper part.
- **FR-022**: The report MUST hold one outcome row for each attempted target that returned no valid reply. The row MUST state the outcome (failed, skipped, or cancelled) and the reason.
- **FR-023**: Every row MUST show the run time in UTC in ISO 8601 form, the scope, the organization, the site, and the switch. The switch data MUST include its identifier and its host name.
- **FR-024**: Every hardware row MUST show its level, its path from the chassis, its element type, and every field that the switch returned for that item. A field that an item lacks stays empty. The report MUST NOT drop a returned field.
- **FR-025**: The columns MUST keep a fixed order. The rows MUST keep a stable order: organization, site, switch, then the order of the reply.
- **FR-026**: The tool MUST write a text value that starts with `=`, `+`, `-`, `@`, a tab, or a carriage return so that a spreadsheet does not read it as a formula.
- **FR-027**: The portal MUST publish the report in one atomic step. No partial file may appear under the final name. The CLI MUST write the report through the standard exporter under a unique UTC-stamped name under `data/`. It MUST then check the file against the rows and MUST remove the file and report an error when the check fails.
- **FR-028**: The CLI MUST send the rows through the configured output backends and MUST force the CSV format for the report file. The rows MUST carry natural keys.
- **FR-041**: The tool MUST keep the report within the saved-output limit of the run. The portal limit is 64 MiB. The tool MUST NOT publish a report that would pass the limit, and it MUST say so.

CLI menu:

- **FR-029**: Menu 309 MUST require the typed phrase `RUN <target_count> TARGETS` before any shell opens. It MUST stop safely on end of input and on interrupt.
- **FR-030**: Menu 309 MUST appear in the operation registry in a category that the `--test` and `--testinteractive` sweeps skip.
- **FR-031**: Menu 309 MUST appear in the generated menu reference and in the operator guide.

Portal:

- **FR-032**: The Multi Site action **Collect EX hardware inventory** MUST offer the output **One combined CSV report**.
- **FR-033**: With that output, the run MUST save the report in its run folder, list it in the manifest, and offer it for download.
- **FR-034**: The portal action MUST use the same scope rules, fixed command, confirmation phrase, and concurrency variable as the menu.
- **FR-035**: Each new control MUST carry a stable test identifier. A browser test MUST cover the new output choice.
- **FR-036**: The existing XML, JSON, and both outputs MUST keep their behavior.

Safety and observability:

- **FR-037**: The tool MUST NOT print, log, or save the token, a WebSocket address, or any other credential.
- **FR-038**: Every meaningful action MUST log before it runs and after it finishes. Log text uses ASCII only.
- **FR-039**: The tool MUST obey the Mist rate limit and MUST use bounded concurrency. On HTTP 429, the tool MUST stop the affected step, report it, and go on. It MUST NOT retry in a tight loop.
- **FR-040**: Live validation MUST use read-only commands and MUST run on one organization only.

### Mist Cloud Transport Requirements

- The plan names each Mist method that the feature uses and states which existing method it reuses.
- The feature adds no new WebSocket transport and sends no direct HTTP request to a Mist REST endpoint.
- Contract tests prove the SDK authentication, the endpoint parity, the failure safety, and the secret redaction of the reused path.

### Key Entities

- **Scope**: The set of organizations that one run covers. It is organization scope or MSP scope.
- **Organization**: One Mist organization with its identifier and its name.
- **Target**: One connected EX switch chosen for collection, with its organization, site, and device identity.
- **Hardware item**: One part of a switch: the chassis, a module, a sub-module, or a deeper part. It carries the fields that the switch returns.
- **Outcome**: The result for one target: collected, failed, skipped, or cancelled, with a reason.
- **Report**: The one CSV file of a run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator starts the whole workflow with one menu choice and one typed phrase and sees no other prompt.
- **SC-002**: In a mocked run, the report holds the hardware items of 100 percent of the connected EX switches that return valid replies. It holds no hardware row for any other device.
- **SC-003**: Every target that a run attempts appears in the report as hardware rows or as one outcome row.
- **SC-004**: In a mocked run with limits of 1, 3, and the maximum, the peak number of open shells never exceeds the limit.
- **SC-005**: In a live run on the test organization, the set of serial numbers in the report equals the set of serial numbers in the saved device replies, and the output holds no credential.
- **SC-006**: In a mocked MSP run with one failing organization, the report holds complete data for every other organization.
- **SC-007**: A spreadsheet opens the report and runs no cell as a formula.
- **SC-008**: The XML, JSON, and both outputs of issue #4769 stay byte-identical to their earlier output for the same input.

## Assumptions

- The feature covers the EX family only, because the working collector of issue #4769 covers only EX. A switch of another family stays out of scope.
- The credential is a Mist API token or an interactive login. The tool does not create or change a credential.
- An MSP report holds the data of several customers. The operator handles the file under the same rules as any other export.
- Mist offers no field that names the token type. The tool decides the scope from the profile grants and from the result of the MSP organization list.
- The CLI reads the organization from the existing `org_id` setting. The portal reads it from its configured organization.
- The tool reuses the collector, the target filter, the fixed command, and the typed confirmation of issue #4769.
- The menu category is `resource_intensive`, because the action opens a shell on many devices. The unattended sweeps skip that category.
- The portal keeps one authenticated Mist session. An MSP run in the portal uses the same session for every organization.
- Live validation uses the one test organization of the configured token. The owner tests MSP scope later.
- Tests use mocked Mist responses and a fake WebSocket. They need no production credential.
- The 1000-target limit, the concurrency default of 3, and the concurrency range of 1 through 5 come from the existing Multi Site batch limits.

## Non-Goals

- Collecting hardware from gateways, access points, or any non-EX device.
- Running any command other than the fixed command.
- Changing a Mist organization, a site, or a device.
- Running a live MSP validation in this change.
- Replacing the XML, JSON, or both outputs of issue #4769.
- Scheduling or repeating the run.
