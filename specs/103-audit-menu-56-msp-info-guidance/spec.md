# Feature Specification: MSP info guidance (Audit)

**Feature Branch**: `103-audit-menu-56-msp-info-guidance`
**Created**: 2026-04-03
**Status**: Draft
**Input**: User description: "Create a feature specification for MistHelper Menu #56: \"MSP info guidance\"\n\nFunction: OrgConfigExporter.msp\nCategory: info_display\nSQL export relevant: No\n\nThis is an AUDIT spec — analyze the existing implementation in MistHelper.py, document current state, identify issues, and define acceptance criteria for fixes.\n\nCRITICAL: You MUST write the spec file to disk at this exact path: specs/103-audit-menu-56-msp-info-guidance/spec.md"

---

## Summary

This is an audit specification for the existing MistHelper Menu #56 implementation: OrgConfigExporter.msp (function name: msp) located in MistHelper.py. The audit covers current behavior, user-facing information display (UX), input validation, error handling, test coverage, and identified issues. The goal is to document current state, define testable acceptance criteria for fixes, and provide a prioritized list of required changes with measurable success criteria.

Scope: analysis limited to the existing Python implementation in MistHelper.py (function msp) and its immediate helpers (DataProcessingUtils, DataExporter, InputUtils). This spec does not prescribe implementation details (languages, frameworks) but defines WHAT must change and WHY.

---

## Current Implementation (observed)

Location: MistHelper.py, function msp (approx. lines 13220-13344)

Behavior summary (current):

- Checks global `msp_privileges`. If falsy, prints a block of guidance explaining MSP-level access requirements (interactive login, personal API token from MSP Super User), logs a warning, and returns.
- If `msp_privileges` is present: if there is a single MSP available, it is selected automatically and the name is printed. If multiple MSPs exist, it prints a numbered list of MSP names and roles and prompts the user for a numeric selection via `InputUtils.safe_input("  Select MSP (number): ", context="msp_export")`.
- The selection code casts the input to int, index adjusts, validates the index bounds, and on invalid selection prints "X Invalid selection" and returns. It catches `ValueError` and `SystemExit`, prints "X Invalid input", and returns.
- Once a MSP is selected, it verifies `apisession` is not None; if None, prints error and returns.
- Calls mistapi.v1.msps.orgs.listMspOrgs(apisession, msp_id) and expects a `response` object with `.data`. If response missing or response.data falsy, prints error and returns.
- Normalizes `orgs_data` to a list, processes it with `DataProcessingUtils.flatten_nested_fields` and `DataProcessingUtils.escape_multiline`, adds `msp_id` and `msp_name` fields to each record, and calls `DataExporter.save_data_to_output(processed, "MspOrganizations.csv")`.
- On successful export, prints number of exported organizations and logs info. It then prints a short summary showing the first 10 organizations (name and the first 8 chars of the org id followed by '...') and, if more than 10, prints the remainder count.
- There is a broad `except Exception as e:` around the API call and processing which prints and logs the exception.

---

## Audit Findings (issues, risks, UX and validation gaps)

1. Input validation and UX
   - Selection path:
     - The prompt accepts raw input then converts with `int(choice)`. It handles ValueError and SystemExit only; it does not explicitly handle `KeyboardInterrupt` which may surface if users press Ctrl+C.
     - On invalid selection or conversion error, the function prints an error and returns immediately. There is no retry mechanism, no descriptive guidance for valid values (e.g., range), and no indication of a default behavior for non-interactive environments.
     - When `msp_privileges` length == 1 the code auto-selects the single MSP; however there is no flag or feedback option for non-interactive usage (e.g., command-line switch) if automation is desired.
   - UX text:
     - Guidance when MSP privileges are missing is plain-text instructions. It lacks machine-parsable exit codes or structured output that automation could detect.
     - The summary of exported organizations truncates org ID via `org_id[:8]...` without verifying the type/length, which could raise if id is not a string or shorter than 8 chars.

2. Error handling
   - The `except Exception as e:` block is broad and will mask specific failure modes; while errors are logged, the function prints a generic message and continues to return. There is no differentiation between transient API errors and permanent failures.
   - The function checks `if not response or not hasattr(response, "data")` but does not check for `response.data` types or for API error payloads (e.g., HTTP status, error messages).
   - When the API returns an empty org list the code calls `DataExporter.save_data_to_output([], "MspOrganizations.csv")` and returns; it logs info but does not indicate whether an empty CSV was created successfully or whether callers should check file existence.

3. Data handling and robustness
   - `orgs_data` normalization attempts to coerce non-list into a list, but the code will produce odd records if the API's .data contains unexpected types (e.g., dict of metadata). There are no schema assertions or minimal shape checks for required fields (e.g., `name`, `id`).
   - The code mutates `processed` records in place to add `msp_id` and `msp_name` without checking for key collisions.

4. Test coverage gaps
   - There are no observable unit-test hooks or modularization to facilitate unit testing of msp(): it is implemented as a long function with direct printing and side effects (DataExporter.save_data_to_output). There are no obvious tests verifying: guidance text, selection behavior (including invalid input), behavior when apisession is None, handling of API responses, correct usage of DataProcessingUtils, or correct CSV output creation.

5. Logging and observability
   - Logging calls exist, but the user-visible messages are printed to stdout. There is no machine-friendly output option (JSON, exit codes) to integrate with automation.

6. Security/privilege messaging
   - The guidance correctly notes that organization-scoped tokens cannot access MSP APIs, but messaging could be more explicit about where to obtain an MSP token or links to documentation.

---

## Assumptions

- `InputUtils.safe_input` returns a string or raises. Its behavior for EOF or interrupts is not fully documented here; the audit assumes it behaves similarly to Python's built-in input() unless otherwise defined.
- `DataExporter.save_data_to_output` writes a CSV file to the configured output directory and raises on fatal filesystem errors.
- `DataProcessingUtils.flatten_nested_fields` and `escape_multiline` operate as documented and return lists/dicts suitable for CSV export.
- `msp_privileges` is a list of dict-like objects with keys `msp_id`, `msp_name`, and `role`.
- Non-interactive usage is a desired capability for automation but not currently required; clarification requested below.

---

## User Scenarios & Testing (mandatory)

### User Story 1 - View guidance when MSP access is not available (Priority: P1)

An operator runs Menu #56 on a user account that does not have MSP privileges.

**Why this priority**: Prevents user confusion and reduces support requests by providing clear guidance.

Independent Test:
- Run the msp function with `msp_privileges` falsy. Observe the printed guidance block, ensure it contains the three guidance points (interactive login, personal API token from MSP Super User, token scope note), and verify the function exits without raising.

Acceptance Scenarios:
1. Given msp_privileges is empty, When the user runs Menu #56, Then the CLI prints an "MSP ACCESS NOT AVAILABLE" block containing guidance on required credentials and returns with a non-zero exit code or documented status (see Success Criteria).
2. Given msp_privileges is empty, When the function runs in non-interactive mode, Then the function returns a structured error (or sets an exit code) that automation can detect. [NEEDS CLARIFICATION: desired non-interactive behavior]

---

### User Story 2 - Select an MSP and export organizations (Priority: P1)

An operator with MSP privileges runs Menu #56, selects an MSP, and exports organizations to MspOrganizations.csv.

Independent Test:
- Run the msp function with a mocked `apisession` and mocked `mistapi.v1.msps.orgs.listMspOrgs` that returns a known list of organization dicts. Verify MspOrganizations.csv is created and contains all returned org records with added `msp_id` and `msp_name` columns.

Acceptance Scenarios:
1. Given valid msp_privileges and apisession, When the user selects a valid MSP index, Then the function calls the API, processes the response, writes all organizations to MspOrganizations.csv, prints the number exported, and prints a summary list showing names and stable identifiers.
2. Given the user enters an invalid selection (out-of-range or non-integer), When prompted, Then the function should display a clear validation message including the valid numeric range and allow up to 3 attempts before aborting. [NEEDS CLARIFICATION: retry vs immediate abort policy]

---

### User Story 3 - Failures and recoverability (Priority: P2)

Operator or automation triggers an export but the API call fails (network error, 5xx, unexpected payload).

Independent Test:
- Simulate API throwing an exception and verify the function prints a clear error, logs the exception, and returns a consistent non-zero status without raising an uncaught exception.

Acceptance Scenarios:
1. Given the API call raises a transient exception, When the function runs, Then it logs the exception, prints a concise error message including an optional hint ("retry later"), and returns gracefully.
2. Given API returns an unexpected payload shape, When processed, Then the function detects the missing required fields and writes an empty CSV with headers or aborts with a clear error message.

---

### Edge Cases

- User presses Ctrl+C during selection (KeyboardInterrupt) — should be handled gracefully.
- API returns very large org lists (10k+) — memory and performance considerations; ensure DataExporter supports streaming or files won't blow memory.
- `org.get("id")` returning None or non-string — avoid slicing errors when showing short IDs.
- `DataExporter.save_data_to_output` raises (disk full, permission) — surface clear error messages.

---

## Functional Requirements (testable)

- FR-001: When `msp_privileges` is falsy, the CLI MUST print a guidance block containing three required points: interactive login, MSP Super User personal token, and note that organization-scoped tokens cannot access MSP APIs. The guidance MUST be stable and testable via unit test asserting printed text.

- FR-002: When multiple MSPs exist, the CLI MUST present a numbered list with indices starting at 1 and MUST accept numeric selection. On invalid input the CLI MUST display the valid range (e.g., "Select MSP (1-3):") and allow up to 3 attempts before aborting with a clear message and documented exit status.

- FR-003: The input prompt MUST handle `KeyboardInterrupt` and EOF without leaving the program in an inconsistent state; it MUST return a documented non-zero status and not produce a stack trace to the user.

- FR-004: The function MUST verify `apisession` before calling the API and return a documented error if None.

- FR-005: The function MUST validate API responses: assert that `response` has `.data` and that `.data` is list-like or convertable to a list of dicts. If required fields (`id`, `name`) are missing from records, the function MUST either add placeholder values or report malformed records without crashing.

- FR-006: The export MUST include `msp_id` and `msp_name` columns for all exported records.

- FR-007: The CLI MUST not assume fixed-length org IDs when printing short identifiers; it MUST safely handle missing or short IDs.

- FR-008: On API or IO errors, the function MUST log the exception details and return a documented non-zero status; user-facing messages must be concise and actionable.

- FR-009: Add a non-interactive option (e.g., a flag or environment variable) so automation can run the export without interactive prompts; when enabled and multiple MSPs exist, the function MUST either pick a configurable default (e.g., first MSP) or fail with a documented error explaining required input.

- FR-010: Add unit tests covering: (a) guidance output when no privileges, (b) valid selection path, (c) invalid selection and retry behavior, (d) API returning empty list, (e) API throwing exception, (f) processing adding msp context, (g) CLI handling KeyboardInterrupt.

Note: FR-009 requires product decision — see clarifications.

---

## Success Criteria (measurable)

- SC-001: 100% of the mandatory guidance text lines appear when `msp_privileges` is falsy (verified by unit test asserting substrings).
- SC-002: Selection input validation accepts only integers in the displayed range; providing 3 consecutive invalid inputs terminates the prompt and returns documented status (testable by simulating input sequences).
- SC-003: Export creates MspOrganizations.csv with a row count equal to the number of organizations returned by the API in test scenarios (mocked API), and includes `msp_id` and `msp_name` columns for every row.
- SC-004: All error paths return a documented non-zero status (or produce structured error output) and do not raise uncaught exceptions in unit tests.
- SC-005: Required unit tests (listed in FR-010) are added and pass in CI.
- SC-006: UX: For interactive runs, summary output prints up to 10 organizations and shows an accurate "... and N more" count. For IDs, the display must not raise errors for short/missing ids.

---

## Key Entities

- `msp_privileges` (list): items with `msp_id` (str), `msp_name` (str), `role` (str)
- `apisession`: API session object (mistapi session)
- `response`: API response object, expected to have attribute `data` containing list of organizations
- `orgs_data`: list of organization dicts; expected fields: `id`, `name`, plus other metadata
- `processed`: flattened and escaped list of dicts prepared for CSV export

---

## Recommended Fixes (prioritized)

P1 (high priority)
- Add robust input validation with clear prompt showing valid range and allow configurable retry attempts (default 3). Handle KeyboardInterrupt and EOF gracefully.
- Harden response validation: check `hasattr(response, 'data')` and validate that `response.data` is list-like and that each record is a dict. On malformed records, log detailed info and either sanitize or omit them, but do not crash.
- Replace broad except with targeted exception handling where possible; ensure exceptions are logged with traceback for debugging but user messages are concise.
- Ensure safe slicing/formatting of org IDs when summarizing; use `str(org_id)[:8] if org_id` pattern.

P2 (medium priority)
- Add a non-interactive mode or explicit CLI/environment input to support automation.
- Make summary output machine-friendly via an optional JSON output mode or well-documented exit codes.
- Add unit tests as specified in FR-010, using mocks for `apisession`, `mistapi` calls, and `DataExporter` to avoid IO in unit tests.

P3 (low priority)
- Improve guidance text to include a doc link (if available) or command examples for obtaining MSP tokens.
- Consider streaming large datasets to CSV to avoid memory pressure if API can return very large org lists.

---

## Test Coverage Gaps and Required Tests

List of tests to be added (unit tests):

- TC-001: test_no_msp_privileges_shows_guidance
- TC-002: test_single_msp_auto_selects_and_exports
- TC-003: test_multiple_msps_valid_selection_exports
- TC-004: test_invalid_selection_retry_and_abort
- TC-005: test_keyboard_interrupt_during_selection
- TC-006: test_apisession_none_reports_error
- TC-007: test_api_returns_empty_list_creates_empty_csv
- TC-008: test_api_returns_malformed_data_handles_gracefully
- TC-009: test_data_processing_adds_msp_context
- TC-010: test_export_io_error_logged_and_reported

Each test should mock network and filesystem IO and assert on printed output, logs, and that DataExporter.save_data_to_output is invoked with expected arguments.

---

## Acceptance Criteria (ready for dev & QA)

- AC-001: Guidance block appears as specified (FR-001) and is covered by unit tests.
- AC-002: Selection UX updated to show valid numeric range and supports up to 3 retries before aborting (FR-002). Tests TC-004 and TC-005 pass.
- AC-003: API response validation prevents crashes on malformed data and either sanitizes or omits invalid records; exported CSV contains only valid rows with `msp_id` and `msp_name` (FR-005, FR-006). Tests TC-007 and TC-008 added and pass.
- AC-004: All exceptions in the API/export path are logged with details and result in user-friendly messages and a documented non-zero exit status. TC-010 passes.
- AC-005: Unit test coverage for msp() reaches a minimum acceptable threshold (project-defined; e.g., 80% on the function) and all new tests pass in CI (SC-005).

---

## Open Questions ([NEEDS CLARIFICATION], max 3)

1. [NEEDS CLARIFICATION: Non-interactive behavior]
   - Context: The current implementation is interactive. For automation we need to know desired behavior when multiple MSPs exist and the user cannot interact.
   - What we need to know: Should the function accept a non-interactive flag that (A) selects the first MSP automatically, (B) fails with a clear error requiring the caller to pass a specific MSP id, or (C) accept an environment variable or CLI argument to specify the MSP id to use?

2. [NEEDS CLARIFICATION: retry policy for invalid selection]
   - Context: Current code aborts on invalid selection. We need a policy for retries.
   - What we need to know: Preferred policy: (A) allow 3 attempts then abort, (B) allow infinite retries until valid input or Ctrl+C, (C) treat any invalid input as immediate abort and return an error.

3. [NEEDS CLARIFICATION: short ID display]
   - Context: The code prints a truncated org id using slicing (first 8 chars). Desired presentation may vary.
   - What we need to know: Should the summary display (A) full org id, (B) first 8 chars plus ellipsis (current), or (C) a stable short id generated (e.g., last 6 chars)? Note: for privacy/security, truncated IDs may be preferred for screen output.

Please answer Q1..Q3 together (e.g., "Q1: B, Q2: A, Q3: C").

---

## Implementation Notes for Developers (non-normative)

- Prefer adding small helper functions to encapsulate prompting and validation to facilitate unit testing (e.g., `choose_msp(msp_privileges, retries=3, non_interactive=None)`).
- Use targeted exception handling for known failure modes (network error, HTTPError, JSON decode errors, IO errors) and reserve broad `except Exception` only as a last-resort catch that still re-raises or returns a documented status code.
- Add dependency injection points for `DataExporter` and `mistapi` calls in tests to allow mocking.
- Keep user-facing guidance text stable to avoid brittle tests; store strings in a single place or provide constants for test assertions.

---

## Report: Spec ready for planning

Status: SUCCESS — spec is ready for planning, but 3 clarifications are required (above). After those clarifications are provided the spec will be updated in-place and must be re-validated.


