# Feature Specification: Distinct Gunicorn control sockets

**Feature Branch**: `jmorrison-juniper-gunicorn-control-sockets`

**Created**: 2026-10-01

**Status**: Specified

**Input**: [Issue #3370](https://github.com/jmorrison-juniper/MistHelper/issues/3370).

## User Scenarios & Testing

### User Story 1 - Start both portals with control access (Priority: P1)

The operator starts the container. Both portals retain their own control access.

**Why this priority**: A shared control socket can direct a command to the wrong portal.

**Independent Test**: Start two real Gunicorn masters under one account with temporary applications and the parsed startup arguments.

**Acceptance Scenarios**:

1. Given two portal masters, when both start, each control socket identifies its own master.
2. Given both running portals, when either master receives SIGHUP, both control sockets retain their correct master identity.
3. Given a clean start and reload, when the test reads both logs, neither log reports a control socket collision.

### Edge Cases

- An absent startup script must fail the contract.
- An absent socket option, a repeated option, or a shared path must fail the contract.
- A comment that names a socket must not substitute for an active startup argument.
- A third master or a missing master must fail the startup command count.
- A missing Unix process or socket capability must report a failure, not a passing skip.
- Each test must stop its own masters and remove its temporary sockets.

## Requirements

### Functional Requirements

- **FR-001**: The web portal must use `/home/misthelper/.gunicorn/portal.ctl`.
- **FR-002**: The capture portal must use `/home/misthelper/.gunicorn/capture.ctl`.
- **FR-003**: Both masters must retain control access. The repair must not disable the control sockets.
- **FR-004**: Startup must preserve the ports, workers, threads, timeouts, environment, application entrypoints, and shutdown behavior.
- **FR-005**: The contract must parse active startup arguments and report the number of commands it checks.
- **FR-006**: Real process tests must verify separate control identities before and after SIGHUP in both reload orders.
- **FR-007**: Tests must retain their logs and verify zero control server errors and zero address collisions.
- **FR-008**: Tests must use temporary applications and owned processes. Tests must not contact Mist, production portals, or stores.

### Key Entities

- The web portal master serves `wsgi:app`.
- The capture portal master serves `wsgi_capture:app`.
- A control socket identifies one master.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The contract checks exactly two startup commands and two distinct explicit socket paths.
- **SC-002**: Each real control response identifies the expected master after every tested reload.
- **SC-003**: Both portal responses identify the same user account and the expected master.
- **SC-004**: Each completed test leaves zero owned masters or control sockets.
- **SC-005**: Both error logs contain zero `Control server error` or address collision messages.

## Assumptions

- The current runtime requirements supply Gunicorn 26.
- Gunicorn creates each socket directory and retains its default socket permissions.
- The repair authorizes isolated proof only. Production deployment requires separate approval.
- Publication requires the parent's explicit verified-main release after issue #3215.
