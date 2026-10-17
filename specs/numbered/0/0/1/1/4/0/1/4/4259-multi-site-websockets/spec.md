# Feature Specification: Multi-site WebSocket operations

**Feature Branch**: `jmorrison-juniper-multi-site-websockets`

**Created**: 2026-10-16

**Status**: Draft

**Input**: Add Single Site and Multi Site tabs to the Operations portal WebSockets page. Let operators run catalog operations across selected or all sites and eligible devices, routers, switches, gateways, Mist Edges, or clients. Keep results separate by target and save them as one file or in a folder hierarchy. Use complete Mist pagination and maximum page sizes.

## User Scenarios & Testing

### User Story 1 - Use the single-site tab (Priority: P1)

An operator opens the WebSockets page and selects the Single Site tab. The operator uses the current catalog, target fields, session controls, and output view without a change to the current workflow.

**Why this priority**: The current workflow must remain reliable while the new workflow is added.

**Independent Test**: Start a current single-site operation and verify its output, stop control, and download.

**Acceptance Scenarios**:

1. **Given** the WebSockets page is ready, **When** the operator opens Single Site, **Then** the current catalog and single-target form remain available.
2. **Given** the operator starts a valid single-site operation, **When** results arrive, **Then** the current session view shows them without a batch target label.

### User Story 2 - Select organization targets (Priority: P1)

An operator selects Multi Site, chooses an operation, and selects all eligible sites or a site subset. The page then offers only target types and target choices that the selected operation supports.

**Why this priority**: Dynamic target selection makes organization-wide work practical and prevents invalid target combinations.

**Independent Test**: Select representative site, device, and client operations. Verify each target list follows catalog metadata and filters devices by family.

**Acceptance Scenarios**:

1. **Given** an operation needs a site, **When** the operator selects all sites or a site subset, **Then** the page shows that target set and no unrelated target fields.
2. **Given** an operation needs a device, **When** the operator selects sites, **Then** the page offers all eligible devices or a selected device subset for those sites.
3. **Given** an operation supports client selection, **When** the operator selects all clients or named clients, **Then** the target choices remain scoped to the selected site and device.
4. **Given** a device family or target is not valid for the selected operation, **When** the page builds the selection, **Then** it excludes that target and explains why.

### User Story 3 - Run and monitor a multi-target operation (Priority: P1)

An operator starts one operation across the selected targets. The page reports progress and status for each target, keeps each result tied to its site and target, and shows partial failures without hiding successful results.

**Why this priority**: Operators need one coordinated run with enough detail to act on each device outcome.

**Independent Test**: Run a mocked batch where one target succeeds, one fails, and one completes later. Verify status, result identity, cancellation, and session limits.

**Acceptance Scenarios**:

1. **Given** the selected target set is valid, **When** the operator starts the batch, **Then** the portal starts one parent session and processes targets with bounded concurrency.
2. **Given** one target fails, **When** other targets return results, **Then** the page shows each outcome and retains successful output.
3. **Given** a batch is live, **When** the operator stops it, **Then** the portal stops queued work and requests a stop for every active target session.
4. **Given** the selected operation is a remote shell, **When** the operator previews an ordered command list, **Then** the portal runs it on each confirmed device and displays output by device.
5. **Given** a site or device result arrives, **When** the page displays it, **Then** the result includes its site and target identity.
6. **Given** the initial shell output contains a normalized device prompt, **When** a command returns that same prompt and two seconds without output, **Then** the portal records the output and continues to the next command.
7. **Given** the initial or command prompt is not recognized within 30 seconds, **When** collection stops, **Then** the portal preserves partial output, marks the target unproven, and skips later commands.

### User Story 4 - Save batch results (Priority: P2)

An operator chooses combined output, target folders, or both. The operator can download the saved results and find them grouped by site, device type, device, or client.

**Why this priority**: Operators need usable evidence after a long-running or large batch ends.

**Independent Test**: Generate mixed success and failure results. Verify the combined file and each requested folder contain the correct target records.

**Acceptance Scenarios**:

1. **Given** a batch has output, **When** the operator selects combined output, **Then** one file contains every result with its target identity.
2. **Given** a batch has output, **When** the operator selects a folder layout, **Then** each result is saved under the selected grouping.
3. **Given** a label or identifier contains an unsafe path character, **When** the portal saves a result, **Then** it uses a safe name and does not write outside the approved data directory.

### Edge Cases

- The organization has no sites or has more sites than one Mist response page.
- A site has no eligible devices, or a selected device no longer belongs to its site.
- The operation accepts sites but not devices, or accepts a device family that is absent from a selected site.
- A client picker returns no rows, an incomplete page, or a response that does not prove site and device association.
- Mist denies access to one site while it allows access to other selected sites.
- A target fails before it starts, disconnects while it runs, or returns no output.
- The operator changes a target selection while a picker response is still in flight.
- The operator stops a batch while targets wait or run.
- The selected target list exceeds the current session limit or a documented batch limit.
- A shell command times out, returns no prompt, or does not finish its output before the deadline.
- A download contains empty output, partial results, unusual device names, or duplicate result records.

## Requirements

### Functional Requirements

- **FR-001**: The WebSockets page MUST provide separate Single Site and Multi Site tabs.
- **FR-002**: The Single Site tab MUST preserve the current catalog, start form, session list, terminal controls, and downloads.
- **FR-003**: The Multi Site tab MUST derive eligible sites and target fields from the selected catalog operation.
- **FR-004**: The Multi Site tab MUST let the operator choose all eligible sites or a site subset.
- **FR-005**: For operations that declare device targets, the Multi Site tab MUST let the operator choose all eligible devices or a device subset.
- **FR-006**: Device choices MUST show site and device identity and MUST filter by the selected operation's supported device family.
- **FR-007**: For operations that declare client targets, the Multi Site tab MUST let the operator choose all eligible clients or a client subset scoped to the selected sites and devices.
- **FR-008**: The portal MUST refuse a batch with an unknown operation, invalid target, invalid parameter, missing confirmation, or target outside the configured organization.
- **FR-009**: One parent session MUST report overall batch state and each target's queued, running, completed, stopped, or failed state.
- **FR-010**: Every batch result and error MUST retain the operation, site, target type, and target identity.
- **FR-011**: The portal MUST run target work with a bounded concurrency limit and MUST stop queued work after cancellation.
- **FR-012**: The remote shell batch MUST accept an ordered command list during preview, send each command only to confirmed devices, and collect output per device. It MUST capture the initial normalized prompt and require that same prompt plus two seconds without output before continuing. After the 30-second initial-output deadline or a 30-second per-command deadline, it MUST retain partial output, mark completion unproven, and skip later commands. Collection completion MUST NOT imply command success when no device status exists.
- **FR-013**: The portal MUST preserve current operation safety classes, feature locks, and typed confirmations. A batch MUST bind its confirmation to the exact operation, parameters, commands, and target set. Single Site confirmation MUST remain unchanged.
- **FR-014**: The portal MUST offer combined output and folder layouts grouped by site, device type, device, or client.
- **FR-015**: Saved output MUST remain under the existing `data/` directory and MUST use server-created safe paths.
- **FR-016**: Target discovery MUST use Mist SDK methods, the validated runtime page limit, and checked SDK page or cursor traversal to read every page.
- **FR-017**: Target discovery MUST reuse complete fetched lists during one batch and MUST not repeat a discovery request without a changed scope.
- **FR-018**: The portal MUST show access, pagination, and target errors separately from an empty list.
- **FR-019**: The portal MUST redact API tokens, WebSocket addresses, and shell secrets from logs, API responses, and saved output.
- **FR-020**: Live validation MUST use read-only commands only and MUST not change Mist cloud configuration or device state.
- **FR-021**: A channel batch MUST multiplex its catalog paths through the owned WebSocket transport and demultiplex results by target identity. It MUST not use the Single Site ten-path validation limit.
- **FR-022**: The portal MUST reject more than 1000 resolved targets without truncation and MUST show this limit in the preview.
- **FR-023**: The preview MUST show effective concurrency and output limits. It MUST reject shell lists over 20 commands, 4096 UTF-8 bytes per command, 16384 bytes per list, or 64 MiB saved output without truncation.

### Mist Cloud Transport Requirements

- Site discovery MUST use `mistapi.api.v1.orgs.sites.listOrgSites` with the validated runtime `limit` and complete SDK page traversal.
- Device discovery MUST use `mistapi.api.v1.sites.devices.listSiteDevices` with `type="all"`, the validated runtime `limit` where accepted, and complete SDK page traversal.
- Existing client suggestions MUST use `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients` with complete page or cursor traversal and verified site-device association.
- Map, asset, SDK client, and Mist Edge selectors MUST use their existing SDK methods and complete SDK page or cursor traversal when the method returns paged data.
- The owned WebSocket transport MUST continue to use catalog-defined channel paths and Mist SDK utility triggers. The SDK utility path supports one device per trigger, so the batch must keep a separate target identity for each trigger and result.
- Contract tests MUST prove that each SDK method uses the authenticated session, requests the maximum supported page size, reads all pages, preserves each result identity, reports a failed page, and redacts secrets. Tests MUST prove that the existing owned WebSocket transport preserves first output and split control sequences.

### Key Entities

- **Operation**: A catalog channel or utility with its supported scope, target fields, parameters, safety class, and output type.
- **Target**: One eligible site, device, Mist Edge, map, asset, or client selected for an operation.
- **Batch session**: One operator action that owns target work, reports overall state, and supports cancellation.
- **Target result**: The output or failure from one operation on one target, with stable site and target identity.
- **Output layout**: The selected combined file or folder grouping for saved target results.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An operator can move between Single Site and Multi Site without changing the existing single-site result for the same operation.
- **SC-002**: Every eligible target returned by complete discovery appears in the selected all-target set, with no target from another site or device family.
- **SC-003**: Every accepted batch result and failure identifies one site and one target.
- **SC-004**: A test batch with mixed outcomes completes without losing successful results or hiding failed targets.
- **SC-005**: A target list that spans multiple API pages produces the same complete target set as a single-page fixture.
- **SC-006**: The portal writes no result file outside `data/` and includes all target results in the selected output layout.
- **SC-007**: The portal stops queued work and requests termination of active work after one batch cancellation.
- **SC-008**: The preview shows the 1000-target cap, concurrency, shell limits, and 64 MiB output cap. The portal rejects an over-limit request without truncation.
- **SC-009**: A channel batch uses one transport connection and concurrency one. Utility and shell target concurrency ranges from one through five, with a default of three.

## Assumptions

- The portal uses one authenticated Mist organization. Cross-organization selection is out of scope.
- Multi Site supports operations that the existing catalog declares. It does not expose arbitrary REST paths or undeclared device commands.
- The selected operation's metadata is the source of truth for target requirements, device family, client selector, output type, and safety class.
- A batch counts as one public live session. Its target work uses the existing live session limit and a separate bounded target concurrency limit.
- A channel batch uses one owned connection for its selected paths. Utility and shell work use bounded per-target executions.
- A remote shell preview accepts a finite command list before start, requires the existing shell feature lock, and binds confirmation to the operation, commands, and exact target set.
- The Single Site tab retains the current repeatable channel behavior, including its ten-path limit. Multi Site channel batches use their own target validation.
- The preview resolves an all-device selection to explicit identities before the operator confirms it.
- The batch runs the previewed list against each confirmed device with bounded concurrency.
- The batch captures output per device and closes each shell after output collection or a 30-second deadline.
- The existing Single Site interactive shell remains unchanged.
- User-facing device labels come only from catalog families. The current families are access point, EX switch, SRX gateway, Session Smart router, and Mist Edge. Plain MX routers are not assumed when the catalog does not declare them.
- Results remain available with the batch session and use the existing `data/` output boundary.
- Live testing may use the Morrison House Oregon site for read-only operations such as `show route`, `show arp`, and Virtual Chassis statistics.
- Tests use mocked SDK responses and do not require a production Mist credential.

## Non-Goals

- Running destructive commands during live validation.
- Changing Mist organization, site, device, or firmware configuration.
- Supporting multiple Mist organizations in one batch.
- Adding operations that are not present in the current WebSockets catalog.
