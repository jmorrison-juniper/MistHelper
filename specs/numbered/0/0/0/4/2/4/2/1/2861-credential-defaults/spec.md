# Feature Specification: Credential default audit

**Feature Branch**: `chore/2861-credential-defaults`

**Created**: 2026-11-26

**Status**: Complete. Three human decisions block three tasks. See D-5, D-6, and D-7.

**Input**: Issue #2861, "chore: audit credential defaults that mask missing inputs."

## Scope

Issue #2861 owns credential, token, password, secret, username, authentication flag, and session-token defaults. This record covers the 64 baseline candidates and the container credential defaults outside Python. The owner keeps the issue open until every candidate is repaired.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop on a missing database credential (Priority: P1)

An operator starts a tool or portal without a database credential. The run stops and names the missing field. No default database account is used.

**Why this priority**: A default account can read or write the wrong database.

**Independent Test**: Construct `DatabaseConfig` with a sample credential value. Load portal settings in container runtime without `ARANGO_USERNAME`.

**Acceptance Scenarios**:

1. **Given** a `DatabaseConfig` built with no credential, **When** its fields are read, **Then** no credential field holds a non-empty default.
2. **Given** a sample credential value, **When** `DatabaseConfig` is constructed, **Then** construction is rejected and the message names the field only.
3. **Given** container runtime and no `ARANGO_USERNAME`, **When** portal settings load, **Then** loading is refused and the message names the variable.
4. **Given** local runtime and no `ARANGO_USERNAME`, **When** portal settings load, **Then** the image account name applies and a log line names the variable.

### User Story 2 - Prompt or refuse for a missing Mist token (Priority: P1)

An operator starts the MistHelper command line without a Mist token. In a terminal, MistHelper asks for the token without echo. Without a terminal, MistHelper refuses and never prompts.

**Why this priority**: A missing token must not pass as a usable session.

**Independent Test**: Run credential preflight with terminal and non-terminal fakes. Count prompts and check the exit status.

**Acceptance Scenarios**:

1. **Given** both standard streams are terminals and no token variable, **When** preflight runs, **Then** one hidden prompt occurs and the token stays in process memory.
2. **Given** either stream is not a terminal, **When** preflight runs, **Then** no prompt occurs and the run exits with status 1.
3. **Given** the prompt reads end of file or receives an interrupt, **When** the prompt ends, **Then** the run exits with status 1 and logs no input.

### User Story 3 - Reject conflicting Mist token variables (Priority: P1)

An operator sets both `MIST_API_TOKEN` and `MIST_APITOKEN`. Equal values pass during migration. Different values stop the run before any Mist call. The integration test helper follows the same rule.

**Why this priority**: A conflict can select the wrong Mist account.

**Independent Test**: Run the existing conflict tests and the new helper test.

**Acceptance Scenarios**:

1. **Given** different non-empty values, **When** preflight runs, **Then** the run is refused before organization lookup.
2. **Given** equal non-empty values, **When** preflight runs, **Then** the canonical value passes.
3. **Given** different values in the integration environment, **When** the helper runs, **Then** the test session fails and names both variables.

### User Story 4 - Keep a ratchet on credential defaults (Priority: P2)

A maintainer changes Python code. The guard prints the scan count. The guard fails on a new candidate, on a stale baseline entry, or on a zero-file scan.

**Why this priority**: The ratchet stops new defaults while the campaign runs.

**Independent Test**: Run the guard on the repository and on two fixtures.

**Acceptance Scenarios**:

1. **Given** the repository, **When** the guard runs, **Then** it prints the stable count line and passes with the baseline.
2. **Given** zero scanned files, **When** the guard runs, **Then** it fails with `files=0`.
3. **Given** a fixture with an environment default and a dataclass credential default, **When** the scanner runs, **Then** it reports both.

### User Story 5 - Keep accepted defaults unchanged (Priority: P3)

A maintainer reviews display and intentional defaults. Each accepted entry keeps its reason in the baseline. No behavior changes for these entries.

**Acceptance Scenarios**:

1. **Given** an accepted entry, **When** the guard runs, **Then** the entry has a non-empty reason.

### Edge Cases

- A credential value with only whitespace counts as missing.
- A sample credential value in standalone mode is rejected. Standalone mode allows empty credentials.
- `MIST_API_TOKEN` and `MIST_APITOKEN` contain only delimiters. The value counts as absent.
- The prompt receives end of file during the first read. The run is refused.
- The baseline file is missing or invalid JSON. The guard fails.
- A candidate line moves but keeps its fingerprint. The guard keeps the entry.
- A new `mistapi.APISession` call without `apitoken` appears outside the allowlist. The guard fails.
- The compose file keeps a literal fallback password until D-7 is decided.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `DatabaseConfig` dataclass fields must hold no non-empty credential default.
- **FR-002**: `DatabaseConfig` must reject a sample credential value in any credential field.
- **FR-003**: Standalone database mode must keep local host and port defaults and empty credentials.
- **FR-004**: The upgrade portal must require `ARANGO_USERNAME` in container runtime.
- **FR-005**: Outside container runtime, the portal may use its image account name and must log the variable name.
- **FR-006**: MistHelper must prompt for a missing Mist token only when stdin and stdout are terminals.
- **FR-007**: MistHelper must refuse with status 1 when no terminal exists or input ends.
- **FR-008**: A prompted token must stay in process memory and must not be echoed, logged, stored, or exported.
- **FR-009**: MistHelper must reject different non-empty `MIST_API_TOKEN` and `MIST_APITOKEN` values before any Mist call.
- **FR-010**: MistHelper must accept equal values during migration.
- **FR-011**: The integration test helper must read `MIST_API_TOKEN` first and must fail on a conflict.
- **FR-012**: Session-scoped Mist code must not use a process token when the session token is missing.
- **FR-013**: `MistSessionFactory` must apply decision D-6 to its configured-token fallback.
- **FR-014**: The guard must print the stable count line and must prove both failure modes.
- **FR-015**: The baseline must key each entry by path, scope, kind, and fingerprint. Each batch must reduce open entries.
- **FR-016**: Exception handlers, logging redaction, and accepted display or test defaults must not change.
- **FR-017**: A `mistapi.APISession` call without `apitoken` must stay inside a reviewed allowlist.
- **FR-018**: Container credential defaults outside Python must follow decision D-7.

### Key Entities *(include if feature involves data)*

- **Candidate**: A Python expression that supplies a default for a credential-bearing name.
- **Baseline entry**: A reviewed candidate with a group, a fingerprint, and a reason.
- **Credential source**: An ordered input, such as an environment variable, a prompt, a cache, Vault, or a configured setting.
- **Reject**: The code does not accept an input value. **Refuse**: The run stops with status 1.

## Success Criteria *(mandatory)*

- **SC-001**: The guard prints the stable count line on the repository. The line reports zero parse failures.
- **SC-002**: After batch 1, no open baseline entry remains for the three database fields or the portal username.
- **SC-003**: All 19 planned tests pass in the changed test modules.
- **SC-004**: Tests show no credential value in captured logs or messages.
- **SC-005**: Each changed file passes its applicable local gate from the local gates table.
- **SC-006**: Each changed file keeps the same number of `except` clauses.

## Assumptions

- Owner decisions 1 to 5, recorded in issue comments dated 2026-10-21, bind this record.
- The target runtime is Python 3.15, from `pyproject.toml:23`.
- The `mistapi` pin is `mistapi==0.64.1` in `requirements.txt:129`. `pyproject.toml:29` allows `>=0.64.1,<0.65`.
- Windows 11 is the first target. Commands use Windows paths. macOS and Linux must still run.
- No batch in this record edits `web_portal/app.py`. Open PR #4208 does not block this record.

## Out of Scope

- Generic code defaults (#2753) and organization or site identifier defaults (#2863).
- Upgrade input defaults (#2862, closed).
- The analyzer connection-error candidate in `mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py`. Coordinate with the owner and #4748 first.
- The output-safety change for `src/mist/resources/device/_utility_commands_action.py:371`. A separate issue owns it.
- The keyword defect at `src/interfaces/visualization/maps/maps_manager.py:2689`. A separate issue owns it.
- Live Mist, Vault, Redis, Arango, or SMTP tests and any live credential.
- Changes to the `mistapi` SDK.
- Branch protection, queue settings, and merge actions.

## Clarifications

- **Q1**: Must a missing credential prompt? **A1**: Interactive prompt allowed. Unattended runs fail without prompting. Source: owner decision 1, 2026-10-21T05:54:19Z.
- **Q2**: How do conflicting token variables behave? **A2**: Reject conflicts. Accept equal values during migration. Remove the legacy path later. Source: owner decision 2 and its correction, 2026-10-21T05:55:25Z.
- **Q3**: What applies to standalone database credentials? **A3**: Keep local defaults for standalone mode. Reject known sample credential values. Source: owner decision 3, 2026-10-21T05:56:49Z.
- **Q4**: How does the baseline change? **A4**: Baseline all 64 reviewed candidates. Reduce the baseline in each repair batch. Source: owner decision 4, 2026-10-21T05:57:31Z.
- **Q5**: When does the issue close? **A5**: After every candidate is repaired and full validation passes. Source: owner decision 5, 2026-10-21T05:58:02Z.
- **Q6**: What applies to the configured-token fallback in `MistSessionFactory`? **A6**: No owner answer exists. Decision D-6 is a human decision.
