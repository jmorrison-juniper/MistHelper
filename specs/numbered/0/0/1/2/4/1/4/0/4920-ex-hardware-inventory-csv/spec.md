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

### User Story 6 - Get one master XML file that other programs can read (Priority: P1)

A customer system reads the hardware of every EX switch. The system wants one XML file, not one file for each switch. The file must meet the XML standard in every detail, so that any conforming parser reads it with no repair.

**Why this priority**: The customer added this requirement on 2026-11-25. A file that one parser reads and another parser refuses causes silent data loss in the customer system.

**Independent Test**: Run mocked collections with replies that hold namespaces, special characters, and hostile names. Check each file with the checks of the tool, and with parsers that the tool does not use.

**Acceptance Scenarios**:

1. **Given** a run in which at least one switch collected, **When** the run ends, **Then** the CLI writes one XML file next to the CSV report, and the portal publishes one XML file when the operator chose that output.
2. **Given** the file, **When** any conforming XML 1.0 parser with namespace support reads it, **Then** the parser reports no error.
3. **Given** a switch reply, **When** the tool puts it in the file, **Then** the file holds the same elements, attributes, text, namespace addresses, and prefixes as the reply.
4. **Given** a switch with no valid reply, and an organization that Mist could not read, **When** the tool writes the file, **Then** each one appears as an element with its status and its reason, so no target is missing.
5. **Given** a check that fails, **When** the tool is about to publish the file, **Then** it publishes no XML file, says so, and keeps the CSV report and the saved replies.

### Edge Cases

- The organization has no EX switch, no connected EX switch, or no site.
- The organization has more sites or devices than one Mist page returns.
- A switch goes offline between the preview and its turn.
- A switch accepts the shell but never shows a stable prompt.
- A switch reply is empty, truncated, malformed, larger than the limit, or holds a credential.
- A virtual chassis has several members, or two switches share one host name.
- The token cannot open a shell on a device (HTTP 403 on shell creation). The live test of 2026-11-24 met this case: an organization token with the read-only role got HTTP 403 for each of 15 connected switches. The tool notes the read-only role at step 1 and gives each switch one `failed` outcome row.
- A sync client or a virus scanner holds the manifest of the run folder for a moment. The second live test of 2026-11-24 met this case: with an admin-role token, 14 of 15 switches collected, and one manifest replace got a Windows permission error. That error failed the whole batch record, so the last switch was refused. The store waits and tries again (FR-044).
- Mist answers HTTP 429 during discovery or while the tool opens a shell.
- The MSP organization list is denied, or it lists an organization whose devices the token cannot read.
- An MSP has more than 1000 connected EX switches in total. The CLI runs each organization as its own batch. The portal refuses the whole preview.
- The operator ends the input or presses Ctrl+C at the prompt or during the run.
- The output folder is not writable, or the report name already exists.
- Two organizations hold devices with the same host name or the same serial number.
- The CLI and the portal run this action at the same time.
- The operator wants to read the report in the browser. The live test of 2026-11-25 showed that the portal offered only a download. The page shows a table with a filter and page buttons (FR-049 through FR-053). The report can be over the preview limit, or a cell can hold markup.
- A reply holds a DTD, an entity declaration, or more than 100 levels of nesting (FR-062).
- A name from Mist holds a control character, a markup character, or a character that XML 1.0 forbids (FR-060).
- Two replies bind the same prefix to different namespace addresses, a reply root declares a default namespace, or a reply declares `xmlns=""`.
- A run has only failed targets, or the master XML would pass the size limit (FR-064).

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
- **FR-044**: When a file replace in the run folder gets a permission error, the store MUST try the replace again, up to five tries in total, with waits of 50, 100, 200, and 400 milliseconds. Any other error MUST fail at once. When a save still fails, the report detail MUST say that the reply could not be saved, and MUST NOT call the reply invalid. Issue #4926.
- **FR-045**: The Multi Site page MUST keep the Targets card when the hardware action is on. The default MUST stay all sites, and the request for all sites MUST carry no site field. A subset MUST carry `sites: {"mode": "selected", "ids": [...]}`. The server MUST refuse an empty subset, a repeated site, an unknown site, an identifier that is not a UUID, all-site mode with identifiers, and any other shape. The preview MUST give the number of chosen sites and no site name. Issue #4927.
- **FR-046**: The review card MUST list the four steps, MUST name the confirmation word in the label and in the placeholder of the box, and MUST give the one next action above **Start batch**. A disabled **Start batch** button MUST give the same sentence as its title. A changed choice after a preview MUST clear the preview and the word. Issue #4928.
- **FR-047**: `python MistHelper.py --web-portal` MUST resolve the organization before it builds the portal, in the same order as the interactive mode, and MUST NOT ask when the context already holds one. Issue #4929.
- **FR-048**: Each Mist list call of this feature that accepts a `limit` MUST pass `limit=1000`. The MSP organization list takes no limit, and the tool follows its pages.
- **FR-049**: When a run publishes the combined CSV report, the Multi Site page MUST show the report as a table in the batch progress card, and MUST keep the **Download CSV report** button. The table MUST stay hidden for the other output formats, while the report is not ready, and when the output failed. Issue #4931.
- **FR-050**: The route `GET /api/websockets/batches/<id>/csv-preview` MUST return the column names and one page of rows. It MUST read the report through the same checked read as the download, so it gives the same refusals. It MUST accept only the fields `offset`, `limit`, and `q`. The offset is a whole number from 0. The limit is a whole number from 1, the default is 1000, and a larger value becomes 1000. The text `q` has 100 characters or fewer.
- **FR-051**: The filter `q` MUST be a plain, case-insensitive text search over every cell of the whole report, and the server MUST NOT build a pattern from it. The answer MUST give `total` (the data rows) and `matched` (the rows that match), so the page can say which rows it shows.
- **FR-052**: The preview MUST bound its work. A cell is cut at 1000 characters, and the answer gives the number of cut cells. A report over 16 MiB gets the refusal `too_large` with a message that points to the download. A damaged report (not UTF-8, empty, or with a row of the wrong width) gets the refusal `output_failed`.
- **FR-053**: The page MUST set every cell, every column name, and every message as plain text. A cell that holds markup MUST show as text.
- **FR-054**: The page MUST NOT open a Multi Site batch parent as a terminal, even when the parent keeps the output name `terminal` from its shell action. It MUST read the messages of the parent like those of any other session, and it MUST send no terminal read or resize request for it. Issue #4932.

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

Master XML:

- **FR-055**: A run that has at least one target result MUST be able to write one master XML file. The CLI MUST write it on every run, next to the CSV report, with the same UTC stamp and the extension `.xml`. The portal MUST offer it through the output choices `master-xml` (one combined XML file) and `csv-master-xml` (the combined CSV report and the combined XML file). Issue #4933.
- **FR-056**: The file MUST be one XML 1.0 document in UTF-8 with the declaration `<?xml version="1.0" encoding="UTF-8"?>` and no byte order mark. It MUST be well-formed and MUST follow Namespaces in XML 1.0. It MUST hold no DTD, no entity declaration, and no external reference.
- **FR-057**: The file MUST use the structure of `design/contracts/report-xml.md`: the root element `hardware-inventory`, then the elements `organization`, `site`, and `device`, in the namespace `urn:misthelper:ex-hardware-inventory:1`. The root MUST carry the run time in UTC, the scope, the fixed command, and the counts.
- **FR-058**: A collected device MUST hold exactly one child element, which is the reply of the switch. The reply MUST keep its elements, attributes, text, namespace addresses, and prefixes. The tool MAY drop the XML declaration, the comments, and the processing instructions of the reply.
- **FR-059**: A device with no valid reply MUST be an element with the status `failed`, `skipped`, or `cancelled`, a reason code, and a plain sentence. An organization that Mist could not read MUST be an element with the status `failed` and no site. The statuses MUST equal the statuses of the CSV report for the same run.
- **FR-060**: The tool MUST write the identifiers, the names, and the reasons of its own elements so that the file stays valid. It MUST escape each markup character. It MUST replace each character that XML 1.0 forbids, and each character that XML 1.0 discourages, with U+FFFD.
- **FR-061**: The tool MUST check the final bytes before it publishes them: strict UTF-8, the character rules of XML 1.0, a strict parse that knows namespaces and refuses a DTD, the declared structure, the counts on the root, and the equality of each embedded reply with its source. The equality check compares the events of the parser: elements, attributes, namespaces, prefixes, and text. A file that fails a check MUST NOT be published.
- **FR-062**: The tool MUST refuse a reply that holds a DTD, an entity declaration, or more than 100 levels of nesting. The device MUST then show the status `failed` and the detail `The saved reply could not be read.`
- **FR-063**: The portal MUST publish the master XML in the same atomic step as the CSV report when the operator chose both. The CLI MUST write the file under a unique UTC-stamped name under `data/`, read it back, check the bytes that it read, and remove the file when a check fails.
- **FR-064**: The tool MUST keep the master XML within the saved-output limit of the run (64 MiB). It MUST NOT publish a file over the limit, and it MUST say so.
- **FR-065**: The portal MUST list `hardware/inventory.xml` in the manifest, put it in the archive, and offer `GET /api/websockets/batches/<id>/download?format=xml` with the media type `application/xml`. The download name is `ExHardwareInventory_<UTC>.xml`.
- **FR-066**: The page MUST show a **Download combined XML** link when the output holds the XML and is ready. The CSV link and the table MUST keep their rules for the outputs that hold the CSV. Each new control MUST carry a stable test identifier, and a browser test MUST cover it.
- **FR-067**: The repository MUST hold a schema for the wrapper elements, `documentation/schemas/ex-hardware-inventory.xsd`, and a reference page for the format, `documentation/ex-hardware-master-xml.md`. The schema MUST accept each file that the tool writes.
- **FR-068**: The XML, JSON, both, and CSV outputs of the portal MUST keep their behavior and their bytes.
- **FR-069**: The title of menu 309 MUST name both outputs, and the generated menu pages MUST show the title.

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
- **Master XML**: The one XML file of a run. It holds the reply of each collected switch, and one element for each other target.

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
- **SC-009**: In a mocked run with every kind of reply that the tests hold (plain, namespaced, escaped, large, and hostile), 100 percent of the files that the tool publishes pass every check of FR-061.
- **SC-010**: Readers that the tool does not use read each file of the live runs with no error: the SAX and DOM readers of the Python standard library, and the .NET reader of Windows. The .NET reader also validates the file against the schema.
- **SC-011**: In a live run on the test organization, the file holds the reply of each collected switch, and the set of serial numbers in the file equals the set of serial numbers in the saved replies.
- **SC-012**: A file that a fault injection makes invalid is never published. Each injected fault is caught by a check.

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
- The customer reads the master XML with programs that follow XML 1.0 and Namespaces in XML 1.0. No program needs a DTD. The schema serves the programs that validate.
- The master XML keeps the vocabulary of Junos unchanged. It adds only the wrapper elements of this feature.

## Non-Goals

- Collecting hardware from gateways, access points, or any non-EX device.
- Running any command other than the fixed command.
- Changing a Mist organization, a site, or a device.
- Running a live MSP validation in this change.
- Replacing the XML, JSON, or both outputs of issue #4769.
- Scheduling or repeating the run.
- Converting the Junos XML to another vocabulary, or merging the JSON replies into the master XML.
- Validating the Junos elements against a Junos schema. No public schema covers each release.
