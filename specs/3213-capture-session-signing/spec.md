# Feature Specification: Stable capture session signing

**Feature Branch**: `jmorrison-juniper-capture-session-signing-key`

**Created**: 2026-10-02

**Status**: Approved for a bounded local repair

**Input**: Part of issue [#3213](https://github.com/jmorrison-juniper/MistHelper/issues/3213) and the parent's isolated repair assignment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure a stable signing key (Priority: P1)

An operator finds the supported signing variable in the deployment template.
The operator generates a private key and keeps the same value across portal restarts.

**Why this priority**: A new signing key invalidates every existing signed session cookie.

**Independent Test**: Check the template and the main Compose service as two separate deployment inputs.

**Acceptance Scenarios**:

1. **Given** the deployment template, **When** the operator reads it, **Then** it names an optional, commented, blank `CAPTURE_SECRET_KEY`.
2. **Given** a key in `.env`, **When** Compose starts `misthelper`, **Then** `env_file` forwards the value without an `environment` override.
3. **Given** the operator instructions, **When** the operator follows them, **Then** the instructions generate a private key without a shared example credential.

### User Story 2 - Keep the signed cookie valid (Priority: P1)

An operator's browser sends the same signed cookie to a new application instance.
The configured signing key remains unchanged.

**Why this priority**: This is the exact signed-session acceptance criterion of issue #3213.

**Independent Test**: Use the actual configuration, application factory, Flask client, sign-in route, and session serializer.

**Acceptance Scenarios**:

1. **Given** the same configured key, **When** a second application receives the original cookie, **Then** it reads the original signed session.
2. **Given** retained server-side authentication state, **When** that browser opens the organization page, **Then** the actual session guard permits access.
3. **Given** a changed key, **When** the same cookie and form token return, **Then** the application refuses the signed session and the form.
4. **Given** a fresh worker registry, **When** the same-key cookie returns, **Then** the cookie remains valid but authenticated access returns `401`.

### User Story 3 - Preserve development and credential safety (Priority: P2)

A developer starts the portal without a configured key.
The portal keeps its explicit warning and generates a new development key.

**Why this priority**: The repair must not change the supported development behavior or expose credentials.

**Independent Test**: Check missing, empty, and whitespace values, application warnings, response surfaces, and decoded cookies.

**Acceptance Scenarios**:

1. **Given** an unset or blank key, **When** the portal starts twice, **Then** each start generates a different key and names only `CAPTURE_SECRET_KEY` in its warning.
2. **Given** synthetic credentials, **When** sign-in succeeds or fails, **Then** logs, responses, HTML, and decoded cookies contain no credential value.
3. **Given** a browser without authentication, **When** it reads the sign-in page, **Then** its cookies contain no signing key or synthetic credential.

### Edge Cases

- A key with surrounding whitespace uses the existing stripped value.
- A valid signed cookie cannot replace a missing cloud session record.
- A valid signed cookie cannot replace the matching `browser_id` cookie.
- A missing or unreadable deployment input fails the deployment contract.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Add the optional blank setting to `deploy/.env.example`.
- **FR-002**: Document safe generation, private storage, Compose forwarding, and key replacement consequences.
- **FR-003**: Prove actual signed cookie and form-token behavior across independent application instances.
- **FR-004**: State the separate limit of the in-memory authentication registry.
- **FR-005**: Keep production source, Compose settings, access rules, cookie rules, and the multi-site write gate unchanged.
- **FR-006**: Use only synthetic credentials and owned test state. No test may reach a production store or Mist operation.
- **FR-007**: Count checked deployment inputs and restart decisions. Prove the unchanged template fails the new contract.

### Key Entities

- **Signing key**: The private environment value that validates the signed browser session.
- **Signed session**: The Flask cookie with safe session fields, not a cloud credential.
- **Authentication record**: The live cloud session reference in the process-local `SessionRegistry`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The deployment contract checks both required inputs and rejects a template without the signing variable.
- **SC-002**: The same-key cookie survives application recreation. A changed key rejects the same control cookie.
- **SC-003**: The registry-loss control reports valid cookie contents and refused authenticated access separately.
- **SC-004**: Missing, empty, and whitespace key cases retain the warning and random development behavior.
- **SC-005**: All owned tests pass without a live service. No production source file changes.

## Assumptions

- The existing configuration and signing implementation already support stable keys.
- Compose already forwards `.env` to the `misthelper` service.
- A real worker restart clears the current in-memory authentication registry.
- This repair does not add persistent authentication or promise uninterrupted authenticated access after a worker restart.
- The parent confirmed every local reservation. The issue claim reserves `documentation/upgrade_capture_portal.md`.
- The full sign-in continuity goal remains outside this deployment-guidance repair.
- [The authentication issue](https://github.com/jmorrison-juniper/MistHelper/issues/3714) records the separate registry-loss requirement.
- Publication waits for position 37 and the parent's explicit full verified-main SHA grant.
