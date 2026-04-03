# Feature Specification: Interactive Marvis AI troubleshooting (AUDIT)

**Feature Branch**: current-branch (do not create or switch branch)  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "Interactive Marvis AI troubleshooting" (Menu #62)  

Summary
-------
This is an AUDIT specification for the existing Interactive Marvis (VNA) troubleshooting feature exposed by MistHelper.menu item #62 and implemented in TroubleshootUtils.launch_interactive (and related Marvis utilities) in MistHelper.py.

Goal: document the current implementation's behavior (interactive flow, auth/token handling, timeouts, logging, and testability), identify issues and gaps, and define clear, testable acceptance criteria for required fixes.

Scope
-----
- Analyze interactive user flow and how options/inputs are collected and handled.  
- Review authentication and token handling for Marvis API calls (cache/refresh, storage, error handling).  
- Review enforcement of timeouts for both user input and external API/network calls.  
- Review logging and observability (what is logged, levels, structure, correlation).  
- Review testability: ability to unit-test interactive flows and mock Marvis/mistapi responses.  

Out of scope: implementation details of Marvis backend; changes to external APIs. No branching or commits will be created by this audit — this is a documentation + acceptance-criteria artifact only.


User Scenarios & Testing (mandatory)
------------------------------------
Prioritized user journeys focusing on interactive troubleshooting and recovery paths.

### User Story 1 - Interactive troubleshooting happy path (Priority: P1)

An operator invokes the Marvis interactive menu, chooses a troubleshooting target (client/device/network), provides required identifiers, and receives a diagnostic summary and optional CSV export.

Why this priority: This is the core value of the feature — make Marvis insights accessible via an interactive flow.

Independent Test:
- Run the interactive function in a controlled environment with a recorded/mocked Marvis response. Verify the flow prompts for expected inputs, calls Marvis, prints / returns a summary, and (if requested) produces a CSV file path.

Acceptance Scenarios:
1. Given valid org context and Marvis entitlement, When user selects "client" troubleshooting and provides a client MAC, Then the tool calls Marvis troubleshoot, displays a readable summary, and writes a CSV with expected columns.
2. Given invalid client identifier, When user provides input, Then the tool reports a clear, user-facing error and logs the detail at an appropriate log level.

---

### User Story 2 - Auth token expiry and refresh (Priority: P1)

The interactive session should detect an expired or invalid token, attempt a refresh (or re-auth) automatically where appropriate, and surface clear guidance to the operator if re-authentication is required.

Why this priority: Auth failures block the feature entirely; automated handling reduces operator friction.

Independent Test:
- Simulate a token with a short TTL or a 401 response from Marvis; verify the session attempts token refresh and either succeeds or presents a clear instruction.

Acceptance Scenarios:
1. Given an expired token and a valid refresh path, When the Marvis call fails with authentication, Then the system refreshes/re-acquires a token and retries once automatically before reporting failure.
2. Given no refresh path (e.g., missing credentials), When auth fails, Then the tool prompts the user with next steps (how to provide credentials) and logs the failure.

---

### User Story 3 - Network/API timeouts and retry behavior (Priority: P2)

Network calls to Marvis may be slow or transiently fail. The interactive workflow should enforce configurable timeouts, provide user feedback when Marvis is slow, and retry sensibly when safe.

Why this priority: Prevents the interactive session from hanging indefinitely and improves reliability.

Independent Test:
- Simulate slow Marvis responses and verify the interactive command applies configured timeouts and returns a user-facing timeout message.

Acceptance Scenarios:
1. Given Marvis API is slow (exceeds API timeout), When the tool calls Marvis, Then the call is aborted after the configured timeout and a helpful message is shown to the user.
2. Given an intermittent network failure, When the tool calls Marvis, Then the call is retried with backoff up to the configured retry count and logs include retry attempts.

---

Edge Cases
----------
- Operator abandons the interactive session (e.g., hits Ctrl-C) while request in-flight — system should clean up and not leave partial files or hanging resources.  
- Marvis returns unexpected payload shapes — system should fail gracefully and surface a relevant error including a correlation id for investigation.  
- Permission/entitlement differences between orgs (Marvis disabled) — interactive flow should detect this early and exit with guidance.


Requirements (mandatory)
------------------------
Functional Requirements (testable)
- FR-001: The interactive menu MUST present clear, ordered options for Client, Device, Network troubleshooting, and a "view capabilities" item.
- FR-002: The interactive flow MUST validate user inputs (MAC format, device name non-empty, site id numeric/uuid pattern) and reject invalid inputs with clear messages.
- FR-003: The module MUST use a single Marvis client abstraction (a callable/service object) for all Marvis API calls to allow mocking in tests.
- FR-004: Authentication tokens used for Marvis MUST be cached with expiry metadata and MUST support automatic refresh where a documented refresh mechanism exists.
- FR-005: All outgoing Marvis API calls MUST enforce a configurable timeout (default value documented in assumptions) and report timeout events to the user and in logs.
- FR-006: The interactive user input prompts MUST support a configurable input timeout and a sensible default to avoid indefinite blocking in automated test runs.
- FR-007: The tool MUST use structured logs for Marvis flows containing at least: timestamp, log level, component, correlation_id (request id), user action, and error details.
- FR-008: Console-facing user messages MUST be produced via an abstraction (output writer) so tests can capture and assert on messages (avoid untestable direct print() usage).
- FR-009: The module MUST not mix side-effecting global imports with business logic; functions that perform Marvis calls MUST accept client/session dependencies (dependency injection) to enable unit testing.
- FR-010: The system MUST write CSV output into a configurable output directory and MUST provide the generated path to the caller for verification in tests.
- FR-011: The module MUST provide a way to inject mocked Marvis responses for unit tests and an integration test harness that can replay recorded Marvis responses.
- FR-012: All Marvis call failures (auth, 4xx, 5xx, network) MUST be logged with correlation_id and an actionable message for operators.

Key Entities
------------
- MarvisSession / MarvisClient: abstraction representing credentials, token cache, and HTTP client for Marvis calls.  
  - Attributes: token, token_expires_at, org_id, refresh_credentials_info (if available).  
- InteractiveSession: ephemeral object per invocation storing correlation_id, start_time, selected_target, and prompt state.  
- MarvisRequest / MarvisResponse: request metadata (type, parameters) and parsed response (summary, raw payload, CSV rows).  
- LogEntry: structured log objects emitted during flow (see FR-007).


Current Implementation Observations (audit findings)
---------------------------------------------------
Note: findings are based on a static review of MistHelper.py and observed patterns (prints + logging + dynamic imports). Specific code references are in MistHelper.py (MarvisDataUtils and Marvis troubleshooting utilities).

1) Mixed output channels
- The Marvis interactive flow uses both print(...) and logging.*(...) in multiple places. User-facing text is often printed directly which makes automated capture and assertions for tests difficult.

2) Auth/token handling not centralized
- The code appears to rely on a global or project-level authentication mechanism (mistapi imports and global namespace population). There is no clear, isolated MarvisClient class with transparent token caching and refresh logic. Token lifecycle and refresh retry behavior are not obvious from the call sites.

3) Timeouts are inconsistent
- Timeouts are applied in subprocess and some dependency-install flows (see UV/pip timeouts), but there is no obvious, consistently-applied timeout configuration for Marvis API calls or for interactive user prompts. This risks blocking behavior during slow network conditions or unattended automation runs.

4) Logging is unstructured and inconsistent
- The code uses logging.* in many places, but messages vary in granularity and often lack a correlation id or request id that ties a particular interactive session to subsequent logs. Error messages are sometimes only printed, sometimes logged; log levels appear ad-hoc.

5) Hard-to-test global state
- The import manager populates globals() with imported modules and falls back to dynamic global variables (e.g., mistapi, paramiko). The Marvis code calls out to these global objects which makes unit tests brittle and requires heavy patching of module globals instead of dependency injection.

6) Lack of clear retry/backoff policy
- When Marvis calls fail with transient errors, there is no documented or visible retry and backoff policy; callers either proceed or fail, which reduces resiliency.

7) No explicit interactive timeouts
- Interactive prompts appear to be plain blocking input calls (or similar). For use in CI or automation, the ability to set prompt timeouts or to run in non-interactive mode is missing.

8) CSV generation and file handling not surfaced for automation tests
- CSV files are written (naming patterns observed) but the code does not consistently return the path or a result object; instead the flow prints completion messages. This complicates automated verification.


Issues and Risk Summary
----------------------
- Testability risk: high — global state and direct prints hinder unit and integration testing.  
- Reliability risk: medium — missing timeouts and retries may cause long-running or hanging interactive sessions.  
- Observability risk: medium — inconsistent logging and lack of correlation ids impede debugging.  
- Security/UX risk: medium — unclear token refresh behavior may surface secrets or require repeated manual auth.


Assumptions
-----------
- Marvis API surface returns HTTP status codes, supports token-based auth, and can return 401/403 for auth failures.  
- There is an existing authentication mechanism in the codebase (mistapi) which can supply tokens or credentials programmatically.  
- Default API timeout for Marvis calls (reasonable baseline) will be set to 30 seconds unless product owner specifies otherwise.  


[NEEDS CLARIFICATION: 1] Interactive input timeout policy
- What default behavior should the interactive prompts use if the operator does not answer? Options include: no timeout (current), a short timeout (e.g., 120s), or fail-fast for CI mode. This impacts how the feature behaves in automation.

[NEEDS CLARIFICATION: 2] Token refresh semantics
- If a token expires during an interactive session, should the tool attempt automatic refresh (if refresh credentials are available), silently re-authenticate, or surface a manual re-auth flow? This impacts security and user experience.


Functional Fixes and Acceptance Criteria
---------------------------------------
The following acceptance criteria are the minimal, testable items that must be implemented to address the audit findings. Each is phrased to be verifiable via tests or inspection.

AC-001: Marvis client abstraction
- There MUST be a MarvisClient (or equivalent) object used by the interactive flow. Tests must be able to instantiate MarvisClient with mocked token behavior and stubbed HTTP responses.
- Test: unit test that swaps MarvisClient with a fake and verifies interactive flow calls the fake with expected parameters.

AC-002: Centralized token cache & refresh
- Tokens MUST be stored with expiry metadata. On a 401 from Marvis, the client MUST attempt a single automatic refresh and retry the original request once. If refresh fails, the interactive session MUST show a clear, actionable message.
- Test: simulate 401 -> ensure refresh+retry is attempted; simulate refresh failure -> ensure user-facing guidance and a log entry with correlation_id.

AC-003: Configurable API and prompt timeouts
- All Marvis API calls MUST accept a configurable timeout (default 30s). Interactive prompts MUST support a configurable input timeout (default 120s) and a non-interactive mode must be supported for automation.
- Test: inject a Marvis client that delays beyond the timeout and assert the calling code raises or returns a documented timeout error and logs it.

AC-004: Structured logging with correlation id
- Each interactive session MUST generate a correlation_id (UUID-like) included in all logs and in any CSV/footer written for that session. Error logs MUST include the correlation_id so operators can trace issues.
- Test: run an interactive flow with a fixed correlation_id and assert emitted logs/return values include that id.

AC-005: Replace direct prints with output abstraction
- Console/output MUST be emitted through an injected OutputWriter with methods like info(), warn(), error() so tests can capture messages.
- Test: use a fake OutputWriter in unit tests to assert expected messages are produced in each scenario.

AC-006: Retry policy and backoff for transient errors
- The Marvis client MUST implement a configurable retry count (default 2) with exponential backoff for 5xx or network-level failures. Retries MUST be logged with attempt numbers.
- Test: simulate transient failures and assert the client retried expected number of times and logs show attempts.

AC-007: Expose CSV path and structured result
- The interactive function MUST return a structured Result object (or raise a documented exception) that includes: correlation_id, success boolean, summary text, raw response metadata, and csv_paths list.
- Test: call the function in test mode and assert the returned object contains csv_paths and correlation_id.

AC-008: Dependency injection for imports/global state
- The interactive flow MUST accept dependencies (MarvisClient, OutputWriter, Logger) as parameters or via a configuration object rather than reading them from module globals.
- Test: ensure unit tests can pass in mocks without mutating module-level globals.

AC-009: Test harness and mocks
- Provide a set of unit tests and an integration test harness that can replay recorded Marvis responses. The repository MUST include at least 1 unit test per acceptance scenario and an integration test that asserts end-to-end behavior against recorded responses.
- Test: CI must run these tests; local instructions for running tests must be documented.

AC-010: Clear handling for Marvis disabled or insufficient permission
- If organization lacks Marvis entitlement or user permissions, the interactive flow MUST detect this before prompting for detailed inputs and must show next steps (contact admin/enable feature).
- Test: mock Marvis metadata response indicating entitlement disabled and assert the tool exits early with a helpful message.


Testing & Validation
--------------------
- Unit tests should replace MarvisClient with a FakeMarvisClient to assert request parameters and returned summaries.  
- Integration tests should use recorded HTTP fixtures (VCR-like) and assert CSV contents and summary text.  
- Logging tests should capture emitted logs and validate presence of correlation_id and error details.


Metrics and Success Criteria
----------------------------
- SC-001: 100% of interactive happy-path acceptance scenarios pass in unit/integration tests.  
- SC-002: Marvis API calls time out within configured timeout 100% of the time under simulated slow responses.  
- SC-003: Automatic token refresh succeeds in the simulated refresh scenario and results in successful retry at least 95% of runs in the test harness.  
- SC-004: All error logs include correlation_id and a human-friendly operator message.  
- SC-005: Test coverage for the interactive Marvis flow >= 80% (unit + integration for this module).


Implementation Notes (guidance, not prescriptive)
-------------------------------------------------
- Prefer small, testable functions: prompt -> validate -> call -> format -> output.  
- Use an injected HTTP client or MarvisClient to centralize retry/backoff and timeout logic.  
- Use structured logging (JSON or key=value) for machine parsing in SRE/debugging.  
- Keep interactive code UI-focused; heavy parsing and CSV formatting live in MarvisDataUtils and are already a good separation of concerns.


Deliverables (audit -> fixes)
-----------------------------
1. Spec file (this document).  
2. A small set of unit tests and a test harness demonstrating injection of a fake MarvisClient.  
3. Code changes: MarvisClient abstraction, OutputWriter abstraction, add correlation_id to session logs, enforce configurable timeouts and prompt timeouts, ensure CSV paths are returned.  
4. Updated documentation for running the interactive flow in non-interactive/CI mode.


Next steps
----------
- Resolve the two clarifications above (interactive input timeout policy and token refresh semantics).  
- Implement changes incrementally using the acceptance criteria above; target P1 items first (Marvis client abstraction, token handling, output abstraction).  


Status: SUCCESS (spec ready for planning)


References
----------
- Relevant code: MistHelper.py (MarvisDataUtils and Marvis troubleshooting sections).  
- Feature: Menu #62 - Interactive Marvis AI troubleshooting


Appendix: Extracted [NEEDS CLARIFICATION] markers
------------------------------------------------
1) [NEEDS CLARIFICATION: Interactive input timeout policy]  
2) [NEEDS CLARIFICATION: Token refresh semantics]
