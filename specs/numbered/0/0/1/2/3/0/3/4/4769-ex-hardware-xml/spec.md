# Feature Specification: EX Hardware XML Collection

**Feature Branch**: `feat/4769-ex-hardware-xml`

**Created**: 2026-11-10

**Status**: Draft

**Input**: Issue #4769: Add a dedicated Operations portal WebSockets action that runs the fixed read-only Junos command `show chassis hardware detail | display xml | no-more` on every EX switch in the configured organization and saves XML, JSON, or both formats in unique files per switch hostname.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect Hardware Inventory Across an Organization (Priority: P1)

An Operations portal user selects the dedicated EX hardware inventory action, chooses XML, JSON, or both formats, and reviews which eligible EX switches will be included. The user starts the run and obtains the selected output for every responding EX switch, plus a clear per-switch outcome for anything that could not be collected.

**Why this priority**: The primary value is to gather consistent chassis hardware inventory from all eligible EX switches without manually entering commands or saving each device response.

**Independent Test**: With a mocked organization containing multiple sites, EX switches, non-EX devices, and an unavailable switch, start the dedicated action in each output mode and verify the preview and final downloadable results include every eligible EX switch, exclude non-EX devices, and retain the unavailable switch's failure outcome.

**Acceptance Scenarios**:

1. **Given** an organization with eligible EX switches across multiple sites, **When** the user previews and starts the dedicated action, **Then** the preview spans every site and the run attempts each unique eligible EX target.
2. **Given** an eligible switch returns a complete Junos XML reply and the user chooses XML, **When** its collection completes, **Then** the archive contains one separate `.xml` file with the complete, well-formed chassis hardware response.
3. **Given** the organization contains non-EX devices or a virtual chassis whose member records repeat a physical target, **When** the preview is built, **Then** non-EX devices are excluded and each virtual chassis logical device is targeted only once.
4. **Given** the user chooses JSON, **When** collection completes, **Then** the switch runs `show chassis hardware detail | display json | no-more` once.
5. **Given** the user chooses both formats, **When** collection completes, **Then** the switch runs the XML command, then the native JSON command.

### Acceptance correction for issue #4770

- XML and JSON are separate native Junos responses. The server must not convert XML into JSON.
- XML selection runs only `show chassis hardware detail | display xml | no-more`.
- JSON selection runs only `show chassis hardware detail | display json | no-more`.
- BOTH runs each command once, in XML then JSON order, on each currently online EX switch.
- Current Mist running statistics determine device status. Preview excludes offline and unknown devices with separate counts.
- Dispatch checks status again. A newly offline or unknown device receives a skipped outcome, not a command failure.
- The collector waits for a verified CLI prompt. A banner or partial prompt cannot release a command.
- Each command has a separate capture boundary and must return to the same prompt before the next command.
- The parser removes only verified command echo, prompt, and Junos routing-engine status framing.
- Native JSON must contain a nonempty `chassis-inventory` array. The saved JSON preserves the native response text.
- Each format has a separate outcome. A failed format must not remove another format's successful file.
- A partial target cannot report complete success. The manifest retains its successful files and each format failure.
- Hardware files and the manifest remain under the unique run directory after session expiry and process restart.
- The preview displays the exact typed confirmation phrase.

The authorized live probe on 2026-11-11 observed `{master:0}` between the XML reply and the CLI prompt.
This framing caused the previous XML parser failure. Native JSON contained the top-level `chassis-inventory` array.
Both native commands accepted the final `| no-more` filter.

References:

- [Junos output filters](https://www.juniper.net/documentation/us/en/software/junos/cli/topics/topic-map/filtering-operational-command.html)
- [Chassis hardware command](https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/show-chassis-hardware.html)

### User Story 2 - Review Safe Targeting and Run Outcomes (Priority: P1)

An operator can confirm the action's exact scope and fixed command before execution, and can distinguish successful, unavailable, failed, and cancelled device outcomes after the run.

**Why this priority**: The action fans out across an organization and collects device inventory, so predictable scope and clear outcomes are necessary for safe operations.

**Independent Test**: Use mocked device inventories and command-session results to verify the command is fixed, only eligible EX targets are accepted, and preview, setup errors, timeouts, per-device failures, and cancellation are represented without hiding successful files from other devices.

**Acceptance Scenarios**:

1. **Given** a user configures or submits a different command or includes a non-EX device, **When** the server validates the action, **Then** it rejects the altered command or ineligible target rather than running it.
2. **Given** one device fails to establish a command session or returns an unsuccessful response, **When** the rest of the batch continues, **Then** that device has an explicit failure outcome and successful device files remain available.
3. **Given** the operator cancels an active run, **When** cancellation is applied, **Then** pending work is stopped, completed results remain valid, and remaining devices receive an explicit cancelled outcome.

### User Story 3 - Reliably Save and Download XML and JSON (Priority: P2)

An operator downloads an archive for the run and can identify each device's XML file even when hostnames are missing, unsafe as file names, or duplicated without regard to case.

**Why this priority**: Stable, valid file names and an intact archive make collected inventory practical to use and prevent one device's response from overwriting another's.

**Independent Test**: Supply chunked and multi-byte XML responses, duplicate and unsafe hostnames, missing names, malformed or oversized responses, and verify only valid selected outputs are saved under distinct safe file names while each failure is recorded in the run manifest.

**Acceptance Scenarios**:

1. **Given** hostname collisions, missing names, or path-like names, **When** output files are created, **Then** each target receives a safe unique filename that includes a stable device identifier.
2. **Given** an XML response is split across transport chunks or a UTF-8 character boundary, **When** collection completes, **Then** the saved XML preserves the decoded content and namespaces without prompts, banners, or transport artifacts.
3. **Given** JSON output is selected, **When** the native JSON command completes, **Then** the file preserves the complete native Junos JSON response.
4. **Given** the XML response is incomplete, malformed, exceeds the configured response limit, or fails to complete before its timeout, **When** the run is finalized, **Then** no successful-looking XML or JSON file is produced for that device and the manifest reports the failure.
5. **Given** a complete run has mixed successes and failures, **When** the user downloads the run archive, **Then** it contains all selected successful formats and a manifest of all device outcomes without exposing credentials.

### Edge Cases

- The organization has no eligible EX switches or no accessible sites.
- Site or device inventory requires multiple pages; later pages contain additional EX targets.
- Inventory contains virtual chassis member records that map back to one logical device, as well as duplicate or case-variant hostnames.
- A device is offline, lacks a usable hostname or stable identifier, or changes state after preview.
- Session setup returns client or server errors, a command prompt is not recognized, or the run is cancelled while some work is pending.
- XML is fragmented across chunks, includes a multibyte character split between chunks, or is surrounded by command echo, prompt text, terminal controls, or a login banner.
- XML is truncated, malformed, unexpectedly wrapped, too large, or includes a prohibited document type declaration or external entity.
- Native JSON contains nested arrays, repeated inventory records, numeric-looking strings, malformed syntax, or no chassis inventory.
- An otherwise valid response contains secrets; saved output, the manifest, logs, and error messages must not disclose credentials.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Operations portal MUST provide a clearly named dedicated action for collecting EX hardware inventory; users MUST NOT need to copy the command into a general-purpose command field.
- **FR-002**: The server MUST run only the selected fixed native commands. XML uses `display xml`, and JSON uses `display json`. Both commands end with `| no-more`.
- **FR-003**: The action MUST be available only when the existing WebSockets shell capability is enabled and MUST reuse existing authentication, authorization, confirmation, capacity, timeout, cancellation, and artifact access safeguards.
- **FR-004**: Preview MUST enumerate every organization site and complete device and running-statistics pages. It MUST exclude offline and unknown-status targets with separate counts.
- **FR-005**: Target selection MUST be restricted to EX switches and MUST deduplicate virtual-chassis member records that refer to the same logical target.
- **FR-006**: The dedicated action MUST offer XML, JSON, and both-format output choices, validate the choice on the server, and default to XML.
- **FR-007**: Each selected format MUST yield a complete native Junos reply with chassis inventory. XML MUST preserve the original document and namespaces.
- **FR-008**: Saved XML MUST NOT include terminal banners, command prompts, command echoes, ANSI control sequences, a no-paging command, or accidental JSON wrapping.
- **FR-009**: JSON MUST preserve native `display json` text with a nonempty `chassis-inventory` array and chassis content. The server MUST NOT convert XML into JSON.
- **FR-010**: XML and JSON choices MUST run only their respective command. BOTH MUST run XML, then JSON, once each, with separate captures.
- **FR-011**: Each run MUST have a unique output location and each target's filename MUST be safe and unique, including for duplicate or case-insensitive hostname collisions, missing hostnames, and unsafe path characters. A stable device identifier MUST distinguish collisions.
- **FR-012**: Collection MUST handle transport chunk boundaries and UTF-8 characters split across chunks. Incomplete, malformed, oversized, timed-out, or unsafe XML MUST produce a failure outcome and MUST NOT be saved as a successful XML or JSON result.
- **FR-013**: XML parsing MUST NOT resolve DTDs or external entities.
- **FR-014**: The run MUST retain a per-device outcome manifest and a downloadable archive. A device failure or cancellation MUST NOT discard successful files from other devices.
- **FR-015**: Saved files, manifests, logs, and error messages MUST NOT expose credentials or secrets; output sanitization MUST preserve valid XML and structured JSON content.
- **FR-016**: Existing general-purpose batch actions and single-shell sessions MUST continue to behave as before.
- **FR-017**: Dispatch MUST check current running status again. Offline or unknown devices MUST receive skipped outcomes without a shell request.
- **FR-018**: Per-format outcomes MUST retain successful files when another format fails. Hardware files and manifests MUST survive session expiry and process restart.
- **FR-019**: Artifact validation MUST reject credential fields and values without rejecting public namespace URLs or slash-separated hardware descriptions. Log redaction MUST remain unchanged.

### Mist Cloud Transport Requirements

- This feature uses the existing Mist WebSocket shell-session flow to obtain Junos terminal output, rather than a Mist Cloud REST operation.
- The flow MUST preserve the existing shell-session authentication and endpoint contracts. It MUST retain the first output and fragmented control/data boundaries needed to produce the complete command response.
- Tests MUST verify the existing Mist WebSocket authentication and endpoint behavior, fixed-command output, setup failure safety, cancellation, and secret redaction. No new direct Mist REST transport is in scope.

### Key Entities

- **Organization Run**: A single dedicated collection request scoped to all sites in one selected/configured organization, with a unique run identifier and shared lifecycle.
- **EX Target**: A unique eligible EX switch or virtual-chassis logical device with site and stable device identity, hostname when available, and availability state.
- **Device Result**: A target outcome with separate format states and all successful files, including files from partially failed targets.
- **Run Archive**: The downloadable set of successful selected-format device files and a manifest describing every target outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a test organization with at least two sites, the preview lists 100% of unique eligible EX targets across all inventory pages and lists 0 non-EX targets as executable.
- **SC-002**: For every valid, complete mocked device reply, XML output is parseable with the original reply's root, namespaces, and chassis inventory content intact.
- **SC-003**: In test runs with duplicate, missing, or unsafe hostnames, 100% of successful device outputs have distinct safe filenames.
- **SC-004**: Native JSON tests preserve response text without XML conversion. BOTH tests assert two distinct commands, independent captures, and partial-format outcomes.
- **SC-005**: In mixed-result test runs, 100% of failed, unavailable, excluded, and cancelled targets have a visible manifest outcome, while all successful outputs remain downloadable.
- **SC-006**: Existing WebSockets batch and single-shell regression tests pass without changing their user-visible behavior.

## Assumptions

- The requested scope is every site in the selected/configured organization, not every organization managed by an MSP.
- The action is limited to EX switches, and the existing portal shell capability flag and user authorization remain prerequisites.
- Existing concurrency, target limits, confirmation, and cancellation remain authoritative. Hardware artifacts use durable retention instead of session expiry.
- The Juniper operational command documentation states that `show chassis hardware detail` includes additional hardware details and that EX Virtual Chassis FPC entries represent members. Junos `display xml` renders command output in XML tag format. These general references do not certify every Junos release; implementation tests must validate captured output behavior without running commands on production devices.
- When needed to prevent pagination, the implementation may use the existing terminal no-paging mechanism or a safe terminal setup, but it MUST preserve the requested command's exact read-only semantics and MUST NOT put a no-paging command into the saved XML.
- Automated tests use mocked responses. The user authorizes read-only live acceptance after checking current Mist running status.

## References

- Juniper, `show chassis hardware` command reference: https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/show-chassis-hardware.html
- Juniper, filtering operational command output and `display xml`: https://www.juniper.net/documentation/us/en/software/junos/cli/topics/topic-map/filtering-operational-command.html
