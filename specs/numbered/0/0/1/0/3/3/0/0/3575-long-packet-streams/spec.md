# Feature Specification: Long packet capture

**Feature Branch**: `jmorrison-juniper-issue-3575-long-packet-capture`

**Created**: 2026-11-07

**Status**: Draft

**Input**: Issue #3575 and the preserved specification on `recovery/3575-handoff-20261004`.

## User Scenarios & Testing

### User Story 1 - Select a capture duration (Priority: P1)

An operator selects a packet capture duration from 60 through 3600 seconds. The
capture remains active during quiet periods until its duration ends or the
operator stops it.

**Why this priority**: The current 60-second default prevents operators from
observing faults that occur later.

**Independent Test**: Use a local fake stream and a controlled clock. Verify
that a 120-second capture remains active through quiet periods and accepts
records at 59, 61, and 119 seconds.

**Acceptance Scenarios**:

1. **Given** a valid target, **When** the operator selects 60 or 3600 seconds,
   **Then** the request accepts that duration.
2. **Given** a 3600-second capture, **When** a matching record arrives at 3599
   seconds, **Then** the capture session displays that record.
3. **Given** an invalid duration, **When** the operator starts the capture,
   **Then** the request fails before it starts a capture.

### User Story 2 - Receive only matching packet records (Priority: P1)

The tab confirms the selected stream channel before it starts a capture. It
shows records only when their scope and capture identifier match the request.

**Why this priority**: A missing first record or a record from another capture
can hide the cause of a fault.

**Independent Test**: Use a fake stream. Delay subscription confirmation and
the start response separately. Send matching and nonmatching records.

**Acceptance Scenarios**:

1. **Given** a stream without subscription confirmation, **When** the tab waits,
   **Then** it sends no capture request.
2. **Given** confirmation for the selected channel, **When** the tab starts,
   **Then** it sends one capture request.
3. **Given** another channel or capture identifier, **When** its records arrive,
   **Then** the selected card does not show them.
4. **Given** a matching end event with no packet record, **When** the tab reads
   it, **Then** the session ends normally without showing a null packet.

### User Story 3 - Stop and release the capture (Priority: P1)

An operator stops a capture before its selected duration ends. The tab checks
the active capture identifier before it sends the existing cloud stop request.
It releases the stream and reports whether the stop completed.

**Why this priority**: Closing a stream alone does not stop the cloud capture.

**Independent Test**: Stop a fake capture through the existing session
controller. Verify the identifier check, cloud request count, final state, and
owned resources.

**Acceptance Scenarios**:

1. **Given** the active identifier matches, **When** the operator stops the
   capture, **Then** the tab sends one cloud stop and reports completion.
2. **Given** the active identifier does not match, **When** the operator stops
   the capture, **Then** the tab sends no cloud stop and reports failure.
3. **Given** the cloud stop fails or remains unconfirmed, **When** the session
   ends, **Then** the tab does not report a successful stop.
4. **Given** the operator stops before capture start, **When** the subscription
   completes, **Then** the tab sends no capture request.

### Edge Cases

- Reject durations below 60 or above 3600 seconds.
- Reject fractional, negative, Boolean, Unicode-digit, and oversized duration
  values.
- Use 60 seconds when the request omits the duration.
- Refuse a subscription failure or timeout without starting a capture.
- Ignore a capture-end event with another capture identifier.
- Keep quiet captures active until their duration or a matching end event.
- Preserve idle cleanup, memory limits, packet limits, and other stream limits.
- Report unexpected disconnects and uncertain starts without a success state.
- Release owned resources after completion, stop, disconnect, timeout, or error.

## Requirements

### Functional Requirements

- **FR-001**: The tab MUST accept whole capture durations from 60 through 3600 seconds.
- **FR-002**: The form and server MUST reject invalid durations before a capture starts.
- **FR-003**: The tab MUST confirm the selected subscription before capture start.
- **FR-004**: A capture MUST remain active through quiet periods until its selected duration or a matching end event.
- **FR-005**: The tab MUST show records only for the selected channel and capture identifier.
- **FR-006**: The tab MUST treat a matching end event as normal completion and MUST NOT display a null packet.
- **FR-007**: A manual stop MUST check the active status object and MUST send no stop if that status reports a different capture identifier.
- **FR-008**: A failed or uncertain start or stop MUST produce a failure state, not a success state.
- **FR-009**: Each terminal path MUST release the resources owned by the capture session.
- **FR-010**: The change MUST preserve current capture cleanup, target checks, regional authentication, and safety flags.
- **FR-011**: The change MUST preserve packet length, packet count, idle, memory, and non-capture stream limits.
- **FR-012**: Tests MUST use local fakes or mocks and MUST NOT make live Mist or production calls.

### Mist Cloud Transport Requirements

- Capture start uses the existing `mistapi` session `mist_post`. Stop checks use
  `mist_get` and `mist_delete`. Trigger parity covers
  `mistapi.device_utils.ap.remotePcapWired`,
  `mistapi.device_utils.ap.remotePcapWireless`,
  `mistapi.device_utils.ex.remotePcap`,
  `mistapi.device_utils.srx.remotePcap`,
  `mistapi.device_utils.ssr.remotePcap`,
  `mistapi.device_utils.mxedge.orgRemotePcap`, and
  `mistapi.device_utils.mxedge.siteRemotePcap`.
- Reuse the existing `/api-ws/v1/stream` transport and the `site_pcaps` or
  `org_pcaps` channel. Do not add an owned transport or copy the recovery
  branch's separate transport.
- Contract tests MUST verify request parity, subscription-before-start order,
  failure safety, identifier checks, and secret-free output with local fakes.

### Key Entities

- **Capture request**: The checked target, filter, packet limits, and duration.
- **Capture session**: The existing card state, bounded records, and counters.
- **Capture identity**: The channel scope and identifier used to filter records and authorize a stop.
- **Capture connection**: The stream connection owned by one capture session.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The form accepts both duration boundaries and rejects every listed invalid duration.
- **SC-002**: Controlled records at 59, 61, 119, and 3599 seconds remain visible in the matching card.
- **SC-003**: Every tested capture request follows confirmation for its own subscription.
- **SC-004**: Quiet captures end only at the selected duration, a matching end event, or an operator stop.
- **SC-005**: A manual stop sends one stop only after the active capture identifier matches.
- **SC-006**: Every tested terminal path leaves no owned stream connection or helper thread.
- **SC-007**: All feature tests use local fakes or mocks and make zero live Mist calls.

## Assumptions

- The default duration remains 60 seconds.
- A capture can end before its selected duration when the cloud sends a matching end event.
- The documented capture scopes, safety classifications, packet limits, and active-status cleanup endpoint remain authoritative.
- Status and stop use `/api/v1/{sites|orgs}/{id}/pcaps/capture`. The stop operation accepts no capture identifier.
- Warning: a replacement between status and stop can receive the scope-wide stop. The identity check cannot provide atomic cancellation.
- The current generic session life limit remains unchanged for non-capture streams.
- The capture session may remain active through the selected duration plus a 30-second completion margin.
- The feature changes no menu operation, database schema, dependency, or environment variable.
- Publication requires a serial slot. No push, pull request, merge, or auto-merge is in scope.
