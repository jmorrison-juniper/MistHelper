# Feature Specification: Menu 243 Result File Not Found

**Feature Branch**: `fix/4036-menu-243-preview-test`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4036, open, with labels that include `bug`, `web-portal`, `in-progress`, and `needs-human-review`

**Input**: User description: "Menu 243 downloads succeed but the result panel reports File not found"

## Current State

- PR #4081 fixed the output list on `main`. The PR merged on 2026-10-09.
- PR #4615 fixed nested JSON preview routing on `main`. The PR merged on 2026-11-13.
- The original live symptom is not independently verified. Issue #4036 stays open until the live check passes.
- The browser regression that the owner ran on 2026-11-17 is not published. It exists only in unmerged commit `18ce4c8`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview the generated ledger (Priority: P1)

An operator runs menu 243 and opens the Results panel. The panel shows the rows of the generated ledger.

**Why this priority**: The reported symptom blocks review of the ledger that menu 243 writes.

**Independent Test**: Run menu 243 in a test portal. Open the Results panel. Confirm that ledger rows appear and no error text appears.

**Acceptance Scenarios**:

1. **Given** menu 243 completes, **When** the Results panel opens, **Then** the panel shows rows from `mib_generator/oid_assignments.json`.
2. **Given** a nested JSON output file exists, **When** the operator previews it, **Then** the preview route answers HTTP 200 with that file's rows.

---

### User Story 2 - Download and preview agree (Priority: P2)

An operator downloads an output file and previews the same path. Both requests succeed and read the same file.

**Why this priority**: A working download with a failing preview makes operators distrust the Results panel.

**Independent Test**: Request the download route and the preview route for one nested path.

**Acceptance Scenarios**:

1. **Given** a valid output file, **When** the download route is requested, **Then** HTTP 200 returns the unchanged file bytes.
2. **Given** the same valid output file, **When** the preview route is requested, **Then** HTTP 200 returns the rows of that file.

---

### User Story 3 - Show only generated outputs (Priority: P3)

The output list of menu 243 names the generated ledger. The list omits the read-only allowlist input.

**Why this priority**: An input file is not a result of the run. Listing it misleads the operator.

**Independent Test**: Finalize the output list for a run whose log names both files.

**Acceptance Scenarios**:

1. **Given** the run log names the allowlist and the ledger, **When** the output list is finalized, **Then** only the ledger path remains.

### Edge Cases

- A nested file that is removed after listing returns `File not found` and no stale rows.
- A nested file with malformed JSON returns its parse reason, not `File not found`.
- Traversal, absolute paths, and links outside the data directory stay denied.
- A JSON file inside a directory whose name ends in a database suffix stays a file preview.
- The MIB file written outside the data directory is not listed and not served.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Results panel MUST preview each listed JSON output file that exists under the data directory at any depth.
- **FR-002**: A JSON file path MUST NOT reach the SQLite table route.
- **FR-003**: Preview and download MUST resolve the same relative path to the same file.
- **FR-004**: The Results panel MUST show `File not found` only for a missing or refused path.
- **FR-005**: The output list MUST exclude the allowlist input and MUST keep the generated ledger.
- **FR-006**: A JSON read failure MUST NOT disclose an absolute path to the operator.
- **FR-007**: A pending preview MUST clear rows and page controls from the previous result.
- **FR-008**: SQLite table previews, path denials, and downloads MUST keep their current behavior.
- **FR-009**: The regression test MUST fail when the table route returns to the preview path.
- **FR-010**: Issue #4036 MUST stay open until a live check on the deployed container shows the ledger in the Results panel.

### Key Entities *(include if feature involves data)*

- **Output file**: A file that a run lists. Its natural key is its path relative to the data directory.
- **Preview request**: A request for rows of one output file or one SQLite table, with page, size, search, and order.
- **Preview response**: Columns, rows, and totals, or an error text with its status.
- **Run record**: The run identifier, the menu number, the status, and the ordered output file paths.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The end-to-end browser test passes on the pull request head. Both downloads return HTTP 200, and the preview returns HTTP 200.
- **SC-002**: The end-to-end test fails with preview status 404 when the table route is restored in a scratch copy.
- **SC-003**: The route, error, and denial tests in `tests/unit/web_portal/test_preview_row_order.py` pass with no change to their expected results.
- **SC-004**: The live check on the deployed container shows ledger rows and no error text. The result is posted to issue #4036.
- **SC-005**: The pull request adds one fragment under `changelog.d/` and adds no direct child under `specs/`.
- **SC-006**: Each local gate that applies to the changed files reports zero failures.

## Assumptions

- The reported symptom came from the table-route layout in revision `2a48cee`. Werkzeug sorted that route first for nested paths.
- Menu 243 needs no Mist API token. It reads checked-in files only.
- The deployed container writes output files under `/app/data`.
- The container installs Werkzeug 3.1.9 from `requirements.txt`.

## Out of Scope

- A redesign of the result list or of the SQLite table route.
- Any change to the path guard, the JSON reader, or the output rule of PR #4081.
- The missing OpenAPI container defect that issue #3104 records.
- Merging or enabling auto-merge without orchestrator authorization.
- Any change to `.specify/feature.json` or to the legacy record folder.

## Clarifications

### Session 2026-11-26

- Q: Should PR #4615 close issue #4036? A: No. The owner keeps the issue open until the symptom resolves independently. Comments of 2026-11-09 and 2026-11-17 state this.
- Q: Is the 2026-11-17 browser regression published? A: No. Commit `18ce4c8` holds it. No pull request contains that commit.
- Q: Does a second path or file-lifetime condition explain the symptom? A: No code path explains it. The live check decides. See research finding F-07 and item UR-01.
- Q: Which closing keyword applies to the pull request? A: `Relates to #4036`. The orchestrator closes the issue after the live check. See decision D-04.
