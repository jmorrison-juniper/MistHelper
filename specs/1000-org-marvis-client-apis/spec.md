# Feature Specification: Org Marvis Client APIs Menu Set

**Feature Branch**: `[1000-org-marvis-client-apis]`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Create a new feature specification for MistHelper to add menu operations for mistapi 0.63.0 Org Marvis Client APIs."

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

### User Story 1 - Export Org Marvis Client Insights (Priority: P1)

As a NOC operator, I can run a safe org-level menu operation to export Marvis Client Insights data so I can review current AI-derived client insights without using ad hoc scripts.

**Why this priority**: Insights export is the highest-value baseline workflow and provides immediate operational visibility.

**Independent Test**: Can be fully tested by running the insights menu operation with and without optional filters and verifying CSV/SQLite outputs are generated and populated.

**Acceptance Scenarios**:

1. **Given** a valid org context, **When** an operator selects the insights export operation and accepts default filters, **Then** the system exports insights records to selected output targets and reports record count.
2. **Given** a valid org context, **When** an operator enters optional filters and duration values, **Then** only matching insights records are exported and the applied filter summary is shown.

---

### User Story 2 - Analyze Org Marvis Client Events (Priority: P2)

As a NOC operator, I can run count and search menu operations for Marvis Client Events so I can quickly size event volume and then retrieve detailed event records for investigation.

**Why this priority**: Event count+search pairing supports common triage workflows and reduces blind full-data exports.

**Independent Test**: Can be tested by running event count first, then event search with same filter scope, and confirming search results align with count expectations for sampled windows.

**Acceptance Scenarios**:

1. **Given** a valid org context, **When** an operator runs the event count operation with optional filters, **Then** the system returns grouped/total counts and persists output.
2. **Given** a valid org context, **When** an operator runs event search with pagination parameters including search-after continuation, **Then** the system returns paged event records without duplication or record loss across pages.

---

### User Story 3 - Analyze Org Marvis Client Stats (Priority: P3)

As a NOC operator, I can run count and search menu operations for Marvis Client Stats so I can monitor client-health trends and investigate detailed stat records from the same workflow.

**Why this priority**: Stats analysis is high value but follows the same operational pattern as events, so it is prioritized after events.

**Independent Test**: Can be tested by running stats count and stats search operations for the same period and validating expected continuity and export integrity.

**Acceptance Scenarios**:

1. **Given** a valid org context, **When** an operator runs stats count then stats search with consistent filters, **Then** the resulting records reflect the requested scope and can be exported to CSV/SQLite.
2. **Given** paginated stats search results, **When** the operator continues via search-after token flow, **Then** subsequent pages append non-overlapping records until completion.

---

### Edge Cases

- Operator provides no optional filters and no duration (default bounded query must still run safely).
- Operator provides invalid duration format or out-of-range values (system must reject with clear guidance and reprompt).
- Search operation returns empty dataset while count operation is non-zero due to changed time boundary (system must show execution window and avoid silent mismatch).
- search-after token is expired or malformed (system must fail safely and offer restart from first page).
- API page returns partial records followed by transient failure (system must preserve already retrieved records and support safe retry without duplicate exports).
- CSV or SQLite write target unavailable (operation must fail with actionable message and no corrupted partial output artifact).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The menu system MUST add a coherent, read-only Org Marvis Client workflow covering insights export, event count/search, and stats count/search.
- **FR-002**: Each new operation MUST be explicitly marked and handled as safe read-only behavior with no write, mutate, or delete action against Mist resources.
- **FR-003**: The system MUST provide operator prompts for optional filters relevant to each endpoint, including the ability to skip filters and run defaults.
- **FR-004**: The system MUST provide operator prompts for duration or time-window inputs where supported and validate input format before execution.
- **FR-005**: Search operations MUST support search-after continuation handling, including prompt/accept/use flow for continuation tokens.
- **FR-006**: Search operations MUST support pagination flow that allows operators to retrieve complete datasets beyond one page.
- **FR-007**: Count operations MUST support exportable outputs suitable for reporting and downstream reconciliation.
- **FR-008**: All new datasets (insights, events count/search, stats count/search) MUST be exported through existing CSV/SQLite-capable export workflow used by MistHelper data operations.
- **FR-009**: Each dataset class (insight, count, search) MUST define and register primary-key strategy requirements in the endpoint primary-key strategy map before release.
- **FR-010**: Search dataset key strategy MUST enforce idempotent storage behavior across retries and pagination to prevent duplicate rows.
- **FR-011**: Count dataset key strategy MUST support deterministic update behavior for repeated runs with identical scope.
- **FR-012**: Insight dataset key strategy MUST preserve record uniqueness and support repeat exports without uncontrolled row growth.
- **FR-013**: Operations MUST surface execution summary to operator, including selected filters, effective time window, page traversal status, and exported row counts.
- **FR-014**: Failure states (API errors, invalid tokens, empty results, output failure) MUST produce actionable operator-facing messages and preserve auditability of what ran.
- **FR-015**: Regression tests MUST cover happy path and failure path behavior for optional filters, duration parsing, pagination, and search-after continuation.
- **FR-016**: Regression tests MUST verify that pagination/search-after retrieval yields no dropped or duplicated records across pages.
- **FR-017**: Regression tests MUST verify CSV and SQLite export compatibility for every new operation.
- **FR-018**: Documentation updates MUST include README menu/operation count changes and CHANGELOG entry describing new Org Marvis Client APIs operations and scope.
- **FR-019**: The feature MUST maintain compatibility with mistapi 0.63.0 endpoint naming and expected request/response workflow for the listed Org Marvis Client APIs.

### Key Entities *(include if feature involves data)*

- **Marvis Client Insight Record**: Org-level client insight entry used for AI-assisted client analysis; includes identity fields, scope fields, and insight context.
- **Marvis Client Event Count Result**: Aggregated event count dataset for a selected scope/time window; used to size event volume before detailed retrieval.
- **Marvis Client Event Record**: Detailed event-level dataset retrievable via paginated search with continuation token semantics.
- **Marvis Client Stats Count Result**: Aggregated client-stat count dataset for reporting and trend checks.
- **Marvis Client Stats Record**: Detailed client-stat dataset retrievable via paginated search with continuation token semantics.
- **Query Scope Input**: Operator-provided optional filters and duration/window values that determine dataset boundaries.
- **Pagination Continuation Token**: Search-after token used to request subsequent result pages in event and stats search workflows.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can execute any new Org Marvis Client operation end-to-end (prompting, retrieval, export) in under 3 minutes for typical single-page queries.
- **SC-002**: 100% of new operations provide successful CSV and SQLite output generation in regression test scenarios.
- **SC-003**: Pagination/search-after regression tests demonstrate 0 dropped records and 0 duplicate records across multi-page retrieval scenarios.
- **SC-004**: At least 95% of invalid-input scenarios (filters/duration/search-after) return clear corrective guidance on first response.
- **SC-005**: README and changelog documentation for operation additions are updated in the same release cycle as feature delivery.

## Assumptions

- Primary users are MistHelper operators running menu-driven workflows in trusted NOC environments.
- Feature scope is limited to new org-level Marvis Client APIs listed in request and excludes unrelated endpoint additions.
- Existing org selection/authentication flow remains unchanged and reused.
- Existing export workflow for CSV/SQLite remains authoritative and is extended, not replaced.
- Existing pagination and retry conventions are reused where applicable.
- Existing test framework and docs update process are in place and must be extended for new operations.
