# Feature Specification: mistapi signature mismatch repair

**Feature Branch**: `fix/2741-signature-mismatch`
**Created**: 2026-09-16
**Status**: Draft
**Input**: User description: "Repair issue #2741. Two MistHelper call sites use incompatible `mistapi` 0.64.0 signatures."

## User Scenarios & Testing

### User Story 1 - Create a CLI shell session (Priority: P1)

A NOC engineer starts the interactive CLI shell for a site device. MistHelper must call the installed SDK with the required body.

**Why this priority**: The shell session cannot start when the SDK raises `TypeError`.

**Independent Test**: A unit test patches the SDK call. The test fails if MistHelper omits the `body` argument.

**Acceptance Scenarios**:

1. **Given** a device and a successful shell response, **When** MistHelper creates the session, **Then** it passes `body={}`.
2. **Given** a malformed SDK call, **When** the SDK raises `TypeError`, **Then** MistHelper raises the error to the caller.

---

### User Story 2 - Reconcile a firmware run from running-version evidence (Priority: P1)

A NOC engineer reconciles a stopped upgrade run. The portal must read running firmware from the approved site statistics endpoint.

**Why this priority**: A broken read can push a caller toward stale configured firmware.

**Independent Test**: A unit test patches the installed `listSiteDevicesStats` signature. The test fails if `fields` is passed.

**Acceptance Scenarios**:

1. **Given** a stored run target, **When** the portal reads site statistics, **Then** it passes only supported SDK arguments.
2. **Given** a statistics row with `version` and `fwupdate`, **When** reconciliation reads it, **Then** the evidence row contains the running version.

## Evidence

- `createSiteDeviceShellSession(mist_session, site_id, device_id, body)` is the installed `mistapi` 0.64.0 signature.
- `documentation/api/utilities/POST_sites_site_id_devices_device_id_shell.md` documents the body schema `shell_node`.
- The schema defines one optional field, `node`, for HA cluster node selection.
- No `required` array exists in `components.schemas.shell_node`.
- `mistapi.device_utils.__tools.shell.create_shell_session` calls `createSiteDeviceShellSession(..., body={})`.
- `listSiteDevicesStats(mist_session, site_id, type=None, status=None, limit=None, page=None)` is the installed signature.
- The OpenAPI operation `GET /api/v1/sites/{site_id}/stats/devices` lists `type`, `status`, `limit`, and `page` only.

## Requirements

### Functional Requirements

- **FR-001**: MistHelper MUST pass the required shell session body to `createSiteDeviceShellSession`.
- **FR-002**: MistHelper MUST use `{}` as the shell body when the operator selects no HA node.
- **FR-003**: MistHelper MUST NOT catch `TypeError` from a malformed SDK signature as a network failure.
- **FR-004**: The upgrade portal MUST NOT pass `fields` to `listSiteDevicesStats`.
- **FR-005**: The upgrade portal MUST keep `gate.STATISTICS_FIELDS` as a client-side projection after the read.
- **FR-006**: The upgrade portal MUST preserve `running_version` and `fwupdate_status` in reconciliation evidence.
- **FR-007**: Tests MUST fail on the two broken call shapes and pass after the repair.

### Key Entities

- **Shell session request**: The SDK call that opens a WebSocket shell session for one site device.
- **Reconciliation evidence row**: The safe row that proves a firmware run no longer writes to a target.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The shell session unit test proves that `body={}` reaches the SDK.
- **SC-002**: The shell session unit test proves that a signature `TypeError` reaches the caller.
- **SC-003**: The reconciliation unit test proves that `fields` is absent from the site statistics call.
- **SC-004**: The reconciliation unit test proves that the evidence row contains the running firmware version.
- **SC-005**: The SDK compatibility guard passes without a known-failure entry for issue #2741.

## Repair Decisions

### Shell body

Use `body={}`. The OpenAPI `shell_node` schema contains only the optional `node` field. The installed SDK helper `create_shell_session` also passes `{}`.

### Site statistics fields

Drop the `fields` keyword from the cloud call. Keep `gate.STATISTICS_FIELDS` as the local projection after pagination.

This decision makes no extra API calls. It can increase response bytes, because the cloud returns the default site statistics row. The bounded cost is one paged site statistics read with `limit=1000` for reconciliation. No live token was used, so this plan estimates a worst case of one default statistics page per reconciliation request.

## Assumptions

- The operator selected no HA node, so the shell request needs no `node` value.
- The installed SDK version is `mistapi` 0.64.0.
- This repair makes no live Mist API request.
