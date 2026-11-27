# Feature Specification: Webhook response status

**Feature Branch**: `fix/4718-webhook-log-comments`

**Created**: 2026-11-26

**Status**: Partly delivered. PR #4852 merged the status gates. The repair remains open.

**Input**: Issue #4718 requires failed initial webhook responses to remain errors instead of empty results.

## Clarifications

### Session 2026-11-26

- Q: Does `main` contain the status fix? A: Yes, in part. PR #4852 merged on 2026-11-19 as commit b1307510. It adds the status gates and their tests. It omits the inline comments and debug lines that Principles VI and VII require.
- Q: Does PR #4852 close issue #4718? A: No. Its body says "Refs #4718". Issue #4718 remains open.
- Q: Does the legacy record stay? A: No. This record replaces the eight legacy files in the same folder. Decision D-6 gives the reason.
- Q: Does the web portal selector belong to this issue? A: No. Decision D-1 gives the reason.
- Q: Do the commits named in the issue comments and in the legacy record reach `main`? A: No. Commits 520da641 and 9662426f do not reach `main`. Squash commits a3e8a2e7 (PR #4849) and b1307510 (PR #4852) carry the change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a failed list call as an error (Priority: P1)

The operator sees an error when the list call does not prove success. The operator does not see the notice for no configured webhooks.

**Why this priority**: A false empty result hides an authorization, transport, or cloud failure.

**Independent Test**: Return synthetic native responses from the list call with HTTP 403, HTTP 503, and no HTTP status. Run menu 256. Check the log lines and the pagination calls.

**Acceptance Scenarios**:

1. **Given** an initial list response with HTTP 403 or HTTP 503, **When** menu 256 runs, **Then** the exporter logs one error and makes zero pagination calls.
1. **Given** a list response with no integer HTTP status, **When** menu 256 runs, **Then** the exporter logs one error about the missing or invalid status.

### User Story 2 - Report a failed delivery call as an error (Priority: P1)

The operator sees an error when the delivery call does not prove success. The operator gets no delivery export file for that response.

**Why this priority**: A false empty export looks like a valid report with no deliveries.

**Independent Test**: Return synthetic native responses from the delivery call with HTTP 403, HTTP 500, HTTP 503, and no HTTP status. Check the pagination calls and the writer calls.

**Acceptance Scenarios**:

1. **Given** a delivery response with HTTP 403, 500, or 503, **When** the delivery call runs, **Then** the exporter makes no pagination or writer call.
2. **Given** a delivery response with no integer HTTP status, **When** the delivery call runs, **Then** the exporter logs one error for that status.

### User Story 3 - Keep valid results unchanged (Priority: P2)

A valid empty response keeps its empty-result notice. A successful response keeps the selection, the return values, the endpoint metadata, and the #4715 writer result.

**Why this priority**: The repair must not hide valid data or change the export contract.

**Independent Test**: Run the offline unit tests with synthetic responses at the status boundaries 200, 201, 204, and 299.

**Acceptance Scenarios**:

1. **Given** a valid empty response with HTTP status 200, **When** either call runs, **Then** the exporter logs the existing empty-result notice and logs no error.
2. **Given** a successful delivery response and a failed writer, **When** the export runs, **Then** the exporter logs the existing write failure and no success line.

### User Story 4 - Trace each HTTP status and comment each changed line (Priority: P1)

The operator finds one debug line after each initial call. The line names the call and the HTTP status. Each executable changed line carries an inline comment.

**Why this priority**: Principles VI and VII block review when code lacks inline comments or action logging.

**Independent Test**: Capture the debug lines of one list call and one delivery call. Check each line for the call name and the HTTP status. Inspect each changed line for an inline comment.

**Acceptance Scenarios**:

1. **Given** an initial list response with HTTP status 200, **When** menu 256 lists webhooks, **Then** one debug line reads "listOrgWebhooks returned HTTP 200".
2. **Given** a delivery response with no integer HTTP status, **When** the delivery call runs, **Then** one debug line reads "searchOrgWebhooksDeliveries returned no valid HTTP status".

### Edge Cases

- A Boolean status, such as True, is rejected.
- A numeric string, such as "200", is rejected.
- A float, such as 200.0, is rejected.
- A status below 200 or at 300 or above is rejected. Examples are 199, 300, 399, 404, 500, 503, and 600.
- A status of 299 is accepted.
- A status of 200 with an empty list or an empty results object keeps its empty-result notice.
- A response object with no status attribute is rejected.
- A native transport failure with status None is rejected.
- An undocumented HTTP 503 from the list call is rejected by the same rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The exporter MUST validate the initial list response HTTP status before it calls `mistapi.get_all`.
- **FR-002**: The exporter MUST validate the initial delivery response HTTP status before it calls `mistapi.get_all`.
- **FR-003**: The exporter MUST accept only an integer HTTP status from 200 through 299 that is not a Boolean.
- **FR-004**: The exporter MUST log an error for each rejected initial response. The error MUST NOT carry an empty-result, completion, or persistence message.
- **FR-005**: The exporter MUST keep the empty-result notice for a valid empty response.
- **FR-006**: The exporter MUST keep the selection, the return values, the endpoint metadata, and the #4715 writer result behavior.
- **FR-007**: The exporter MUST keep the two SDK endpoints. It MUST NOT add a direct HTTP request.
- **FR-008**: The repair MUST NOT change shared pagination or any later page.
- **FR-009**: The exporter MUST write one debug line after each initial SDK call. The line MUST name the call and show the integer HTTP status, or state that no valid HTTP status exists.
- **FR-010**: Each executable line that the repair touches MUST carry an inline comment.
- **FR-011**: Each verification MUST run offline with synthetic native responses and no socket, DNS, or SQLite access.

### Mist Cloud Transport Requirements

- The feature uses `mistapi.api.v1.orgs.webhooks.listOrgWebhooks`. The SDK defines it at `.venv\Lib\site-packages\mistapi\api\v1\orgs\webhooks.py` line 17.
- The feature uses `mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries`. The SDK defines it in the same file at line 255.
- The feature uses `mistapi.get_all`. The SDK defines it at `.venv\Lib\site-packages\mistapi\__pagination.py` line 39.
- The feature adds no direct HTTP transport and no owned WebSocket transport.
- SDK insufficiency: `APIResponse.data` defaults to an empty dictionary at `__api_response.py` line 39. `get_all` returns an empty list for that value at `__pagination.py` lines 55 and 74. A failed response therefore reads as an empty result.
- SDK authentication: the exporter passes the resolver session to each SDK call. The uses appear at exporter lines 74, 83, 135, and 145.
- SDK endpoint parity: the Mist API documents both operations in `documentation\mist-api-openapi31yaml.yaml` at lines 23864 to 23886 and lines 24059 to 24118. `documentation\MIST_API_GET_ENDPOINTS.md` lists both operations at lines 1001 and 1002.
- Failure safety: the offline tests cover 23 rejected HTTP status values for each call. The rejection test starts at `tests\unit\export\test_org_webhook_deliveries_exporter.py` line 329.
- Secret redaction: each log line names an organization identifier, a webhook identifier, a display name, or an integer HTTP status. No token, password, or response body appears in a log line.

### Key Entities

- **Initial response**: The first result of the list call or the delivery call. It exposes an HTTP status and a data value.
- **HTTP status**: The integer status attribute of an initial response. Only an integer from 200 through 299 proves success.
- **Webhook row**: One list item with a stable `id` and an optional `name`.
- **Delivery row**: One result item. Its natural key is `id`, `webhook_id`, and `timestamp`, defined at `src/foundation/support/refactors/endpoint_primary_key_strategies.py` lines 1610 to 1612.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each rejected initial response produces exactly one error and zero pagination calls or writer calls.
- **SC-002**: Each valid empty response with HTTP status 200, 201, 204, or 299 keeps its notice and logs no error.
- **SC-003**: The stable selection test and the #4715 writer tests pass without a change to their assertions.
- **SC-004**: Each initial SDK call produces exactly one debug line that names the call and the HTTP status.
- **SC-005**: The offline verification records zero socket, DNS, and SQLite attempts.
- **SC-006**: Issue #4718 closes through a merged pull request whose body contains `Closes #4718`.

## Assumptions

- The pinned SDK version is 0.64.1. Its metadata file states the version at line 3.
- The SDK sets `status_code` to None after a transport failure. The lines are `__api_response.py` lines 43 and 48.
- The owner comments of 2026-11-09 still apply. Only issues #4715 and #4718 own the exporter and its reserved tests.
- Shared pagination, later pages, and the #4715 writer stay unchanged.
- The orchestrator authorizes the repair merge.

## Out of Scope

- Shared pagination and any later page of a response.
- The web portal menu 256 choice provider in `web_portal\routes\settings.py` (decision D-1).
- Other exporters that default a missing HTTP status to 200 (decision D-11).
- Structural remediation of the Principle I violations listed in `plan.md` (decision D-12).
- The menu 45 webhook export path (decision D-11).
- README and operator guide changes. Neither file holds webhook behavior text.

Caution: until the web portal issue merges, menu 256 in the browser shows an empty choice list for a missing HTTP status.
