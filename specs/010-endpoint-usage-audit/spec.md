# Feature Specification: Mist API Endpoint Usage Audit

**Feature Branch**: `010-endpoint-usage-audit`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Go through the MistHelper program and verify all API endpoint calls are correct and used properly, cross-referencing against the enriched API documentation in documentation/api/. Check both endpoint selection (right endpoint for the job) and usage correctness (right parameters, filters, pagination, HTTP method)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Endpoint Selection Audit (Priority: P1)

A developer reviews MistHelper's ~102 unique API function calls (278 call sites) to verify each menu operation uses the most appropriate Mist API endpoint for its stated purpose. For example, if a menu operation says "Export Device Events" but calls a stats endpoint instead of an events/search endpoint, that is flagged as a mismatch. The developer cross-references each call against the enriched API documentation in `documentation/api/` to confirm the endpoint's documented purpose matches the operation's intent.

**Why this priority**: Using the wrong endpoint entirely is the most severe class of bug -- it means the operation returns fundamentally wrong data or performs the wrong action. This is the highest-impact finding category.

**Independent Test**: Can be tested by producing an audit report that maps each menu operation to its API call(s) and comparing the operation's stated goal (from README/menu label) against the endpoint's documented purpose. Each mismatch is a finding.

**Acceptance Scenarios**:

1. **Given** MistHelper has 123 menu operations (keys 0-122) using ~102 unique API functions across 278 call sites, **When** each operation's purpose is compared against its endpoint's documented behavior, **Then** a report identifies any operations using a wrong or suboptimal endpoint
2. **Given** the enriched API docs describe each endpoint's purpose in the "Usage Context" section, **When** an operation's intent does not match the endpoint's documented purpose, **Then** the mismatch is flagged with the current endpoint, the recommended endpoint, and the rationale
3. **Given** some operations may use org-level endpoints when site-level would be more appropriate (or vice versa), **When** the scope mismatch is identified, **Then** it is flagged with the performance or correctness impact

---

### User Story 2 - Parameter and Usage Correctness Audit (Priority: P2)

A developer verifies that each API call passes the correct parameters, uses proper query filters, handles pagination correctly, and follows the endpoint's documented contract. For example, if an endpoint supports a `type` filter to include switches and gateways but MistHelper omits it (defaulting to APs only), that is flagged. Similarly, if an endpoint requires pagination but MistHelper only fetches the first page, or if optional parameters that improve data quality are consistently ignored.

**Why this priority**: Even with the right endpoint, incorrect parameter usage leads to incomplete data, missing device types, truncated results, or unnecessary API calls. This is the second-highest impact category because it causes subtle data quality issues that NOC engineers might not notice.

**Independent Test**: Can be tested by reading each API call site in the code, extracting the parameters passed, and comparing against the endpoint's documented parameter list (from the enriched docs). Each missing required parameter, misused optional parameter, or pagination gap is a finding.

**Acceptance Scenarios**:

1. **Given** an API endpoint documents required and optional parameters, **When** MistHelper calls that endpoint, **Then** all required parameters are verified as present and optional parameters are checked for appropriate usage
2. **Given** the known pitfall that `listSiteDevices` defaults to APs only without `type="all"`, **When** operations that need all device types are audited, **Then** any missing `type` filters are flagged
3. **Given** endpoints that return paginated results, **When** MistHelper's pagination handling is reviewed, **Then** any operations that may silently truncate results are identified

---

### User Story 3 - Deprecation and Best Practice Check (Priority: P3)

A developer checks whether any API calls use deprecated endpoints, deprecated parameters, or patterns flagged in the endpoint documentation's "Gotchas" sections. This includes checking for known issues documented in the enriched API docs, such as Dash 3.x API changes, rate limiting considerations, or response format changes.

**Why this priority**: Deprecated endpoints may stop working in future API versions, causing silent failures. Best practice violations (like not using bulk endpoints when available) lead to performance issues and rate limiting. These are lower urgency than wrong endpoints or wrong parameters but still need attention.

**Independent Test**: Can be tested by cross-referencing the "Gotchas" section of each used endpoint's documentation against the actual usage in MistHelper, and checking the Mist API changelog for any deprecation notices affecting current calls.

**Acceptance Scenarios**:

1. **Given** some endpoints have documented gotchas or deprecation warnings, **When** MistHelper uses those endpoints, **Then** any usage that violates the documented warnings is flagged
2. **Given** some operations iterate per-site when an org-level bulk endpoint exists, **When** the iteration pattern is identified, **Then** it is flagged with the recommended bulk alternative

---

### User Story 4 - Audit Report and Fix Plan (Priority: P4)

After the audit is complete, a structured report is produced that categorizes all findings by severity (Critical, High, Medium, Low), provides the specific code location, explains the issue, and recommends the fix. This report becomes the implementation plan for corrective changes.

**Why this priority**: The report is the deliverable that enables action. Without a structured report, individual findings are hard to prioritize and track. This story depends on stories 1-3 completing their analysis.

**Independent Test**: Can be tested by verifying the report contains all findings from stories 1-3, each with severity, location, description, and recommended fix. The report should be actionable without additional context.

**Acceptance Scenarios**:

1. **Given** findings from endpoint selection, parameter usage, and deprecation checks, **When** the audit report is generated, **Then** each finding includes: severity, menu operation affected, current code reference, current endpoint/usage, recommended change, and rationale
2. **Given** the audit report, **When** a developer reads a finding, **Then** they can implement the fix without needing additional research

---

### Edge Cases

- What happens when an endpoint is used correctly for one menu operation but incorrectly for another (same endpoint, different usage contexts)?
- How are WebSocket-based operations (menus 5-8, 87-89) handled, since they use a different communication pattern than REST endpoints?
- What about operations that chain multiple API calls -- does the audit cover the full call sequence or just individual calls?
- How are destructive operations (menus 90-100) audited given they cannot be safely test-executed?
- What if the enriched API documentation itself has errors that lead to false-positive findings?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Audit MUST catalog every `mistapi.api.v1.*` call site in MistHelper.py, maps_manager.py, and wsgi.py, mapping each to the menu operation that invokes it
- **FR-002**: Audit MUST cross-reference each API call against the corresponding endpoint documentation in `documentation/api/` to verify purpose alignment
- **FR-003**: Audit MUST verify that required parameters documented for each endpoint are actually passed in the code
- **FR-004**: Audit MUST check optional parameters and categorize findings into two tiers: (a) "Incorrect" — omission or misuse that causes wrong or incomplete results (e.g., missing `type="all"` for device listings), and (b) "Suboptimal" — usage that works but does not follow best practices or misses available improvements
- **FR-005**: Audit MUST verify pagination handling for all endpoints that return paginated results, flagging any operations that may truncate
- **FR-006**: Audit MUST check for deprecated endpoints or parameters by reviewing the "Gotchas" sections of the enriched API docs
- **FR-007**: Audit MUST identify operations that iterate per-site when an equivalent org-level bulk endpoint exists
- **FR-008**: Audit MUST produce a structured report with findings categorized by severity (Critical, High, Medium, Low) and by correctness tier (Incorrect vs Suboptimal)
- **FR-009**: Each finding MUST include: severity, affected menu operation(s), code location, current behavior, recommended change, and rationale
- **FR-010**: Audit MUST cover the full chain of API calls for operations that use multiple endpoints in sequence
- **FR-011**: Audit report MUST be delivered as two files: a structured JSON file (machine-parseable, suitable for automated processing) and a companion Markdown summary containing: severity breakdown table, tier breakdown table, category breakdown table, top 10 findings by severity, coverage statistics, and scope metadata

### Key Entities

- **Menu Operation**: A numbered user-facing operation (0-122, 123 entries) with a stated purpose, mapped to one or more API calls
- **API Call Site**: A specific location in MistHelper.py where a `mistapi.api.v1.*` function is invoked, including the parameters passed
- **Endpoint Documentation**: The enriched markdown file in `documentation/api/` describing the endpoint's purpose, parameters, gotchas, and related endpoints
- **Audit Finding**: A discrepancy between how an endpoint is used and how it should be used, with severity and recommended fix
- **Audit Report**: The complete structured output containing all findings, organized by severity and menu operation

## Clarifications

### Session 2026-03-08

- Q: Should corrections be applied immediately during audit or report-only first? → A: Report-first, then fix in separate phase
- Q: For operations using correct endpoint but suboptimal parameters, how should findings be categorized? → A: Both — flag all suboptimal parameter usage AND wrong/incomplete results, but separate them into distinct finding categories in the report
- Q: How should the audit report be delivered? → A: Structured JSON file (machine-parseable) with a companion Markdown summary (human-readable), both in the specs directory

## Assumptions

- The audit produces a report-only deliverable first; code corrections are applied in a separate implementation phase after the full report is reviewed
- The enriched API documentation in `documentation/api/` (1,013 files from Feature 009) is treated as the authoritative reference for endpoint behavior
- The `mistapi` SDK (v0.59+) function signatures accurately reflect the underlying Mist REST API
- WebSocket operations (menus 5-8, 87-89) are in scope for the audit but may require different validation criteria than REST endpoints
- The audit is a code review activity -- it does not require executing API calls against a live Mist environment
- Operations marked as WIP (menus 63-65) are still audited for correctness but findings are flagged as lower priority
- The audit focuses on MistHelper.py as the primary codebase; auxiliary files (maps_manager.py, wsgi.py) are included if they contain API calls

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the ~107 unique API functions (across 370 call sites in MistHelper.py, maps_manager.py, and wsgi.py) are reviewed and documented in the audit report
- **SC-002**: Every finding includes enough context (code location, current usage, recommended fix) that a developer can implement the correction without additional research
- **SC-003**: Zero Critical-severity findings remain unaddressed after the corrective implementation phase *(deferred -- verifiable only after corrective implementation feature)*
- **SC-004**: All High-severity findings have a documented fix plan with clear before/after expectations *(deferred -- verifiable only after corrective implementation feature)*
- **SC-005**: Operations that previously returned incomplete data (e.g., missing device types) return complete results after corrections are applied *(deferred -- verifiable only after corrective implementation feature)*
