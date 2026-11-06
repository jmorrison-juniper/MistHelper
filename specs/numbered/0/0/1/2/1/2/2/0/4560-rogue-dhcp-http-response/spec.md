# Feature Specification: Reject Failed HTTP Data in Rogue DHCP Scans

**Feature Branch**: `jmorrison-juniper-fix-4560-rogue-dhcp-http-503`

**Created**: 2026-11-06

**Status**: Draft

**Input**: Issue #4560 reports that the rogue DHCP scan accepts an alarm from a failed HTTP 503 response.

## User Scenarios & Testing

### User Story 1 - Trust only successful scan responses (Priority: P1)

A network operator runs a rogue DHCP scan. The scan must not report a security finding from an API request that failed.

**Why this priority**: A false finding can send an operator to investigate a device without reliable evidence.

**Independent Test**: Return a failed response with a valid-looking rogue DHCP alarm and verify that the scan does not use that alarm.

**Acceptance Scenarios**:

1. **Given** a failed HTTP response with a rogue DHCP alarm body, **When** the scan reads the response, **Then** it rejects the body and reports the request failure.
2. **Given** a successful HTTP response with a rogue DHCP alarm, **When** the scan reads the response, **Then** it keeps the finding.

### Edge Cases

- A failed response can contain a valid-looking results list.
- A failed response can occur during an organization search or a site search.
- A response without a valid success status must not provide scan records.

## Requirements

### Functional Requirements

- **FR-001**: The scan MUST use response data only when the request has a successful HTTP status.
- **FR-002**: The scan MUST validate every response status before it reads that page body.
- **FR-006**: The scan MUST reject a malformed page body instead of treating it as a valid empty result.
- **FR-003**: The scan MUST report an organization request failure instead of presenting its response body as a finding.
- **FR-004**: The scan MUST report a site request failure and exclude its response body from findings.
- **FR-005**: The scan MUST keep valid findings from successful responses.

### Mist Cloud Transport Requirements

- The scan uses the existing Mist SDK methods `searchOrgAlarms`, `searchOrgDeviceEvents`, `searchSiteAlarms`, `searchSiteDeviceEvents`, `searchSiteMarvisConfigActions`, and `listOrgSites`, plus the SDK next-page reader.
- This change adds no transport, endpoint, or authentication behavior.
- Tests MUST show that each failed page stops pagination, malformed page bodies are rejected, and successful pages remain usable. Existing SDK authentication and endpoint paths remain unchanged.

### Key Entities

- **Scan response**: The result of one Mist request, including its transport status and response data.
- **Rogue DHCP finding**: Evidence that the scanner accepts from a successful response.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Zero findings come from response bodies with failed HTTP statuses.
- **SC-002**: A valid finding from a successful response remains in the scan result.
- **SC-003**: A failed site request appears in the scan's failed-site report.
- **SC-004**: A failed organization request stops the scan before pagination reads its body.
- **SC-005**: Zero records come from a later page with a failed status or malformed results.

## Assumptions

- A failed request cannot provide reliable security evidence, even when its body resembles a valid alarm.
- Existing list-based test doubles remain supported. Mist SDK response objects must provide a successful HTTP status before the scanner reads their data.
- The SDK next-page reader returns one response at a time, so the scanner can validate each page before it reads its body.
