# Feature Specification: Browser Skip Visibility

**Feature Branch**: Current worktree. No branch creation is permitted.

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #3380 requires browser tests to fail when expected portal content or seeded data is absent.

## User Scenarios & Testing

### User Story 1 - Report Missing Test Preconditions (Priority: P1)

A test maintainer receives a clear failure when the portal omits an expected row, element, link, comparison, record, or version.

**Why this priority**: A skip can report false success and can hide a product or test-data defect.

**Independent Test**: Remove one required browser item from a focused case. Confirm that the case fails with a message that names the missing item.

**Acceptance Scenarios**:

1. **Given** a browser test expects portal content, **When** the content is absent, **Then** the test fails and names the missing content.
2. **Given** a browser test expects seeded data, **When** the data is absent, **Then** the test fails and names the missing data.
3. **Given** the red-first policy guard examines the approved repair sites, **When** one site can still skip for missing content, **Then** the guard fails.

---

### User Story 2 - Complete the Capture Click Walk (Priority: P1)

A test maintainer can prove the upgrade journey through current controls without a false skip at the options page.

**Why this priority**: The stale bulk selector stops the journey before the confirm and History browser checks.

**Independent Test**: Run the focused capture journey and confirm that it uses each type selector, reaches confirm, and returns through History.

**Acceptance Scenarios**:

1. **Given** the seeded upgrade options page, **When** the walk opens the page, **Then** all three type selectors are visible.
2. **Given** each visible type selector, **When** the walk reads its options, **Then** at least one nonempty version option exists.
3. **Given** valid type selections, **When** the walk saves the plan, **Then** it reaches the confirm page through browser actions.
4. **Given** the saved run, **When** the walk opens History and selects its run, **Then** it returns to the confirm page through browser actions.

---

### User Story 3 - Preserve Capability Skips (Priority: P2)

A test maintainer sees a skip only when the workstation lacks a genuine browser capability.

**Why this priority**: A missing browser runtime is an environment limitation, not a portal failure.

**Independent Test**: Run a browser-capability case without the required browser component. Confirm that the case skips with the capability cause.

**Acceptance Scenarios**:

1. **Given** the workstation cannot provide the required browser capability, **When** a browser test starts, **Then** the test can skip with the cause.
2. **Given** the browser starts, **When** portal content or seeded data is absent, **Then** the test fails instead of skipping.

### Edge Cases

- A locator exists but is not visible. The test must fail and name the locator.
- A selector contains only its empty prompt. The test must fail and name the selector.
- A comparison page returns to the picker. The test must fail and include the refusal reason.
- A previous-page control has no link when the test requires another page. The test must fail and name the page.
- A fixture helper serves several tests. Each affected focused test must report a failure, not one hidden skip.
- A browser package, executable, or server capability is unavailable. The existing capability skip can remain.

## Requirements

### Functional Requirements

- **FR-001**: Browser tests MUST use a skip only for a genuine unavailable browser capability.
- **FR-002**: Missing expected UI content MUST cause a failure with a message that names the missing content.
- **FR-003**: Missing seeded test data MUST cause a failure with a message that names the missing data.
- **FR-004**: The red-first policy guard MUST examine all 16 approved repair sites.
- **FR-005**: The red-first policy guard MUST fail when an approved site can skip because expected UI or seeded data is absent.
- **FR-006**: The guard failure MUST identify the file, location, and forbidden skip condition.
- **FR-007**: The operations workflow MUST fail when no accordion category reveals an operation row.
- **FR-008**: The token sign-in flow MUST fail when no row matches its required identifier prefix.
- **FR-009**: The capture flow MUST fail when the site picker has no site row.
- **FR-010**: The capture walk MUST fail when a required upgrade version control is missing or has no real option.
- **FR-011**: The comparison flow MUST fail when a required comparison table has no row.
- **FR-012**: The comparison flow MUST fail when the expected comparison does not render.
- **FR-013**: The comparison picker MUST fail when it has no stored-capture option.
- **FR-014**: The History flow MUST fail when the site picker has no site row.
- **FR-015**: The History flow MUST fail when the seeded store has no capture row.
- **FR-016**: The History flow MUST fail when a required previous-page control has no link.
- **FR-017**: The sign-in flow MUST fail when no row matches its required identifier prefix.
- **FR-018**: The site-selection flow MUST fail when no row matches its required identifier prefix.
- **FR-019**: The site-selection flow MUST fail when the inventory table has no row.
- **FR-020**: The stop flow MUST fail when the site picker has no site row.
- **FR-021**: The existing-run flow MUST fail when the site picker has no site row.
- **FR-022**: The two-operator flow MUST fail when the site picker has no site row.
- **FR-023**: The capture walk MUST replace `upgrade-version-select-all` with the AP, switch, and gateway controls.
- **FR-024**: The capture walk MUST require `upgrade-version-select-ap` to be visible and to offer a real option.
- **FR-025**: The capture walk MUST require `upgrade-version-select-switch` to be visible and to offer a real option.
- **FR-026**: The capture walk MUST require `upgrade-version-select-gateway` to be visible and to offer a real option.
- **FR-027**: The capture walk MUST select a real option from each required type control.
- **FR-028**: The capture walk MUST preserve its confirm-page and History return checks.
- **FR-029**: The repair MUST preserve browser-capability skips and their specific cause messages.
- **FR-030**: The repair MUST NOT change production code or shared fixtures.
- **FR-031**: The repair MUST NOT edit `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`.

### Approved Repair Inventory

The implementation must repair these 16 statements and no additional skip category.

| ID | Test file | Missing condition that must fail |
| - | - | - |
| R-01 | `tests/e2e/web_portal/test_operations_panel_workflow.py` | No accordion category reveals an operation row |
| R-02 | `tests/e2e/upgrade_portal/test_browser_token_signin.py` | No element matches the required row prefix |
| R-03 | `tests/e2e/upgrade_portal/test_capture.py` | The site picker has no site row |
| R-04 | `tests/e2e/upgrade_portal/test_capture.py` | A required type version control is absent or has no real option |
| R-05 | `tests/e2e/upgrade_portal/test_comparison.py` | A required comparison table has no row |
| R-06 | `tests/e2e/upgrade_portal/test_comparison.py` | The expected comparison does not render |
| R-07 | `tests/e2e/upgrade_portal/test_comparison.py` | The picker has no stored-capture option |
| R-08 | `tests/e2e/upgrade_portal/test_history.py` | The site picker has no site row |
| R-09 | `tests/e2e/upgrade_portal/test_history.py` | The seeded store has no history row |
| R-10 | `tests/e2e/upgrade_portal/test_history.py` | A required previous-page control has no link |
| R-11 | `tests/e2e/upgrade_portal/test_signin.py` | No element matches the required row prefix |
| R-12 | `tests/e2e/upgrade_portal/test_site_selection.py` | No element matches the required row prefix |
| R-13 | `tests/e2e/upgrade_portal/test_site_selection.py` | The inventory table has no row |
| R-14 | `tests/e2e/upgrade_portal/test_stop.py` | The site picker has no site row |
| R-15 | `tests/e2e/upgrade_portal/test_run_controls/test_existing.py` | The site picker has no site row |
| R-16 | `tests/e2e/upgrade_portal/test_two_operators.py` | The site picker has no site row |

### Scope Boundaries

- Production code is out of scope.
- Shared browser fixtures are out of scope.
- Shared seeded-data fixtures are out of scope.
- Browser capability detection is out of scope, except to preserve valid skips.
- Timeout values, browser markers, test order, and unrelated assertions are out of scope.
- Cancellation of a foreign run is out of scope.
- Direct API cleanup as a replacement for the browser walk is out of scope.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The red-first policy guard fails when one approved repair site retains a missing-content skip.
- **SC-002**: The red-first guard reports 16 examined repair sites and identifies the introduced violation.
- **SC-003**: All 16 approved statements fail with specific messages when their required UI or seeded data is absent.
- **SC-004**: Every focused test affected by the 16 repairs completes with zero skips after the repair.
- **SC-005**: The focused capture journey completes with one pass and zero skips.
- **SC-006**: The capture walk proves visibility for all three current type controls.
- **SC-007**: The capture walk proves that each current type control offers at least one real version.
- **SC-008**: The capture walk reaches both confirm-page visits through browser actions.
- **SC-009**: Genuine missing browser capability cases continue to report a skip with a specific cause.
- **SC-010**: The implementation diff contains no change to `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`.
- **SC-011**: The implementation diff contains no production-code or shared-fixture change.

## Assumptions

- The approved structural assessment identifies the complete set of 16 skip statements.
- Existing isolated test inputs can supply the required rows, records, comparisons, links, and versions.
- The current options page uses separate AP, switch, and gateway version controls.
- A real version option is any selectable option after the empty prompt.
- Existing focused browser tests define the correct user journeys and do not need new production behavior.
