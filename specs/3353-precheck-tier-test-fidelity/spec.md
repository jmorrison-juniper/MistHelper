# Feature Specification: Pre-check tier test fidelity

**Feature Branch**: `jmorrison-juniper-precheck-tier-test-fidelity`

**Created**: 2026-10-01

**Status**: Locally verified

**Input**: [Issue #3353](https://github.com/jmorrison-juniper/MistHelper/issues/3353) requests a test-only repair.

## User Scenarios & Testing

### User Story 1 - Read the selected capture tier (Priority: P1)

The browser store returns the identifier and tier of the selected standalone pre-check.
The store uses the existing selection rules.

**Why this priority**: Without the pair reader, the route assigns tier 2 to every browser pre-check.

**Independent Test**: Compare the returned identifier and tier against explicit expected values in unit tests.

**Acceptance Scenarios**:

1. Given a verified standalone capture with tier 3, the pair reader returns its identifier and tier 3.
2. Given a newer capture that a run owns, the pair reader returns the selected standalone capture and its tier.
3. Given captures in reverse start-time order, the pair reader returns the newest matching capture and its tier.
4. Given no matching capture, the pair reader returns an empty identifier and the production default tier.
5. Given a missing or malformed tier, the pair reader uses the existing production conversion.

### User Story 2 - Prove the displayed tier (Priority: P1)

The browser journey reads the tier cells after the operator takes and retakes standalone pre-checks.

**Why this priority**: The request body proves the requested tier, but it does not prove the displayed tier.

**Independent Test**: Run the missing-pre-check journey in an isolated Chromium browser.

**Acceptance Scenarios**:

1. With the current seeds, expect tier 2 for the first site and a dash for the second site.
2. After a tier 3 capture of the second site, expect 3 in its tier cell.
3. After tier 2 captures of both sites, expect 2 in both tier cells.
4. The operation must retain the identifiers from the retake.

### Edge Cases

- The tier field can hold an integer, text, a boolean, an unsupported number, an empty value, or another shape.
- A missing capture must not cause an exception or adopt a capture from another site.
- Equal start times retain the existing store-order decision.
- The existing capture-origin, time, and verification rules remain unchanged.

## Requirements

### Functional Requirements

- **FR-001**: `PortalRecordStore` must expose `newest_precheck_tier(site_id) -> tuple[str, int]`.
- **FR-002**: The pair reader must reuse `newest_precheck` to select the capture.
- **FR-003**: The pair reader must reuse the production tier conversion and default without adding a fallback policy.
- **FR-004**: Unit tests must prove the returned identifier and tier together.

- **FR-005**: Browser assertions must read actual tier cells before and after the captures.
- **FR-006**: The adjacent single-site, standalone-adoption, and tier journeys must retain their behavior.
- **FR-007**: Production code, shared factories, authentication, dependency files, and quality baselines must remain unchanged.

### Key Entities

- A standalone pre-check contains a capture identifier, site identifier, tier, role, start time, and verification state.
- A tier cell displays the selected capture's tier, or a dash when no capture exists.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The pair tests fail against the unchanged stand-in and pass after the repair.
- **SC-002**: The tier 3 cell assertion fails against the unchanged stand-in and passes after the repair.
- **SC-003**: The focused unit tests cover every executable line and branch of the new method.
- **SC-004**: Run the relevant journeys in isolated Chromium. Require no browser dependency skip.
- **SC-005**: The local commit contains only the seven reserved issue-owned files.

## Assumptions

- The starting main revision is `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.
- That revision already contains the repair of standalone selection for issue #3360.
- The current tier 3 seed belongs to a run. The separate standalone seed stores tier 2.
- This session stops after a clean local commit and an evidence report to the parent.
- Remote publication requires the parent's explicit release after issue #3290.
