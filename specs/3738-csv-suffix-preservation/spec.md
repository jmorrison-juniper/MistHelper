# Feature Specification: CSV suffix preservation

**Feature Branch**: `jmorrison-juniper-csv-suffix-preservation`

**Created**: 2026-10-03

**Status**: Locally verified. Publication remains unauthorized.

**Issue**: [#3738](https://github.com/jmorrison-juniper/MistHelper/issues/3738)

**Input**: Preserve the advertised CSV filename without changing another output backend.

## User Scenarios & Testing

### User Story 1 - Find the advertised client file (Priority: P1)

An engineer selects menu 64 and selects a site. The operation writes the client
and session data to `SiteWiFiClients.CSV`. The filename agrees with the menu
title and the completion notice.

**Why this priority**: The current writer creates `SiteWiFiClients.CSV.csv`.
The file exists, but its name differs from the advertised name.

**Independent Test**: Execute the actual menu handler with controlled SDK
responses and the real local CSV writer. Count every final write.

**Acceptance Scenarios**:

1. **Given** one client and one matching session, **when** menu 64 runs,
   **then** one `SiteWiFiClients.CSV` file contains the complete merged record.
2. **Given** that run, **when** the engineer reads its notice and menu title,
   **then** both name the file that exists.
3. **Given** that run, **when** the output scanner checks the temporary directory,
   **then** it reports `SiteWiFiClients.CSV`, not `SiteList.csv`.

### User Story 2 - Preserve supplied filenames (Priority: P2)

An engineer exports rows with an existing CSV suffix. The writer preserves the
stem, directory, Unicode content, and letter case.

**Why this priority**: Other CSV callers use the same writer.

**Independent Test**: Write and read real CSV files for each filename case.

**Acceptance Scenarios**:

1. **Given** any ASCII letter case of `.csv`, **when** the writer runs,
   **then** it preserves the supplied filename.
2. **Given** a name without a final CSV suffix, **when** the writer runs,
   **then** it appends exactly one lowercase `.csv`.
3. **Given** an existing output file, **when** the writer runs again,
   **then** it uses the same file and preserves normal truncation behavior.

### User Story 3 - Preserve backend contracts (Priority: P3)

An engineer selects SQLite or a configured external backend. Filename recognition
does not change the table name, endpoint metadata, data, or routing behavior.

**Why this priority**: A table-name change would require a separate migration decision.

**Independent Test**: Use private counted backend fakes and a temporary SQLite
database. Compare the received names and rows with the current behavior.

**Acceptance Scenarios**:

1. **Given** a SQLite target with uppercase `.CSV`, **when** the writer runs,
   **then** the existing case-sensitive table-name rule remains unchanged.
2. **Given** a CSV target, **when** the external router receives the data,
   **then** it receives the original endpoint metadata and data once.
3. **Given** an empty input or a write failure, **when** the writer runs,
   **then** its existing refusal, error, and logging behavior remains unchanged.

### Edge Cases

- A directory name ends with `.csv`, but the filename has no suffix.
- A filename contains an internal `.csv` segment or a different final suffix.
- A Unicode stem precedes an ASCII CSV suffix.
- A supplied field order differs from the normal sorted field order.
- A record contains a comma, a quote, a newline, or a list.
- A non-string filename reaches the existing error boundary.
- A repeat write replaces a longer file with a shorter file.

## Requirements

### Functional Requirements

- **FR-001**: Recognize a final ASCII `.csv` suffix in every letter case.
- **FR-002**: Preserve the complete supplied filename when that suffix exists.
- **FR-003**: Append one lowercase `.csv` when that suffix does not exist.
- **FR-004**: Preserve the existing path policy, data processing, and column order.
- **FR-005**: Preserve empty-input refusal and write-error behavior.
- **FR-006**: Preserve SQLite table names and every non-CSV export method.
- **FR-007**: Preserve endpoint metadata, primary keys, schemas, and router calls.
- **FR-008**: Keep `FilePathUtils`, `WifiClientsExporter`, and menu titles unchanged.
- **FR-009**: Verify the data browser and output scanner without changing them.
- **FR-010**: Do not rename or delete an existing user file.

### Key Entities

- **CSV filename**: The supplied stem, directory, and optional final suffix.
- **Export record**: The client data and session data already produced by the operation.
- **Endpoint metadata**: The existing API function name used for database routing.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The native run measures one handler, one site answer, and two SDK requests.
- **SC-002**: That run measures one final CSV write, one router write, and one complete merged record.
- **SC-003**: That run measures zero live HTTP requests and creates no `.CSV.csv` client file.
- **SC-004**: All filename cases pass actual write and read assertions.
- **SC-005**: The original case-sensitive decision fails the uppercase contract while lowercase and bare controls pass.

## Assumptions

The task authorizes a local validated commit only. Queue position 47 remains
unpublished. An explicit parent grant must name a full verified-main SHA before
publication. Remote checks, merge, and proof on the resulting main revision
belong to that later grant.

No new environment variable, dependency, API operation, UI control, or schema
belongs to this repair. The README and generated references remain read-only.
