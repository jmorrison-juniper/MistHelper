# Feature Specification: Export documented trend objects

**Feature Branch**: `jmorrison-juniper-documented-trend-object-export`

**Created**: 2026-10-02

**Status**: Local repair and verification. Publication remains blocked.

**Input**: Repair [#3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) without publication.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export both trend documents (Priority: P1)

A network operator selects either existing trend operation.
The selected output contains one record with the complete available trend values.

**Why this priority**: The current exporter discards both successful documented responses.

**Independent Test**: Supply each documented response through the actual SDK operation and inspect the selected output.

**Acceptance Scenarios**:

1. **Given** the documented summary response, **when** the operator selects its operation, **then** the output contains one summary record.
2. **Given** the documented classifier response, **when** the operator selects its operation, **then** the output contains one classifier record.
3. **Given** nonempty sample arrays and nested classifiers, **when** the output is written, **then** each value remains available.
4. **Given** legitimate `error` fields in a successful response, **when** the output is written, **then** those fields remain available.

### User Story 2 - Refuse an unsuccessful response (Priority: P1)

The operator receives a clear failure notice instead of an exported error document.
The exporter preserves earlier output when the current response is unsuccessful.

**Why this priority**: A new object path must not turn an error document into a successful export.

**Independent Test**: Supply refusal statuses and unusable responses through the actual operation and inspect every output callback.

**Acceptance Scenarios**:

1. **Given** HTTP `403`, `404`, `429`, `500`, or `503`, **when** the operation runs, **then** no output callback occurs.
2. **Given** a missing or unusable HTTP status, **when** the operation runs, **then** a failure notice names the operation.
3. **Given** malformed JSON or an empty HTTP `200` body, **when** the operation runs, **then** no successful empty-result notice appears.
4. **Given** a transport failure, **when** the operation runs, **then** the execution boundary contains and reports the failure.
5. **Given** an object with an unsupported next-page link, **when** the operation runs, **then** the exporter does not claim a complete record.

### User Story 3 - Preserve established export behavior (Priority: P2)

The operator retains the existing arguments, output names, paginated records, and database keys.
The repair adds no menu operation or dependency.

**Why this priority**: A shared exporter change must not alter unrelated records or output routing.

**Independent Test**: Execute existing family, catalog, routing, key, SQLite, SDK, and refusal tests without policy changes.

**Acceptance Scenarios**:

1. **Given** successful list or `results` pages, **when** the operation runs, **then** record order and actual next-page calls remain unchanged.
2. **Given** a valid empty response, **when** the operation runs, **then** the exporter creates no output.
3. **Given** either trend operation with obsolete SDK attributes absent, **when** the operation runs, **then** the selected output remains correct.
4. **Given** repeated selected-output writes, **when** the same records return, **then** the existing database strategy remains unchanged.

### Edge Cases

| Response condition | Required outcome |
| --- | --- |
| HTTP `200`, documented object, no next link | One normalized record reaches the selected output. |
| HTTP `200`, object with legitimate `error` or classifier fields | HTTP status, not field names, controls acceptance. |
| HTTP `200`, `[]`, `{}`, or `{"results": []}` | No selected output callback. |
| HTTP `200`, valid JSON `null` or an SDK-unsupported tuple | Preserve the existing empty collection behavior. |
| HTTP `204`, empty body | No output. Preserve the successful no-content result. |
| HTTP `200`, malformed JSON or empty wire body | Report a failure and preserve earlier output. |
| Non-success status with JSON or HTML | Refuse before shape selection or normalization. |
| No status, a non-integer status, or `APIResponse(None, url)` | Refuse without a success default. |
| A non-`results` object with a next link | Report the unsupported shape without a next-page call or output. |
| Successful native list or `results` pagination | Keep SDK link construction and record order. |
| A later page fails | Refuse the complete export before any output write. The parent approved checked native traversal. |
| An empty nested array | Retain the exact raw value. Preserve the existing convention that omits its flattened empty field. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both exact documented trend objects MUST reach the existing selected output as one record.
- **FR-002**: Every nonempty nested classifier and sample value MUST survive the established flattening and escaping rules.
- **FR-003**: The exporter MUST decide the actual HTTP status before response shape or normalization.
- **FR-004**: Refused, missing-status, malformed, and transport-failure responses MUST produce zero unintended output callbacks.
- **FR-005**: A failure notice MUST name the operation without echoing the response body or a credential.
- **FR-006**: The exporter MUST reject an unsupported object next link instead of claiming complete data.
- **FR-007**: Successful list, `results`, empty, argument, filename, and endpoint-label behavior MUST remain unchanged.
- **FR-008**: Existing endpoint registrations, database key strategies, SDK constraints, and output routing MUST remain unchanged.
- **FR-009**: Tests MUST execute actual SDK endpoint functions, native response decoding, the exporter, and real selected-output code.
- **FR-010**: Tests MUST count actual endpoint calls, next-page calls, records, output bytes, callbacks, and forbidden network requests.
- **FR-011**: Direct negative proofs MUST fail when object retention disappears or HTTP refusal is bypassed.
- **FR-012**: Only reserved files and owned temporary resources MAY change.
- **FR-013**: The candidate MUST remain local and unpublished until the parent grants a full verified-main SHA.

### Key Entities *(include if feature involves data)*

- **Trend document**: A summary or classifier object with time bounds, labels, and sample arrays.
- **Response**: The actual HTTP status, decoded document, wire-body evidence, and SDK next link.
- **Export record**: The document after the existing normalization, flattening, and escaping rules.
- **Selected output**: The existing CSV or SQLite result with its unchanged endpoint identifier.
- **Reservation**: The exact paths the single owner may edit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both literal documents produce exactly one output record instead of zero.
- **SC-002**: Every tested refusal produces zero output callbacks and leaves prior output bytes unchanged.
- **SC-003**: Every tested successful pagination journey makes the exact expected next-page calls and preserves record order.
- **SC-004**: All changed operational statements and branches receive measured test coverage.
- **SC-005**: The configured local gates pass without a baseline, threshold, exclusion, dependency, or metadata change.
- **SC-006**: The final local commit contains only reserved paths, with a clean relevant worktree and an exact full SHA.
- **SC-007**: The parent receives the local evidence without a push, PR, merge, workflow start, or delivery-completion claim.

## Assumptions

- The preparation base is `77699c7483c1e90df14f9650ed90e98e512bee97`.
- The parent later granted local refresh on accepted main `7a4435bdf8ceff7e1dd527e4d2fd854e79542f37`.
- [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335) removed metadata only and did not repair the object response.
- The completed owner released the two shared paths in public claim `5936510347`.
- This owner's public claim `5953810192` records the release and every approved support path.
- The parent approved the reader package, checked native pages, and the existing empty-array formatting convention before source edits.
- The parent approved a typed response contract whose object policy belongs only to the SLE caller.
- The completed #3300 owner released four generated pages in public claim `5955903781`.
- Tests use only an isolated `.test` host and owned temporary files.
- No live Mist call, production store, container, browser journey, or firmware operation is necessary.
- The unchanged local template controls later evidence, not current permission to publish.

## Specification Quality Review

The three user stories cover successful documents, refusals, and preservation.
Each requirement has a measurable result and a task in [the task list](tasks.md).
No unspecified product feature or new output schema is required.
The parent resolved both concrete boundary decisions.
The repair changes neither the flattener nor a shared SDK response helper.
