# Feature Specification: Gated Converter Administration and Unassignment

**Feature Branch**: `feat/4645-cisco-converter-administration`

**Created**: 2026-11-26

**Status**: Draft. Offline design and synthetic tests only. Live Mist writes stay disabled.

**Input**: GitHub issue 4645, "[Spec]: Add gated converter administration and unassignment". Complete tasks T025 and T026 from the full-parity task map in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`. The parent feature is issue 4224.

## Clarifications

### Session 2026-11-26

- Q: Does this issue enable a live Mist write? A: No. Issue 4645 authorizes no production operation. Decisions D-1 and D-2 keep every live write disabled until owner approval exists.
- Q: Which template family does deletion cover? A: Gateway templates only, through `deleteOrgGatewayTemplate`. Decision D-4.
- Q: Where do the tests go? A: In `tests/integration/web_portal/cisco_config_converter/administration/`. Decision D-5.
- Q: Where does the source go? A: In `engine/administration/`. Issue 4636 moves `conversion.py` into `engine/` first. Decision D-6.
- Q: Does site-template unassignment stay in scope? A: The issue names it. No verified write contract exists. The path stays refused until decision D-3 and issue 4634 close.
- Q: Do two confirmations mean two typed words? A: No. The first confirmation echoes the scope digest. The second is the exact typed word `CONFIRM`. Decision D-10.
- Q: Does the deployed portal expose these routes? A: No. Shared registration waits for issue 4648. Decision D-16.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep administration hidden and refused by default (Priority: P1)

An operator opens the converter page. Administrative controls stay hidden until the owner enables the mode. The server checks the family and the operator identity before any read or write.

**Why this priority**: A hidden and refused path prevents accidental production changes.

**Independent Test**: Call each administrative route with the mode disabled, with a disabled family, and without a verified identity. Count the SDK write calls. The count is zero for each call.

**Acceptance Scenarios**:

1. **Given** administrative mode is disabled, **When** an operator requests an administrative route, **Then** the portal returns 404 and makes no Mist call.
2. **Given** the mode is enabled and the family is not, **When** the operator submits the family, **Then** the portal returns 403 with no write.
3. **Given** no verified operator identity, **When** the operator submits a scope review, **Then** the portal returns 403 and makes no write.

### User Story 2 - Review and confirm the exact scope (Priority: P1)

An authorized operator selects object IDs. The portal shows each object, its references, its backup status, and a scope digest. The operator confirms the digest and types `CONFIRM`.

**Why this priority**: A wrong object or a stale view can delete production configuration.

**Independent Test**: Use synthetic objects, references, and backup manifests. Change one object after the review. Confirm that the run refuses and makes no write.

**Acceptance Scenarios**:

1. **Given** explicit object IDs, **When** the operator submits a scope review, **Then** the portal shows each object, its references, backup status, and digest.
2. **Given** a live reference from an outside object, **When** the operator submits a scope review, **Then** the review status is `blocked`.
3. **Given** a missing or wrong `CONFIRM`, **When** the operator starts a run, **Then** the portal returns 400 and makes no write.

### User Story 3 - Run the approved changes and record each outcome (Priority: P2)

After two confirmations and a verified backup, the executor unassigns devices from profiles. It then deletes gateway templates, networks, and services. It reads back each object after its write. It stops at the first failed or indeterminate outcome.

**Why this priority**: The executor is the only path that changes Mist. Each outcome must be visible to the operator.

**Independent Test**: Simulate SDK responses for success, 4xx, 429, timeout, and a read-back mismatch. Check each outcome and each SDK call count.

**Acceptance Scenarios**:

1. **Given** a current approval and a verified backup, **When** the operator starts a run, **Then** each object gets one write call and one outcome.
2. **Given** a write without a verified read-back, **When** the executor finishes, **Then** the object is `indeterminate`, the run stops, and no write repeats.
3. **Given** a changed object after approval, **When** the executor reads the state, **Then** the run stops and later objects get `not_attempted`.

### User Story 4 - Use the administration page safely (Priority: P2)

An authorized operator sees the exact scope and the backup status. A change to the selection clears the review and disables the run control.

**Why this priority**: A stale view must never start a run.

**Independent Test**: Use the Flask test client with the mode enabled and a simulated operator. Change one object ID in the page state. Check the run control state.

**Acceptance Scenarios**:

1. **Given** administrative mode is disabled, **When** a user opens the administration page, **Then** the page returns 404.
2. **Given** a current scope review, **When** the operator changes one object ID, **Then** the run control stays disabled until a new scope review succeeds.

### Edge Cases

- A scope with zero objects, duplicate IDs, malformed IDs, or more than 25 objects returns 400.
- A device profile unassignment with an empty MAC list returns 400.
- An approval exactly 15 minutes old returns 409. The expiry boundary is inclusive.
- A store that cannot persist the operation record returns 503 before the first write.
- A read-back that times out marks the object `indeterminate` and stops the run.
- A before-state read that returns 404 stops the run before any write. The reviewed state changed.
- A 429 response does not start an automatic retry. The read-back decides the outcome.
- A backup manifest with incomplete pagination, a wrong organization, or a wrong family blocks the run with 409.
- A site-template scope returns 403 until decision D-3 and issue 4634 close.
- A reference that issue 4634 does not verify blocks the scope review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Administrative mode MUST stay disabled unless `CISCO_CONVERTER_ADMIN_MODE` equals `enabled`. Each administrative route MUST return 404 while the mode is disabled.
- **FR-002**: Each family MUST stay disabled unless `CISCO_CONVERTER_ADMIN_FAMILIES` lists it. Valid families are `gateway_templates`, `networks`, `services`, `device_profile_unassign`, and `site_template_unassign`.
- **FR-003**: Each administrative route MUST refuse a request without a verified operator identity with 403. The production verifier MUST refuse every identity until decision D-1 closes.
- **FR-004**: Each administrative POST MUST pass the existing CSRF guard before any read or write.
- **FR-005**: The operator MUST select objects by explicit IDs. A scope MUST hold one to 25 unique IDs for one organization and one family. Invalid input MUST return 400.
- **FR-006**: A scope review MUST return each object's family, ID, name, before-state digest, reference status, and backup status. It MUST return a scope digest, which is a SHA-256 digest of canonical JSON.
- **FR-007**: A live reference from an object outside the scope MUST set the review status to `blocked`. A run with a blocked review MUST return 409. The portal MUST NOT detach a reference automatically.
- **FR-008**: Each family in a run MUST have a verified backup manifest from the issue 4643 catalog. The manifest MUST cover each selected object. A missing, unverified, wrong-organization, or wrong-family manifest MUST return 409.
- **FR-009**: The approval step MUST require a scope confirmation that equals the current scope digest. The run MUST require the approval ID and the exact typed word `CONFIRM`. A missing or wrong value MUST return 400 before any write.
- **FR-010**: An approval MUST bind one operator, one scope digest, and one use. It MUST expire 15 minutes after creation. An expired, reused, or mismatched approval MUST return 409.
- **FR-011**: Before each write, the executor MUST read the current object and compare its digest with the reviewed before-state digest. A changed digest or a missing object MUST stop the run before that write.
- **FR-012**: The operation record MUST persist before the first write. A persistence failure MUST return 503 before the first write.
- **FR-013**: Device profile unassignment MUST send only the reviewed MAC addresses in the `macs` array. The array MUST hold one or more unique values.
- **FR-014**: Each gateway template, network, and service deletion MUST call one SDK delete function for one object with explicit arguments.
- **FR-015**: Site-template unassignment MUST stay refused until decision D-3 approves the path and issue 4634 verifies its contract.
- **FR-016**: After each write, the executor MUST read back the object. A read-back that shows the reviewed change marks the object `verified`. A read-back that shows no change marks the object `failed`. A read-back error or timeout marks the object `indeterminate`.
- **FR-017**: The executor MUST NOT repeat a write automatically. An object marked `failed` or `indeterminate` MUST stop the run. The executor MUST mark each later object `not_attempted`.
- **FR-018**: The response and the operation record MUST list each object's family, ID, action, outcome, and detail. They MUST NOT hold raw Mist response bodies, tokens, or passwords.
- **FR-019**: The executor MUST preserve unrelated fields. A device profile unassignment MUST change only the listed MAC addresses. A deletion MUST change only the selected object.
- **FR-020**: Each administrative action MUST write an `info` log line before the action and a `debug` log line after it. Logs MUST NOT hold the typed word, tokens, or request bodies.
- **FR-021**: The administration page MUST show the exact scope, the backup status, and the scope digest. A change to the selection MUST clear the review and disable the run control.
- **FR-022**: Each new interactive control MUST carry a stable `data-testid` attribute.
- **FR-023**: No administrative route MUST register on the shared portal in this issue. Registration waits for issue 4648 under gate G3.
- **FR-024**: Each refusal test MUST prove zero SDK write calls. The file `design/checklists/security.md` lists each refusal case.
- **FR-025**: Each new folder MUST hold five children or fewer. The source MUST use `engine/administration/` after issue 4636 moves `conversion.py` into `engine/`.
- **FR-026**: Each Mist call MUST use a mistapi function with explicit arguments. The code MUST NOT forward `*args` or `**kwargs`.
- **FR-027**: The change MUST add `CISCO_CONVERTER_ADMIN_MODE` and `CISCO_CONVERTER_ADMIN_FAMILIES` to `deploy/.env.example` with safe defaults.
- **FR-028**: The change MUST add one changelog fragment named `changelog.d/issue-4645-converter-administration.md`.

### Mist Cloud Transport Requirements

- Use mistapi functions only. Each call passes explicit arguments. Direct HTTP to a Mist endpoint is prohibited.
- Write functions in scope are `deleteOrgGatewayTemplate`, `deleteOrgNetwork`, `deleteOrgService`, and `unassignOrgDeviceProfile`.
- Read functions for before-state and read-back are `getOrgGatewayTemplate`, `getOrgNetwork`, `getOrgService`, and `getOrgDeviceProfile`. A device read for each MAC address is unverified (UV-06).
- Reference reads need verified contract rows before a scope review can clear a reference (UV-01 and UV-09).
- The site-template path uses `updateSiteInfo` as a candidate only. The path stays refused under FR-015.
- Each write stays blocked until issue 4634 records payload, response, and read-back evidence (gate G2). The owner must also approve the family (gate G4).
- The operation `deleteOrgServicePolicy` exists in the SDK and the OpenAPI file. It stays out of scope under decision D-13.

### Key Entities

- **Administrative scope**: Explicit object IDs for one organization and one family. It holds before-state digests, reference status, and backup status. It holds no secret values.
- **Scope digest**: A SHA-256 digest of the canonical JSON form of the scope. It binds each approval to the reviewed state.
- **Approval**: `ApprovalRecord` from issue 4636. It binds one operator, one scope digest, and one use. It expires 15 minutes after creation.
- **Operation record**: `OperationRecord` from issue 4636. It holds the phase, the approval reference, the backup references, and each object outcome.
- **Backup manifest**: `BackupManifest` from issue 4636, created under issue 4643. It holds the verified object inventory for one family.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each administrative route returns 404 in every test while the mode is disabled.
- **SC-002**: Each refusal test records zero SDK write calls.
- **SC-003**: Each successful run test requires a scope confirmation, a typed `CONFIRM`, and a verified backup manifest.
- **SC-004**: Each object outcome appears in the response and in the operation record.
- **SC-005**: Each unknown outcome stops the run. No write repeats.
- **SC-006**: The administration page disables the run control after each selection change until a new scope review succeeds.
- **SC-007**: The existing preview, review, and export tests in `tests/integration/web_portal/cisco_config_converter/test_routes.py` pass without edits.

## Assumptions

- **A-1**: The owner keeps administrative mode disabled in production until decisions D-1, D-2, and D-3 close.
- **A-2**: Issue 4636 lands the `state/` package and the `engine/` move before this issue writes source code.
- **A-3**: Issue 4643 supplies a verified backup catalog for each family in scope.
- **A-4**: Issue 4634 verifies each write, read, reference, and read-back contract before this issue enables a family.
- **A-5**: The repository holds no operator identity provider. Tests inject a simulated verifier. Production refuses writes.
- **A-6**: Shared portal routes stay unregistered until issue 4648 completes the integration handover.
- **A-7**: The existing credential service creates each Mist session. This change adds no credential source.

## Out of Scope

- Restore and recovery (issues 4644 and 4646).
- Apply (issue 4644) and discovery (issue 4642).
- Shared portal registration and navigation (issue 4648).
- Visual journeys (issue 4647).
- Service policy deletion, device profile deletion, site deletion, inventory unassignment, and template deletion for other families.
- Bulk operations and automatic reference detachment.
- Live Mist operations of any kind.

Warning: A live deletion removes a Mist object. This code cannot restore that object. Recovery needs a verified backup and a new approval (issue 4646).

Warning: A deleted network or service can break a live site when a template still uses it. The scope review blocks each such reference.

Caution: A device profile unassignment removes the profile from the listed devices. Reassignment restores the link. The operation record stores each before-state digest.

Warning: A site-template unassignment can change inheritance for live sites. The path stays refused until decision D-3 closes.
