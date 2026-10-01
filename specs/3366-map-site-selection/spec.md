# Feature Specification: Maps Site Selection

**Feature Branch**: `jmorrison-juniper-maps-site-selection-race`

**Created**: 2026-10-01

**Status**: Specified

**Input**: Repair [issue #3366](https://github.com/jmorrison-juniper/MistHelper/issues/3366) without changing ordinary Maps behavior.

**Claim**: [Session ownership](https://github.com/jmorrison-juniper/MistHelper/issues/3366#issuecomment-5936415025).

**Initial source**: `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.

**Session**: `30f76f57-bbfa-4033-8d6b-b01332decdeb`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the latest site's floor plans (Priority: P1)

The operator selects a site and receives only that site's floor plans.
An earlier response must not change the controls after a later selection.

**Why this priority**: A contaminated list permits selection of the wrong site's floor plan.

**Independent Test**: Hold A's actual Chromium request, select B, complete B, then release A.
Use the actual Site control and a private local server.
Require only B's floor plan after both responses complete.
Record exactly two GET requests and zero temporary stale mutations.

**Acceptance Scenarios**:

1. **Given** A remains pending, **When** B completes and then A completes, **Then** B's controls remain exact.
2. **Given** A remains pending, **When** A completes before pending B, **Then** B's controls remain blank and disabled.
3. **Given** the operator selects A-B-A, **When** A2 completes before A1, **Then** only A2 can change the controls.
4. **Given** B's map is visible, **When** A completes, **Then** B's selection and displayed map remain unchanged.

The A-B journey must fail against unchanged production source before the repair.
An environment error, timeout, or skip does not prove the defect.

### User Story 2 - Show current failures only (Priority: P1)

The operator receives one visible error when the current map-list request fails.
Earlier successes and failures must not change the current error.

**Why this priority**: A silent failure falsely suggests that a site has no floor plans.

**Independent Test**: Complete actual browser requests with controlled transport, status, body, and list failures.

**Acceptance Scenarios**:

1. **Given** the current request fails, **When** its continuation runs, **Then** one visible error appears with blank, disabled controls.
2. **Given** the response reports an error with an empty or nonempty list, **When** it completes, **Then** the error takes precedence.
3. **Given** B is pending, successful, or failed, **When** A succeeds or fails, **Then** B's complete state remains unchanged.
4. **Given** A2 is successful or failed, **When** A1 fails, **Then** A2's state remains unchanged despite their equal site identifier.
5. **Given** a current error appears, **When** another site is selected, **Then** the new selection clears the prior error.

### User Story 3 - Preserve blank and empty selections (Priority: P2)

The operator can clear a selection safely.
A valid empty list remains a success.

**Why this priority**: Earlier responses must not restore cleared controls or a cleared map.

**Independent Test**: Clear a site with pending requests and complete a valid empty list separately.

**Acceptance Scenarios**:

1. **Given** a current empty list, **When** it completes, **Then** the blank option remains enabled without an error.
2. **Given** A remains pending, **When** the blank site is selected, **Then** the controls, map, image note, and device panel clear.
3. **Given** the blank site remains selected, **When** A succeeds or fails, **Then** the cleared state remains unchanged.
4. **Given** A-blank-A occurs, **When** A1 completes after A2, **Then** A2 alone controls the page.
5. **Given** a visible map, **When** the blank map is selected, **Then** the map clears without another data or image request.

### User Story 4 - Preserve ordinary Maps behavior (Priority: P2)

The operator retains floor plan labels, dimensions, images, device positions, and readable theme titles.

**Why this priority**: The repair must not weaken existing map rendering or late-response protection.

**Independent Test**: Run unchanged adjacent Maps tests, including image handling and measured title contrast.

**Acceptance Scenarios**:

1. **Given** a current list, **When** it completes, **Then** option identifiers, order, safe labels, image suffixes, and dimensions remain correct.
2. **Given** a map selection, **When** its data completes, **Then** existing rendering, image notes, dimensions, devices, and current errors remain correct.
3. **Given** an earlier map-data or image completion, **When** the selection changes, **Then** the existing view protection remains effective.
4. **Given** any shipped theme, **When** the title appears, **Then** its measured contrast remains at least 4.5:1.
5. **Given** a displayed map, **When** the theme changes, **Then** its viewing state remains unchanged without another Maps request.

### Edge Cases

- Stale successes and failures complete while the current selection is pending, successful, failed, or blank.
- A-B-A and A-blank-A reuse a site identifier but create distinct selection occurrences.
- Valid empty lists differ from explicit errors, failed status codes, unreadable bodies, and invalid lists.
- Invalid entries after valid entries must not produce partial selectable lists.
- Untrusted labels and errors must remain safe text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every site selection MUST create a distinct occurrence, including blank and repeated site selections.
- **FR-002**: Every site selection MUST reset the floor plan controls and clear the prior view and error immediately.
- **FR-003**: Only the latest occurrence MUST populate or enable controls or show a request error.
- **FR-004**: Every stale success and failure MUST cause zero control, selection, dimension, notification, or view changes.
- **FR-005**: Current successful lists MUST preserve the blank option, order, identifiers, labels, image suffixes, and dimensions.
- **FR-006**: Current valid empty lists MUST enable only the blank option without an error or automatic map selection.
- **FR-007**: Observable current failures MUST NOT become successful empty results. An explicit error MUST take precedence over any list.
- **FR-008**: Current failures MUST show one safe visible error and leave blank, disabled controls.
- **FR-009**: Blank site selections MUST invalidate earlier work without another map-list, data, or image request.
- **FR-010**: Blank map selections MUST clear the existing view without another data or image request.
- **FR-011**: Request paths, methods, options, and counts MUST remain unchanged. Each nonblank site selection starts one map-list GET.
- **FR-012**: Existing map rendering, images, device positions, current map-data errors, and view protection MUST remain unchanged.
- **FR-013**: All four shipped themes MUST retain title contrast of at least 4.5:1 and preserve the map without additional requests.
- **FR-014**: Labels and errors MUST remain safe text without executing markup or exposing credentials.

### Verification Requirements

- **VR-001**: Prove the primary real Chromium race red before changing production source. Compare the template bytes with the initial revision.
- **VR-002**: Prove A-B-A and A-blank-A with distinct A1 and A2 floor plans and exact request counts.
- **VR-003**: Cover actual connection failure, HTTP 4xx and 5xx, invalid JSON, empty bodies, explicit errors, and missing or invalid lists.
  Every request wait has a 15-second bound.
  Require actual completion-handler execution and zero uncaught page errors after handled failures.
- **VR-004**: Execute the shipped script offline with controlled promises.
  Independently prove one accepted observation and at least five rejected incorrect observations.
- **VR-005**: Required guards MUST fail for missing source, snapshot, or request-order evidence.
  Report nonzero checked counts and name unreadable or missing inputs.
- **VR-006**: Keep traces, screenshots, coverage, ledgers, observations, and logs below `data/issue-3366/`.
  Separate red and green evidence and record source identity.
- **VR-007**: Run unchanged adjacent Maps, image-route, safe-text, title-theme, image-browser, and title-contrast tests.
  Do not edit shared fixtures or expectations.
- **VR-008**: Run full configured Ruff, Black, exact CI MYPY_PATHS, configured Bandit, and the unchanged quality ratchet.
  Run runtime dependency audit, owned Markdown links, and STE.
  Report missing STE dictionary or PowerShell capabilities as unavailable, not measured.
- **VR-009**: Use only synthetic local records.
  Reject unexpected remote browser requests.
  Use no credentials, production API, production store, container, dependency change, suppression, or baseline change.

### Key Entities *(include if feature involves data)*

- **Selection occurrence**: One Site control change that owns the current floor plan list.
- **Map-list response**: The success or failure of one request for a selection occurrence.
- **Floor plan option**: Its identifier, plain label, image suffix, width, and height.
- **Page observation**: Complete controls, visible error, displayed map, and request-order evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every A-B case retains only the current floor plan with exactly two map-list requests.
- **SC-002**: A-B-A retains A2 only with exactly three requests. A-blank-A retains A2 only with exactly two requests.
- **SC-003**: Every current failure shows one error. Every stale completion causes zero temporary or final changes.
- **SC-004**: Blank choices add zero requests. Valid empty lists remain enabled without errors.
- **SC-005**: Required observations complete within their 15-second bounds. Zero required cases skip.
- **SC-006**: Adjacent Maps checks pass unchanged, including all four title themes at or above 4.5:1.
- **SC-007**: Reviewers receive defect-specific red evidence, green behavior, independent guard failures, changed-region coverage, and exact gate outcomes.

## Assumptions

The repair covers failures observable at the browser boundary.
It does not change the backend's existing conversion of some SDK failures into empty lists.
Existing local Python, Node, and Chromium packages provide execution support.
Missing required execution capability blocks behavioral acceptance.

The explicit feature directory replaces shared SpecKit state.
All writes remain in the eight reserved files.
Do not edit README, CHANGELOG, dependencies, quality settings, exclusions, or shared browser support.

Publication waits at position 15 after issue #3353.
Only the parent's explicit full verified-main SHA releases publication.
After release, repeat local proof on the released base before publication and protected merge.
Run exact merged-main tests in this same isolated worktree.
No deployment or production service action is authorized.
