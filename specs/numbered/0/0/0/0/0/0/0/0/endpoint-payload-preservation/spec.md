# Feature Specification: Endpoint Payload Preservation

**Feature Branch**: `endpoint-payload-preservation`

**Created**: 2026-10-06

**Status**: Ready for planning

**Input**: User description: Preserve non-empty object payloads in endpoint-family exports.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve documented object exports (Priority: P1)

As a network operator, I want a successful endpoint-family operation with a documented non-empty object response to export that object, so that the output represents the Mist Cloud response.

**Why this priority**: The current behavior silently produces no rows for valid non-empty responses.

**Independent Test**: Use each documented SLE trend object with controlled local transport, run the normal export path, and verify one output record contains the response data.

**Acceptance Scenarios**:

1. **Given** a successful summary trend object without `results`, **When** the operator runs the summary trend operation, **Then** the existing normalization and output path receives one record.
2. **Given** a successful classifier trend object without `results`, **When** the operator runs the classifier trend operation, **Then** the existing normalization and output path receives one record.

### User Story 2 - Preserve existing paginated exports (Priority: P2)

As a network operator, I want list and `results` responses to keep their current pagination behavior, so that existing exports do not change.

**Why this priority**: Endpoint-family exports already support these response forms and must remain compatible.

**Independent Test**: Run controlled list and `results` responses, including a following page, and compare received records, order, and output calls with the current contract.

**Acceptance Scenarios**:

1. **Given** a top-level array response, **When** the export runs, **Then** every received array record remains available to normalization and output.
2. **Given** a `results` envelope with a following page, **When** the export runs, **Then** records from all valid pages remain available in the existing order.

### User Story 3 - Distinguish empty results from discarded payloads (Priority: P2)

As a network operator, I want a true empty result to remain empty while a non-empty documented object produces a record, so that an empty export has an accurate meaning.

**Why this priority**: A discarded object and a true empty response currently produce the same operator result.

**Independent Test**: Supply documented non-empty objects and defined empty responses to the same export path, then compare received and written record counts.

**Acceptance Scenarios**:

1. **Given** an empty list, an empty `results` envelope, or an empty object, **When** the export runs, **Then** no output record is written.
2. **Given** a successful non-empty documented object, **When** the export runs, **Then** the received record count and written record count both equal one.

### Edge Cases

- A successful object that is not proven by the OpenAPI specification or a recorded response must not gain object handling from assumption alone.
- A non-empty object without `results` must not be mistaken for a true empty result.
- An empty list, an empty `results` envelope, and an empty object must remain empty.
- A valid later page must preserve pagination order and all received records.
- An unavailable, malformed, or error response must preserve current logging and non-raising behavior.
- A record-count mismatch between received records and written records must be visible to validation and must not be treated as a successful complete export.
- Existing primary-key behavior must remain unchanged.
- The two SLE trend operations must remain available when deprecated SDK attributes are absent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The export must preserve a non-empty top-level object when its response shape is proven by the repository OpenAPI specification or a recorded response.
- **FR-002**: The export must preserve the two documented SLE trend object shapes: the summary trend object with `start`, `end`, `sle`, and `classifiers`, and the classifier trend object with `start`, `end`, `metric`, and `classifier`.
- **FR-003**: The export must pass each preserved object through the existing normalization and output behavior as one received record.
- **FR-004**: The export must retain top-level list behavior and `results`-shaped pagination behavior, including valid following pages, record order, arguments, labels, filenames, and endpoint metadata.
- **FR-005**: The export must distinguish a discarded non-empty object from an actual empty result.
- **FR-006**: The export must compare received records with written records during validation so a successful response cannot silently produce an incomplete output.
- **FR-007**: The export must preserve current error status handling, including non-raising behavior and safe logging for unsuccessful or unusable responses.
- **FR-008**: The export must preserve all existing primary-key strategies and output backends.
- **FR-009**: The export must preserve Mist SDK compatibility under the current supported SDK range and must not require a dependency or schema migration.
- **FR-010**: The repair must not modify `endpoint_primary_key_strategies.py`.
- **FR-011**: Production code changes are out of scope for this specification phase. This phase must create only the managed specification records.
- **FR-012**: The repair must not claim support for an operation whose response shape is untyped or empty in the OpenAPI specification unless recorded-response evidence proves its shape.
- **FR-013**: The repair must cover the six endpoint-family menus 263 through 268 and the 132 operations they expose, with the measured scope recorded as 97 confirmed object-payload losses.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- Use the existing `mistapi` REST methods for `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend`. Direct HTTP requests are prohibited when these methods are available.
- Use the existing Mist SDK response decoding and pagination interfaces. Do not change the supported SDK version range.
- Contract evidence must show that SDK decoding retains each documented object, that pagination retains list and `results` responses, and that an object without `results` is not discarded before normalization.
- Contract evidence must cover successful authentication without exposing credentials, endpoint parity for both SLE trend methods, failure-safe handling for unsuccessful responses, and secret redaction in logs.
- No WebSocket transport is required.

### Key Entities *(include if feature involves data)*

- **Response payload**: A decoded Mist Cloud response in a proven top-level list, `results` envelope, or documented non-paginated object shape.
- **Received record**: A response record available after response-shape handling and before output persistence.
- **Written record**: A normalized record accepted by the selected output backend.
- **SLE trend object**: A documented summary or classifier trend response containing its required time, metric, sample, and classifier fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both documented SLE trend object examples produce exactly one written record when supplied as successful responses.
- **SC-002**: Every covered operation with a proven top-level list or `results` shape retains its existing record count, order, and pagination behavior.
- **SC-003**: All 97 operations with specification-proven non-empty object shapes no longer lose a valid non-empty response before normalization.
- **SC-004**: All true empty results in the defined empty-result cases produce zero written records.
- **SC-005**: Validation identifies every mismatch between received and written records in the covered response tests.
- **SC-006**: The repair changes no primary-key strategy, output backend contract, SDK dependency constraint, or schema migration state.
- **SC-007**: Operators can distinguish a true empty export from a discarded non-empty payload through the export result and validation evidence.

## Assumptions

- The repository OpenAPI specification at `documentation/mist-api-openapi31json.json` is the authority for proven response shapes.
- The two recorded SLE trend examples in issue #3699 are valid local evidence and contain no secrets.
- The current Mist SDK remains within `mistapi>=0.64.0,<0.65`.
- Existing normalization, output backends, primary-key behavior, menu registration, and endpoint metadata are the compatibility baseline.
- The 97 confirmed losses identify the measured object-payload scope. Each operation remains eligible only when its response shape is proven by the OpenAPI specification or recorded-response evidence.
- A record-count comparison can identify discarded or incomplete output without changing the selected output backend.
- No live Mist Cloud request, production store, container action, dependency update, or schema migration is required.
- This specification intentionally excludes production and test implementation. Planning will define those changes later.
