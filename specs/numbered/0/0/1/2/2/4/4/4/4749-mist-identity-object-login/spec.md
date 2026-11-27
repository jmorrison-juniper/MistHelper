# Feature Specification: Mist Identity Object Sign-In

**Feature Branch**: `fix/4749-mist-identity-object-login`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4749, "Runtime: a valid Mist identity object is discarded during login". The issue names `mist-ops-platform/src/shared/services/auth.py` and `mist-ops-platform/src/shared/mist/endpoints.py`.

## Clarifications

### Session 2026-11-26

- Q: Why does a valid token fail at sign-in? → A: `list_all_entities` drops the dictionary body of `GET /api/v1/self`. `AuthService` then reads an empty list and returns empty privileges. The sign-in path reports that result as an invalid token. Evidence: endpoints.py line 316 and auth.py line 123 on `main`.
- Q: Did a change cause the drop? → A: Probably. Pull request #1896 changed `endpoints.py` and the status test that pins the drop. The pull request diff was not read, so the cause stays unverified (research Unverified list, item 11). The drop also removes the identity object.
- Q: Should the fix change the list rule for every endpoint? → A: No. Only the registry entry `self_identity` gets the object rule. Every other list endpoint keeps the rule from issue #1884.
- Q: Must the identity fix ship with the token check? → A: Yes. Warning: an identity fix alone lets a rejected token sign in with the identity of the active SDK token.
- Q: Does this change share work with issue #4748? → A: Both issues change `_fetch_self` in auth.py. Issue #4748 changes the 503 mapping for a timeout. Each issue gets its own pull request. Issue #4748 lands first when its repair lands. Otherwise, this change lands alone.
- Q: Where do the new tests go? → A: In `mist-ops-platform/tests/contract/`. The folder holds two tracked children now. The change adds two, which keeps it at four. No existing test module changes.
- Q: Does sign-in need a new Mist call? → A: No. A validation keeps one `GET /api/v1/self` call.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign in with a valid token (Priority: P1)

A NOC engineer signs in with a valid Mist token. The ops platform reads the identity object from `GET /api/v1/self`. The engineer sees the privileges of that identity.

**Why this priority**: Caution: a valid token that fails at sign-in blocks every operator. This is the reported defect.

**Independent Test**: Mock `mistapi.api.v1.self.self.getSelf` to return HTTP 200 with an identity object. Call `MistEndpointService.list_all_entities` with `self_identity`. The result holds one identity record.

**Acceptance Scenarios**:

1. **Given** a successful `/self` identity response, **When** the service lists `self_identity`, **Then** the result holds that object as one record.
2. **Given** a successful `/self` response for the supplied token, **When** `AuthService.validate_token` runs, **Then** it returns the privileges of that identity.
3. **Given** a successful `/self` response with an empty object, **When** the service lists `self_identity`, **Then** the result holds no record.

### User Story 2 - Refuse a token that the SDK session does not use (Priority: P1)

A caller presents a token. The SDK session can hold a different active token from the process environment. The ops platform must not read the identity of that other token.

**Why this priority**: Warning: without this rule, User Story 1 lets a rejected token return another identity.

**Independent Test**: Mock the SDK session with active token `ENV-TOKEN`. Mock `/self` with HTTP 200 for that session. Call `validate_token("TOKEN")`. The result holds empty privileges.

**Acceptance Scenarios**:

1. **Given** the active token is not a supplied token, **When** `validate_token` runs, **Then** it returns empty privileges.
2. **Given** the SDK session holds no active token, **When** `validate_token` runs, **Then** it returns empty privileges.
3. **Given** comma-separated supplied tokens with one active token, **When** `validate_token` runs, **Then** it returns that identity.

### User Story 3 - Keep list endpoints unchanged (Priority: P2)

A maintainer lists any other registry entity. The rule from issue #1884 still applies. A Mist error body never becomes a data record.

**Why this priority**: The repair must not reopen issue #1884.

**Independent Test**: List `org_site_list` with a dictionary body. The result holds no record.

**Acceptance Scenarios**:

1. **Given** a list endpoint with a dictionary body, **When** the service lists it, **Then** the result holds no record.
2. **Given** an object endpoint returns 4xx or 5xx, **When** the service lists it, **Then** no record is held.

### Edge Cases

- A 2xx response with a list body keeps every record in the list.
- A 2xx response with an empty object yields no record. Sign-in then returns HTTP 401.
- A 4xx response returns empty privileges. A 5xx response or a transport fault raises `MistApiUnavailableError`.
- A 429 response uses the existing retry loop without change.
- An object endpoint never follows a `next` cursor, even when the body or a header sets one.

Caution: until this fix ships, a valid operator sees "Invalid API token" at sign-in.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST return the identity object of a successful `GET /api/v1/self` response as one identity record.
- **FR-002**: The system MUST NOT produce an identity record from a non-2xx `/self` response.
- **FR-003**: The system MUST keep every record of a successful list-shaped `/self` body.
- **FR-004**: The system MUST keep the list rule for every registry entry without the object flag, including the drop of dictionary bodies.
- **FR-005**: The system MUST make one SDK call for an object endpoint and MUST NOT follow a pagination cursor.
- **FR-006**: The system MUST return the identity privileges for a valid supplied token.
- **FR-007**: The system MUST return empty privileges, and MUST NOT parse the identity, when the active SDK token is not a supplied token.
- **FR-008**: The system MUST return empty privileges for a 4xx `/self` response and MUST raise `MistApiUnavailableError` for a 5xx response or a transport fault.
- **FR-009**: Each changed line MUST carry an inline comment, and each changed action MUST carry an info line before and a debug line after.
- **FR-010**: No new log line MUST hold a token value or an identity body.
- **FR-011**: The change MUST call the mistapi method `getSelf` through the registry and MUST NOT add a direct HTTP request.
- **FR-012**: The change MUST add one changelog fragment under `changelog.d/` and MUST NOT edit `CHANGELOG.md`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature uses one mistapi REST method, `mistapi.api.v1.self.self.getSelf`. The SDK module sends the request `GET /api/v1/self` (research row R80).
- The feature adds no owned WebSocket transport.
- Contract-test evidence for SDK insufficiency is not required. The defect sits in the list layer of this repository. The OpenAPI file defines the object response (rows R33 and R35).
- SDK authentication: the active-token check reads the attributes `_apitoken` and `_apitoken_index`. The existing SDK contract test pins both names (row R31).
- Endpoint parity: the registry entry `self_identity` drives every call. Tests TC-01 to TC-07 prove the object path.
- Failure safety: tests TG-05 and TG-06 cover the 4xx and 5xx outcomes at sign-in.
- Secret redaction: FR-010 forbids a token value or an identity body in a new log line.

### Key Entities *(include if feature involves data)*

- **Identity object**: The Mist `admin` object that `GET /api/v1/self` returns with HTTP 200. The record reads the email, the names, and the privileges (rows R33 and R35).
- **Object endpoint**: A registry entry with `object_response` set to true. It makes one call and reads one object (decision D-1).
- **Active SDK token**: The token at `_apitoken_index` in the list `_apitoken` of the SDK session (row R83).
- **Supplied token**: The token value that a caller passes to `validate_token`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 13 new contract tests pass after the change. Each new test module fails before the change, which proves that the tests can fail.
- **SC-002**: The four existing test modules named in plan.md pass with no edit.
- **SC-003**: The Ops platform gate reports at least 390 collected tests and coverage of at least 56 percent.
- **SC-004**: The test-quality gate reports zero new findings against the baseline.
- **SC-005**: Every required remote check passes on the pull request before auto-merge.

## Assumptions

- The pinned SDK is mistapi 0.64.1 (row R87). The brief pins `mistapi>=0.64.0,<0.65`.
- The OpenAPI files define the response contract. This record makes no live Mist call.
- The tests run offline with patched SDK methods. This record does not execute them.
- No operator document describes the sign-in result. The research sources list the documents that were checked.
- A token that Mist rejects returns a 4xx status for `GET /api/v1/self`. The existing tests assume this behavior.

## Out of Scope

- The timeout mapping of issue #4748.
- Isolation of environment variables in the SDK session. A follow-up issue owns it.
- Negative caching of empty privileges on the session record. A follow-up issue owns it.
- The folder splits named in the complexity tracking table of plan.md.
- The root CLI login, the menus, and the upgrade capture portal.
