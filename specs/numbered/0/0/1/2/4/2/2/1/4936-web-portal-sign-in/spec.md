# Feature Specification: Browser sign-in with 2FA for the web portal

**Feature Branch**: `feat/4936-web-portal-sign-in`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4936, "Web portal: add a browser sign-in with two-factor support to the operations portal"

**Record**: `specs\numbered\0\0\1\2\4\2\2\1\4936-web-portal-sign-in`

## Terms

Each term has one meaning in this record.

- **Web portal**: The Flask application on port 8055, served by `wsgi.py`. The issue calls it the operations portal.
- **Upgrade capture portal**: The separate Flask application on port 8056.
- **Browser sign-in**: The password step in the browser. It takes the work email, the password, and the cloud.
- **2FA step**: The second page. It takes the 2FA code.
- **Pending sign-in**: The half-finished sign-in that waits for the 2FA code.
- **Process session**: The one signed-in Mist session that the web portal uses for every route and menu operation.
- **SDK session**: One `mistapi.APISession` object.
- **Session lifetime**: The minutes that the `session_expiry` field of the admin profile gives.

## Safety notes

- Warning: A log record that holds a password gives every reader of the log that account password.
- Warning: A session that serves a different account changes the scope of every menu operation.
- Caution: A wrong `session_expiry` value ends the session early or late. The portal then refuses the next request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use the browser sign-in with a password and a 2FA code (Priority: P1)

A NOC operator opens the web portal in a browser. The operator submits the work email, the password, and the cloud. When the account requires a 2FA code, the portal shows the 2FA step. After the code is accepted, the process session serves the dashboard, the maps, and the operations for that account.

**Why this priority**: The issue reports that a 2FA account cannot run menu 309 from a container. The terminal path cannot reach a container.

**Independent Test**: Start the web portal with no token and no `.env` credentials. Submit the password and the code with a fake SDK that requires a 2FA code. The dashboard then names the signed-in account.

**Acceptance Scenarios**:

1. **Given** the web portal starts with no token, **When** the operator opens `/auth/signin`, **Then** the page shows the email, password, and cloud choice.
2. **Given** the account requires a 2FA code, **When** the operator submits the password, **Then** the portal shows the 2FA step and sets no process session.
3. **Given** a pending sign-in, **When** the operator submits the current 2FA code, **Then** the portal sets the process session and opens the next page.
4. **Given** a signed-in process session, **When** the operator previews the Multi Site hardware action, **Then** the preview shows the credential, scope, and organization count lines.

### User Story 2 - Read one plain sentence for each failure (Priority: P1)

A refused password, a wrong 2FA code, and an expired 2FA step each show one plain sentence. The sentence names the next action.

**Why this priority**: The operator cannot act on a failure with no reason. Issue #3087 records the same problem for the CSRF error.

**Independent Test**: Use three fake SDK cases. One refuses the password, one refuses the code, and one lets the pending sign-in expire. Each case shows one sentence from the sentence table.

**Acceptance Scenarios**:

1. **Given** the cloud refuses the password, **When** the operator submits the form, **Then** the page shows the `bad_credentials` sentence and keeps no pending sign-in.
2. **Given** a pending sign-in, **When** the operator submits a wrong code, **Then** the page shows the `bad_two_factor_code` sentence and keeps the pending sign-in open.
3. **Given** a pending sign-in older than 300 seconds, **When** the operator submits a code, **Then** the page shows the `two_factor_expired` sentence.
4. **Given** a session whose lifetime ended, **When** the operator opens a page, **Then** the page shows the `session_expired` sentence and a sign-in link.

### User Story 3 - End the session and keep the account lifetime (Priority: P2)

The operator submits the sign-out form. The process session ends, and the pending sign-in of that browser ends too. The session lifetime comes from the account profile.

**Independent Test**: Run a sign-in with a fake SDK, submit the sign-out form, and check that the process session and the pending sign-in are empty. Repeat with a fake clock and a `session_expiry` value of 10.

**Acceptance Scenarios**:

1. **Given** a signed-in session, **When** the operator submits the sign-out form, **Then** the process session is empty and the browser opens the sign-in form.
2. **Given** a `session_expiry` value of 1440, **When** the sign-in completes, **Then** the session lifetime is 1440 minutes from the sign-in time.
3. **Given** no `session_expiry` value, **When** the sign-in completes, **Then** the portal logs one warning and sets no local timer.

### User Story 4 - Keep the token and terminal paths (Priority: P2)

An operator with `MIST_APITOKEN` in `.env` or in the container environment starts the web portal as before. The startup session serves the portal with no sign-in. The terminal `--login` path keeps its prompts.

**Independent Test**: Start the web portal with a fake token in the environment, then check that the process session exists. The sign-in form stays available. Run the existing CLI login tests.

**Acceptance Scenarios**:

1. **Given** a token in the environment, **When** the web portal starts, **Then** the process session is set at startup and the sign-in form remains available.
2. **Given** `python MistHelper.py --login --web-portal`, **When** the terminal prompts appear, **Then** the terminal login path runs as before.

### User Story 5 - Read the updated documents (Priority: P3)

The web portal page, the operator guide, the CLI reference, the API login pages, and the changelog describe the browser sign-in. None of them says that the page has no sign-in form or that issue #4936 tracks the sign-in.

**Independent Test**: Run the documentation test module and the STE gate on the changed pages.

**Acceptance Scenarios**:

1. **Given** the operator guide, **When** the reader opens "Sign in for an MSP run", **Then** the table has a row for the browser sign-in.
2. **Given** the API login pages, **When** the reader checks the call sites, **Then** the pages name the browser sign-in as a third call site.

## Edge Cases

- The password is refused. The portal keeps no pending sign-in and keeps no password.
- The 2FA code is wrong. The pending sign-in stays open until its 300-second window ends.
- A 2FA code arrives with no pending sign-in. The portal shows the `two_factor_expired` sentence.
- The cloud answers HTTP 429 to a login call. The portal shows the `rate_limited` sentence and sends no retry.
- The network fails during a login call. The portal shows the `network_fault` sentence and keeps no pending sign-in.
- The cloud host is not in the catalog. The portal uses the default host and logs one warning.
- The account has no organization privilege and no `MIST_ORG_ID`. The portal sets the process session and shows the `no_organization` sentence on the next page.
- A browser submits a sign-in while an operation runs. The portal refuses the change with the `run_active` sentence.
- A second browser signs in. The second sign-in replaces the process session, and the first browser shows the new account name on its next page.
- The `session_expiry` value is outside 10 to 20160. The portal treats the value as absent.
- A browser posts with no CSRF token. The existing CSRF protection refuses the request.
- A client outside `PORTAL_ALLOWED_IPS` requests a sign-in page. The existing allowlist answers 403.
- A proxy caches the sign-in page. The portal sends `Cache-Control: no-store`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The web portal MUST serve a sign-in form at `GET /auth/signin`. It MUST accept the form at `POST /auth/signin`.
- **FR-002**: The sign-in form MUST accept a work email, a password, and one cloud from the existing catalog.
- **FR-003**: The web portal MUST serve the 2FA step at `GET /auth/twofactor`. It MUST accept a code at `POST /auth/twofactor` only for an open pending sign-in.
- **FR-004**: The password and the 2FA code MUST NOT be stored, shown, logged, or written to a cookie, a file, or a response.
- **FR-005**: The browser flow MUST call `mistapi.api.v1.login.login.login` and `mistapi.api.v1.login.two_factor.twoFactor` on one SDK session. It MUST NOT call `APISession.login()` or `login_with_return()`.
- **FR-006**: After each accepted step, the portal MUST call `getSelf`. It MUST accept the sign-in only when `two_factor_required` is false.
- **FR-007**: A successful sign-in MUST replace the process session in the app configuration and in `MainEntrypoint.context` under one lock.
- **FR-008**: Sign-out MUST clear the process session and the pending sign-in of the browser. It MUST then open the sign-in form.
- **FR-009**: The session lifetime MUST come from `session_expiry`, which accepts 10 to 20160 minutes. When the value is absent or outside this range, the portal MUST set no timer and MUST log one warning.
- **FR-010**: A pending sign-in MUST end 300 seconds after the password step.
- **FR-011**: A Mist HTTP 429 answer MUST produce the `rate_limited` sentence. The login SDK session MUST set the retry count to 0.
- **FR-012**: A wrong 2FA code MUST keep the pending sign-in open until the window ends. The portal MUST NOT count wrong codes.
- **FR-013**: Each failure state MUST show one sentence from the sentence table below. Each sentence MUST appear in the matching test.
- **FR-014**: Each POST MUST use the existing CSRF protection. Each sign-in page MUST obey `PORTAL_ALLOWED_IPS`. Each sign-in page MUST send `Cache-Control: no-store`.
- **FR-015**: A web request MUST NOT call `input()` or `getpass()`.
- **FR-016**: The shared logic MUST live in `src/mist/access/auth/browser/`. The capture portal MUST import it and MUST NOT keep a copy.
- **FR-017**: Each SDK call MUST write one info record before it and one debug record after it. Each record MUST use ASCII text, the email digest, and no secret.
- **FR-018**: The organization after sign-in MUST come from `MIST_ORG_ID`. When that value is empty, the portal MUST use the first organization privilege of `getSelf`.
- **FR-019**: When the startup bootstrap fails, the web portal MUST start with no process session. The sign-in form MUST remain available.
- **FR-020**: The web portal page, the operator guide, the CLI reference, the API login pages, and a changelog fragment MUST describe the browser sign-in. The "#4936 tracks" sentences MUST be removed.
- **FR-021**: The upgrade capture portal MUST keep its behavior. Its contract tests MUST pass after the move.

### Failure sentences

| Code | Sentence |
| - | - |
| `bad_credentials` | The portal could not authenticate you. Check the email address and the password, then try again. |
| `bad_two_factor_code` | The portal could not accept that code. Type the current code from your authenticator application, then try again. |
| `two_factor_expired` | The 2FA step is no longer open. Start the sign-in again. |
| `session_expired` | Your Mist session expired. Start the sign-in again to run operations. |
| `rate_limited` | The Mist cloud refused more sign-in attempts for now. Wait a short time, then try again. |
| `network_fault` | The portal could not reach the Mist cloud. Check the network connection, then try again. |
| `no_organization` | The account has no organization for this portal. Set MIST_ORG_ID in the environment, then start the portal again. |
| `run_active` | An operation is running. Wait for it to finish, then try again. |

### Mist Cloud Transport Requirements

- **mistapi functions used**:
  - `mistapi.APISession` builds the SDK session with `email`, `password`, `host`, `console_log_level=20`, and `show_cli_notif=False`. This is a constructor, not a REST call.
  - `mistapi.api.v1.login.login.login` sends POST `/api/v1/login`.
  - `mistapi.api.v1.login.two_factor.twoFactor` sends POST `/api/v1/login/two_factor`.
  - `mistapi.api.v1.self.self.getSelf` sends GET `/api/v1/self` after each accepted step, and for the lifetime and the organization.
- **Owned WebSocket transport**: None. The feature adds no transport.
- **Contract-test evidence**:
  - SDK insufficiency: a test calls `APISession.login()` with a fake HTTP layer that reports `two_factor_required`. The test patches `input` and proves that the SDK asks for a code (`__api_session.py:1137`).
  - SDK authentication: a test checks that the token list is empty and that the retry count is 0 before the first call.
  - SDK endpoint parity: a test checks that the two URI paths equal `/api/v1/login` and `/api/v1/login/two_factor` (R-58).
  - Failure safety: tests cover HTTP 400, 401, 429, and a connection fault.
  - Secret redaction: tests scan the log records and the response bodies for the password and the code.

### Key Entities

- **PendingSignIn**: The half-finished sign-in of one browser. It holds the browser identifier, the email digest, the host, the start time, and the SDK session object. It holds no password and no code.
- **ProcessSession**: The one signed-in SDK session. It holds the email digest, the host, the organization identifier, the start time, the expiry time or none, and the SDK session object.
- **SignInMessage**: One failure sentence with its code from the table.
- **SessionLifetime**: Minutes from `session_expiry`, or the state unknown.
- **CloudChoice**: One label and one host from the catalog.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the fake-SDK journey test, an operator with a 2FA account reaches the dashboard through the browser sign-in.
- **SC-002**: For a fake MSP profile, the hardware preview shows the credential, scope, and organization count lines.
- **SC-003**: No log record, response body, cookie, or file in the sign-in tests contains the password or the 2FA code.
- **SC-004**: Each failure state in the tests shows exactly one sentence from the failure table.
- **SC-005**: The capture portal contract tests pass after the move. The count of passed tests equals the count before the move.
- **SC-006**: The changed documents contain no sentence that says the page has no sign-in form or that issue #4936 tracks the sign-in.

## Assumptions

- The fake SDK in the tests follows the documented OpenAPI behavior (R-58, R-61).
- One operator uses one web portal process at a time.
- The web portal process can serve requests on several threads, so the holder writes use a lock.
- The `session_expiry` field can be absent (U-3).
- The owner checks the live 2FA path in issue #4925 (U-1).

## Clarifications

- **Q1. Does the web portal need its own browser sign-in?** Answer: Yes. The terminal path cannot serve a container, and the issue asks for a 2FA sign-in in the browser (R-34, R-35).
- **Q2. Which session scope applies?** Answer: One process session (D-3). The issue proposal asks for one session for each browser. Every menu operation reads one shared session (R-38), so the record keeps one process session. The choice sets the account for every visitor, so it is a credential policy. HUMAN-DECISION-REQUIRED.
- **Q3. Which 2FA mechanism applies?** Answer: Two public SDK calls on one SDK session. The record keeps no password between steps (D-4).
- **Q4. What limits wrong codes?** Answer: The 300-second pending window and the Mist 429 response. The portal keeps no counter (D-6, U-2).
- **Q5. Where does the lifetime come from?** Answer: The admin `session_expiry` field (D-5). The organization field of the same name is a different field.
- **Q6. Does the password need its own credential policy?** Answer: Yes. The record accepts the password on every allowed address (D-1). HUMAN-DECISION-REQUIRED.
- **Q7. Does the capture 2FA defect block this change?** Answer: No. The defect gets a separate issue (D-15).

## Out of Scope

- Per-browser Mist sessions. D-3 records the alternative.
- Repair of the capture portal 2FA retry. D-15 records the decision.
- SSO, OAuth, and Mist provider login flows (R-58 describes them, and this record does not use them).
- Persistent sessions across a process restart.
- New environment variables.
- Changes to the terminal login path and its prompts in `login_orchestrator.py`.
- Changes to menu operations, operation categories, or the hardware inventory logic.
- Live MSP validation (issue #4925).

## Human decisions

- HUMAN-DECISION-REQUIRED D-1: Confirm the credential policy for browser password entry on every allowed address. The recommended option accepts it.
- HUMAN-DECISION-REQUIRED D-3: Confirm one process session instead of one session for each browser. The recommended option keeps one process session.
