# Feature Specification: Portal hardware inventory unlock without the free-form shell

**Feature Branch**: `feat/4939-portal-hardware-inventory-unlock`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4939: The Collect EX hardware inventory action needs `PORTAL_WS_ENABLE_SHELL=true`. That setting also unlocks the free-form remote shell. Offer a narrower unlock that opens only the fixed inventory command.

## Open Decision

HUMAN-DECISION-REQUIRED: The owner chooses one option from issue #4939. This record recommends option 1.

- Option 1: Add the hardware flag. It unlocks only the hardware preset. This record recommends it.
- Option 2: Keep the shell flag rule and document it. Pull request #4940 completed this option on 2026-11-26.
- Option 3: Keep the shell flag rule and add operator sign-in. Issue #4936 tracks this option. This record excludes it.

Implementation starts only after the owner records option 1. If the owner chooses option 2, close this record without code.

## Clarifications

### Session 2026-11-26

- Q: Does the free-form shell stay locked when only the hardware flag is true? A: Yes. The shell flag still controls every request that accepts operator text.
- Q: Does the shell flag still unlock the hardware preset? A: Yes. Existing deployments keep their current behavior.
- Q: Which code path receives the narrower unlock? A: Only the server-owned hardware preset path. Browser fields cannot widen the unlock.
- Q: Does menu 309 change? A: No. The CLI already runs with the shell unlock in code.

## Terms

- **Hardware preset**: The server-owned batch that runs one fixed command on each connected EX switch. Its identifier is `ex-hardware-xml`.
- **Free-form shell**: Any shell that accepts operator text. It covers the Single Site "Remote shell" and every generic Multi Site shell batch.
- **Shell flag**: The environment variable `PORTAL_WS_ENABLE_SHELL`.
- **Hardware flag**: The new environment variable `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
- **Lock scope**: The server-owned value `hardware_preset`. A request has it only in the hardware preset path.
- **Lock**: The refusal with code `locked` and HTTP status 403.

Warning: A free-form shell gives full command line access to the device. Keep the shell flag false unless an operator needs it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect the hardware inventory with the hardware flag only (Priority: P1)

An operator wants the read-only EX hardware inventory. The operator sets the hardware flag and restarts the portal. The operator then runs the Collect EX hardware inventory action without the free-form shell.

**Why this priority**: This is the reason for the issue. It gives the inventory without full command line access.

**Independent Test**: Set only the hardware flag in a test with a mocked organization. The preview lists the connected EX switches.

**Acceptance Scenarios**:

1. **Given** the hardware flag is true and the shell flag is false, **When** the operator previews the hardware preset, **Then** the portal returns the target list with HTTP 200.
2. **Given** the hardware flag is true and the shell flag is false, **When** the operator starts the confirmed preview, **Then** the portal opens one shell per target and sends only the fixed command.

### User Story 2 - Keep the free-form shell locked (Priority: P1)

The owner wants the hardware flag to unlock the inventory only. A caller who reaches the port cannot open a free-form shell or send operator commands.

**Why this priority**: The shell flag gives full command line access today. This story removes that access from the inventory unlock.

**Independent Test**: Set only the hardware flag in a test. Start a Single Site shell and preview a generic shell batch. Both requests return HTTP 403 with code `locked`.

**Acceptance Scenarios**:

1. **Given** the hardware flag is true and the shell flag is false, **When** a caller starts the Single Site "Remote shell", **Then** the portal returns HTTP 403 with code `locked` and flag `PORTAL_WS_ENABLE_SHELL`.
2. **Given** the hardware flag is true and the shell flag is false, **When** a caller previews a generic shell batch with commands, **Then** the portal returns HTTP 403 with code `locked`.

### User Story 3 - See the unlock name in the page and the documents (Priority: P2)

An operator sees which variable unlocks the action when the action is locked.

**Why this priority**: The current page says only that the stream is locked. The operator must search the documents to find the variable.

**Independent Test**: Load the Multi Site tab with both flags false. The page shows the hardware flag name near the hardware preset control.

**Acceptance Scenarios**:

1. **Given** both flags are false, **When** the operator selects Collect EX hardware inventory, **Then** the page shows the text that names `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
2. **Given** the operator opens the operator guide section for the action, **When** the operator reads it, **Then** the section names both flags and the limits of each flag.

### User Story 4 - Keep existing shell unlocks working (Priority: P2)

An existing deployment sets `PORTAL_WS_ENABLE_SHELL=true` for the hardware action. The action keeps working after the update.

**Why this priority**: A change must not stop a running NOC workflow.

**Independent Test**: Set only the shell flag. The hardware preset preview returns the target list.

**Acceptance Scenarios**:

1. **Given** the shell flag is true and the hardware flag is false, **When** the operator previews the hardware preset, **Then** the portal returns the target list with HTTP 200.

### Edge Cases

- What happens when the hardware flag holds an invalid value such as `maybe`? The portal reads it as false and writes one warning that names the variable.
- What happens when both flags are true? Warning: the free-form shell opens with the hardware preset and gives full command line access. Both unlocks apply.
- What happens when the hardware flag turns false after a preview? The start request refuses the stored preview with HTTP 403 and code `locked`.
- What happens when a browser sends commands with the hardware preset? The parser refuses the unknown field with HTTP 400 and code `bad_request`.
- What happens when a browser sends an unknown output format for the hardware preset? The parser refuses the format with HTTP 400.
- What happens in MSP scope? The same lock scope applies to the checker of each organization. The lock result does not depend on the organization.
- What happens when menu 309 runs with both flags false? The CLI runs, because the CLI sets the shell unlock in code, as before.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST run the hardware preset when the hardware flag is true and the shell flag is false.
- **FR-002**: The portal MUST keep every free-form shell locked when only the hardware flag is true.
- **FR-003**: The portal MUST refuse the hardware preset with HTTP 403 and code `locked` when both flags are false. The flag field MUST name `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
- **FR-004**: The portal MUST keep the shell flag as an unlock for the hardware preset and for every shell path.
- **FR-005**: The portal MUST set the lock scope only in the server-owned hardware preset branch. Browser fields MUST NOT set or widen the lock scope.
- **FR-006**: The portal MUST check the lock scope at preview, for each target, and at start admission.
- **FR-007**: The catalog payload MUST add `flags.hardware_inventory` with the keys `enabled` and `variable`. The keys `changes` and `shell` MUST keep their current form.
- **FR-008**: The settings reader MUST parse the hardware flag with the existing flag rules. An invalid value MUST give false and one warning that names the variable.
- **FR-009**: The Multi Site tab MUST show the hardware flag name when the hardware preset is locked and the shell flag is false.
- **FR-010**: The operator guide, the Web Portal wiki settings table, and `deploy/.env.example` MUST name the hardware flag, its scope, and the free-form shell warning.
- **FR-011**: The guardrail test for the shell lock documents MUST check the hardware flag refusal and the new steps.
- **FR-012**: Menu 309 MUST keep its current behavior and MUST need no setting.
- **FR-013**: Each hardware preset start MUST keep the WARNING audit event that shell starts write.
- **FR-014**: The change MUST NOT add a transport, a Mist REST call, a menu, or a change to the fixed command.
- **FR-015**: The changelog fragment MUST name issue #4939 and each change type that it uses.
- **FR-016**: The contract `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/portal.md` MUST receive a dated amendment for the new lock rule.

### Mist Cloud Transport Requirements

- The feature adds no mistapi REST method. The hardware preset reuses the existing `WebSocketBatchService` in `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` at line 865.
- The shell path keeps the owned shell client `ShellClient` in `src/mist/realtime/websocket_streams/live/transport/shell_client.py`. The feature changes no transport code.
- The shell path creates the owned shell client `ShellClient` at line 90 of `src/mist/realtime/websocket_streams/live/runners/shell/lifecycle/opening.py`. The SDK shell function `mistapi.device_utils.__tools.shell.create_shell_session` is not part of this change.
- The SDK contract pin for `_apitoken` stays unchanged (`src/mist/realtime/websocket_streams/live/transport/endpoint.py` line 45). No new owned transport starts.

### Key Entities *(include if feature involves data)*

- **Hardware flag**: The environment variable `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`. It defaults to false. It unlocks only the hardware preset.
- **Shell flag**: The environment variable `PORTAL_WS_ENABLE_SHELL`. It keeps its default of false. It unlocks the hardware preset and every free-form shell.
- **Lock scope**: The server-owned value `hardware_preset`. It is absent for every other request.
- **Lock refusal**: The response with code `locked`, HTTP status 403, the standard message, and the variable that unlocks the request.
- **Catalog flags**: The page payload key `flags`. It holds `changes`, `shell`, and `hardware_inventory`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every preview of the hardware preset with both flags false returns HTTP 403, code `locked`, and the hardware flag name. Tests T002, T004, and T005 check this.
- **SC-002**: Every free-form shell request returns HTTP 403 when only the hardware flag is true. Tests T002, T003, and T004 check this.
- **SC-003**: The hardware preset returns its target list when only the hardware flag is true. Tests T002 and T005 check this.
- **SC-004**: The guardrail test passes after the documents change and checks the hardware flag refusal. Test T008 checks this.
- **SC-005**: The Multi Site tab shows the hardware flag name when the action is locked. Test T007 checks this.

## Assumptions

- The owner chooses option 1 before any code starts.
- The portal keeps no user login. `PORTAL_ALLOWED_IPS` stays the only network limit.
- The fixed command stays `show chassis hardware detail | display xml | no-more`.
- The owned shell transport does not change in this feature.
- The pinned mistapi release does not change in this feature.
- The portal reads the flags when it starts. An operator restarts the portal after each change.
- A preview expires after 300 seconds. A flag change inside that time refuses the start.

## Non-Goals

- Operator sign-in or two-factor authentication. Issue #4936 tracks that work.
- A general flag for every fixed-command preset. The change adds a flag for the one preset that exists.
- Any change to the free-form shell behavior or to the shell flag rule.
- Any change to menu 309 or to its settings.
- Any change to the fixed command or to the output formats.
- Any edit to `CHANGELOG.md` or to the constitution.
