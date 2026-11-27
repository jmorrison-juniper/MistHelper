# Feature Specification: Interactive login request timeout

**Feature Branch**: `fix/4827-interactive-login-timeout`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4827, "Runtime: missing session timeout module in LoginOrchestrator". The issue reports a deferred import of a module that does not exist. PR #4830 removed that import on `main`. This specification covers the timeout contract that the issue still needs.

**Record**: `specs\numbered\0\0\1\2\3\3\0\2\4827-interactive-login-timeout`

## Background

The interactive login has no request timeout. Its requests can wait without a limit when a connection stalls. The timeout contract that the token path uses does not reach the interactive login. The remote evidence for each claim is in `design/research.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The interactive login stops after the request timeout (Priority: P1)

An operator starts the interactive login. A connection stalls during a login request. The request stops after the configured request timeout, and the operator sees a failure message. The operator does not wait without a limit.

**Why this priority**: This story removes the hang that the issue describes. It protects each run that starts with the interactive login.

**Independent Test**: Start a local server that never answers. Apply the timeout adapter to a session with a request timeout of 1 second. Send a login request. The request fails with a read timeout within 5 seconds.

**Acceptance Scenarios**:

1. **Given** a request timeout of 1 second, **When** a login request receives no answer, **Then** the request raises a read timeout within 5 seconds.
2. **Given** a request timeout of 1 second, **When** the two-factor replay receives no answer, **Then** the replay raises a read timeout within 5 seconds.

---

### User Story 2 - The removed import stays removed (Priority: P1)

A maintainer runs the import-resolution test. The test resolves every import in `login_orchestrator.py` from the real source tree. A stale import fails the test.

**Why this priority**: The defect in the issue came from an import that no source tree held. A regression test must keep this path closed.

**Independent Test**: Run `TestImportResolution` on the current tree. The test passes on `main` (RC-09, RC-10).

**Acceptance Scenarios**:

1. **Given** the orchestrator source on `main`, **When** the import-resolution test runs, **Then** no import of the orchestrator is unresolved.

---

### User Story 3 - The SDK hook is pinned (Priority: P2)

A maintainer upgrades the pinned SDK. The SDK compatibility test checks the transport factory and both login paths. A change that removes the hook fails in CI before it reaches an operator.

**Why this priority**: The timeout depends on a private SDK hook. A silent SDK change would remove the timeout without a warning.

**Independent Test**: Run the SDK compatibility test with the pinned mistapi 0.64.1.

**Acceptance Scenarios**:

1. **Given** mistapi 0.64.1, **When** the test inspects `APISession`, **Then** `_new_session` exists and both login paths call it.

---

### User Story 4 - The operator sees the cause of an invalid timeout (Priority: P3)

An operator sets the request timeout to 0 or to a negative value. The interactive login fails before its first request. The message names the setting.

**Why this priority**: A zero timeout makes each request fail at once (RC-90). The message lets the operator correct the value without a code change.

**Independent Test**: Create the orchestrator with a request timeout of 0. Run the interactive login with a fake SDK session. The message names `API_REQUEST_TIMEOUT`, and no login request is sent.

**Acceptance Scenarios**:

1. **Given** a request timeout of 0, **When** the interactive login starts, **Then** the console shows a message that names `API_REQUEST_TIMEOUT`, and no login request is sent.

### Edge Cases

- The SDK builds a new transport for each login call. The two-factor replay builds a second transport. Both transports must carry the timeout adapter.
- The caller sets a timeout on one request. The timeout adapter keeps the caller value.
- The SDK does not expose the transport factory. The login fails before any request, and the message names the missing hook.
- The request timeout is zero or negative. The login fails before any request, and the message names `API_REQUEST_TIMEOUT`.
- A connect timeout occurs during a login request. The existing connection error handler reports the failure.
- A read timeout occurs during a login request. The SDK reports an authentication failure, and the operator sees the failure message.
- The SDK session holds a cached API token. The orchestrator clears the token before login, as it does today. The timeout adapter does not read or change the token.
- The token path builds its session through `MistSessionConfigurator.configure_once`. That path keeps its own timeout adapter and its read retries.
- The loopback test server stops when the test ends. The server thread ends within the 5 second cap.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The orchestrator must not import `src.mist.access.auth.session_timeout`.
- **FR-002**: The import-resolution test must resolve every import of `login_orchestrator.py` without a `sys.modules` stub.
- **FR-003**: Interactive login must apply `API_REQUEST_TIMEOUT` to every login transport before the first login request.
- **FR-004**: The timeout adapter must fill a missing request timeout and keep a caller-set timeout.
- **FR-005**: The timeout adapter must make one attempt for each request, so a login request is never repeated.
- **FR-006**: Each transport built during interactive login, including the two-factor replay, must carry the timeout adapter.
- **FR-007**: A zero or negative request timeout must fail before any login request. The message must name `API_REQUEST_TIMEOUT`.
- **FR-008**: A missing SDK transport factory must fail the login closed. The SDK compatibility test must detect the same drift in CI.
- **FR-009**: New log lines must not contain a password, a token, or a session value.
- **FR-010**: The token path must keep the behavior of `MistSessionConfigurator.configure_once`.
- **FR-011**: The README, the operator guide, and the CONTRIBUTING row must describe the interactive timeout and the corrected `configure_session_timeout` entry point.
- **FR-012**: The change must add one changelog fragment named `issue-4827-interactive-login-timeout.md`.
- **FR-013**: The change must add no direct child to `src/mist/access/auth/interactive/`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- **Mist REST methods used**: `APISession.login_with_return` posts to `/api/v1/login` through `_process_login`, posts to `/api/v1/login/two_factor` through `_two_factor_authentication`, and reads `/api/v1/self` through the SDK helper `mist_get` (RC-55, RC-57, RC-58, RC-88, RC-89). The change adds no direct HTTP request. The OpenAPI paths are at RC-41, RC-42, and RC-43.
- **Owned WebSocket transport**: Not required. The change owns no WebSocket transport.
- **SDK insufficiency**: The pinned SDK exposes no timeout parameter (RC-60). Its request wrapper sends no timeout (RC-61). Contract test: `test_sdk_exposes_transport_hook_and_no_timeout_parameter`.
- **SDK authentication**: The timeout adapter changes no header. Contract test: `test_apply_wraps_each_transport_and_keeps_headers`.
- **SDK endpoint parity**: The timeout adapter changes no URL. Contract test: `test_apply_wraps_each_transport_and_keeps_headers`.
- **Failure safety**: A stalled request fails within the bound. Contract tests: `test_loopback_stall_raises_read_timeout_within_bound`, `test_non_positive_timeout_is_rejected`, and `test_missing_transport_hook_fails_closed`.
- **Secret redaction**: The new log lines contain no password. Contract test: `test_pipeline_bounds_transports_before_first_login`.

### Key Entities *(include if feature involves data)*

- **Login transport**: The requests session that the SDK builds for one login call. It carries the timeout adapter. It exists only in memory.
- **Request timeout**: The number of seconds that one request waits for a response. The environment variable `API_REQUEST_TIMEOUT` sets it. The default is 120 seconds.
- **Timeout adapter**: The transport adapter that fills a missing request timeout and makes one attempt for each request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A login request that receives no answer raises a read timeout within 5 seconds when the request timeout is 1 second.
- **SC-002**: Every new and changed test passes, and no new test is skipped.
- **SC-003**: Pylint reports a score of 9.5 or above for `src/`, and mypy reports no issue for `src/`.
- **SC-004**: The SDK compatibility test passes on mistapi 0.64.1, and its failure message names the missing hook.
- **SC-005**: Remote CI on the pull request reports every required check as passed before the `auto-merge` label is added.
- **SC-006**: The changelog guard reports the fragment as present and valid.

## Assumptions

- **A-1**: The pinned SDK stays mistapi 0.64.1 (`requirements.txt` line 129). The constraint in `pyproject.toml` line 29 allows `>=0.64.1,<0.65`.
- **A-2**: The installed `requests` version is 2.34.2 (`requirements.txt` line 221).
- **A-3**: The startup code publishes `API_REQUEST_TIMEOUT` before the first login (`main_entrypoint.py` lines 181 and 284 to 286).
- **A-4**: Tests run without network access and without any Mist credential.
- **A-5**: The default of 120 seconds suits interactive login, as the comment in `MistHelper.py` lines 2518 to 2520 states.

## Out of Scope

- Retry behavior for interactive login. The change keeps one attempt for each request.
- The token path in `src/foundation/support/refactors/initialize_mist_session.py`. Open PR #4208 changes that file, and its behavior stays unchanged.
- The environment template `deploy/.env.example`. Open PR #4208 changes that file. A follow-up adds the variable after that PR merges.
- The `configure_session_timeout` entry point in `MistHelper.py`. It stays a no-op until a separate change removes it.
- Upgrades of mistapi beyond the 0.64 line.
- Login paths that do not use `LoginOrchestrator`.

## Clarifications

- **C-1**. Question: Does PR #4830 close the defect? Answer: Partly. PR #4830 removes the import, the dead helper, and its call. Its body says "Refs #4827", so the issue stays open for the timeout contract (RC-01, RC-07, RC-08).
- **C-2**. Question: Should a module named `session_timeout` exist? Answer: No. Decision D-1 in `design/research.md` keeps it absent.
- **C-3**. Question: Does interactive login call the token configurator today? Answer: No. The interactive initializer builds only the orchestrator (RC-13, RC-14). The configurator runs only on the token path (RC-12).
- **C-4**. Question: Does the SDK set a request timeout? Answer: No. The SDK request wrapper sends no timeout (RC-61). One direct call sets 30 seconds (RC-59).
- **C-5**. Question: Does a record for issue 4827 already exist? Answer: No. No path under `specs\` contains 4827 (RC-84), and the route leaf is absent (RC-83).
- **C-6**. Question: Which value sets the wait? Answer: `API_REQUEST_TIMEOUT`, read at startup with the default of 120 (RC-19, RC-15).
- **C-7**. Question: Does the change need a changelog fragment? Answer: Yes. Operators see a new bounded wait, so the internal-only exemption does not apply (RC-28).
