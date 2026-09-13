# Feature Specification: Global Wired Client Search Report

**Feature Branch**: `[001-wired-client-global-report]`  
**Created**: 2026-04-17  
**Status**: Draft  
**Input**: User description: "Create a new menu option to generate a global wired client report with partial MAC and partial manufacturer filtering, using query-time filtering where possible and reliable local filtering fallback, then export to local report and standard CSV output."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Generate global wired client report (Priority: P1)

A network operator runs a single menu option to retrieve a full organization-wide wired client report and save it as an export artifact.

**Why this priority**: The core business value is organization-wide wired visibility in one operation; without this, filtering behavior is irrelevant.

**Independent Test**: Can be fully tested by running the menu option with no filters and confirming that a complete wired client report is produced and saved.

**Acceptance Scenarios**:

1. **Given** an operator has organization access, **When** they run the new menu option with no filters, **Then** the system generates a global wired client report covering all retrievable wired clients.
2. **Given** the report generation completes, **When** output artifacts are inspected, **Then** the results are available through the normal CSV export path and as a local report artifact.

---

### User Story 2 - Filter MAC with positional operators reliably (Priority: P2)

A network operator selects a MAC filter operator and value (when required) and receives only matching wired clients, even when upstream matching behavior is inconsistent.

**Why this priority**: Operators often investigate incomplete MAC fragments; reliable matching is required for troubleshooting speed and accuracy.

**Independent Test**: Can be fully tested by using a known dataset and validating operator behavior for contains, starts with, ends with, and negated variants.

**Acceptance Scenarios**:

1. **Given** a MAC fragment that exists in the middle of one or more client MAC addresses, **When** the operator uses MAC operator `contains`, **Then** all matching clients are included regardless of MAC delimiter or case formatting.
2. **Given** a MAC prefix and suffix in the dataset, **When** the operator uses `starts with` or `ends with`, **Then** only records satisfying the selected positional operator are retained.
3. **Given** a MAC value and operator `doesn't contain` or `is not`, **When** the report runs, **Then** only records not satisfying the positive form of the condition are retained.

---

### User Story 3 - Filter manufacturer with positional operators (Priority: P3)

A network operator selects a manufacturer filter operator and value (when required) and receives a filtered report, with fallback behavior that still works when remote manufacturer filtering is unavailable or incomplete.

**Why this priority**: Manufacturer targeting is useful for vendor-focused investigations, but data/source behavior can vary and requires resilient handling.

**Independent Test**: Can be fully tested by running with known manufacturer values and validating contains, starts with, ends with, and negated variants.

**Acceptance Scenarios**:

1. **Given** manufacturer text exists in client records, **When** the operator filters by `contains`, `starts with`, or `ends with`, **Then** matching records are returned using case-insensitive logic.
1. **Given** negated manufacturer operators (`doesn't contain`, `doesn't start with`, `is not`) are selected, **When** report generation completes, **Then** only records satisfying the selected negated condition are included, and blank/missing manufacturer values remain non-matches unless a blank/null operator is explicitly selected.
1. **Given** remote manufacturer filtering does not reduce results as expected, **When** report generation completes, **Then** local filtering still enforces the requested manufacturer operator and value.

---

### Edge Cases

- User provides both MAC and manufacturer filters; records must satisfy both filters.
- User selects an operator that requires an input value (`is`, `is not`, `contains`, `doesn't contain`, `starts with`, `doesn't start with`, `ends with`, `doesn't end with`) but provides no value.
- User provides only punctuation or whitespace in MAC input; normalized search term becomes empty and should be treated as no MAC filter.
- User selects `is blank`, `is not blank`, `is null`, or `is not null`; value input is ignored for operator evaluation.
- Manufacturer field is missing, blank, or null in some records while a manufacturer filter is provided.
- No records match filters; output must still be generated with headers and a clear summary.
- Upstream filtering returns broad or unexpected results; local filtering must remain authoritative for final inclusion.
- Result set spans multiple pages; all pages must be included before final local filtering.
- API call fails or is rate-limited mid-run; operation must fail safely with clear status and no misleading success output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a new read-only menu option that generates an organization-wide wired client report.
- **FR-002**: The menu option MUST allow optional operator-based filtering for both MAC and manufacturer fields using this shared operator set: `is`, `is not`, `contains`, `doesn't contain`, `starts with`, `doesn't start with`, `ends with`, `doesn't end with`, `is blank`, `is not blank`, `is null`, `is not null`.
- **FR-003**: The system MUST support a two-stage filtering strategy: remote pre-filtering when available and local post-filtering for final match enforcement.
- **FR-004**: Local MAC filtering MUST evaluate the selected operator using normalized, case-insensitive comparison and must ignore MAC delimiters for all value-based operators.
- **FR-005**: Local manufacturer filtering MUST evaluate the selected operator using case-insensitive comparison, with equivalent positional semantics to MAC filtering.
- **FR-006**: When both filters are provided, the system MUST apply logical AND semantics so only records matching both criteria are included.
- **FR-007**: The system MUST aggregate all retrievable wired client records for the chosen query scope before applying final local filtering.
- **FR-008**: The output MUST be written both as a local report artifact and through the existing standard CSV export flow used by menu exports.
- **FR-009**: The report MUST include summary metadata: requested filters, final filtering method used (remote/local/both), total records retrieved, total records matched, and generation timestamp.
- **FR-010**: If no records match, the system MUST still generate a valid empty report with summary metadata and explicit "0 matches" outcome messaging.
- **FR-011**: The feature MUST follow established organization export behavior patterns for user prompts, progress visibility, and output consistency.
- **FR-012**: The feature MUST fail safely on API errors or rate-limit interruptions, returning a clear failure state without claiming successful completion.
- **FR-013**: The feature MUST preserve compatibility with existing reporting and downstream analysis workflows that consume CSV exports.
- **FR-014**: For operators that require a value, the system MUST require non-empty input after normalization before execution; null/blank operators MUST execute without requiring a value.

### Key Entities *(include if feature involves data)*

- **Wired Client Search Criteria**: User-provided per-field filter definitions including selected operator and optional value for MAC and manufacturer.
- **Wired Client Record**: A normalized representation of one wired client entry, including identity fields (such as MAC), vendor/manufacturer attributes, and contextual connection details.
- **Filtering Decision Metadata**: Per-run summary describing how filtering was applied (remote, local, or combined) and counts before/after filtering.
- **Global Wired Client Report**: Final export dataset and summary section produced by the new menu option.

## Assumptions

- Operators running this feature already have valid organization context and permissions to retrieve wired client data.
- Existing organization export flows remain the baseline for output location, format expectations, and user interaction style.
- Local filtering is the source of truth for final match correctness whenever any filter is provided.
- Manufacturer values may be inconsistent or absent across records; for value-based manufacturer operators, blank/missing values are non-matches, while `is blank`/`is null` style operators can match them by definition.
- During implementation, the menu option number will be assigned to the next available read-only slot without altering destructive operation ranges.

## Clarifications

### Session 2026-04-17

- Q: Should MAC and manufacturer use the same positional operators? → A: Yes. Both fields use the same operator catalog: `is`, `is not`, `contains`, `doesn't contain`, `starts with`, `doesn't start with`, `ends with`, `doesn't end with`, `is blank`, `is not blank`, `is null`, `is not null`.
- Q: Which operators require a value? → A: `is`, `is not`, `contains`, `doesn't contain`, `starts with`, `doesn't start with`, `ends with`, and `doesn't end with` require non-empty normalized input; blank/null operators do not.
- Q: How are MAC and manufacturer values compared? → A: MAC matching is case-insensitive and delimiter-insensitive; manufacturer matching is case-insensitive, with equivalent positional semantics.
- Q: How are blank/missing manufacturer values handled with negated operators? → A: For value-based negated operators (`is not`, `doesn't contain`, `doesn't start with`, `doesn't end with`), blank/missing manufacturer values remain non-matches; blank/null records are only matched when blank/null operators are explicitly selected.
- Q: What is authoritative when remote query behavior differs from expected matching? → A: Remote filtering is optimization only; local filtering is authoritative for final inclusion.
- Q: What does global scope and output parity mean for this report? → A: Scope is all retrievable organization-wide wired records during the run, and local report + standard CSV must contain identical matched sets and summary counts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In validation runs, 100% of records in filtered output match the selected MAC/manufacturer operator semantics and user-provided values after normalization rules are applied.
- **SC-002**: In a test dataset containing known contains, starts-with, and ends-with examples, the report returns all expected positional matches and 0 known false positives for both MAC and manufacturer filtering.
- **SC-003**: 100% of successful report runs produce both required artifacts (local report + standard CSV export) with identical matched record counts.
- **SC-004**: For no-match scenarios, users receive a completed run with explicit zero-match summary and a valid empty export artifact in 100% of tested cases.
- **SC-005**: Operators can execute the workflow end-to-end (run, optionally filter, locate output) without requiring manual post-processing in at least 95% of acceptance test runs.
- **SC-006**: For both MAC and manufacturer fields, operator validation rejects 100% of value-required filters that normalize to empty input prior to execution.
