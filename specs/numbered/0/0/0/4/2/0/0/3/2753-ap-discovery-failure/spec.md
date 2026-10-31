# Feature Specification: AP discovery failure

**Feature Branch**: `jmorrison-juniper-audit-missing-input-defaults`

**Created**: 2026-10-30

**Status**: Approved bounded scope

**Input**: Repair one first-batch missing-input default. Part of #2753. Do not merge.

## User Scenarios & Testing

### User Story 1 - Refuse incomplete site discovery (Priority: P1)

An operator needs a complete site read before an AP migration plan.
A failed read must not appear as a successful empty or partial read.

**Why this priority**: An incomplete plan can omit APs without a warning.

**Independent Test**: Simulate a failed site read with absent, empty, and populated first-page data.

**Acceptance Scenarios**:

1. **Given** a failed site read, **When** discovery runs, **Then** it reports the error and stops.
2. **Given** a failed site read, **When** migration runs, **Then** it creates no plan, backup, or device change.
3. **Given** a successful empty read, **When** discovery runs, **Then** it preserves the empty result.
4. **Given** a successful complete read, **When** discovery runs, **Then** it preserves the selected AP records.

### Edge Cases

- The response can lack data when the read fails.
- A failed later page can leave populated first-page data.
- An explicit successful empty collection remains valid.

## Requirements

### Functional Requirements

- **FR-001**: A failed organization site read must stop AP discovery with the original error.
- **FR-002**: The error log must identify the failed site read without response bodies or credentials.
- **FR-003**: A failed read must not produce an empty-success message, migration plan, backup, or device change.
- **FR-004**: Successful empty reads and complete AP selection must retain their current results.
- **FR-005**: The repair must change only the site-read failure boundary.

### Mist Cloud Transport Requirements

Retain `mistapi.api.v1.orgs.sites.listOrgSites`, `mistapi.get_all`, and
`mistapi.api.v1.sites.devices.listSiteDevices`. Add no transport.
Use mocked SDK calls for all evidence. Do not contact Mist.

### Key Entities

- **Site collection**: The complete organization site list used for AP discovery.
- **Discovery failure**: An error that prevents a complete site collection.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every simulated site-read failure stops discovery and produces an error log.
- **SC-002**: Failed discovery produces zero plans, confirmations, backups, and device changes.
- **SC-003**: Successful empty and populated reads preserve their exact expected records.

## Assumptions

- This slice covers a raised site-pagination error, not every possible malformed SDK response.
- Per-site device-read failures retain their existing behavior and remain outside this slice.
- Credential and resource identifier validation belong to #2861 and #2863.
- The 99 unresolved upgrade candidates and shared analyzer baseline remain unchanged.
- The coordinator reviews the pull request. Issue #2753 remains open.
