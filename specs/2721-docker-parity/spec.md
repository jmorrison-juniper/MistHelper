# Feature Specification: Docker deployment parity statement

**Feature Branch**: `docs/2721-docker-parity`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2721: Document Docker deployment parity.

## Scope decision

This feature does not make Docker a supported deployment method. Docker was not
installed on the validation host, so no Docker runtime test ran. The feature
extends `documentation\container-deployment.md` with an honest parity statement
that separates verified facts from file-based analysis.

## Verified facts

- `podman --version` returned `podman version 6.0.2`.
- `docker --version` failed because no `docker` binary existed on `PATH`.
- `podman ps` showed `misthelper-app`, `misthelper-arangodb`, and
  `misthelper-redis` running and healthy.
- `scripts\compose.ps1` uses `podman_compose` and `podman inspect`.
- `deploy\misthelper.container` is a Podman Quadlet unit.
- `deploy\misthelper.service` runs Python on the host without a container.

## Analysis

- `compose.yml` defines service names, published ports, volumes, health checks,
  dependencies, and the shared network for a Compose provider.
- The application uses `misthelper-arangodb` and `misthelper-redis` as service
  names on `misthelper-network`.
- `Containerfile` and `Dockerfile` both define the non-root user, `/app/data`,
  exposed ports, and an image health check.
- A Docker host must still prove DNS, health checks, data folder writes, and
  `--no-deps` behavior before this repository publishes Docker commands.

## User Scenarios & Testing

### User Story 1 - Read the Docker status (Priority: P1)

A junior network engineer can see that Podman is supported and Docker is not
verified here.

**Why this priority**: A false Docker support claim can cause a production
outage.

**Independent Test**: Read `documentation\container-deployment.md` and confirm
that the Docker section separates verified facts from analysis.

**Acceptance Scenarios**:

1. **Given** the operator reads the Docker section, **When** Docker is absent on
   this host, **Then** the document does not claim a Docker start was tested.
2. **Given** the operator needs production deployment, **When** they read the
   Docker section, **Then** the document directs them to Podman.

### User Story 2 - Find the parity differences (Priority: P1)

An engineer can see each known parity difference and the file that supports it.

**Why this priority**: A parity list prevents an engineer from assuming equal
runtime behavior.

**Independent Test**: Read the parity table and confirm that it names the
Compose, health check, helper script, and systemd differences.

**Acceptance Scenarios**:

1. **Given** the engineer reads the parity table, **When** they compare runtimes,
   **Then** they can identify each untested Docker area.

### User Story 3 - Run future Docker verification (Priority: P2)

A future engineer can run a bounded Docker test plan without editing the
Podman workflow.

**Why this priority**: Docker support needs evidence before it reaches
operators.

**Independent Test**: Read the future verification list and confirm that it
covers Docker Compose, DNS, health, data writes, and `--no-deps`.

**Acceptance Scenarios**:

1. **Given** Docker is installed, **When** an engineer follows the list, **Then**
   they can record which Docker claims are verified.

### Edge Cases

- If Docker stays absent, the document must continue to call Docker status
  analysis only.
- If Docker passes some checks later, a later change must update only the
  proven rows.
- If Docker fails a check, the document must state the failure rather than hide
  it.

## Requirements

### Functional Requirements

- **FR-001**: The document MUST state that Docker was not installed on the
  validation host.
- **FR-002**: The document MUST state that Docker deployment is not verified by
  this change.
- **FR-003**: The document MUST list each parity area with a status and a
  parity statement.
- **FR-004**: The document MUST name the files used for analysis.
- **FR-005**: The document MUST include a future Docker verification list.
- **FR-006**: The change MUST not edit generated API documentation.
- **FR-007**: The change MUST not modify the Podman workflow.

### Key Entities

- **Parity statement**: The documentation section that separates verified facts
  from analysis.
- **Compose stack**: The services, ports, volumes, health checks, and network in
  `compose.yml`.
- **Docker verification list**: The checks a future engineer must run before
  Docker commands reach operators.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Docker section uses the word `analysis` for every Docker claim
  that no runtime test proved.
- **SC-002**: The Docker section names every required source file from issue
  #2721.
- **SC-003**: The future verification list includes at least eight concrete
  Docker checks.
- **SC-004**: The STE linter scores each changed Markdown file at 80 or higher.

## Assumptions

- Podman remains the primary and documented runtime.
- Docker can become documented only after a future engineer tests it on a host
  with Docker installed.
- The existing compose file remains the source of truth for service names,
  ports, volumes, and internal DNS.
