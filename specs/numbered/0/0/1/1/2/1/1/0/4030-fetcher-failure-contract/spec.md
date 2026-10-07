# Feature Specification: Fetcher Failure Contract

**Feature Branch**: `jmorrison-juniper-fix-4030-fetcher-failure-contract`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #4030: Menu 95 reports Complete after required site resolution fails.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report the missing site as a failure (Priority: P1)

As a network operator, I need Menu 95 to report a clear failure when it cannot
resolve a site. I must not receive a Complete status for an operation that did
not reach the device data request.

**Why this priority**: A false Complete status hides a required-input failure
and can cause the operator to trust unrelated output as the requested result.

**Independent Test**: Run the device fetcher with no resolvable site. Verify
that it returns an explicit failure and emits the exact operator error.

**Acceptance Scenarios**:

1. **Given** the device fetcher has no site ID and site selection returns no
   value, **When** the fetch starts, **Then** it emits
   `! Error fetching device data: site ID could not be resolved.`.
2. **Given** the site ID cannot be resolved, **When** the fetch ends, **Then**
   it returns explicit `False` and does not continue to device selection.
3. **Given** the site ID cannot be resolved, **When** the fetch ends, **Then**
   it makes no Mist cloud request and creates no requested result file.

---

### User Story 2 - Keep the portal verdict correct with unrelated output (Priority: P2)

As a portal operator, I need Menu 95 to report Failed even when another process
creates unrelated output during the run. The unrelated output must not convert
the fetcher failure into a Complete status.

**Why this priority**: Issue #4030 includes concurrent output contamination.
The status must use the operation failure evidence before output evidence.

**Independent Test**: Execute Menu 95 through the real display and fetcher path.
Add unrelated output evidence during the run. Verify that the pre-repair path
reports completed and the repaired path reports failed.

**Acceptance Scenarios**:

1. **Given** Menu 95 cannot resolve a site and unrelated output appears during
   the run, **When** the portal assesses the result, **Then** the run status is
   Failed.
2. **Given** the fetcher emits the required error, **When** the portal scans the
   run log, **Then** the existing `error fetching` handled-error marker selects
   the exact error as the failure reason.
3. **Given** the fetcher returns `False`, **When** the existing Menu 95 display
   path receives the result, **Then** it does not log its completion message.

### Edge Cases

- A pre-supplied valid site ID continues to the existing device selection and
  fetch flow.
- A missing device ID after successful site resolution keeps its existing
  behavior. This feature changes only the site-resolution failure.
- An honest empty Mist response after a successful request keeps its existing
  no-data behavior.
- Unrelated files or site-analysis rows can appear during the run. They do not
  override the handled-error verdict.
- The error text is case-sensitive in operator output, but portal matching
  remains case-insensitive through the existing marker classifier.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `DeviceDataFetcher.fetch()` MUST treat unresolved `site_id` as an
  explicit failed fetch.
- **FR-002**: The unresolved-site path MUST emit the operator-visible error
  `! Error fetching device data: site ID could not be resolved.`.
- **FR-003**: The unresolved-site path MUST return explicit `False`.
- **FR-004**: The unresolved-site path MUST stop before device selection, Mist
  cloud access, data processing, display rendering, or result-file creation.
- **FR-005**: The repair MUST remain in the device fetcher. It MUST NOT change
  `web_portal/services/operation.py`, `PARAMETER_REGISTRY`, or
  `src/interfaces/visualization/ui/interactive_display_utils.py`.
- **FR-006**: The existing display contract that suppresses completion after an
  explicit `False` result MUST remain unchanged.
- **FR-007**: The error wording MUST include the existing portal
  `error fetching` handled-error marker.
- **FR-008**: The specification MUST record that FR-007 depends on the
  log-marker coupling tracked by issue #3168.
- **FR-009**: A focused fetcher contract test MUST verify the exact error,
  explicit `False`, and the absence of device selection and fetch activity.
- **FR-010**: A portal regression test MUST execute the real Menu 95 display
  and fetcher path rather than substitute a fake fetcher result.
- **FR-011**: The portal regression MUST add unrelated output evidence and
  prove that the run reports completed before the repair and failed after it.
- **FR-012**: The portal regression MUST verify that the portal failure reason
  contains the exact fetcher error.
- **FR-013**: The change MUST add a release-note fragment for issue #4030.
- **FR-014**: This feature specification MUST NOT implement product code.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested unresolved-site attempt returns a failed result
  before any device request begins.
- **SC-002**: The operator sees the required error text in 100 percent of the
  tested unresolved-site attempts.
- **SC-003**: Menu 95 reports Failed in the portal when unrelated output exists
  during the same unresolved-site run.
- **SC-004**: The focused fetcher test and the portal regression each fail
  against the pre-repair behavior and pass after the fetcher repair.
- **SC-005**: Existing successful Menu 95 behavior and non-site failure behavior
  remain unchanged in the applicable regression suite.

## Assumptions

- Issue #4030 covers only the false terminal verdict. Missing portal controls
  remain outside this feature.
- The existing portal handled-error classifier continues to check the
  `error fetching` marker before it accepts output evidence.
- Issue #3168 remains the owner of the broader work to replace log-prose
  coupling with an explicit outcome contract.
- The implementation phase can extend existing fetcher and portal test modules
  or add focused issue-specific test modules.

## Dependencies

- **Issue #3168**: The portal currently infers handled failures from log text.
  This feature intentionally uses that established coupling and does not
  replace it.
- **Existing display contract**: `InteractiveDisplayUtils.device_tests()`
  already stops its completion log when the fetcher returns explicit `False`.

## Out of Scope

- Adding Menu 95 site or gateway controls.
- Changing portal parameter definitions or operation classification.
- Refactoring the portal outcome model from log markers to typed outcomes.
- Changing device-resolution, Mist response, or successful export behavior.
