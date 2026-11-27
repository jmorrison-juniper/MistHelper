# Feature Specification: Menu 304 serial number browser test

**Feature Branch**: `fix/4603-menu-304-serial-browser-test`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4603, "Test failure: menu 304 serial number browser test"

**Input**: User description: "Reproduce the menu 304 browser test failure from the CI log, then specify the test repair."

## Clarifications

### Session 2026-11-26

- Q: Does the failure reproduce on current main? A: Not in the 15 newest Quality Gates runs. Their web-portal E2E jobs all passed. Evidence: research R7.
- Q: Must the repair change production code? A: Not until the cause is proven. The issue states that no cause is confirmed. Decision D-1 and D-7.
- Q: Which dependency pins apply? A: The pins on main: Dash 4.5.1 and Playwright 1.65.2. Decision D-4.
- Q: Must the change add a changelog fragment? A: Yes. The constitution requires one fragment for each change. Decision D-5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Name the reason for a failed menu 304 selection (Priority: P1)

A maintainer reads a failed browser run. The failure message names the menu, the parameter path, the HTTP status or the missing response, and any browser error. The maintainer then knows which step failed.

**Why this priority**: The current failure reports only a locator timeout. It does not show whether the click started the parameter request.

**Independent Test**: Run `test_menu_304_names_a_refused_parameter_request`. The test refuses the parameter request with HTTP 503. It passes only when the helper message names the path and the status.

**Acceptance Scenarios**:

1. **Given** the parameter request returns HTTP 503, **When** the helper selects menu 304, **Then** it raises an assertion naming the path and `503`.
2. **Given** the parameter request never starts, **When** the response wait times out, **Then** the assertion states that no parameter response arrived. This path has review coverage only (decision D-9).

---

### User Story 2 - Prove that a menu 304 selection reaches its parameter request (Priority: P1)

The menu 304 browser test waits until the parameter response returns HTTP 200 and the selected title reads `Menu 304`. Only then does the test check the serial number control and run the lookup.

**Why this priority**: The current helper can pass before any request starts. The test then does not prove the selection.

**Independent Test**: Run `test_menu_304_waits_for_serial_numbers_then_saves_each_asset`. Repeat it 20 times with Python 3.15.2 and Dash 4.5.1. All 20 runs pass.

**Acceptance Scenarios**:

1. **Given** menu 304 is selected, **When** the parameter response returns HTTP 200, **Then** the serial number control becomes visible within the timeout.
2. **Given** the test runs with the current main pins, **When** it repeats 20 times, **Then** 20 of 20 runs pass.

---

### User Story 3 - Keep production code unchanged until the cause is proven (Priority: P2)

A reviewer sees that the change touches only the test module, the changelog fragment, and the spec record. A production change starts only when the matrix meets the trigger in decision D-7.

**Why this priority**: The cause is unknown. A production change without evidence can hide the defect.

**Independent Test**: Review the pull request file list. It shows no change under `web_portal/` unless task T007 started.

---

### Edge Cases

- The parameter response returns HTTP 503. The helper names the status (TC-2).
- The response arrives before the selected title changes. The helper waits until both conditions hold before it returns.
- The response wait starts after the click. The helper registers the wait before the click, so a fast response is not lost.
- Menu 298 has no parameter fields. The helper still passes. The parameter response still arrives, and the title still reads `Menu 298`.
- An unrelated page error occurs during a selection. The helper reports it in the message and does not fail by itself.
- `pytest-timeout` is missing. The conftest skips the E2E tests (`tests/e2e/conftest.py` line 209). The runner must install it first.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST name the failing test ID and the failing assertion from CI run 42173674615.
- **FR-002**: `select_menu` MUST register a response wait that targets the parameter path of the selected menu before the click. It MUST require HTTP 200.
- **FR-003**: `select_menu` MUST wait until `#selectedOpTitle` reads `Menu` followed by the menu number. Then it MUST return.
- **FR-004**: When a wait fails, `select_menu` MUST raise an `AssertionError`. The message MUST name the menu number, the parameter path, and either the HTTP status or the words `no parameter response`.
- **FR-005**: The failure message MUST list up to five browser page errors and console errors captured during the selection.
- **FR-006**: `select_menu` MUST NOT use a fixed sleep to decide correctness. `SETTLE_MS` MUST remain for screenshots only.
- **FR-007**: The existing menu 304 assertions after the selection MUST remain, with the same intent.
- **FR-008**: The changed test module MUST keep every module-level name unchanged.
- **FR-009**: Each changed or added line MUST carry an inline comment. Each action in the changed code MUST carry a log line before it and after it.
- **FR-010**: The menu 304 test MUST pass 20 of 20 local runs under combination D. The matrix MUST record each result for combination A.
- **FR-011**: The record MUST state the Python, Dash, and pytest-playwright versions for each CI run that it cites.
- **FR-012**: The change MUST add the changelog fragment `changelog.d/issue-4603-menu-304-serial-browser-test.md`.
- **FR-013**: A production file MUST NOT change unless task T007 starts under decision D-7.
- **FR-014**: The test module MUST stay in `tests/e2e/web_portal/`, so the web-portal E2E shard keeps it.
- **FR-015**: The negative test MUST pass only when the helper message names the parameter path and HTTP 503.

### Test Cases

- **TC-1**: `test_menu_304_waits_for_serial_numbers_then_saves_each_asset[chromium]`. Existing test. Its helper changes. Covers FR-002, FR-003, FR-006, FR-007, and FR-010.
- **TC-2**: `test_menu_304_names_a_refused_parameter_request[chromium]`. New test. Covers FR-004, FR-005, and FR-015.

### Key Entities *(include if feature involves data)*

Not applicable: this change adds no data entity, natural key, or stored state.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: menu 304 reads Juniper service APIs and makes no Mist REST call. Evidence: research R10, rows RV-23 and RV-25.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: TC-2 passes on every local run. Its failure text names `/api/operations/parameters/304` and `503`.
- **SC-002**: TC-1 passes 20 of 20 local runs under combination D (Python 3.15.2, Dash 4.5.1).
- **SC-003**: The matrix records the pass count and the failure count for combination A (Python 3.13.18, Dash 4.5.0). It uses 20 runs.
- **SC-004**: The pull request head shows a green web-portal E2E job. The first main run after merge shows a green web-portal E2E job.
- **SC-005**: The browser module passes 19 of 19 tests locally. The module held 18 tests before this change.
- **SC-006**: The record contains no unfinished marker and passes the self-review checks in the brief.

## Out of Scope

- Repairing `web_portal/static/js/operations.js` without proven evidence. Only task T007 covers it, under decision D-7.
- Changing the Dash, Playwright, mistapi, or Python pins.
- Changing the CI workflow, the E2E job, or the diagnostics artifact.
- Other menus and other browser tests.
- Documentation drift for the mistapi pin and for the menu counts. Each needs a separate issue.
- Downloading the failed run artifact. Its download returned HTTP 403 for the owner.

## Assumptions

- The web-portal E2E job on main keeps the pins in `requirements.txt` (line 45) and `requirements-dev.txt` (lines 76, 272).
- A local Chromium browser exists after `python -m playwright install chromium`.
- `pytest-timeout` is installed in the local environment, so the E2E tests do not skip.
- The test data is synthetic. The browser test uses the double in `juniper_browser_harness.py`. It sends no call to Juniper or Mist.
- The single failing observation in CI represents the failure. Its frequency is unknown.

Warning: never run this test with live Juniper settings, because each export holds personal data.

## Evidence Sources

Details appear in `design/research.md`. The failing run is 42173674615. The failing job is 127747809271. The failing head is `1b8c06a8a0d15abbbe1ae8edb840dd0dd81e1bb6`.
