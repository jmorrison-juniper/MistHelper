# Feature Specification: MistAPI 0.63 Org Async Claim Menu Operations

**Feature Branch**: `[203-org-async-claims]`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Create a new feature specification for MistHelper to add menu operations for mistapi 0.63.0 Org Async Claim APIs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Org Async Claims (Priority: P1)

As a NOC engineer, I can run a safe menu operation that lists organization async claim records and exports them using the standard output flow, so I can audit claims without changing configuration.

**Why this priority**: Read-only visibility is the fastest way to validate new upstream support and delivers immediate operational value with low risk.

**Independent Test**: Can be fully tested by selecting the list/export menu operation with a valid org context and confirming records are presented and exported in the same way as other safe export operations.

**Acceptance Scenarios**:

1. **Given** valid organization credentials and at least one async claim, **When** the operator runs the async claim list/export operation, **Then** the system returns claim records and writes export output through the standard export workflow.
2. **Given** valid organization credentials and no async claims, **When** the operator runs the async claim list/export operation, **Then** the system completes successfully with an empty-result response and clear operator feedback.

---

### User Story 2 - Create Org Async Claim (Priority: P2)

As a NOC engineer, I can create a new org async claim from the menu with explicit typed confirmation, so I can safely perform a configuration-changing action while preventing accidental execution.

**Why this priority**: This action is operationally important but riskier than read-only export; safety controls must be preserved.

**Independent Test**: Can be tested by selecting the create operation, verifying typed confirmation gating, and validating that request execution only occurs after correct confirmation input.

**Acceptance Scenarios**:

1. **Given** a valid claim payload and operator at the create operation, **When** the operator provides the required typed confirmation exactly, **Then** the system submits the create request and returns the created async claim response.
2. **Given** a valid claim payload and operator at the create operation, **When** the operator provides incorrect or empty typed confirmation, **Then** the system cancels the operation without sending a create request.

---

### User Story 3 - Retrieve Async Claim Status by ID (Priority: P3)

As a NOC engineer, I can query async claim status by claim ID, so I can track lifecycle progress and verify completion/failure after submission.

**Why this priority**: Status checks are important for operational follow-up but rely on the existence of claim IDs from list/create workflows.

**Independent Test**: Can be tested independently by entering a known claim ID and validating returned status details and export behavior.

**Acceptance Scenarios**:

1. **Given** a valid org and an existing async claim ID, **When** the operator runs the status operation with that ID, **Then** the system returns claim status details and exports the result using standard output behavior.
2. **Given** a non-existent or malformed claim ID, **When** the operator runs the status operation, **Then** the system returns clear failure feedback and does not crash or hang.

### Edge Cases

- Empty or whitespace claim ID input for status lookup must be rejected with a user-friendly retry/cancel path.
- API permission failures (insufficient org privileges) must return actionable operator feedback for all three operations.
- Partial or delayed async claim availability (eventual consistency) must be handled without duplicate submissions or misleading completion messages.
- Create operation interruption (EOF/session disconnect) must exit safely before dispatching a write action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add one new safe menu operation to list org async claims and produce operator-viewable/exportable results.
- **FR-002**: System MUST add one new configuration-changing menu operation to create an org async claim.
- **FR-003**: System MUST require explicit typed destructive confirmation before executing async claim creation.
- **FR-004**: System MUST abort async claim creation when confirmation text is incorrect, empty, or cancelled.
- **FR-005**: System MUST add one new menu operation to retrieve org async claim status by claim ID.
- **FR-006**: System MUST validate required user input (including claim ID for status lookup) before invoking upstream requests.
- **FR-007**: System MUST preserve existing MistHelper interactive UX conventions for input handling and destructive-operation safety prompts.
- **FR-008**: System MUST preserve existing MistHelper export/output conventions so list and status operations produce outputs consistent with current menu exports.
- **FR-009**: System MUST define endpoint primary-key strategies for async-claim list output, create response output, and status output to prevent duplicate persistence and support repeatable upserts.
- **FR-010**: System MUST include automated test coverage for success, validation failure, and API error paths for all three operations.
- **FR-011**: System MUST mark the destructive create operation as skipped in default `--test` execution unless explicitly enabled by the project’s destructive-test policy.
- **FR-012**: System MUST update documented operation counts to include the three new menu operations (207 to 210).
- **FR-013**: System MUST add a changelog entry documenting mistapi 0.63.0 org async claim menu support and operation-number additions.

### Key Entities *(include if feature involves data)*

- **OrgAsyncClaimRecord**: Read-only async claim metadata returned by org-level claim listing; includes business identifiers, timestamps, and claim lifecycle fields.
- **OrgAsyncClaimCreateRequest**: Operator-provided claim payload used to submit a new async claim; must pass input validation and destructive confirmation gating.
- **OrgAsyncClaimStatusRecord**: Claim status view retrieved by claim ID; includes processing state and result/error indicators.
- **MenuOperationDefinition**: Operation metadata for menu number, safety class (safe vs destructive), prompts, and export behavior.
- **EndpointPrimaryKeyStrategy**: Persistence identity rules used to deduplicate list/create/status outputs across repeated runs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of manual runs for the new list operation complete without configuration changes and return either valid records or an explicit empty-result outcome.
- **SC-002**: 100% of create-operation attempts without exact typed confirmation are blocked before any upstream create request is sent.
- **SC-003**: Operators can complete a status lookup by known claim ID in one menu flow without requiring external tooling.
- **SC-004**: Automated tests covering new operations pass in CI, with destructive create tests skipped by default in the standard `--test` run profile.
- **SC-005**: Project documentation reflects the new total operation count (210) and includes a dated changelog entry for this capability.

## Assumptions

- MistHelper upgrades to mistapi 0.63.0 include stable availability of `listOrgAsyncClaims`, `createOrgAsyncClaim`, and `getOrgAsyncClaimStatus` endpoints.
- Existing menu numbering has available contiguous slots for three new operations after current operation 207.
- Existing export and persistence pathways can store async claim outputs once primary-key strategies are defined.
- Default automated test execution continues to exclude destructive operations unless explicitly opted in.
- Existing operator permissions and organization context selection behavior are reused with no role model changes in this feature.
