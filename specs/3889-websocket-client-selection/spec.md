# Feature Specification: WebSocket Client Selection

**Feature Branch**: `jmorrison-juniper-websocket-client-selection`

**Feature Directory**: `specs/3889-websocket-client-selection`

**Created**: 2026-10-04

**Status**: Implementation is complete for verified EX client choices. Human review remains required before merge.

**Input**: Issue #3889 requires scoped client choices for DHCP release and MAC table retrieval.
The user authorized implementation after ownership transferred.
The app-managed branch remains in use.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select DHCP clients safely (Priority: P1)

A NOC engineer selects a site and device before preparing a DHCP release.
The engineer can select known clients or enter client MAC addresses manually.
The engineer reviews the target and confirms the operation before it starts.

**Why this priority**: DHCP release changes client state. A wrong target can interrupt service.

**Independent Test**: Use simulated discovery results and a recorded submission.
Check one client, multiple clients, and mixed input for each supported device family.
Do not invoke a real device utility.

**Acceptance Scenarios**:

1. **Given** a selected site and device, **When** discovery succeeds, **Then** each choice has evidence of association with that device.
2. **Given** known clients, **When** the engineer selects multiple clients, **Then** the optional `macs` field contains those MAC addresses.
3. **Given** a disconnected or unlisted client, **When** the engineer enters its MAC address, **Then** discovery membership is not required.
4. **Given** selected and manually entered clients, **When** the engineer prepares the operation, **Then** both sets remain available for review.
5. **Given** an empty optional field, **When** the engineer prepares the operation, **Then** the existing empty-field behavior remains unchanged.
6. **Given** any selection or discovery error, **When** the dialog updates, **Then** no utility starts.
7. **Given** a prepared DHCP release, **When** confirmation is absent, **Then** the operation does not start.

---

### User Story 2 - Preserve MAC table filters (Priority: P1)

A NOC engineer prepares a switch MAC table request.
The engineer can select a known client or enter a value accepted by the existing validator.
The field can remain empty.

**Why this priority**: A choice list must not prevent searches for clients that discovery cannot list.

**Independent Test**: Prepare recorded requests with a selected client, an unlisted complete MAC, and an empty field.
Compare each request with the existing manual-input behavior.

**Acceptance Scenarios**:

1. **Given** `ex.retrieveMacTable`, **When** the engineer selects a known client, **Then** its MAC address populates the optional `mac_address` field.
2. **Given** an unlisted MAC or a filter accepted by the current validator, **When** the engineer enters it, **Then** the choice list does not reject it.
3. **Given** an empty `mac_address` field, **When** the engineer prepares the request, **Then** the existing unfiltered request behavior remains unchanged.
4. **Given** invalid input under the existing operation contract, **When** the engineer prepares the request, **Then** validation prevents submission.

---

### User Story 3 - Continue when discovery fails (Priority: P1)

A NOC engineer sees the current discovery state without losing manual fields.
The engineer can prepare valid manual input during loading or after a discovery failure.

**Why this priority**: Discovery is optional assistance. It must not become a requirement for existing workflows.

**Independent Test**: Simulate success, empty results, access errors, service errors, unavailable support, and a request that never completes.
Check the visible state, manual fields, and utility call count.

**Acceptance Scenarios**:

1. **Given** an active lookup, **When** no result is available, **Then** the dialog shows loading and retains editable manual fields.
2. **Given** a successful lookup with no eligible clients, **When** it completes, **Then** the dialog shows an empty state.
3. **Given** a 4xx response, **When** it completes, **Then** the dialog shows a request or access error rather than an empty state.
4. **Given** a 5xx response, **When** it completes, **Then** the dialog shows a service error rather than an empty state.
5. **Given** unsupported discovery or missing association evidence, **When** lookup ends, **Then** the dialog shows unavailable and offers no unsupported choices.
6. **Given** a stalled lookup, **When** ten seconds pass, **Then** loading ends and the dialog shows unavailable.
7. **Given** any discovery failure, **When** the engineer enters valid manual input, **Then** existing review and confirmation remain available.

---

### User Story 4 - Keep choices within the current target (Priority: P1)

A NOC engineer changes the site, device, or operation.
The dialog removes old choices and ignores late results for the previous target.
The dialog never silently reuses selected clients for a different target.

**Why this priority**: An old choice can direct a state-changing operation at the wrong client.

**Independent Test**: Delay the first simulated lookup. Change each target component before it completes.
Complete the new lookup first. Check that the old response cannot alter the new dialog.

**Acceptance Scenarios**:

1. **Given** listed and selected clients, **When** the site changes, **Then** old choices and selector-derived values clear immediately.
2. **Given** listed and selected clients, **When** the device changes, **Then** old choices and selector-derived values clear immediately.
3. **Given** listed and selected clients, **When** the operation changes, **Then** old choices and selector-derived values clear immediately.
4. **Given** an older lookup, **When** it completes after a target change, **Then** its data and error state do not affect the current dialog.
5. **Given** manual input and a discovery refresh, **When** discovery completes or fails, **Then** it does not overwrite that input.
6. **Given** a locked or canceled dialog, **When** discovery completes, **Then** it does not unlock, reopen, or start the operation.
7. **Given** an aggregate stream, **When** the engineer opens it, **Then** no client selector or client lookup appears.

---

### User Story 5 - Review evidence before delivery (Priority: P1)

A maintainer reviews ownership, safety tests, and compatibility evidence before delivery.
The maintainer gives explicit human approval for DHCP changes.

**Why this priority**: Parallel work can own required files. DHCP changes must not merge automatically.

**Independent Test**: Review the ownership record and the proposed delivery evidence.
An absent handoff or absent human approval must keep the applicable gate closed.

**Acceptance Scenarios**:

1. **Given** an overlapping owner without a recorded handoff, **When** design documents are complete, **Then** regression and implementation remain blocked.
2. **Given** a future ownership transfer, **When** work resumes, **Then** the maintainer checks all overlapping files before approving scope.
3. **Given** passing tests for DHCP changes, **When** delivery is considered, **Then** human review is still required and auto-merge remains prohibited.

### Edge Cases

- Missing site or device information must not start discovery or produce device choices.
- Duplicate client records must produce one choice per MAC address within the current target.
- Identical labels with different MAC addresses must remain distinguishable.
- Malformed records or records without association evidence must not become choices.
- A client can appear at several devices. Each displayed association must be supported for the selected device.
- Historical association must not imply that the client is currently connected.
- Partial results must not appear as a complete client list.
- A late success after timeout must not replace the unavailable state for that expired lookup.
- Manual entries must not disappear after empty results, an error, or a refresh.
- Changing the target must clear selected values without silently replacing independent manual entries.
- Existing target-change rules still govern manual input. Discovery must not weaken review of the current target.
- Mixed manual and selected inputs must retain existing ordering and duplicate-handling rules.
- Keyboard use must support selecting, removing, and reviewing clients without starting a utility.
- Opening, closing, and reopening a dialog must not reuse results from a different target.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST offer optional client choices for `ex.releaseDhcpLeases` when device association is verified.
  SRX and SSR choices MUST remain unavailable until verified discovery proves selected-gateway association.
  Manual input MUST remain available for `srx.releaseDhcpLeases` and `ssr.releaseDhcpLeases`.
- **FR-002**: The system MUST offer optional client choices for `ex.retrieveMacTable`.
- **FR-003**: Each displayed choice MUST belong to the selected site and have verified association with the selected device.
- **FR-004**: The system MUST NOT treat all site clients as clients of the selected device.
- **FR-005**: The system MUST retain editable manual fields for disconnected and unlisted clients in all discovery states.
- **FR-006**: DHCP release MUST accept multiple MAC addresses through the existing optional `macs` contract.
- **FR-007**: MAC table retrieval MUST preserve `mac_address` values accepted by the current validator without requiring discovery membership.
  Pinned-SDK evidence MUST define supported forms before validation changes.
  The current WebSocket validator accepts complete MAC addresses only. Partial and wildcard support remains unverified.
- **FR-008**: Both optional fields MUST retain their existing empty-input behavior. Discovery MUST NOT select a client by default.
- **FR-009**: Selecting a client MUST only update the corresponding input. It MUST NOT invoke a utility.
- **FR-010**: Selected, manual, mixed, and empty input MUST preserve the existing submission payload shape and operation-specific validation.
- **FR-011**: Equivalent selected and manual input MUST produce equivalent SDK utility arguments.
- **FR-012**: Invalid DHCP MAC input MUST prevent submission under existing validation rules. MAC table filters MUST retain their distinct validation contract.
- **FR-013**: Aggregate streams and unrelated utilities MUST NOT receive a client selector or new client lookup.
- **FR-014**: The dialog MUST distinguish loading, available choices, empty results, 4xx errors, 5xx errors, and unavailable discovery.
- **FR-015**: Discovery MUST end loading within ten seconds. Timeout, unsupported discovery, and missing association proof MUST show unavailable.
- **FR-016**: Discovery errors MUST retain manual fields and current manual values. They MUST NOT invoke, retry, or schedule a device utility.
- **FR-017**: Site, device, or operation changes MUST immediately clear stale choices and selector-derived values.
- **FR-018**: Results and errors for an expired or superseded target MUST NOT alter the current choices, inputs, or state.
- **FR-019**: Discovery MUST NOT overwrite independent manual entries. Existing target-change behavior MUST remain intact.
- **FR-020**: Choices MUST show a MAC address and any available identifying label. Duplicate labels MUST remain distinguishable by MAC address.
- **FR-021**: Choice lists MUST exclude malformed and unsupported records and collapse duplicate MAC addresses within the current target.
- **FR-022**: Incomplete discovery MUST disclose its limitation. It MUST NOT imply that unlisted clients are invalid.
- **FR-023**: The system MUST preserve explicit confirmation, action locks, cancellation behavior, and current target review.
- **FR-024**: Discovery completion MUST NOT unlock or reopen a canceled dialog, or change a confirmed operation's target.
- **FR-025**: Client selection MUST support keyboard interaction and an accessible discovery state and error message.
- **FR-026**: Regression and implementation MUST remain blocked while a current owner overlaps without a recorded handoff or approved non-overlapping scope.
  A prior PR merge clears that PR's ownership, not the ownership of another active change.
  Design documents may proceed without editing owned files.
- **FR-027**: Future implementation MUST first establish isolated automated tests for the scenarios below. Tests MUST NOT invoke real device utilities.
- **FR-028**: DHCP changes MUST receive explicit human review before merge. Auto-merge MUST NOT be enabled or used.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

This section records required integration constraints, not an implementation design.
No new owned WebSocket transport is requested.
The existing utility transport and SDK payload contract remain unchanged.

- **TR-001**: Discovery MUST use actual read-only mistapi SDK methods. Invented endpoints and direct HTTP replacements for working SDK methods are prohibited.
  Offline inspection or mocked transport tests MUST verify HTTP GET behavior in the pinned SDK.
- **TR-002**: The verified wired candidate is `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients`.
  Local documentation defines a `device_mac` filter and device association in returned records.
  Future contract tests MUST verify the installed SDK signature, selected device identity, and returned association.
- **TR-003**: The verified WAN candidate is `mistapi.api.v1.sites.wan_clients.searchSiteWanClients`.
  Local documentation does not establish a selected-gateway association contract.
  SRX and SSR choices MUST remain unavailable unless actual SDK methods and response evidence prove that association.
  Do not invent a device filter or infer gateway association from site membership.
- **TR-004**: Future tests MUST prove selected-site isolation, device association, supported pagination, malformed-data handling, and timeout behavior.
  Discovery MUST use existing authorized sessions and preserve access controls.
- **TR-005**: Future tests MUST verify authentication, endpoint parity, failure safety, and secret redaction with mocked GET discovery.
  Tests MUST distinguish successful empty results from 4xx and 5xx failures.
  This feature MUST NOT claim SDK insufficiency without a failing contract test.
- **TR-006**: This work MUST NOT introduce a new utility trigger, capture call, shell call, or transport fallback for discovery.
  Tests and specification work require no credentials or live Mist calls.

### Key Entities *(include if feature involves data)*

- **Target context**: The selected site, device, device family, and operation define the permitted choice scope.
- **Client choice**: A client MAC address, an optional label, and evidence of site and device association identify one choice.
- **Discovery state**: A lookup has a target context, a bounded lifetime, a result state, and an optional user-facing error.
- **Utility input**: Optional `macs` or `mac_address` values can come from selections, manual entry, or both.
- **Ownership record**: File ownership, a recorded handoff, and human review determine whether work can proceed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every displayed client choice has verified association with the selected site and device. No unrelated client appears in scope tests.
- **SC-002**: All discovery attempts leave loading within ten seconds. Manual fields remain editable in every discovery state.
- **SC-003**: Manual, selected, mixed, empty, and currently accepted filter inputs preserve the existing operation meaning and submitted values.
- **SC-004**: All delayed-result cases retain the current target's choices. No selection or discovery failure starts a device operation.
- **SC-005**: Isolated browser tests prove keyboard selection, removal, manual entry, and target review for each supported selector.
  The tests identify the confirmation requirement without releasing real leases.
- **SC-006**: Every DHCP delivery receives recorded human approval. No overlapping implementation proceeds without ownership clearance, and no DHCP delivery uses auto-merge.

## Assumptions

### Scope and Defaults

- The four named utilities define the full client-selection scope.
- Discovery is optional assistance, not an authoritative list of all valid utility inputs.
- Existing authentication and permissions remain unchanged. The feature does not grant additional access.
- Ten seconds is the maximum loading wait, including any retries or pagination.
- The current manual-input behavior is the compatibility baseline. Future tests must record that baseline before changing behavior.
- A missing gateway association contract is a dependency limitation, not permission to show all site clients.
- Historical results may assist selection. The dialog must not describe them as proof of current connectivity.
- This specification adds no persistent client store or new export behavior.

### Ownership Prerequisite

PR #3814 changed these files:

- `src/mist/realtime/websocket_streams/web/static/websockets.js`
- `tests/e2e/websockets_tab/test_websockets_page.py`

PR #3814 merged. PR #3897 then held exclusive ownership of the JavaScript and cancellation baseline.
PR #3897 merged at `56818841691eda43e5db375071a0ec52b7ddd64e`.
The parent transferred JavaScript ownership to issue #3889 after that merge.
The existing page test file remains unchanged.

PR #3892 merged the dialog-audit harness under `tests/e2e/websockets_tab/dialog_audit`.
Only client-picker-specific expectations and fixtures changed in that harness.
PR #3891 merged wording changes. This feature did not edit `utility_text`.
The template and cancellation implementation remain unchanged.
Do not update shared agent instruction files or read other worktrees.

### Test-First Evidence and Human Review

Future work must create isolated Playwright tests and mocked GET contract tests before implementation.
The evidence must cover all of these cases:

- Success, empty results, 4xx, 5xx, unavailable support, and bounded loading waits.
- Site and device isolation, missing association evidence, and stale request races after each target change.
- Manual input, multiple DHCP MACs, mixed input, empty optional fields, and arbitrary MAC table filters.
- Validation, unchanged payload shape, and equivalent selected-input and manual-input SDK arguments.
- Confirmation, locks, cancellation, accessibility, and zero real utility calls.

Use simulated responses and intercepted submissions.
Do not use credentials, live DHCP release, device utilities, captures, or remote shell calls.
Passing tests do not replace human approval.
WARNING: DHCP release changes client state and can interrupt service.
Require human review and prohibit auto-merge.

### Local Evidence and Execution Boundary

The active core templates and `.specify/memory/constitution.md` define this specification.
`utility_fields.py` currently defines optional `macs` and `mac_address` fields.
The user reports that `websockets.js` currently creates plain text inputs.
These existing contracts do not justify removing manual input.
The current complete-MAC validator does not prove support for arbitrary filters.

Local method evidence comes from these files:

- `src/interfaces/visualization/ui/prompt_utils.py`
- `src/operations/exporting/export/site_search_exporter.py`
- `documentation/api/sites/GET_sites_site_id_wired_clients_search.md`
- `documentation/api/sites/GET_sites_site_id_wan_clients_search.md`

This work uses design documents under `specs/3889-websocket-client-selection/`.
The specification, plan, and tasks use this explicit directory without changing the shared feature pointer.
Implementation and isolated regression tests are present on the app-managed branch.
Do not run mutation hooks. Require human review before delivery.
