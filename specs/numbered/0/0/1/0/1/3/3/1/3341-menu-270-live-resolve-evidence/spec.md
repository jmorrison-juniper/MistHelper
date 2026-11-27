# Feature Specification: Menu 270 Live Resolve Acceptance Evidence

**Feature Branch**: `docs/3341-menu-270-live-resolve-evidence`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #3341, "test: menu 270 mode 3 never sent a live resolve PUT, because the lab organization holds no open Marvis Action". The acceptance criteria stay open. The issue comments record one approved live resolve request that returned HTTP 403.

## Clarifications

### Session 2026-11-26

- Q: Did a live resolve request reach Mist? → A: Yes, one request. Issue comment IC_kwDOQltU8c8AAAABeBNT3g (2026-10-21T06:20:32Z) records HTTP 403, outcome `error`, and an action that stayed `open`. The issue title and body predate that comment. This record follows the comment.
- Q: Who runs the live check? → A: The repository owner runs it in the lab organization with the owner's own access. The agent holds no lab credential and sends no Mist request.
- Q: May the resolve request run again now? → A: No. Issue comment IC_kwDOQltU8c8AAAABkIBgGQ (2026-11-08T08:31:40Z) says "Do not retry the resolve." That rule stays until issue #4389 names a cause.
- Q: Does the code need a change? → A: No behavior change is needed. The resolve path, the typed gate, and the offline tests exist on `main`. This change corrects the endpoint report and adds the evidence contract.
- Q: Does the pull request close issue #3341? → A: No. The pull request uses `Refs #3341`. The owner adds `Closes #3341` after the owner evidence record shows acceptance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record one approved live resolve (Priority: P1)

The owner approves one resolve request for one open Marvis Action in the lab organization. The owner runs menu 270 mode 3 with a filter that selects only that action. The owner records the HTTP status, the outcome, and the verified status in issue #3341.

**Why this priority**: This evidence is the only missing proof for menu 270 mode 3. The issue cannot close without it.

**Independent Test**: The owner follows `design\quickstart.md` after approval. The results file holds one row. That row shows the HTTP status, the outcome, and the verified status.

**Acceptance Scenarios**:

1. **Given** owner approval and one open action, **When** the owner types `RESOLVE 1`, **Then** the results file holds one row. The row shows an HTTP 2xx status, outcome `resolved`, and a verified status outside `OPEN_STATUSES`.
2. **Given** Mist refuses the resolve request, **When** the results file shows outcome `error`, **Then** the owner records the HTTP status and the action status. The owner does not retry.
3. **Given** the lab organization holds no open action, **When** the owner lists the actions, **Then** the owner records the list read. No resolve request is sent.

---

### User Story 2 - Keep the endpoint report accurate (Priority: P1)

The maintainer corrects the live-evidence statements in `documentation\marvis-actions-api-endpoints.md`. The report names the date, the HTTP status, and the outcome of each live attempt. The report names the mistapi version that the maintainer checked.

**Why this priority**: The report says that no live resolve request was sent. That statement is wrong after the 2026-10-21 attempt.

**Independent Test**: Read the report after the change. The sentence that says no live resolve request was sent must not remain.

**Acceptance Scenarios**:

1. **Given** the 2026-10-21 attempt, **When** a reader opens the live section, **Then** the section states the date, HTTP 403, outcome `error`, and issue #4389. It also states that the action stayed open.
2. **Given** the mistapi version in the report, **When** a reader compares it with the installed package, **Then** both versions match.

---

### User Story 3 - Hold the offline contract (Priority: P2)

The maintainer runs the existing Marvis Actions tests for the resolve path. The tests prove the request path, the body, the typed gate, and each outcome.

**Why this priority**: These tests are the only automated proof of the request contract until the live check runs.

**Independent Test**: Run `python -m pytest tests\unit\marvis\actions -q`. All tests pass.

**Acceptance Scenarios**:

1. **Given** the resolve path on `main`, **When** the offline tests run, **Then** each test in the test set of `tasks.md` passes.

---

### Edge Cases

- No open action exists. The owner records the list read. No resolve request goes out.
- A filter selects more than one action. The preview shows a count above 1. The owner types no confirmation and stops the run.
- Mist closes the action before the request. The outcome is `error` or `sent_unverified`. The owner records it and does not retry.
- Mist returns HTTP 403 again. The outcome is `error`. No retry occurs until issue #4389 names a cause.
- Mist accepts the request, but the verify read shows an open status. The outcome is `sent_unverified`. The run does not count as acceptance.
- The verify read fails. The outcome is `sent_unverified` with the reason. The run does not count as acceptance.
- The stop signal arrives before the request. The outcome is `not_sent`. No request goes out.
- The action holds no `row_key`. The outcome is `skipped`. No request goes out.
- The operator types a wrong confirmation. No request goes out, and the run ends.

Caution: the live check changes the status of one Mist Marvis Action. You can set the action back to Open in the Mist UI.

Warning: a live check that causes an outage cannot be undone. Do not run a check that can affect a device.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The live check MUST start only after the owner approves one named lab organization and one named Marvis Action.
- **FR-002**: The live check MUST select one open Marvis Action with one filter. The preview MUST show a count of 1.
- **FR-003**: The operator MUST type `RESOLVE 1` before the first resolve request.
- **FR-004**: The live check MUST leave the acknowledge step blank.
- **FR-005**: The owner evidence record MUST state the HTTP status from the `http_status` column of the results file.
- **FR-006**: The owner evidence record MUST state the `outcome` and the `verified_status` from the results file.
- **FR-007**: Acceptance MUST require an HTTP 2xx status, outcome `resolved`, and a verified status outside `OPEN_STATUSES`.
- **FR-008**: The owner MUST NOT retry a refused or unverified resolve request before issue #4389 names a cause. A later run needs written owner approval.
- **FR-009**: The endpoint report MUST state the date, HTTP status, and outcome of each live attempt. It MUST name the mistapi version that the maintainer checked.
- **FR-010**: The issue record MUST NOT contain a credential, a token, or a raw response body.
- **FR-011**: The live check MUST NOT cause an outage or change a device to create evidence.
- **FR-012**: The offline tests for the resolve path MUST pass in the local gate run.
- **FR-013**: Mode 3 MUST keep its `interactive_safe` row and its typed gate until the owner decides item D-5.
- **FR-014**: The pull request MUST use `Refs #3341` until the owner evidence record shows acceptance.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The resolve request uses `APISession.mist_put` from the pinned mistapi package. The path is `/api/v1/labs/orgs/{org_id}/suggestions`.
- The list read uses `APISession.mist_get`, `mistapi.get_all`, and `mistapi.get_next`. The schema read uses `APISession.mist_get`.
- The site read uses `mistapi.api.v1.orgs.sites.listOrgSites`. The alarm search uses `mistapi.api.v1.orgs.alarms.searchOrgAlarms`. The alarm acknowledge uses `mistapi.api.v1.orgs.alarms.ackOrgMultipleAlarms`.
- No owned WebSocket transport is used. No raw HTTP client is used.
- SDK insufficiency: mistapi 0.64.1 holds no method for the `labs` paths. The check covered 288 Python files.
- SDK authentication and endpoint parity: each call uses the mistapi session. The `labs` path constants sit in one module.
- Failure safety: the offline tests cover refused responses, server errors, and missing answers.
- Secret redaction: this change adds no logging and no secret value. No existing test asserts redaction for this path.

### Key Entities *(include if feature involves data)*

- **Marvis Action**: One Mist action in the lab organization. Natural key: `uuid`. Addressing key: `row_key`. Status values appear in `design\data-model.md`.
- **Resolve request**: One PUT for one Marvis Action. It carries the resolution code, the comment, and one run time.
- **Results row**: One row of the results file. Natural key: `result_id`. It carries the HTTP status, the outcome, and the verified status.
- **Owner evidence record**: One comment on issue #3341. It states the date, the HTTP status, the outcome, and the verified status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One owner evidence record shows HTTP 2xx, outcome `resolved`, and a closed verified status.
- **SC-002**: The endpoint report has no current sentence that says no live resolve request was sent.
- **SC-003**: The offline tests in the test set of `tasks.md` pass in the local gate run.
- **SC-004**: Each FR maps to at least one task and at least one test or owner step in `tasks.md`.
- **SC-005**: The agent sends zero Mist requests while it prepares and checks this change.

## Assumptions

- The owner reviews and approves the live check in writing before the run.
- The lab organization may hold zero or one open Marvis Action at the time of the run.
- The HTTP 403 cause may be the account privilege or the beta endpoint. Issue #4389 tracks it.
- The installed mistapi 0.64.1 package matches the pin range `>=0.64.0,<0.65`.
- Mode 3 keeps its `interactive_safe` row until the owner decides item D-5.

## Out of Scope

- The cause of the HTTP 403 response. Issue #4389 tracks it.
- Any change to the resolve body, the filter, the confirmation text, or the cap.
- A new endpoint, a new menu, or a new category.
- A live test of the alarm acknowledge step.
- Any Mist request by the agent.

## Dependencies

- Issue #4389 names the cause of the HTTP 403 response.
- Pull request #3316 added menu 270. It merged on 09/24/2026. Its body says `Closes #3299`.
- Issue #3339 provides the alarm join that mode 3 uses.
