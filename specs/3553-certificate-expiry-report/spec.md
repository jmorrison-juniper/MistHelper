# Feature Specification: Certificate Expiry Report

**Feature Branch**: `feat/3553-certificate-expiry-report`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 272 certificate expiry report. Mist raises a certificate alert 30, 15, 7, 3, and 1 day before expiry for RadSec, SSO, and PSK portal certificates. No MistHelper operation lists every certificate with its days remaining, so an operator cannot plan a renewal across an organization. The metrics gateway already parses device certificate expiry, so a parser pattern exists. CertificateExpiry.csv: one row per certificate with scope (device, org device cert, NAC server cert, SSO IdP, PSK portal IdP, CA cert), owner name or device name, subject, issuer, not_after (UTC), days remaining, and a band (expired, 0-30, 31-90, more than 90). A console summary prints counts per band."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run certificate expiry report without prompts (Priority: P1)

A NOC operator runs menu 272 in test mode after the integration pull request wires the menu entry. This branch delivers the no-prompt handler, export contract, tests, and wiring manifest. The report gives one organization-wide list of certificates and the number of days remaining before each certificate expires.

**Why this priority**: This is the main value of the feature. Operators need one repeatable view of certificate renewal risk instead of manually checking multiple certificate locations.

**Independent Test**: Run the report handler with a unit fixture that replaces the menu dispatcher, Mist session, and exporter. Confirm that it completes without interactive input and requests `CertificateExpiry.csv`. The integration pull request must prove the full `--test` menu path after it registers menu 272.

**Acceptance Scenarios**:

1. **Given** test mode is active and menu 272 is wired by the integration pull request, **When** the operator runs menu 272, **Then** the operation completes without prompting for input.
2. **Given** certificate data exists, **When** the operation finishes, **Then** `data/CertificateExpiry.csv` contains one row for each certificate found.
3. **Given** a certificate row is written, **When** the operator opens the report, **Then** the row includes scope, owner name or device name, subject, issuer, not_after in UTC, days remaining, band, and any note needed to explain parse status.

---

### User Story 2 - Compare certificate renewal urgency across scopes (Priority: P2)

A NOC operator reviews certificate rows from device, organization, NAC, SSO, PSK portal, and CA certificate sources in one file. The operator can sort by days remaining and plan renewals before Mist alert thresholds are reached.

**Why this priority**: The report is useful only when every relevant certificate source maps to the same columns and urgency bands.

**Independent Test**: Use test data with certificates in each supported scope. Confirm that each row uses the same column set and the expected urgency band.

**Acceptance Scenarios**:

1. **Given** a certificate is already expired, **When** the report is created, **Then** the band is `expired`.
2. **Given** a certificate expires in 0 through 30 days, **When** the report is created, **Then** the band is `0-30`.
3. **Given** a certificate expires in 31 through 90 days, **When** the report is created, **Then** the band is `31-90`.
4. **Given** a certificate expires in more than 90 days, **When** the report is created, **Then** the band is `more than 90`.
5. **Given** a device certificate source provides `cert_expiry` as an epoch value, **When** the report is created, **Then** the row maps to the same columns as a certificate parsed from PEM text.

---

### User Story 3 - Handle parse failures safely (Priority: P3)

A NOC operator receives a report even when one certificate value cannot be parsed. The failed certificate is visible as a row to investigate, and the run does not fail.

**Why this priority**: Operational reports must be resilient. One malformed or unexpected certificate value must not hide all other renewal risks.

**Independent Test**: Use test data with a valid PEM certificate string and an unparsable certificate value. Confirm that the valid certificate has a not_after date and the unparsable value creates one row with note `unparsable` and no exception.

**Acceptance Scenarios**:

1. **Given** a PEM certificate string is valid, **When** the parser reads it, **Then** the report records the certificate `not_after` date produced by the `cryptography` package.
2. **Given** a certificate value is unparsable, **When** the report is created, **Then** the report includes one row with note `unparsable`, leaves unavailable date fields blank, uses band `expired` as a fail-safe category, and completes without an exception.

---

### User Story 4 - Protect certificate bodies and private key material (Priority: P4)

A NOC operator can share the report and logs with reviewers without exposing private key material or complete certificate bodies.

**Why this priority**: Certificate reports are operational evidence, but they must not leak sensitive material.

**Independent Test**: Run the report with fixtures containing PEM certificate text and private key-like text. Confirm that logs and output files contain only allowed certificate metadata and never contain certificate bodies or private key material.

**Acceptance Scenarios**:

1. **Given** a source value includes a PEM certificate body, **When** logs and output files are inspected, **Then** no certificate body appears.
2. **Given** a source value includes private key material, **When** logs and output files are inspected, **Then** no private key material appears.
3. **Given** certificate metadata is available, **When** logs and output files are inspected, **Then** only subject, issuer, serial, and date values appear.

---

### User Story 5 - Read a banded console summary (Priority: P5)

A NOC operator reads the console summary after the run and sees how many certificate rows fall into each urgency band.

**Why this priority**: The summary gives immediate risk awareness before the operator opens the CSV file.

**Independent Test**: Run the report handler with known test data and compare each console band count to the exported rows.

**Acceptance Scenarios**:

1. **Given** the report has certificate rows in multiple bands, **When** the operation finishes, **Then** the console summary states how many rows each band holds.
2. **Given** a band has no rows, **When** the operation finishes, **Then** the console summary shows zero for that band.

---

### User Story 6 - Verify release and wiring evidence (Priority: P6)

A reviewer checks that the feature has the required planning and release artifacts before implementation is accepted.

**Why this priority**: The project requires traceable work and release notes for each change.

**Independent Test**: Confirm that `specs/3553-certificate-expiry-report/wiring.md` has every fleet contract section and that `changelog.d/issue-3553-certificate-expiry-report.md` exists before release.

**Acceptance Scenarios**:

1. **Given** the specification is complete, **When** the reviewer opens `specs/3553-certificate-expiry-report/wiring.md`, **Then** every fleet contract section is present.
2. **Given** the implementation is ready for release, **When** the reviewer checks release notes, **Then** `changelog.d/issue-3553-certificate-expiry-report.md` exists.

### Edge Cases

- A certificate expires exactly at the current UTC time. The report treats it as expired.
- A certificate expires later on the current UTC date. The report places it in the `0-30` band with zero days remaining.
- A certificate has no available subject or issuer. The report leaves the missing metadata blank while still writing the row.
- Multiple certificates share the same subject or issuer. The report writes each certificate as a separate row under its own scope and owner.
- A certificate source is absent for a scope. The report writes no row for that absent source and does not fail the run.
- A certificate value is unparsable. The report writes exactly one row with note `unparsable`, uses band `expired` as a fail-safe category, and does not raise an exception.
- A source contains private key text or a full PEM body. The report and logs omit the sensitive body and key material.
- A device certificate has `cert_expiry` as an epoch value. The report converts it into the shared date, days remaining, and band columns.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: This branch MUST prepare the menu 272 report handler and fleet wiring evidence. The integration pull request MUST register menu 272 before release.
- **FR-002**: The integrated operation MUST run in `--test` with no prompt. This branch MUST prove the handler no-prompt behavior with a unit fixture.
- **FR-003**: The operation MUST pass the bare filename `CertificateExpiry.csv` to `DataExporter`, which writes under `data/`.
- **FR-004**: The CSV MUST contain one row per certificate found.
- **FR-005**: Each CSV row MUST include scope, owner name or device name, subject, issuer, serial, not_after in UTC, days remaining, band, and note.
- **FR-006**: Supported scope values MUST include `device`, `org device cert`, `NAC server cert`, `SSO IdP`, `PSK portal IdP`, and `CA cert`.
- **FR-007**: A valid PEM certificate string MUST parse to a `not_after` date using the `cryptography` package.
- **FR-008**: An unparsable certificate value MUST produce exactly one CSV row with note `unparsable` and MUST NOT raise an exception.
- **FR-009**: A device with `cert_expiry` as an epoch value MUST map to the same output columns as a PEM certificate source.
- **FR-010**: Each certificate row MUST include a band of `expired`, `0-30`, `31-90`, or `more than 90`.
- **FR-011**: The `expired` band MUST apply when the certificate not_after time is earlier than or equal to the current UTC time.
- **FR-012**: The `0-30` band MUST apply when the certificate has 0 through 30 full days remaining and is not expired.
- **FR-013**: The `31-90` band MUST apply when the certificate has 31 through 90 full days remaining.
- **FR-014**: The `more than 90` band MUST apply when the certificate has more than 90 full days remaining.
- **FR-015**: The console summary MUST state how many rows each band holds.
- **FR-016**: Console band counts MUST match the CSV row counts.
- **FR-017**: No private key material MUST appear in any log line, console line, or output file.
- **FR-018**: No certificate body MUST appear in any log line, console line, or output file.
- **FR-019**: Logs and output files MAY include only subject, issuer, serial, dates, scope, owner, band, and parse note values from certificate material.
- **FR-020**: The wiring manifest `specs/3553-certificate-expiry-report/wiring.md` MUST exist and include every fleet contract section.
- **FR-021**: The release note fragment `changelog.d/issue-3553-certificate-expiry-report.md` MUST exist before release.
- **FR-022**: The operation MUST keep report output inside the `data/` directory.
- **FR-023**: CRL sources MUST be read as metadata-only completeness evidence. They MUST NOT create certificate rows unless a future API exposes a certificate expiry value.
- **FR-024**: Failed CRL reads MUST appear only in the failed-source summary.
- **FR-025**: The handler MUST block export until `certificate_expiry_report` exists in the primary key strategy table.

### Key Entities

- **Certificate Record**: A certificate instance found in one supported source. Key attributes are scope, owner or device name, subject, issuer, serial, not_after, days remaining, band, and parse note.
- **Certificate Source**: The location or category where certificate data originates. Supported values are device, org device cert, NAC server cert, SSO IdP, PSK portal IdP, and CA cert.
- **Expiry Band**: A renewal urgency category derived from days remaining. Values are expired, 0-30, 31-90, and more than 90.
- **Parse Note**: Optional row-level explanation for values that cannot be parsed, including the required `unparsable` note.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The handler test completes without prompting and requests `CertificateExpiry.csv` in 100% of valid fixture runs. The integration pull request proves the full `--test` path.
- **SC-002**: 100% of supported certificate sources in the test fixture produce rows with the required shared column set.
- **SC-003**: 100% of fixture certificates are assigned to the expected band based on their UTC not_after value and days remaining.
- **SC-004**: Unparsable certificate values complete without exception and produce exactly one `unparsable` row in 100% of parse-failure test cases.
- **SC-005**: Console summary counts match CSV band counts exactly for every band in test data.
- **SC-006**: Privacy checks find zero private key strings and zero certificate body strings in logs, console output, and `CertificateExpiry.csv`.
- **SC-007**: A reviewer can verify the wiring manifest and release note fragment paths before release with no missing required artifact.

## Assumptions

- The target users are NOC operators and reviewers who already run MistHelper organization-level reports.
- Menu 272 is reserved for this certificate expiry report.
- Mist certificate alert thresholds of 30, 15, 7, 3, and 1 day are context for why the report needs the `0-30` urgency band.
- Device certificate expiry parsing can follow the existing metrics gateway pattern, but the user-facing output must remain the CSV and console summary described here.
- The release note fragment is required for implementation, but this specify step is limited to files under `specs/3553-certificate-expiry-report/`.
