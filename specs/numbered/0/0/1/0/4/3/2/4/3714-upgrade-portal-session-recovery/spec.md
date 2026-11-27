# Feature Specification: Upgrade Portal Session Recovery

**Feature Branch**: `fix/3714-upgrade-portal-session-recovery`

**Created**: 2026-11-26

**Status**: Draft. Implementation waits for approval of decisions D-1 and D-2 (HUMAN-DECISION-REQUIRED in design/research.md).

**Input**: Issue #3714, "Upgrade portal: a worker restart clears authenticated cloud sessions."

## Problem Statement

The upgrade capture portal stores each authenticated operator session in one process-local registry (`src/interfaces/portals/upgrade_portal/runtime/identity.py:516`). A worker replacement starts a new process with an empty registry. The browser still holds a valid signed cookie. The next protected request returns `401 not_authenticated`.

The stable `CAPTURE_SECRET_KEY` keeps the cookie valid. The key does not keep the cloud session. This spec treats the defect as an availability defect. It does not treat the stale cookie as an authentication bypass.

This spec uses "worker replacement" for every event that starts a new worker process. The issue calls this event a worker restart.

## Terms

- **Registry**: The process-local `SESSION_REGISTRY` (`identity.py:575`).
- **Store**: The shared Redis store that holds store records for environment token sessions.
- **Owner key**: The value `email digest:browser identifier` (`identity.py:457`). The signed cookie holds it.
- **Cloud session**: The `mistapi.APISession` object that serves one operator.
- **Credential mode**: One of `environment_token`, `browser_token`, or `provider_login` (`identity.py:355`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recover an environment token session after worker replacement (Priority: P1)

An operator who authenticated with the `environment_token` mode keeps the portal session after a worker replacement. The operator does not enter the token again.

**Why this priority**: This mode needs no stored credential. The portal rebuilds the cloud session from the process environment. The change fixes the defect for this mode without storing a credential.

**Independent Test**: Authenticate through application A. Create application B with the same signing key and the same store. Send the original cookie to application B. Application B returns the protected page with status 200.

**Acceptance Scenarios**:

1. **Given** an authenticated environment token session and its store record, **When** a replacement application receives the original cookie, **Then** the protected request succeeds.
2. **Given** a replacement application and no store record, **When** the original cookie arrives, **Then** the request returns `401 not_authenticated`.

### User Story 2 - Refuse unrecoverable sessions and report store outages (Priority: P1)

Browser token and provider login sessions do not recover after a worker replacement. A store outage returns a distinct, safe error. No path creates a session without a verified store record.

**Why this priority**: The operator must know whether to authenticate again or to wait for the store. A wrong answer risks a false session or a lost upgrade view.

**Independent Test**: Replacement application requests for browser token and provider login cookies return `401`. A store read failure returns `503`.

**Acceptance Scenarios**:

1. **Given** a browser token or provider login session, **When** a worker replacement occurs, **Then** the operator must authenticate again.
2. **Given** a store outage during recovery, **When** a protected request arrives, **Then** the response has status 503 and code `session_store_unavailable`. No local session is created.
3. **Given** a store outage during sign-in, **When** the operator authenticates with the environment token mode, **Then** the sign-in fails. No session is created.

### User Story 3 - End each session completely (Priority: P2)

Sign-out and expiry remove the store record and the local session. An idle lifetime and an absolute lifetime apply to each session.

**Why this priority**: A stale record can restore access after the operator leaves the workstation.

**Independent Test**: Unit tests with an injected clock and a fake store prove each deletion and expiry path.

**Acceptance Scenarios**:

1. **Given** a recovered session, **When** the operator performs sign-out, **Then** the store record and the local record are removed.
2. **Given** a store record past its idle deadline, **When** a protected request arrives after a worker replacement, **Then** the request returns `401`. The record is removed.
3. **Given** a store record past its absolute deadline, **When** a protected request arrives, **Then** the request returns `401`. The record is removed.

### User Story 4 - Keep recovery data and logs free of credentials (Priority: P2)

The store holds no credential value in plaintext. Logs, responses, cookies, and store payloads hold no synthetic credential value in the contract tests.

**Why this priority**: The portal serves production firmware upgrades. A credential in a log file persists for a long time.

**Independent Test**: A contract test authenticates with synthetic token values. The test searches all outputs for those values.

**Acceptance Scenarios**:

1. **Given** a store record, **When** an administrator reads the stored value, **Then** the value is an encrypted token. No plaintext field holds a credential.
2. **Given** a sign-in with a synthetic token, **When** the test reads logs, responses, cookies, and the store payload, **Then** no synthetic token value appears.

### Edge Cases

- The token name that the cloud returns differs from the stored token name. The portal deletes the record and returns `401 not_authenticated`.
- The token variable is empty during recovery. The portal deletes the record and returns `401 not_authenticated`.
- The cloud login fails during recovery. The portal deletes the record and returns `401 not_authenticated`. The operator authenticates again.
- The encryption key changed and no previous key exists. The record cannot decrypt. The portal deletes the record and returns `401 not_authenticated`.
- A previous encryption key exists. The portal decrypts the record. The next idle refresh writes the record with the active key.
- The idle refresh write fails. The local session continues. The stored idle deadline remains earlier than the local deadline. A later recovery expires sooner. This failure is conservative.
- Two protected requests arrive during one recovery. The portal starts one cloud login for the owner key.
- Sign-out runs while the store is unavailable. The browser session clears. The record remains until its absolute deadline. The portal logs an error with the exception class name.
- A second sign-in from the same browser replaces the earlier registry record and the earlier store record.
- A worker replacement clears the selected sites. The operator selects the sites again. The organization pick stays in the signed session.

### Functional Requirements

- **FR-001**: The portal MUST write one store record for each successful environment token sign-in. The write MUST finish before the portal registers the session.
- **FR-002**: The store record MUST hold only the fields in `design/contracts/store-record.md`. It MUST hold no credential value.
- **FR-003**: The store key MUST derive from a SHA-256 digest of the owner key. The raw owner key MUST NOT appear in the key name.
- **FR-004**: The store MUST encrypt each record with a MultiFernet key set. The key set MUST accept one previous key during rotation.
- **FR-005**: The browser cookie MUST keep only the owner key. The feature MUST NOT add a cookie field.
- **FR-006**: When the registry has no record, the guard MUST read the store record for the owner key.
- **FR-007**: A recovered record MUST match the browser digest, the credential mode, and the token name that the cloud returns.
- **FR-008**: A missing, expired, undecryptable, or mismatched record MUST return `401 not_authenticated`. The portal MUST delete an existing record in each case.
- **FR-009**: Browser token and provider login sign-ins MUST NOT write a store record. Their sessions MUST NOT recover after a worker replacement.
- **FR-010**: A failed store write during sign-in MUST return `503 session_store_unavailable`. The portal MUST NOT register a local session.
- **FR-011**: A failed store read during recovery MUST return `503 session_store_unavailable`. The portal MUST NOT create a local session.
- **FR-012**: Sign-out MUST delete the store record and the local record. A failed delete MUST log an error. The browser session MUST still clear.
- **FR-013**: Each session MUST apply an absolute lifetime and an idle lifetime. The idle deadline MUST refresh at most once each 60 seconds.
- **FR-014**: Logs, responses, and store payloads MUST NOT contain a credential value, an encryption key, the browser identifier, or the raw owner key.
- **FR-015**: All 51 protected handlers MUST keep the `require_session` decorator. A test MUST count the decorated handlers.
- **FR-016**: The defect-asserting checks at `tests/unit/upgrade_portal/test_identity.py` lines 1505 to 1520 and line 1647 MUST change to recovery and refusal checks.
- **FR-017**: A protected page request without a valid session MUST keep the `303` redirect to `/auth/signin`.
- **FR-018**: The capture Gunicorn command MUST keep `--workers 1`. This feature MUST NOT change the worker count.
- **FR-019**: A container deployment MUST require `CAPTURE_SESSION_ENCRYPTION_KEY` at startup when the store is enabled. A local run MUST generate an ephemeral key and log only the variable name.
- **FR-020**: The compose service and `deploy/.env.example` MUST document each new variable. No file MUST contain a key value.
- **FR-021**: The operator guide MUST state the result of a worker replacement for each credential mode.
- **FR-022**: A container deployment MUST refuse to start with the compose default `REDIS_PASSWORD` when the store is enabled. This rule needs decision D-2 approval.
- **FR-023**: The feature MUST NOT edit `tests/contract/upgrade_portal/test_no_credential_leak.py` before issue #2708 completes the handoff of the file.
- **FR-024**: Recovery MUST validate the environment token through `APISession.login` and `mistapi.api.v1.self.self.getSelf`. A failed validation MUST delete the record.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature uses three mistapi calls. The constructor is `mistapi.APISession` (`.venv\Lib\site-packages\mistapi\__api_session.py:55`). The method is `APISession.login` (`__api_session.py:778`). The function is `mistapi.api.v1.self.self.getSelf` (`.venv\Lib\site-packages\mistapi\api\v1\self\self.py:17`).
- The feature sends no direct HTTP request to a Mist REST endpoint.
- SDK insufficiency: not applicable. The feature adds no owned WebSocket transport.
- SDK authentication: the existing builders keep the SDK authentication path. The feature reads no private SDK attribute.
- SDK endpoint parity: the feature calls `getSelf` for identity only. The Mist OpenAPI defines `/api/v1/self` at `documentation/mist-api-openapi31yaml.yaml:25460`.
- Failure safety: a failed login or a failed `getSelf` deletes the store record and returns `401`. Tests TP-18 and TP-19 cover this path.
- Secret redaction: test TP-22 covers logs, responses, cookies, and store payloads.

### Key Entities *(include if feature involves data)*

- **Operator session (existing)**: The registry record `OperatorSession` (`identity.py:469`). It holds the owner, the cloud session, the credential mode, the creation time, and the selected sites.
- **Owner (existing)**: The `SessionOwner` pair (`identity.py:389`). It joins the identity and the browser identifier.
- **Store record (new)**: The encrypted, non-credential record in the store for one environment token session. Defined in `design/contracts/store-record.md`.
- **Lifetime window (new)**: The absolute deadline and the idle deadline inside each store record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the restart contract test, a protected request returns status 200 after application replacement for an environment token session.
- **SC-002**: In the same test, browser token and provider login cookies return `401` after application replacement.
- **SC-003**: A store outage returns `503` during sign-in and during recovery. No session registers locally.
- **SC-004**: Unit tests prove the idle and absolute expiry paths with an injected clock.
- **SC-005**: Contract tests find no synthetic credential value in logs, responses, cookies beyond the owner key, or store payloads.
- **SC-006**: A guard test counts 51 decorated protected handlers.
- **SC-007**: A diff check confirms that the change touches only the files in `tasks.md`.
- **SC-008**: Each applicable local gate in `.github/copilot-instructions.md` passes for the changed files.

## Assumptions

- Redis is reachable from the capture container through `REDIS_HOST` and `REDIS_PORT` (`compose.yml:147` and `compose.yml:148`).
- `cryptography==50.0.2` and `redis==8.1.0` are already pinned (`requirements.txt:37` and `requirements.txt:215`). The feature adds no package.
- The environment token does not change between sign-in and recovery during normal operation.
- Operators authenticate again once, at the deployment that adds the store (decision D-19).
- The capture portal keeps one Gunicorn worker (`container/scripts/start.sh:324`).

## Out of Scope

- Recovery of browser token and provider login sessions. This needs decision D-1 approval.
- Recovery of run driver threads. The threads live in `src/interfaces/portals/upgrade_portal/upgrade/driver.py:1386` and start at `driver.py:1432`. A separate issue is required.
- Revocation across several workers. This needs a separate design before the worker count changes.
- Redis ACL provisioning beyond `requirepass`.
- Edits to `src/foundation/support/utils/logger_utils.py`.
- Edits to `tests/contract/upgrade_portal/test_no_credential_leak.py` before issue #2708 completes the handoff of the file.
- The `mist-ops-platform` session store (issue #2051).
- Removal or reuse of `src/interfaces/portals/upgrade_portal/auth/session.py`.

## Clarifications

### Session 2026-11-26

- Q: Does the issue authorize persistent token storage? A: No. The issue body says it does not authorize persistent token storage. Decision D-1 keeps credential material out of the store.
- Q: Which source path is live? A: `src/interfaces/portals/upgrade_portal/runtime/identity.py` (RC-01, RC-02). The retired issue path `upgrade_portal/runtime/identity.py` is absent (RC-39).
- Q: Does the issue proof test exist? A: No (RC-38). Task T013 adds the restart contract to the existing auth contract module.
- Q: Which base revision applies? A: Remote `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RC-52). The legacy base commits are stale (LC-03 and LC-09 in design/research.md).
- Q: Can the closed PR 4018 record be reused? A: Only verified claims are reused. The record uses a new slug, `upgrade-portal-session-recovery`.
- Q: Does the organization pick survive a worker replacement? A: Yes. The pick stays in the signed session (`select.py:621` and `select.py:1875`).
