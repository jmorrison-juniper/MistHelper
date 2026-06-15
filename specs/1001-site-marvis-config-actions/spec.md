# Feature Specification: Site Marvis Config Actions

**Feature Branch**: `1001-site-marvis-config-actions`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Create a new feature specification for MistHelper to add menu operations for mistapi 0.63.0 Site Marvis Config Action APIs, including safe count/search exports, destructive delete with typed confirmation, mutating feedback with strong validation, UX safety parity, PK strategies, test guards, and documentation updates."

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

### User Story 1 - Export site Marvis config action data safely (Priority: P1)

As a NOC engineer, I want menu operations to count and search site Marvis config actions so I can analyze action volume and details without changing production state.

**Why this priority**: Safe read/export workflows are daily operational tasks and provide immediate value with low risk.

**Independent Test**: Can be fully tested by running count and search operations for a selected site and verifying exported output, row counts, and no state mutation.

**Acceptance Scenarios**:

1. **Given** a valid organization and site context, **When** I run the count operation, **Then** the system returns a count result and exports it using the configured output workflow.
2. **Given** a valid organization and site context, **When** I run the search operation with filters, **Then** the system returns matching action records and exports them with stable keys.
3. **Given** no matching records for the selected filters, **When** I run search, **Then** the system completes successfully with an empty-result export and clear user feedback.

---

### User Story 2 - Submit config-action feedback with guardrails (Priority: P2)

As a NOC engineer, I want to submit feedback for a site Marvis config action so operations and engineering teams can capture action quality signals safely and consistently.

**Why this priority**: Feedback workflows are operationally important but lower frequency than read/export actions.

**Independent Test**: Can be fully tested by entering valid and invalid feedback payloads and verifying strict validation, rejection behavior, and successful submission for valid inputs.

**Acceptance Scenarios**:

1. **Given** a valid site and action context, **When** I submit feedback with valid required fields, **Then** the system submits feedback successfully and logs pre/post action status.
2. **Given** invalid or incomplete feedback input, **When** I attempt submission, **Then** the system blocks submission, explains the validation failure, and does not call the mutating endpoint.

---

### User Story 3 - Delete a config action only with explicit confirmation (Priority: P3)

As a NOC engineer, I want to delete a specific site Marvis config action by ID only after explicit typed confirmation so destructive changes are deliberate and auditable.

**Why this priority**: Destructive operations are required for completeness but must be gated by strong safety controls.

**Independent Test**: Can be fully tested by attempting delete with wrong confirmation, cancel path, and exact confirmation path; verify execution only occurs after correct confirmation.

**Acceptance Scenarios**:

1. **Given** a valid action ID, **When** I enter an incorrect typed confirmation, **Then** the delete operation is aborted and no deletion request is sent.
2. **Given** a valid action ID, **When** I enter the exact required typed confirmation, **Then** the delete request executes and the result is reported with before/after logging.
3. **Given** automated test mode is enabled, **When** destructive operation suites run, **Then** delete remains skipped or guarded to prevent accidental production mutation.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- User provides an invalid or non-existent site identifier for count/search.
- Search returns very large result sets requiring robust pagination and stable exports.
- User provides malformed, empty, or unknown config action ID for delete.
- Feedback input includes unsupported values, missing required fields, or unsafe free-text content.
- Endpoint call succeeds but returns partial metadata; export still needs deterministic schema.
- API timeout, permission failure, or rate limiting occurs during safe, mutating, or destructive operations.
- Automated test mode executes full suite; destructive operation must remain skipped/guarded and reported as intentionally not executed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a safe menu operation to count site Marvis config actions using `countSiteMarvisConfigActions()`.
- **FR-002**: System MUST provide a safe menu operation to search site Marvis config actions using `searchSiteMarvisConfigActions()`.
- **FR-003**: Safe count/search operations MUST follow existing MistHelper read/export UX patterns and MUST NOT mutate remote state.
- **FR-004**: System MUST provide a destructive menu operation to delete a site Marvis config action by explicit action ID using `deleteSiteMarvisConfigAction()`.
- **FR-005**: Delete operation MUST require typed confirmation with an exact confirmation string before execution.
- **FR-006**: Delete operation MUST present clear pre-action warnings describing destructive impact and cancellation behavior.
- **FR-007**: System MUST provide a mutating menu operation for config-action feedback submission using `submitSiteMarvisConfigFeedback()`.
- **FR-008**: Feedback submission flow MUST enforce strong input validation (required fields, allowed values, and format checks) before making API calls.
- **FR-009**: If validation fails, system MUST reject submission, show actionable error feedback, and avoid mutating calls.
- **FR-010**: All four operations MUST preserve existing MistHelper UX safety conventions, including safe interactive input handling, clear warnings, and observable before/after action logging.
- **FR-011**: System MUST define and document primary-key strategy for count output records and search output records to support deterministic export/upsert behavior.
- **FR-012**: Automated test mode MUST include coverage for safe count/search and feedback validation behaviors.
- **FR-013**: Automated test mode MUST skip or hard-guard destructive delete execution, with explicit reporting that destructive path was intentionally not run.
- **FR-014**: Feature delivery MUST include documentation updates for menu operation inventory/count in `README.md` and release entry in `CHANGELOG.md`.

### Key Entities *(include if feature involves data)*

- **Site Marvis Config Action Record**: A searchable action item at site scope, identified by action ID and carrying action metadata used in exports and follow-on operations.
- **Config Action Count Result**: A summarized count payload representing number of matching site config actions for a given query context.
- **Delete Request Context**: User-provided action ID plus confirmation decision state that determines whether destructive execution is permitted.
- **Feedback Submission Payload**: Validated user input associated with a site action, including required fields and feedback classification/value.
- **Operation Audit Event**: Pre/post execution trace data for safe, mutating, and destructive flows used for operator observability and troubleshooting.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can complete safe count/search export workflows for a selected site in under 2 minutes for typical datasets.
- **SC-002**: 100% of destructive delete attempts require exact typed confirmation before any remote change is attempted.
- **SC-003**: 100% of invalid feedback submissions are blocked prior to mutation, with user-visible validation guidance.
- **SC-004**: Automated test runs include explicit evidence that destructive delete is skipped or guarded and that safe/mutating validation paths are covered.
- **SC-005**: Feature release artifacts include updated menu-operation documentation and changelog entry in the same delivery cycle.

## Assumptions

- Target users are authenticated MistHelper operators with permissions to query site config actions and submit feedback; delete permission may be narrower.
- Existing MistHelper safety posture (interactive confirmation, guardrails, warning language, and logging style) remains baseline behavior for new operations.
- Count/search/feedback/delete operations are introduced as incremental menu additions and do not replace existing menu workflows.
- Export pipelines and reporting conventions used by other MistHelper API-backed operations remain the standard for this feature.
- Destructive-path automation remains intentionally constrained in unattended test execution to avoid accidental production state changes.
