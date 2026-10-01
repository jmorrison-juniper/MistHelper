# Feature Specification: SSH database settings

**Feature Branch**: `jmorrison-juniper-ssh-database-settings`

**Created**: 2026-10-01

**Status**: Implemented locally. Protected delivery awaits the parent grant.

**Input**: Repair [issue #3313](https://github.com/jmorrison-juniper/MistHelper/issues/3313).

## User Scenarios & Testing

### User Story 1 - Keep the database copy (Priority: P1)

A NOC engineer starts an SSH session and exports Mist data.
The session needs the database settings that the container process already holds.

**Why this priority**: The current session writes the CSV file but loses every database copy.

**Independent Test**: Run the actual writer, start a fresh shell, and build the actual database configuration.

**Acceptance Scenarios**:

1. Given seven database settings, when the session reads its configuration file, then all seven settings reach the application.
2. Given complete settings, when the actual export pipeline runs, then the selected database receives every fixture record.
3. Given a missing required credential, when the export runs, then the evidence names the missing setting and reports no database success.

### User Story 2 - Protect the credentials (Priority: P1)

The configuration file now contains the Mist API token and two database passwords.
Only the session owner can read this file.

**Why this priority**: A readable password can expose the database to another account.

**Independent Test**: Inspect the actual file, its owner, its mode, and both output streams of the writer.

**Acceptance Scenarios**:

1. Given complete settings, when the writer finishes, then the file has mode `0400` and the requested valid owner.
2. Given unrelated secrets, when the writer runs, then neither the file nor its reports contain those secrets.
3. Given configuration values, when the writer reports its result, then it prints names and a count only.

### User Story 3 - Replace stale settings (Priority: P2)

The container restarts after an operator changes or removes a setting.
The next session must not retain a setting from the earlier start.

**Why this priority**: A stale setting can select the wrong database or prevent authentication.

**Independent Test**: Run the writer twice against the same target and read the result through a fresh shell.

**Acceptance Scenarios**:

1. Given changed settings, when the writer runs again, then the new file contains only the current settings.
2. Given an empty or absent setting, when the writer runs again, then the setting is absent from the new session.
3. Given quotes or shell characters, when the session reads the file, then the characters remain data and execute no command.

### Edge Cases

- Each database setting can contain spaces, quotes, dollar signs, newlines, or Unicode characters.
- An empty value and an absent value must both remain absent from the session file.
- A missing required database credential must still prevent database configuration.
- A missing Bash capability or unreadable test input must fail the new contracts, not report success.

## Requirements

### Functional Requirements

- **FR-001**: Add `ARANGO_HOST`, `ARANGO_DATABASE`, `ARANGO_USERNAME`, `ARANGO_ROOT_PASSWORD`, `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`.
- **FR-002**: Preserve the existing eleven Mist and proxy names and the explicit allowlist.
- **FR-003**: Preserve shell quoting, atomic replacement, empty-value removal, and stale-value removal.
- **FR-004**: Preserve mode `0400` and the requested valid owner.
- **FR-005**: Print no configuration value in a report or an error.
- **FR-006**: State that the session file contains the API token and two database passwords.
- **FR-007**: Prove a fresh-shell export through the actual exporter and router with owned fixture backends.
- **FR-008**: Prove an actual isolated SSH transport when the local capability permits it.
- **FR-009**: Change no output-format behavior, database schema, primary key strategy, dependency manifest, or shared instruction.

### Key Entities

- **Session configuration**: An owner-readable file with eighteen permitted names.
- **Database settings**: Seven values that the actual database configuration reads from the session environment.
- **Export evidence**: Fixture records, the CSV copy, and a database result with the correct record count.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All seven database names pass every value case without a skipped case.
- **SC-002**: The name-only report contains the exact permitted names and their count.
- **SC-003**: The file has mode `0400` and the requested valid owner after every replacement.
- **SC-004**: No unrelated secret reaches the file or either report stream.
- **SC-005**: An owned export stores two fixture records and reports `failed=0`.
- **SC-006**: The original missing-setting case fails before the repair and succeeds after the repair.

## Assumptions

- The container already supplies valid database settings.
- The existing session reader exports the quoted assignments before it starts MistHelper.
- Fixture backends prove configuration and routing. They do not prove a production database write.
- A local SSH fixture proves the SSH transport. It does not prove the deployed OpenSSH service on port `2200`.
- The parent must grant an exact verified `main` SHA before any push or pull request creation.
- The protected merge and exact-main local checks remain separate delivery requirements.

## Specification Quality

The requirements define one concern and measurable outcomes.
Each scenario has a local test plan.
No unresolved scope decision remains.
The app owns the branch, so this workflow uses feature-only files instead of the legacy branch and shared-state hooks.
