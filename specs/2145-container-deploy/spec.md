# Feature Specification: Container deployment workflow

**Feature Branch**: `chore/2145-container-deploy`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2145: Automate and document the container deployment workflow.

## Scope decision

This feature implements the Podman-first deployment workflow that MistHelper supports today. The workflow uses `compose.yml` and `scripts\compose.ps1` as the automation path. It updates the quick start and run guides so an operator does not copy a bare `podman run` command for the supported stack.

## Deliberate exclusions

Docker-specific deployment parity is excluded. The repository instructions name Podman as the documented runtime. Issue #2721 tracks Docker DNS validation and Docker deployment text.

## User Scenarios & Testing

### User Story 1 - Start the supported stack (Priority: P1)

A junior network engineer starts the application, ArangoDB, and Redis with one helper command.

**Why this priority**: The helper command prevents provider selection errors on Windows.

**Independent Test**: Read the guides and start the stack with `scripts\compose.ps1 up -d`.

**Acceptance Scenarios**:

1. **Given** a repository checkout with `.env`, **When** the operator runs `scripts\compose.ps1 up -d`, **Then** the three required services start in the compose group.
2. **Given** a Windows host, **When** the operator reads the guide, **Then** the guide tells them not to run `podman compose up -d`.

### User Story 2 - Protect production data during cleanup (Priority: P1)

An engineer cleans a test container without removing the ArangoDB or Redis production volumes.

**Why this priority**: Those volumes hold every capture and every upgrade run.

**Independent Test**: Run the guardrail test that checks every cleanup code block.

**Acceptance Scenarios**:

1. **Given** a cleanup example, **When** the guardrail test reads it, **Then** the command targets only `misthelper-tmp-<issue|pr><number>-<slug>`.
2. **Given** the production volumes, **When** the guardrail test reads the docs, **Then** no cleanup block removes them.

### User Story 3 - Use a corporate root certificate (Priority: P2)

An operator behind a TLS-inspecting proxy starts the compose stack with the proxy root certificate mounted.

**Why this priority**: The container must keep certificate validation enabled.

**Independent Test**: Read the compose overlay and confirm it mounts the certificate into the application service.

**Acceptance Scenarios**:

1. **Given** `zscaler-root-ca.crt` exists, **When** the operator runs `scripts\compose.ps1 up-corporate-ca -d`, **Then** the helper merges the corporate CA overlay.

### Edge Cases

- If `zscaler-root-ca.crt` is absent, the helper stops before it starts the stack.
- If a document adds `podman volume prune` to a code block, the guardrail test fails.
- If a cleanup command targets a production volume, the guardrail test fails.
- If a service publishes a port in the ephemeral range, the guardrail test fails.

## Requirements

### Functional Requirements

- **FR-001**: The deployment guide MUST direct operators to `scripts\compose.ps1` for the supported stack.
- **FR-002**: The guides MUST not give a bare `podman run` command for the supported application stack.
- **FR-003**: The cleanup examples MUST remove only resources with the `misthelper-tmp-` prefix.
- **FR-004**: The cleanup examples MUST include container, volume, and network cleanup.
- **FR-005**: A guardrail test MUST prove that cleanup code blocks cannot remove `misthelper-arangodb-data` or `misthelper-redis-data`.
- **FR-006**: The corporate CA workflow MUST use compose automation and keep certificate validation enabled.

### Key Entities

- **Compose stack**: The application, ArangoDB, Redis, and optional Observium services in `compose.yml`.
- **Ephemeral resource**: A test container, volume, or network named `misthelper-tmp-<issue|pr><number>-<slug>`.
- **Production store volume**: The `misthelper-arangodb-data` and `misthelper-redis-data` volumes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The guardrail test reports no cleanup command that names a production store volume.
- **SC-002**: The guardrail test reports that each `podman volume rm` cleanup command uses `misthelper-tmp-`.
- **SC-003**: The deployment guide names every production port from `compose.yml` and keeps the ephemeral range free.
- **SC-004**: A local Podman build and compose start complete before the pull request opens.

## Assumptions

- Operators use Podman as the documented runtime on Windows.
- Docker parity needs separate validation before it becomes documented guidance.
- The existing `compose.yml` service names remain the source of truth for internal DNS.
