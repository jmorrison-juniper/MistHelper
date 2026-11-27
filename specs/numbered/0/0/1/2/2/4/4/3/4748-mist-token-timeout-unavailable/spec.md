# Feature Specification: Report a Mist transport fault as an unavailable Mist API

**Feature Branch**: `fix/4748-mist-token-timeout-unavailable`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4748, "Runtime: a Mist token timeout can be reported as an invalid token". Related issues: #4749, #1858, #1884.

## Clarifications

### Session 2026-11-26

- Q: Does HTTP 429 from the privilege lookup map to an invalid token or to an unavailable Mist API? A: It maps to an unavailable Mist API (HTTP 503). A throttle is a transient service fault, not a rejected token.
- Q: Does a 2xx response without an identity object map to an invalid token? A: It maps to an unavailable Mist API (HTTP 503). Mist answered with success, so the fault belongs to the service.
- Q: May the process environment token validate a login? A: No. A login validates only the supplied token. The validation session ignores the process environment.
- Q: Does one pull request cover issues #4748 and #4749? A: Yes. The issue comments ask for one file owner and one pull request for the shared authentication files.
- Q: Does a privilege lookup wait without a limit? A: No. Each request ends within 30 seconds. The SDK used the same bound for its token validation request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A transport fault reports an unavailable Mist API (Priority: P1)

An operator starts a login with a valid token. The privilege lookup reaches a read timeout. The login route answers HTTP 503 with the existing "try the login again" message. The operator does not see an invalid-token message.

**Why this priority**: This is the reported defect. A transient fault must not tell the operator that the token is wrong.

**Independent Test**: Mock the privilege lookup request to raise `requests.exceptions.ReadTimeout`. Call `AuthService().validate_token` with a fake token. The call raises `MistApiUnavailableError`.

**Acceptance Scenarios**:

1. **Given** a read timeout during a privilege lookup, **When** the login route validates the token, **Then** it answers HTTP 503, not HTTP 401.
2. **Given** a privilege lookup that fails with a connection error, **When** the service validates the token, **Then** it raises `MistApiUnavailableError`.
3. **Given** a privilege lookup that returns HTTP 429, **When** the service validates the token, **Then** it raises `MistApiUnavailableError`.

---

### User Story 2 - A rejected token still reports an invalid token (Priority: P1)

An operator enters a token that Mist rejects. The login route answers HTTP 401 with the invalid-token message. The repair does not hide this result behind HTTP 503.

**Why this priority**: The repair changes the same code path. A rejected token must keep its own result.

**Independent Test**: Mock the privilege lookup request to return HTTP 401. Call `AuthService().validate_token`. The call returns empty privileges. The login route answers HTTP 401.

**Acceptance Scenarios**:

1. **Given** Mist answers HTTP 401 for the supplied token, **When** the service validates the token, **Then** it returns empty privileges.
2. **Given** Mist answers HTTP 403 for the supplied token, **When** the service validates the token, **Then** it returns empty privileges.
3. **Given** Mist answers HTTP 200 with an identity object, **When** the service validates the token, **Then** it returns the identity and its privileges.

---

### User Story 3 - The process environment never answers for a login (Priority: P2)

The server process holds a token and a host in its environment. A login with a different supplied token never uses the environment token or the environment host. Each privilege lookup goes to `https://api.mist.com/api/v1/self` with the supplied token only.

**Why this priority**: A login that uses another token can return the privileges of that other token. This defect confuses credentials.

**Independent Test**: Set fake `MIST_APITOKEN` and `MIST_HOST` values with `monkeypatch`. Mock the privilege lookup request and record each call. Every call uses the supplied token and the host `api.mist.com`.

**Acceptance Scenarios**:

1. **Given** a fake environment token, **When** a login validates a different supplied token, **Then** no request carries the environment token.
2. **Given** a fake environment host, **When** a login validates a token, **Then** the request URL is `https://api.mist.com/api/v1/self`.

---

### User Story 4 - Malformed input and logs stay safe (Priority: P2)

A malformed token never reaches the network. No log record and no error message shows the token value, the Authorization header, or a response body.

**Why this priority**: Input checks and redaction protect the credential. They do not change the operator result for valid tokens.

**Independent Test**: Call the service with an empty token, a token that contains a space, and a token that contains a comma. Assert that no request runs. Capture the log records of an unavailable result and an invalid result. Assert that the token value is absent.

**Acceptance Scenarios**:

1. **Given** a token that contains a comma, **When** the service validates the token, **Then** it returns empty privileges and sends no request.
2. **Given** an unavailable result, **When** the log records are read, **Then** no record contains the token value.

### Edge Cases

- A read timeout during the privilege lookup returns HTTP 503. The base class `requests.exceptions.Timeout` follows the same path.
- A connect timeout returns HTTP 503, because `ConnectTimeout` subclasses `ConnectionError`.
- A proxy error returns HTTP 503.
- An HTTP 429 response that remains after the SDK retries returns HTTP 503.
- An HTTP 200 response with an empty body returns HTTP 503.
- A token with a non-ASCII character returns HTTP 401 without a request.
- A process environment `MIST_HOST` that names another cloud host does not change the request host.
- A process environment `MIST_APITOKEN` that differs from the supplied token does not change the Authorization header.
- A privilege lookup request that stalls returns HTTP 503 at the 30-second limit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A transport fault during the privilege lookup MUST raise `MistApiUnavailableError`, never an invalid token.
- **FR-002**: A response that has no HTTP status code MUST raise `MistApiUnavailableError`.
- **FR-003**: HTTP 429 from the privilege lookup MUST raise `MistApiUnavailableError`.
- **FR-004**: HTTP 1xx, 3xx, and 5xx responses MUST raise `MistApiUnavailableError`.
- **FR-005**: HTTP 2xx responses without an identity object MUST raise `MistApiUnavailableError`.
- **FR-006**: HTTP 401 and other HTTP 4xx responses, except 429, MUST return empty privileges.
- **FR-007**: HTTP 2xx responses with an identity object MUST return the privileges that the current parser returns.
- **FR-008**: The validation session MUST NOT read `MIST_HOST`, `MIST_APITOKEN`, `MIST_USER`, or `MIST_PASSWORD` from the process environment.
- **FR-009**: The validation session MUST send each privilege lookup to `https://api.mist.com/api/v1/self`, with the supplied token as the only Authorization value.
- **FR-010**: A token that is empty or contains a space, comma, control character, or non-ASCII character MUST return empty privileges without a request.
- **FR-011**: Each privilege lookup request MUST end within 30 seconds.
- **FR-012**: No log record, exception message, or result MUST contain the token value, the Authorization header, or a response body.
- **FR-013**: The privilege lookup MUST call the mistapi method `getSelf` through the registry entry `self_identity`.
- **FR-014**: The registry entry `self_identity` MUST return one identity object as one row. Other list entities MUST keep the list-only rule.
- **FR-015**: An `ApiResult` with no status code MUST report failure and carry no data rows.
- **FR-016**: The login route and the middleware MUST keep their HTTP 401 and HTTP 503 mapping. No new client status code MUST appear.
- **FR-017**: Automated tests MUST use mocked HTTP only. No test MUST call the live Mist cloud or use a production credential.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- **Mistapi method**: `mistapi.api.v1.self.self.getSelf`, which sends GET `/api/v1/self`. The method runs through the registry entry `self_identity` in `mist-ops-platform/src/shared/mist/types.py`.
- **Direct HTTP**: No direct HTTP call is added. The SDK method performs the request.
- **Owned WebSocket transport**: Not applicable: the feature owns no WebSocket transport.
- **SDK insufficiency**: Contract tests `test_sdk_read_timeout_drops_token_contract` and `test_sdk_rejected_token_raises_value_error_contract` prove that the SDK token check cannot classify a fault.
- **SDK authentication**: Contract test `test_validation_session_sends_only_supplied_token_to_self_endpoint` proves the Authorization value.
- **SDK endpoint parity**: The same test proves the URL `https://api.mist.com/api/v1/self`.
- **Failure safety**: Tests `test_fetch_self_read_timeout_reports_unavailable`, `test_fetch_self_connection_error_reports_unavailable`, and `test_fetch_self_http_429_reports_unavailable` prove the failure mapping.
- **Secret redaction**: Test `test_log_records_never_contain_token` proves the redaction.

### Key Entities *(include if feature involves data)*

- **Supplied token**: The credential that the operator sends to the login route, or the token in a session store entry. It is secret. It never appears in a log or a result.
- **Validation session**: The SDK session that holds one supplied token and ignores the process environment. It serves one privilege lookup.
- **Privilege lookup outcome**: One of three results. It is an identity, an invalid token, or an unavailable Mist API.
- **Identity object**: The JSON object that GET `/api/v1/self` returns. It holds the email, the name, and the privileges.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 20 planned test functions pass. The plan has 15 new functions and 5 updated functions.
- **SC-002**: One run shows the three issue results. A read timeout gives unavailable. A connection error gives unavailable. HTTP 401 gives empty privileges.
- **SC-003**: The environment isolation test records zero requests that carry the environment token.
- **SC-004**: The ops platform pytest run collects at least 390 tests and reports coverage of at least 56 percent.
- **SC-005**: The ops platform Ruff correctness command reports zero findings.
- **SC-006**: The remote check count in the STATUS file, the research table, and the summary are equal.
- **SC-007**: Each changed Markdown file scores 80 or above in the STE linter.

## Assumptions

- The pinned SDK is mistapi 0.64.1, as `mist-ops-platform/requirements.txt` states.
- A valid token gets an `Admin` object from GET `/api/v1/self`, as the OpenAPI file defines.
- The login route keeps its request body with the `method` and `token` fields.
- No operator needs the process environment token to authenticate a login.
- The change needs no new dependency and no new configuration variable.

## Out of Scope

- Worker session creation in `mist-ops-platform/src/shared/mist/session.py`. A separate issue tracks it.
- Retry delay for HTTP 429. The SDK and the endpoint service both retry. A separate issue tracks it.
- Changes to the Redis privilege cache, the session store, or the login response body.
- Changes to the operator portal text.
- A mistapi upgrade or a fork of the SDK.
