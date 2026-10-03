# Feature Specification: WIP target controls

**Feature Branch**: `jmorrison-juniper-wip-target-controls`

**Created**: 2026-10-02

**Status**: Specified

**Input**: Issue [#3158](https://github.com/jmorrison-juniper/MistHelper/issues/3158) and the bounded parent assignment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the category caution (Priority: P1)

An operator sees a caution before a run of a row in the displayed Work In Progress category.
The caution names the current category and a possible incomplete result.
It tells the operator to verify the result.
It does not claim that the operation is unimplemented.

**Why this priority**: The category currently carries no guidance about incomplete results.

**Independent Test**: Select each current Work In Progress row before any run. Select a normal row afterward.

**Acceptance Scenarios**:

1. **Given** a Work In Progress row, **When** the operator selects it, **Then** the page shows the caution before Run.
2. **Given** a visible caution, **When** the operator selects a normal row, **Then** the page hides the caution.
3. **Given** a changed displayed category, **When** the page lists the row, **Then** the caution follows that category.
4. **Given** an unsafe operation, **When** its displayed category changes, **Then** the safety registry still refuses its run.

### User Story 2 - Select a site and switch (Priority: P1)

An operator selects one site and one switch before menu 63 runs.
The page supplies the site answer first and the switch answer second.
The existing handler resolves both answers and exports the selected switch's virtual chassis.

**Why this priority**: Menu 63 currently supplies only the first answer and never reaches the virtual chassis endpoint.

**Independent Test**: Select a controlled site and switch through the shipped page. Run the actual CLI handler offline.

**Acceptance Scenarios**:

1. **Given** menu 63, **When** no site exists in the selection, **Then** Run remains disabled.
2. **Given** a selected site, **When** no switch exists in the selection, **Then** Run remains disabled.
3. **Given** two valid selections, **When** the operator runs menu 63, **Then** the actual virtual chassis endpoint runs once.
4. **Given** another selected site, **When** its switch list loads, **Then** the previous switch selection does not remain.
5. **Given** an empty virtual chassis response, **When** the handler returns, **Then** the page reports the existing no-record warning.

### User Story 3 - Preserve site-only client exports (Priority: P2)

Menus 64 and 65 retain one required Site control.
They run the existing client exporters with the selected site.
The proof records the actual client output, not a site cache.

**Why this priority**: The historical report predates the existing Site controls and current output guards.

**Independent Test**: Run both actual handlers with controlled native responses and temporary local files.

**Acceptance Scenarios**:

1. **Given** menu 64 or 65, **When** the operator selects the row, **Then** exactly one required Site control appears.
2. **Given** valid client responses, **When** the handler runs, **Then** the proof counts the actual records and exporter metadata.
3. **Given** an empty or failed selector response, **When** the page receives it, **Then** the existing named reason remains visible.

### Edge Cases

- No switch exists at the selected site.
- The inventory contains only another device family.
- Site or device lists are empty.
- A request returns HTTP 403 or 503.
- A request fails during transport.
- Another site permits recovery after a failure.
- A site identifier needs URL encoding.
- Site and switch names contain HTML characters.
- A previous request completes after another site or operation selection.
- The operator uses the keyboard to select a site, select a switch, and activate Run.
- The required metadata or caution metadata is removed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Derive the caution from the actual displayed category, not a guessed menu range.
- **FR-002**: Keep `OperationRegistry` authoritative for `safe` and `interactive_safe`.
- **FR-003**: Never admit destructive, resource-intensive, continuous, websocket, or unregistered operations through caution metadata.
- **FR-004**: Show a recoverable Caution before execution and require result verification.
- **FR-005**: Use the existing required site and switch descriptor helpers for menu 63.
- **FR-006**: Use `device_filter="switch"` and the existing site-then-device prompt order.
- **FR-007**: Keep Run disabled until both required values are valid.
- **FR-008**: Use the existing input bridge and actual handler. Add no alternate handler path.
- **FR-009**: Reset stale selections and reject stale selector completions.
- **FR-010**: Preserve the existing labels, text rendering, loading states, empty reasons, and fault reasons.
- **FR-011**: Keep one required Site control for menus 64 and 65.
- **FR-012**: Use native SDK response fixtures and controlled transport. Make no live Mist request or store connection.
- **FR-013**: Prove the actual output files, notices, rows, and endpoint metadata at the local writer boundary.
- **FR-014**: Count the checked rows, prompt answers, handler calls, endpoint calls, output writes, and live network calls.
- **FR-015**: Prove acceptance fails when the switch descriptor or caution metadata is removed.
- **FR-016**: Preserve the existing HTTP and payload policy. Report any additional source defect to the parent.

### Key Entities

- **Displayed category**: The category name that groups a row on the Operations page.
- **Caution metadata**: A presentation property derived from the displayed category. It grants no run permission.
- **Target controls**: The selected site name and switch name that answer the existing prompts.
- **Output evidence**: Actual local files, record counts, notices, and exporter endpoint metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three current Work In Progress rows show a caution before execution.
- **SC-002**: One normal row hides the previous caution without changing its run permission.
- **SC-003**: Menu 63 submits exactly two prompt answers and calls the selected virtual chassis endpoint exactly once.
- **SC-004**: Menus 64 and 65 each submit one prompt answer and produce their actual client output.
- **SC-005**: Invalid, empty, stale, and failed selections produce zero virtual chassis calls.
- **SC-006**: Both direct negative guards reject the removed acceptance input and state the measured counts.
- **SC-007**: Required browser tests run without skips in a combined collection. All live network callback counts are zero.
- **SC-008**: Owned server threads, browser resources, temporary data, and helper paths are absent after the proof.

## Assumptions

- The current category label remains unchanged. The caution does not reclassify any operation.
- Actual exporter bodies, menu definitions, SDK contracts, primary keys, authentication, and database routing remain read-only.
- Existing tests remain read-only. This repair owns only the new reserved test modules and support package.
- The local source starts at `92dc5d3ebf5fa6d2b9ddba536b5c3bc6cd4ca232`.
- The old remote draft remains at `0f6b375e71243311b5cf5856fe9f220842a14e3b`.
- Publication remains blocked at queue position 46 until the parent grants an exact full verified-main SHA.
- The pre-edit proof found an additional menu 64 suffix mismatch. The parent decides its separate source scope.
