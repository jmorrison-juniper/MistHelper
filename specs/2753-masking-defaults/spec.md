# Feature Specification: Masking Default Audit

**Feature Branch**: `2753-masking-defaults`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Audit code defaults that mask missing inputs for issue #2753."

## User Scenarios & Testing

### User Story 1 - Refuse a missing upgrade input (Priority: P1)

An operator starts a destructive upgrade only when the request names the device list, the firmware version, and the strategy.

**Why this priority**: A missing upgrade input can send destructive work to the wrong target or image.

**Independent Test**: Run `python -m pytest tests\unit\upgrade_portal\test_upgrade_start_input_validator.py -v`.

**Acceptance Scenarios**:

1. **Given** an upgrade start request with no JSON body, **When** validation runs, **Then** the result names `json_body` as missing.
2. **Given** an upgrade start request with no `device_ids`, **When** validation runs, **Then** the result names `device_ids` as missing.
3. **Given** an upgrade start request with no `firmware_version`, **When** validation runs, **Then** the result names `firmware_version` as missing.
4. **Given** an upgrade start request with no `strategy`, **When** validation runs, **Then** the result names `strategy` as missing.

### Edge Cases

- If a device identifier is blank, the validator returns a visible `device_ids` refusal.
- If a strategy is not `serial` or `parallel`, the validator returns a visible `strategy` refusal.
- If `rollback_enabled` is absent, the route keeps `False` because an unapproved rollback is unsafe.

## Requirements

### Functional Requirements

- **FR-001**: The upgrade start route MUST NOT substitute an empty body for a missing JSON body.
- **FR-002**: The upgrade start route MUST NOT substitute an empty list for a missing device list.
- **FR-003**: The upgrade start route MUST NOT substitute an empty string for a missing firmware version.
- **FR-004**: The upgrade start route MUST NOT substitute `serial` for a missing strategy.
- **FR-005**: Each missing input MUST produce a log line that names the missing field.

### Key Entities

- **Upgrade start input**: The device list, firmware version, strategy, and rollback choice for one destructive run.
- **Upgrade input failure**: The field name and message that explain why the route refused the request.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The five tests of the validator pass.
- **SC-002**: Four unsafe defaults no longer exist on the start-upgrade path.
- **SC-003**: The log output names each missing destructive input.

## Assumptions

- The audit uses the visible priority inventory in `specs\1924-failure-evidence\inventory.md`.
- One route for destructive work now has a repair. This change defers the remaining priority candidates.
- The pull request does not close issue #2753.

## Triage Table

| Category | Candidate count | Repaired | Kept | Deferred |
| - | -: | -: | -: | -: |
| Credential or token | 31 | 0 | 3 | 31 |
| Upgrade input | 103 | 4 | 1 | 99 |
| Organization or site identifier | 102 | 0 | 0 | 102 |
| Priority union | 235 | 4 | 4 | 231 |

### Repaired defaults

| File | Default | Category | Result |
| - | - | - | - |
| `src\upgrade_portal\app\routes\upgrade.py` | `request.get_json() or {}` | Upgrade input | Missing JSON body returns `json_body is required for upgrade start`. |
| `src\upgrade_portal\app\routes\upgrade.py` | `body.get("device_ids", [])` | Upgrade input | Missing target list returns `device_ids is required for upgrade start`. |
| `src\upgrade_portal\app\routes\upgrade.py` | `body.get("firmware_version", "")` | Upgrade input | Missing firmware version returns `firmware_version is required for upgrade start`. |
| `src\upgrade_portal\app\routes\upgrade.py` | `body.get("strategy", "serial")` | Upgrade input | Missing strategy returns `strategy is required for upgrade start`. |

### Deliberately kept defaults

| File | Default | Reason |
| - | - | - |
| `src\upgrade_portal\app\routes\upgrade.py` | `body.get("rollback_enabled", False)` | The absent rollback choice must not enable rollback. |
| `web_portal\app.py` | `WEBHOOK_ENABLED` defaults to `true` | Existing code rejects every webhook with code 503 when the secret is absent. |
| `web_portal\app.py` | `WEBHOOK_SECRET` defaults to an empty string | Existing code fails closed and logs the missing secret. |
| `src\upgrade_portal\runtime\identity.py` | token presence reads default to empty strings | Existing code returns presence only and never reads or logs the token value. |

### Deferred defaults

| Follow-up issue | Category | Count | Reason |
| - | - | -: | - |
| #2861 | Credential or token | 31 | Credential review needs separate redaction checks. |
| #2862 | Upgrade input | 99 | Destructive path review needs smaller pull requests. |
| #2863 | Organization or site identifier | 102 | Identifier review needs route-by-route tests. |
