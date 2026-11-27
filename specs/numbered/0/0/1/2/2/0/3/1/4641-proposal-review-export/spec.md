# Feature Specification: Versioned Proposal Review and Safe Export

**Issue**: #4641, "[Spec]: Add versioned proposal review and safe export"

**Feature Branch**: `feat/4641-proposal-review-export`

**Record Path**: `specs\numbered\0\0\1\2\2\0\3\1\4641-proposal-review-export`

**Parent**: #4224. **Task map**: PR #4596, `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`. This record covers tasks T017 and T018 of that map.

**Created**: 2026-11-26

**Status**: Draft. Offline work only. Cloud writes stay blocked.

**Input**: GitHub issue #4641. The issue asks for a structured proposal review, versioned offline operations, and a safe export.

## Terms

Each term keeps one meaning in this record.

- **Source**: The Cisco IOS text file that an operator uploads.
- **Preview**: The action that converts a source into a proposal.
- **Proposal**: The object that a preview returns. Version 2 returns a structured proposal.
- **Review**: The operator action that records approval of the current proposal.
- **Export**: The JSON download of the reviewed proposal.
- **Version 1**: The existing DNS routes, request fields, response keys, and status codes.
- **Version 2**: The new routes under `/cisco-config-converter/v2/` and the structured proposal.
- **Scope**: The fields that identify what a proposal targets.
- **Digest**: The lowercase SHA-256 value of the canonical JSON form of an object.
- **Template type**: The gateway template value `standalone` or `spoke`.
- **Hardware role** and **hardware model**: Scope fields reserved for issue #4638.
- **Object change**: One proposed change to a Mist object.
- **Omission**: A source line or known gap that the converter does not convert.
- **Unresolved mapping**: A value that needs an operator decision before conversion.
- **Verification state**: The local schema result and the cloud state result.

## Clarifications

### Session 2026-11-26

- Q: Which task IDs does this issue own? A: The full-parity tasks T017 and T018. The DNS task list of issue #4224 also uses T017, and this record follows the full-parity meaning that the issue names. Sources: full-parity `tasks.md` lines 63 and 64 (research rows 60 and 61). The #4224 `tasks.md` line 65 uses T017 for export tests (research row 68).
- Q: Does version 2 replace the DNS clients? A: No. Version 1 stays unchanged. Source: issue #4641, "Preserve the existing DNS preview, review, and export clients." Full-parity `design/contracts/portal.md` line 15 requires an explicit version contract.
- Q: Is implementation authorized? A: Yes, for offline work only. The coordinator decision on issue #4633, dated 2026-11-08T23:37:56Z, authorizes "independent, offline implementation and synthetic tests for the Cisco converter."
- Q: May version 2 write to Mist? A: No. Issue #4641 says "Do not introduce cloud writes here." The coordinator comment on issue #4636 (2026-11-09T16:55:13Z) says offline decisions "do not authorize a cloud write or release."
- Q: Does the export use the repository exporter? A: No. The constitution scopes `DataExporter` to API export and data collection. Decision D-5 explains the choice.
- Q: Where do browser tests run? A: In the isolated converter host. The shared portal stays unchanged. Source: issue #4641, "isolated portal host." Decision D-13 explains the file choice.
- Q: Does this issue register routes in the shared portal? A: No. Issue #4641 says "Do not register shared portal routes in this issue." Open PR #4208 owns the shared portal files.
- Q: Which change lands first? A: Issue #4636 lands first. Its package move creates the `state/` package. Decision D-14 explains the order.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review a structured proposal offline (Priority: P1)

An operator uploads a source and runs a version 2 preview. The response shows the scope, object changes, omissions, unresolved mappings, and verification state. No Mist credential is needed.

**Why this priority**: The structured review is the core of issue #4641. An operator must see each change before export.

**Independent Test**: Post a synthetic source to `/cisco-config-converter/v2/preview` without credentials. Check each section of the response.

**Acceptance Scenarios**:

1. **Given** a source with one global IPv4 `ip name-server` line, **When** the operator previews, **Then** `object_changes` holds one gateway template change with action `propose_create`.
2. **Given** a source with an IPv6 name-server line, **When** the operator previews, **Then** `omissions` lists that line with disposition `omitted`.
3. **Given** any valid source, **When** the operator previews, **Then** `verification.cloud_state` is `unavailable`, and `unresolved_mappings` is an empty list.

---

### User Story 2 - Export the exact reviewed proposal (Priority: P1)

An operator reviews the current proposal and exports it. The exported object equals the reviewed object as JSON.

**Why this priority**: The export is a handoff record. It must match what the operator reviewed.

**Independent Test**: Preview, review, and export. Compare the downloaded object with the preview response.

**Acceptance Scenarios**:

1. **Given** a current proposal, **When** the operator reviews it, **Then** the response is HTTP 200 and echoes the same object.
2. **Given** a reviewed proposal, **When** the operator exports it, **Then** the response is an attachment named `cisco-proposal-v2.json` that holds the same object.
3. **Given** no review, **When** the operator exports, **Then** the response is HTTP 409.

---

### User Story 3 - Invalidate review after a relevant change (Priority: P1)

A new preview, an edited proposal, or a changed name, template type, or source removes the review. The export of the older proposal then fails.

**Why this priority**: A stale review can approve content that the operator did not see.

**Independent Test**: Review a proposal. Change the scope or run a new preview. Export the older proposal.

**Acceptance Scenarios**:

1. **Given** a reviewed proposal, **When** the operator runs a new preview, **Then** export of the older proposal returns HTTP 409.
2. **Given** a reviewed proposal, **When** the template name changes and the operator previews again, **Then** review of the older proposal returns HTTP 409.
3. **Given** a version 1 review, **When** a version 2 preview runs, **Then** the version 1 export returns HTTP 409.
4. **Given** a review recorded 15 minutes earlier, **When** the operator exports, **Then** the response is HTTP 409, because the lifetime is inclusive.

---

### User Story 4 - Keep version 1 clients unchanged (Priority: P2)

The DNS routes, request fields, response keys, status codes, and export name stay unchanged.

**Why this priority**: Current tests and operators depend on version 1.

**Independent Test**: Run the existing route tests and the existing browser journey. Neither file changes for version 2 behavior.

**Acceptance Scenarios**:

1. **Given** the existing tests, **When** they run after this change, **Then** each test passes without an edit.

---

### User Story 5 - Keep the work offline, private, and non-writing (Priority: P2)

Version 2 routes open no network connection and make no Mist call. They write no file. Logs, browser session values, and exports hold no source text and no secret value.

**Why this priority**: The coordinator limits this work to offline behavior.

**Independent Test**: Run version 2 routes with network and file access blocked. Search logs, session values, and export for synthetic values.

**Acceptance Scenarios**:

1. **Given** network and file access are blocked, **When** the operator runs preview, review, and export, **Then** each request succeeds.
2. **Given** a synthetic secret in an unsupported line, **When** the operator exports, **Then** the secret is absent from the export, logs, and session.

---

### Edge Cases

- A source with no supported command returns no `dns_servers` and one omission that states that no supported command was found.
- A source with only IPv6 name-server lines returns no `dns_servers` and lists each line as an omission.
- A template name of 120 characters is accepted. A name of 121 characters returns HTTP 400.
- A request with `proposal_version` 1 or 3 returns HTTP 400.
- A request with a missing key or an extra key returns HTTP 400.
- A source over 16 MiB returns HTTP 400. A request body over 16 MiB plus 16 KiB returns HTTP 413.
- Two browser tabs share one browser session. The last preview controls both tabs.
- Caution: A restart with a random portal secret clears every review. The operator must review the proposal again.
- A changed form resets the version 2 controls, as version 1 does.
- A preview or review recorded 15 minutes earlier returns HTTP 409 on the next step. The lifetime is inclusive at 15 minutes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST provide `POST /cisco-config-converter/v2/preview`, which returns a structured proposal with `proposal_version` 2.
- **FR-002**: Each proposal MUST list one object change for the gateway template, with identity, fields, and `existing_state` set to `not_checked`.
- **FR-003**: Each proposal MUST list every unsupported source line and known gap in `omissions`, with disposition `omitted`.
- **FR-004**: `unresolved_mappings` MUST be a list of decisions that remain open. For the DNS subset, it MUST be empty.
- **FR-005**: `verification` MUST report `local_schema` as `passed` and `cloud_state` as `unavailable`, with a reason.
- **FR-006**: `scope` MUST hold the name, template type, source byte count, source suffix, hardware role, hardware model, and target.
- **FR-007**: `scope_digest` MUST equal the digest of `scope`. The proposal digest MUST cover `scope_digest`.
- **FR-008**: `POST /cisco-config-converter/v2/review` MUST record review only for the current proposal. Any other proposal MUST return HTTP 409.
- **FR-009**: `POST /cisco-config-converter/v2/export` MUST return the reviewed proposal as `cisco-proposal-v2.json`. An unreviewed proposal MUST return HTTP 409.
- **FR-010**: Every preview, in version 1 or version 2, MUST clear the earlier review before it publishes a proposal.
- **FR-011**: A changed name, template type, source, or proposal MUST invalidate the review.
- **FR-012**: A version 2 request body MUST hold `proposal_version` 2 and exactly the contract keys. Any other body MUST return HTTP 400.
- **FR-013**: Version 1 routes, request fields, response keys, status codes, headers, and export name MUST remain unchanged.
- **FR-014**: Version 2 routes MUST open no network connection, make no Mist call, and write no file.
- **FR-015**: The version 2 export MUST NOT call `DataExporter.write_with_format_selection`.
- **FR-016**: Logs, browser session values, and responses MUST NOT hold source text, template name, unsupported values, or secret values.
- **FR-017**: Each version 2 POST route MUST require the CSRF token and return HTTP 400 when the token is missing.
- **FR-018**: Each version 2 action MUST write an `info` log line before the action and a `debug` log line after it.
- **FR-019**: Each version 2 success response MUST send `Cache-Control: no-store`.
- **FR-020**: The isolated browser host MUST show the structured sections, review, and export with stable test IDs.
- **FR-021**: The change MUST keep each directory at five children or fewer, and it MUST add no direct child to the converter root.
- **FR-022**: The change MUST add one changelog fragment for the user-visible behavior.
- **FR-023**: A preview MUST NOT be reviewed 15 minutes or more after it is recorded. A review MUST NOT be exported 15 minutes or more after it is recorded. Either case MUST return HTTP 409.

### Mist Cloud Transport Requirements

This feature uses no mistapi method. It makes no Mist REST or WebSocket request. The gateway template shape cites `createOrgGatewayTemplate` for later apply work only. Source: `.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py` line 58, and OpenAPI line 9764. Contract-test evidence for SDK transport is not applicable to this issue.

### Key Entities

- **StructuredProposal**: The version 2 response. It holds ten keys, listed in `design/contracts/proposal-v2.md`.
- **Scope**: The fields that identify the target and the source. Its digest is `scope_digest`.
- **ObjectChange**: One proposed change to the gateway template object.
- **Omission**: One source line or known gap that the converter does not convert.
- **Verification**: The local schema result and the cloud state result.
- **ReviewBinding**: The browser session values that hold the proposal digest, the reviewed digest, and the UTC times of the preview and the review. It holds no source text.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 21 planned test functions pass without network access.
- **SC-002**: The version 2 tests record zero Mist requests, zero network connections, and zero file writes.
- **SC-003**: The existing route tests and the existing browser journey pass without edits.
- **SC-004**: Each stale, unreviewed, and malformed request returns the status code in the route contract.
- **SC-005**: The synthetic secret appears zero times in exports, logs, and browser session values.
- **SC-006**: The isolated browser host shows each stable test ID and completes review and export.
- **SC-007**: The converter root keeps five direct children, and no new direct child enters `tests/e2e/web_portal/`.

## Assumptions

- **A-1**: Issues #4636, #4637, #4638, #4639, and #4640 merge before implementation. Their outputs extend the proposal only through a new contract revision.
- **A-2**: The coordinator approves the three version 2 routes in the route set of issue #4648 before that issue merges.
- **A-3**: Browser session storage holds digests only. Persistence waits for the store of issue #4636 and the backup policy of issue #4643.
- **A-4**: Offline review needs no operator identity, because a review does not authorize a write.
- **A-5**: The Chromium browser test runs in the existing Playwright setup.

## Out of Scope

- Cloud discovery, cloud apply, backup, restore, delete, and unassign. Issues #4642 through #4646 own them.
- Hardware role and model mapping (issue #4638), management review (issue #4639), network conversion (issue #4640), and structured input (issue #4637). This record consumes their output shape only.
- Persisted proposals and sealed approvals. Issue #4636 defines the store, and issue #4643 owns the backup policy.
- Shared portal route registration and shared file edits. Issue #4648 and the integration owner handover own them.
- Visual theme parity (issue #4647) and legal review (issue #4635).
- Mist API contract verification for write payloads (issue #4634).

Warning: Do not add a cloud write route to the converter. A cloud write changes production Mist data, and this repository cannot reverse that change.
