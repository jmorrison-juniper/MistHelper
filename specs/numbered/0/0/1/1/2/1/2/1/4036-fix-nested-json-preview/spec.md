# Feature Specification: Nested JSON Result Preview

**Feature Branch**: `3998-fix-nested-json-preview`

**Created**: 2026-11-06

**Status**: Specified

**Input**: Specify the confirmed remaining JSON result preview defect in issue #4036. Do not implement application changes in this task.

An operator needs to inspect valid JSON result files without leaving the Results panel.
The panel currently reports `Could not read the results: File not found` for an existing nested file.
The same file remains available for download.

Issue [#4036](https://github.com/jmorrison-juniper/MistHelper/issues/4036) remains the source issue.
Merged [PR #4081](https://github.com/jmorrison-juniper/MistHelper/pull/4081) corrected output-list evidence, not this preview defect.
The [evidence record](design/evidence.md) preserves the supplied reproduction and the separate ownership check.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect a nested JSON result (Priority: P1)

As an operator, I can select an existing JSON result in a subdirectory and inspect its contents in the Results panel.
I do not need to download the file to confirm its contents.

**Why this priority**: The current error prevents inspection of a valid result and suggests that an available file is missing.

**Independent Test**: Select synthetic nested JSON results through the normal Results workflow. Compare the displayed values with the fixture contents.

**Acceptance Scenarios**:

1. **Given** a listed, valid `mib_generator/allowlist.json` result, **When** the operator selects its preview, **Then** the panel displays its contents without a missing-file error.
2. **Given** a listed, valid `mib_generator/oid_assignments.json` result, **When** the operator selects its preview, **Then** the panel displays the correct file contents.
3. **Given** valid JSON results at the output root and at two nested directory levels, **When** the operator previews each, **Then** each displays its own contents.
4. **Given** a result with more rows than one preview page, **When** the operator changes pages, **Then** the panel preserves the existing row order, page size, and counts.
5. **Given** a successfully previewed JSON result, **When** the operator downloads it, **Then** the download contains the unchanged file contents.

---

### User Story 2 - Understand a failed preview (Priority: P2)

As an operator, I can distinguish invalid JSON content from a missing result.
I receive the actual JSON parse error when the requested file exists but contains malformed JSON.

**Why this priority**: A correct error tells the operator whether to correct the file contents or locate a missing result.

**Independent Test**: Preview separate malformed and absent nested files with synthetic fixtures.

**Acceptance Scenarios**:

1. **Given** an existing nested file with malformed JSON, **When** the operator requests its preview, **Then** the panel reports the JSON parse error, not `File not found`.
2. **Given** a previously listed result that no longer exists, **When** the operator requests its preview, **Then** the panel reports a missing file without displaying stale contents.
3. **Given** an error that includes an internal absolute path, **When** the panel presents the error, **Then** it does not disclose that internal path.

---

### User Story 3 - Retain existing preview protections (Priority: P2)

As an operator, I can still preview SQLite tables through the existing workflow.
The portal continues to deny access to files outside the permitted output directory.

**Why this priority**: A JSON preview correction must not disrupt table inspection or weaken file access controls.

**Independent Test**: Compare existing table previews and denied-path requests before and after the correction, using local synthetic data.

**Acceptance Scenarios**:

1. **Given** an existing SQLite table preview, **When** the operator requests the same table and page, **Then** the columns, rows, order, and pagination remain unchanged.
2. **Given** a nested SQLite file with an existing table, **When** the operator requests that table, **Then** the portal preserves the existing table-preview behavior.
3. **Given** a missing SQLite table, **When** the operator requests it, **Then** the portal preserves the existing missing-table response.
4. **Given** a request outside the permitted output directory, **When** the portal receives the request, **Then** it preserves the existing denial and exposes no file contents.

### Edge Cases

- JSON objects and arrays retain the existing preview representation. This feature does not introduce new JSON shapes.
- A nested filename must identify the file, not a table within a different file.
- A file removed between output listing and preview produces a missing-file response.
- Malformed JSON at any supported nesting depth produces a parse error rather than a missing-file error.
- Parent-directory traversal, absolute paths, encoded traversal, and links outside the output directory retain their existing security decisions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Results panel MUST preview existing, readable, supported JSON result files within the permitted output directory, including nested files.
- **FR-002**: Preview selection MUST identify the complete requested file path. Directory depth MUST NOT cause a filename to become a table selection.
- **FR-003**: JSON previews MUST preserve the existing content representation, row order, pagination, counts, and empty-result behavior.
- **FR-004**: For an existing malformed JSON file, the panel MUST report the actual JSON parse error rather than a missing-file error.
- **FR-005**: For an absent result file, the panel MUST report a missing file and MUST NOT display stale preview contents.
- **FR-006**: Existing SQLite table previews MUST retain their selection behavior, contents, row order, pagination, and missing-table responses.
- **FR-007**: Preview requests MUST retain all existing path-security checks and access restrictions. Errors MUST NOT disclose internal absolute paths.
- **FR-008**: Preview and download MUST remain read-only. Downloads MUST retain the source file contents and existing successful behavior.
- **FR-009**: The correction MUST leave output-list membership and the merged #4081 input-exclusion behavior unchanged.

### Key Entities *(include if feature involves data)*

- **Result file**: An existing output identified by its complete relative path, format, and readable contents.
- **Preview**: A read-only presentation of a result, including its current page, row order, counts, or error.
- **Table selection**: An existing SQLite table selection that remains separate from a JSON filename.
- **Output directory boundary**: The permitted file location and the existing rules that prevent access outside it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All valid JSON fixtures at the output root, one nested level, and two nested levels display the expected contents.
- **SC-002**: Both named menu 243 result paths display their own synthetic contents without a false missing-file error.
- **SC-003**: All malformed JSON fixtures report parse errors. All absent-file fixtures report missing files.
- **SC-004**: All existing table-preview and path-security regression cases retain their previous outcomes, with zero newly accessible outside-directory files.
- **SC-005**: The complete relative path used by the Results selection URL returns the expected preview without a download.
- **SC-006**: All preview, download, and pagination fixtures retain their source contents and expected ordering. Output-list membership remains unchanged.

## Assumptions

- The issue screenshot and a synthetic Flask request confirm that a nested JSON preview fails while its download succeeds.
- Existing access rights, supported JSON shapes, and preview display conventions remain authoritative.
- The two menu 243 paths identify affected examples, not a request to add read-only inputs to output lists.
- Validation uses temporary synthetic files and local Flask and Playwright requests only. No live Mist calls or production credentials are permitted.
- The correction changes request selection only. It does not change result discovery, JSON parsing rules, deployment, or merge state.
- Before later implementation, confirm the reproduction against current main and inspect current open pull request ownership for every intended file.
- If reproduction fails or ownership overlaps, preserve evidence and report the blocker. Do not open a placeholder pull request.
- A later validated fix must link issue #4036 to its pull request and include `Closes #4036`. Do not merge it.
