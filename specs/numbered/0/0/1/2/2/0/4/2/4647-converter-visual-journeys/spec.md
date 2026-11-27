# Feature Specification: Add independently authored converter visual journeys

**Feature Branch**: `feat/4647-converter-visual-journeys` (planned)

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4647. Parent: #4224. Program tasks: T029 and T030 in the full-parity task map.

**Input**: Issue #4647 body and comments, read on 2026-11-26.

## Clarifications

### Session 2026-11-26

- Q: Which file holds the browser journeys? A: `tests/e2e/web_portal/test_portal_smoke.py`. The planned file `test_cisco_parity.py` would add a child to a noncompliant directory. See D-1.
- Q: Which word confirms export? A: `EXPORT`. The words `APPLY` and `CONFIRM` stay reserved for cloud and administrative tasks. See D-2.
- Q: Does this change register the converter in the production portal? A: No. A test host mounts the converter for one test class. See D-3.
- Q: Which browser storage key may exist after a journey? A: Only `misthelper-theme`, written by the portal host. See D-4.
- Q: Does this change alter server routes or JSON shapes? A: No. The current routes and proposal shapes stay unchanged. See D-6.
- Q: Which themes and viewports apply? A: The four shipped themes and the phone and desktop viewports from the responsive tests. See D-8.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review and export a proposal in the portal (Priority: P1)

An operator opens the converter page in the portal host. The operator selects a synthetic configuration file, enters a template name, and requests a preview. The page shows a structured review. The operator reviews the proposal, types `EXPORT`, and exports the JSON.

**Why this priority**: This journey proves T029 and T030 in the real portal host. No other journey proves the full visual flow.

**Independent Test**: Run `test_structured_review_and_typed_export`. It checks each step, the portal navigation, the storage keys, and the download.

**Acceptance Scenarios**:

1. **Given** the converter page is open, **When** the operator submits a synthetic file, **Then** the review shows template name, unsupported items, and known gaps.
2. **Given** a reviewed proposal, **When** the operator types `EXPORT` and selects the export control, **Then** the browser downloads `cisco-proposal.json` and the status confirms the export.

### User Story 2 - Confirm, cancel, and reset without ambiguity (Priority: P1)

An operator cannot export until the typed word equals `EXPORT`. Cancel clears the typed word. Reset clears all converter state. A changed input clears the proposal and the review.

**Why this priority**: Export must need a deliberate operator action. Unclear state can export the wrong proposal.

**Independent Test**: Run `test_typed_word_gates_export_and_cancel_clears_it` and `test_reset_and_input_change_clear_state`.

**Acceptance Scenarios**:

1. **Given** a reviewed proposal, **When** the typed word is wrong, **Then** the export control stays disabled and the status names the required word.
2. **Given** a typed word, **When** the operator cancels the confirmation, **Then** the typed word clears and the review remains.
3. **Given** a proposal, **When** the operator resets the page or changes the file, **Then** the proposal and the review clear.

### User Story 3 - Use the converter with a keyboard and readable status (Priority: P2)

An operator completes the journey with a keyboard only. A visible focus outline marks each focused control. Each status names its outcome in words, not only in color.

**Why this priority**: The issue requires keyboard access and status that does not depend on color.

**Independent Test**: Run `test_keyboard_only_journey_shows_focus`.

**Acceptance Scenarios**:

1. **Given** the converter page, **When** the operator uses Tab, Enter, and Space only, **Then** the journey completes.
2. **Given** any shipped theme, **When** a control has focus, **Then** a focus outline is visible.

### User Story 4 - Use every shipped theme at phone and desktop widths (Priority: P2)

An operator opens the converter in each shipped theme at a phone viewport and at a desktop viewport. The page shows no horizontal scrolling. The converter uses only host theme tokens for colors.

**Why this priority**: The issue names four theme intentions and two widths.

**Independent Test**: Run `test_shipped_theme_at_viewport` with its eight cases and `test_presentation_uses_host_theme_tokens`.

**Acceptance Scenarios**:

1. **Given** any shipped theme and the phone viewport, **When** the page loads, **Then** the document width equals the viewport width.
2. **Given** the converter stylesheet, **When** a test reads it, **Then** the file contains no color literal.

### User Story 5 - Keep user text inert and cloud operations disabled (Priority: P2)

A template name or command line that contains markup appears as plain text. The browser never sends a request to a host other than the loopback address.

**Why this priority**: Source configuration text is untrusted. The issue forbids cloud writes in browser tests.

**Independent Test**: Run `test_markup_renders_as_text` and `test_cloud_guard_blocks_external_request`.

**Acceptance Scenarios**:

1. **Given** a template name that contains markup characters, **When** the proposal appears, **Then** the characters appear as text and no element is injected.
2. **Given** a journey, **When** the page requests an external host, **Then** the guard aborts the request and counts it.

### User Story 6 - Keep stale responses and failures visible (Priority: P3)

A late response from an older preview never replaces a newer proposal. A server failure shows an error status that starts with `Error:`, and no proposal appears.

**Why this priority**: These states can mislead an operator, but they occur less often than the main journey.

**Independent Test**: Run `test_stale_preview_response_is_ignored` and `test_server_failures_show_text_status`.

**Acceptance Scenarios**:

1. **Given** two preview requests, **When** the older response arrives last, **Then** the newer proposal remains visible.
2. **Given** a server failure, **When** the request fails, **Then** the status starts with `Error:` and the review control stays disabled.

### Edge Cases

- An older preview response arrives after a newer request starts. The page ignores the older response.
- A preview fails after a proposal appears. The page clears the proposal and the review.
- The operator changes the file or the name after a review. The page clears the proposal and the review.
- A template name contains markup characters. The page shows the characters as text.
- A long command line has no break point on a phone viewport. The page wraps the text and does not scroll sideways.
- The browser stores a shipped theme from an earlier visit. The page opens with that theme.
- The portal host stores its theme key in browser storage. The converter writes no other storage key.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tests MUST run each converter journey in the portal host, not in an isolated blueprint.
- **FR-002**: The journeys MUST cover input, preview, structured review, review, typed confirmation, export, and status.
- **FR-003**: Export MUST stay disabled until the typed word equals `EXPORT` exactly.
- **FR-004**: Cancel MUST clear the typed word. Reset MUST clear all converter state in the page.
- **FR-005**: A stale preview response MUST NOT replace a newer proposal.
- **FR-006**: Each status MUST start with a word label, such as `Error:`, that names the outcome.
- **FR-007**: Each control MUST be reachable with a keyboard and MUST show a visible focus outline.
- **FR-008**: The tests MUST cover the four shipped themes: magenta, dark, light, and high-contrast.
- **FR-009**: The tests MUST cover the phone viewport and the desktop viewport with zero horizontal overflow.
- **FR-010**: User text MUST render through DOM text APIs only. Markup MUST NOT create elements.
- **FR-011**: Browser requests MUST stay on the loopback address. The cloud guard MUST abort any other host.
- **FR-012**: Tests MUST use synthetic input. Tests MUST NOT read or print a credential or an environment value.
- **FR-013**: A failed journey MUST keep its trace and screenshot through the existing CI options.
- **FR-014**: Each new interactive control MUST have a stable `data-testid` value from the journey contract.
- **FR-015**: Colors MUST come from host theme tokens. The converter stylesheet MUST contain no color literal.
- **FR-016**: The presentation MUST add no image, font, or animation asset.
- **FR-017**: The test layout MUST add no direct child to `tests/e2e/` or `tests/e2e/web_portal/`.
- **FR-018**: The isolated converter smoke class and its storage assertion MUST leave `tests/e2e/web_portal/test_portal_smoke.py`.
- **FR-019**: The existing portal smoke classes MUST keep passing in the same module.
- **FR-020**: This change MUST NOT register the converter in the production portal. The test host mounts it only.

### Mist Cloud Transport Requirements

Not applicable: this feature sends no Mist Cloud request. The routes module imports no Mist SDK module (RC-07). The browser guard blocks every non-loopback request (FR-011).

### Key Entities

- **Converter page**: The page at `/cisco-config-converter/`. It holds the controls in the journey contract.
- **Proposal**: The JSON object from preview. It holds the gateway template, the unsupported items, and the known gaps.
- **Review approval**: The session digest that binds export to one proposal. The review action sets it.
- **Typed confirmation**: The exact word `EXPORT` that the operator types before export.
- **Test host**: The portal app that one test class builds. It mounts the converter for that class only.
- **Shipped theme**: One of the four theme files that the portal host lists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 20 planned test cases pass in the `web_portal` browser shard.
- **SC-002**: Each shipped theme shows zero horizontal overflow at both viewports.
- **SC-003**: The markup test finds zero injected elements.
- **SC-004**: Each journey records zero requests to a host other than the loopback address.
- **SC-005**: The `web_portal` browser shard finishes within the 20-minute budget.
- **SC-006**: The direct child counts of `tests/e2e/` and `tests/e2e/web_portal/` do not change.
- **SC-007**: The converter stylesheet contains zero color literals and zero image references.
- **SC-008**: Each failed test leaves one trace and one screenshot in the CI artifact.

## Assumptions

- Issues #4636, #4641, and #4642 merge before implementation starts. All three are open on the record date.
- The portal host keeps the `misthelper-theme` storage key and the `applyTheme` function.
- The preview and export JSON shapes stay unchanged unless issue #4641 changes them.
- The CI browser job keeps its Chromium install and its pytest options.
- A developer machine has Chromium from the bootstrap step in the repository guide.

## Out of Scope

- Shared navigation and production registration. See FR-020 and issue #4648.
- Cloud apply, administration, backup, and restore. See issues #4644, #4645, and #4646.
- Legal review of source reuse. See issue #4635.
- Repair of the directory debt under `tests/e2e/`. See remediation action R-1 in `plan.md`.
- Changes to converter routes, models, conversion logic, and session behavior.
