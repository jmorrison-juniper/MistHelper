# Feature Specification: WebSocket Audit Compatibility

**Feature Branch**: `jmorrison-juniper-websocket-live-audit-compatibility`

**Created**: 2026-10-05

**Status**: Draft

**Input**: Issue #3923, a narrow follow-up to #3862 and #3889/#3903 at merge commit `38c957ec`.

## User Scenarios & Testing

### User Story 1 - Audit scoped client discovery (Priority: P1)

An audit maintainer needs the read-only client picker request to pass only when approved site
and device responses establish the exact site-to-device association. The audit must continue to
block every request outside that scope.

**Why this priority**: The current audit rejects a valid client discovery read. A broad exception
could expose unrelated site data or permit an operation request.

**Independent Test**: Use the isolated browser audit with synthetic parent and client responses.
Confirm that the exact approved GET is allowed, that out-of-scope requests are denied before
transmission, and that no live operation runs.

**Acceptance Scenarios**:

1. **Given** an approved site response and that site's approved device response, **When** the
   audit requests `GET /api/websockets/sites/{site_id}/devices/{device_id}/clients` for that
   returned device, **Then** the read is permitted.
2. **Given** a missing, malformed, empty, or unrelated site or device response, **When** the
   audit requests that client path, **Then** the request is denied before transmission.
3. **Given** a valid client path, **When** the request uses another method, origin, query,
   redirect, or encoded path, **Then** the request remains denied before transmission.
4. **Given** any mutation endpoint, **When** the audit encounters it, **Then** it remains denied.
5. **Given** the installed SDK source for each discovery method, **When** verification runs,
   **Then** it confirms a GET implementation without invoking the method.

---

### User Story 2 - Report visible cancellation accurately (Priority: P2)

An audit maintainer needs the result for each dialog to reflect the visible Cancel control,
instead of a fixed unsupported value.

**Why this priority**: The current dialog has a visible Cancel control. A fixed unsupported result
creates a false finding and weakens the audit report.

**Independent Test**: In the isolated browser, inspect the real rendered form and compare the
reported count and cancellation finding with the visible, exact-name Cancel controls.

**Acceptance Scenarios**:

1. **Given** one visible button named `Cancel` with test ID `ws-cancel-selection-button` in the
   operation form, **When** the dialog audit records the form, **Then** it reports one control
   and no missing-cancel finding.
2. **Given** no visible Cancel control, **When** the dialog audit records the form, **Then** it
   reports zero controls and the `operation-cancel` finding used by
   `UtilityExperienceInspector`.
3. **Given** a hidden or duplicate Cancel control, **When** the dialog audit records the form,
   **Then** its count reflects visible controls and the result does not report an exact single
   visible control.

### Edge Cases

- A site response has an invalid shape, invalid identifier, or no rows.
- A device response has an invalid shape, invalid identifier, no rows, or a device from another site.
- The client path has a query, encoded path character, redirect, or an origin that differs from
  the approved origin.
- A request uses `POST`, `PUT`, `PATCH`, `DELETE`, or another non-GET method.
- The rendered form has no `ws-cancel-selection-button`, only a hidden control, or more than one
  visible Cancel control.
- A failure during form inspection must not remove that form from the audit result count.

## Requirements

### Functional Requirements

- **FR-001**: The audit MUST permit the exact client discovery path only as a GET after the
  approved site response and the matching site's approved device response establish both IDs.
- **FR-002**: The audit MUST deny client discovery when either parent response is absent,
  malformed, empty, or does not associate the requested device with the requested site.
- **FR-003**: The audit MUST preserve default denial for non-GET methods, other origins,
  queries, redirects, and encoded paths. It MUST deny mutation endpoints.
- **FR-004**: The audit MUST verify the installed SDK source for each SDK method used by the
  device and client discovery chain. This includes
  `mistapi.api.v1.sites.devices.listSiteDevices`,
  `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients`, and the existing
  `mistapi.api.v1.sites.stats.getSiteSdkStatsByMap` client discovery method. Each method MUST
  have a GET implementation. The audit MUST NOT invoke these SDK methods during verification.
- **FR-005**: The dialog audit MUST measure the number of visible `ws-cancel-selection-button`
  controls named exactly `Cancel` in the actual operation form. It MUST report the measured
  count for each inspected form.
- **FR-006**: The dialog audit MUST use the `operation-cancel` finding when the form has no
  visible Cancel control. It MUST report no missing-cancel finding when exactly one visible
  control exists. A hidden or duplicate control MUST NOT count as one visible control.
- **FR-007**: Isolated regression tests MUST use synthetic responses and local browser routes.
  They MUST verify both permitted scope and denial boundaries without credentials, live
  operations, or portal deployment.
- **FR-008**: The audit MUST preserve a result record for every inventory entry when an
  inspection fails. The result count MUST match the inventory count.

### Mist Cloud Transport Requirements

- Client discovery uses the installed SDK method
  `mistapi.api.v1.sites.wired_clients.searchSiteWiredClients`. Site devices use
  `mistapi.api.v1.sites.devices.listSiteDevices`. The map client picker uses
  `mistapi.api.v1.sites.stats.getSiteSdkStatsByMap`.
- Verify each installed SDK implementation is a GET by reading its source. Do not invoke a
  method or use credentials during verification.
- Keep isolated tests on synthetic local responses. They must show that denied requests do not
  transmit and that no mutation endpoint receives a request.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The exact client discovery GET passes only after the same site's approved device
  response establishes the requested device. All tested scope violations are denied before
  transmission.
- **SC-002**: The isolated denial tests transmit zero requests to a disallowed origin, method,
  query, redirected path, encoded path, or mutation endpoint.
- **SC-003**: Each inspected catalog entry produces one audit record. The record count equals
  the loaded inventory count, which is 72 for the current baseline.
- **SC-004**: The cancellation report equals the count of visible exact-name Cancel controls.
  One visible control produces no missing-cancel finding. Zero visible controls produce the
  `operation-cancel` finding.
- **SC-005**: SDK source verification confirms GET implementations for all three named methods
  without invoking them. Isolated tests use no credentials and transmit no live requests.

## Assumptions

- Approved site IDs come only from the approved site response. Device IDs come only from the
  approved device response for that same site.
- The request path has no query string. Any query or path encoding remains denied.
- The current audit inventory contains 72 entries. Tests compare their result count with the
  loaded inventory rather than treating 72 as a permanent count.
- This change updates the audit harness, its isolated tests, and related documentation.
  It does not change the production portal or authorize mutation requests.
- This internal-only change requires no release fragment under `changelog.d/README.md`.
- The work includes implementation and publication for review. It does not execute live requests or operations.
