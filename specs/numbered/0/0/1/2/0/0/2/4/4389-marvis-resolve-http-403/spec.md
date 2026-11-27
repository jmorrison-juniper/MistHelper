# Feature Specification: Marvis resolve HTTP 403 handling

**Feature Branch**: `fix/4389-marvis-resolve-403`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4389, open, labels `bug`, `MistHelper.py`, `needs-human-review`

**Base commit**: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (remote `main`, checked 2026-11-26)

**Input**: User description: "Issue 4389: menu 270 mode 3 returned HTTP 403 for one approved resolve request. The Marvis Action stayed open. Find the cause, show the refusal safely, and stop the run after an authorization refusal."

## Clarifications

### Session 2026-11-26

- Q: Does the client treat HTTP 403 as success? A: No. Only HTTP 2xx counts as accepted at `client.py` line 187.
- Q: Does the results file already hold the Mist body? A: Yes. The first 300 characters of the body reach the results file. The issue states that the body was not reviewed.
- Q: Does a live repeat of the resolve request close the issue? A: No. The owner comment says not to repeat a resolve request against production.
- Q: Does this change alter the menu category or the confirmation text? A: No. Both stay unchanged.
- Q: Does this change decide the root cause? A: No. The cause stays unverified. The record lists the evidence that a human must collect.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the refusal reason without identifiers (Priority: P1)

An operator runs mode 3. Mist answers the resolve request with HTTP 403. The results file shows the status and a masked reason. No UUID, token value, or email address appears.

**Why this priority**: The current record does not show whether permission or the request contract caused the refusal. The reason is needed before any cause can be separated.

**Independent Test**: Run the client and the workflow with a fake session. The fake session returns HTTP 403 and identifiers in the body. Read the result row and the log line. No live Mist call is made.

**Acceptance Scenarios**:

1. **Given** a resolve request that returns HTTP 403 with a UUID in the body, **When** the client returns the answer, **Then** the error text starts with `HTTP 403` and shows `<uuid>` for the UUID.
2. **Given** a refused resolve request, **When** the results file is written, **Then** the row shows outcome `error`, HTTP status 403, and an empty `verified_status`.

---

### User Story 2 - Stop the run after an authorization refusal (Priority: P1)

After HTTP 401 or HTTP 403, mode 3 sends no later resolve request in the same run. Each later Marvis Action keeps outcome `not_sent` and stays open for a later run.

**Why this priority**: A token role refusal repeats for each Marvis Action. Each repeated request adds a refused write against the production organization.

**Independent Test**: Run three selected Marvis Actions with a fake session. The fake session returns HTTP 403 on the first request. Count the requests and read the result rows.

**Acceptance Scenarios**:

1. **Given** three selected Marvis Actions and HTTP 403 on the first request, **When** the run finishes, **Then** the fake session receives exactly one PUT request.
2. **Given** the same run, **When** the results file is written, **Then** rows two and three show outcome `not_sent` and a message that names HTTP 403.
3. **Given** HTTP 401 on the first request, **When** the run finishes, **Then** the same stop rule applies.

Caution: a refused run leaves the remaining Marvis Actions open. Read the results file before you start a new run.

---

### User Story 3 - Read the diagnosis steps in the documentation (Priority: P2)

A maintainer or operator reads the endpoint report and the operator guide. Both documents state that the cause of HTTP 403 is unverified. Both documents give the stop rule and the role check.

**Why this priority**: The endpoint report states that no live resolve ran before issue 4389. The documents must match the new evidence and the new stop rule.

**Independent Test**: Read the changed sections and the changelog fragment. Run the STE gate. Run the guard test that compares the documented statuses with the code.

**Acceptance Scenarios**:

1. **Given** the endpoint report, **When** a reader searches for HTTP 403, **Then** the report states the stop rule, the masking rule, and the unverified cause.
2. **Given** the operator guide, **When** an operator reads the mode 3 paragraph, **Then** the paragraph states what happens after HTTP 401 or HTTP 403.

---

### Edge Cases

- Mist returns a body that is not JSON on HTTP 403. The text is masked and capped with the same rules.
- Mist returns no HTTP answer. The existing no-answer text stays. The run does not stop for this case.
- Mist returns HTTP 429. mistapi retries the request. The run does not stop for this case.
- The stop signal arrives before a refusal. Rows after the signal keep the stop message.
- A refusal follows accepted requests. The verify read still checks the accepted rows.
- A UUID crosses the 300-character limit. Masking runs before the limit. A cut fragment of the UUID can remain at the cut point.
- A body holds no UUID, token value, or email address. The error text stays the same as before.
- A refused run offers no alarm acknowledgement. No `ACKNOWLEDGE` prompt appears.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The resolve client MUST accept only HTTP 200 through 299 as success. Every other status MUST count as refused.
- **FR-002**: The refused error text MUST mask UUIDs, token values, and email addresses.
- **FR-003**: The error text MUST hold at most 300 characters of printable ASCII text after masking.
- **FR-004**: Mode 3 MUST send no later resolve request after HTTP 401 or HTTP 403 in the same run.
- **FR-005**: Each Marvis Action that FR-004 leaves unsent MUST keep outcome `not_sent` and the refusal message.
- **FR-006**: Mode 3 MUST write one WARNING line that names the status and asks for a role check.
- **FR-007**: The request path, body, typed confirmation, and acknowledgement prompts MUST stay unchanged.
- **FR-008**: The outcomes for HTTP 400, 429, 500, and 503 MUST stay unchanged. Only the masking rule changes their error text.
- **FR-009**: The endpoint report and the operator guide MUST state the unverified cause, the stop rule, and the role check.
- **FR-010**: The unit tests MUST cover HTTP 401, HTTP 403, and the run-level stop rule. No test MAY call the live Mist API.
- **FR-011**: The change MUST add one changelog fragment named `issue-4389-marvis-resolve-403.md`.

### Mist Cloud Transport Requirements

- The resolve request uses `mist_put` on the mistapi session. The local SDK defines it at `.venv\Lib\site-packages\mistapi\__api_request.py`, line 303.
- The list read uses `mist_get` on the same session. That call is unchanged.
- No endpoint-specific mistapi method exists for `/api/v1/labs/orgs/{org_id}/suggestions`. The pinned SDK directory holds no labs path.
- The public OpenAPI document holds no labs path. Its generic HTTP 403 response describes a permission error.
- No owned WebSocket transport is used.
- Contract-test evidence:
  - SDK insufficiency: the SDK has no endpoint method. The session method is the only transport.
  - SDK authentication: the session setup is unchanged. Tests use a fake session.
  - SDK endpoint parity: not testable offline. Unit tests pin the path and the body.
  - Failure safety: tests cover HTTP 400, 401, 403, 429, 500, 503, and no answer.
  - Secret redaction: tests cover UUID, token, and email masking.

### Key Entities

- **Marvis Action**: One record from the Mist list. The natural key is `uuid`. The resolve request names it through `row_key`.
- **Resolve run**: One mode 3 execution. It holds one resolution code, one comment, and one resolve time.
- **Resolve result row**: One row in the results file for each selected Marvis Action. The key is `result_id`.
- **Refusal**: One non-2xx answer to the resolve request. It holds the HTTP status and the masked error text.
- **API token role**: The organization role of the account that owns the API token. The role is outside this repository.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The run-level stop test fails on base commit `f03c6c9b` and passes after the change.
- **SC-002**: In a three-target run with HTTP 403 on the first request, the fake session receives exactly one PUT request.
- **SC-003**: No masked error text in the tests holds a UUID, a token value, or an email address.
- **SC-004**: Each applicable local gate in `tasks.md` reports the expected result.
- **SC-005**: Each changed Markdown file scores 80 or above in the STE gate.

## Assumptions

- The issue evidence is accurate. The evidence shows HTTP 403, outcome `error`, an empty verified status, and an open Marvis Action.
- The API token could read Marvis Actions on 2026-10-21. The issue states that a read-only query succeeded.
- Mist returns a text body or a JSON body for an error. The masking rule applies to both.
- The owner of the approved lab organization can capture one masked error text after this change. The capture is optional for this record.

## Out of Scope

- The menu category of menu 270 stays `interactive_safe`. A separate issue must decide the category.
- A pre-flight role check before the first resolve request is not part of this change.
- The request path, request body, and Mist API contract stay unchanged.
- The alarm acknowledgement feature stays unchanged.
- No live Mist call runs during tests or CI.
- The mistapi logging behavior is outside this repository.
