# Feature Specification: Client Device Fingerprint Census

**Feature Branch**: `feat/3569-client-fingerprint-census`  
**Created**: 2026-09-29  
**Status**: Draft  
**Input**: Menu 289 client device fingerprint census for a site.

## User Scenarios & Testing

### User Story 1 - Export a site fingerprint census (Priority: P1)

A NOC engineer selects menu `289`, chooses one Mist site, chooses one distinct fingerprint field, and receives a CSV report plus a console table with the top rows.

**Why this priority**: NAC design and capacity planning need a current client census before policy design begins.

**Independent Test**: Mock the site prompt, the distinct-field prompt, the Mist count response, and the exporter. Verify that the operation prompts only for the site and field, calls the count endpoint once, writes `ClientFingerprintCensus.csv`, and prints at most 20 rows.

**Acceptance Scenarios**:

1. **Given** a site and a valid distinct field, **When** the operator runs menu `289`, **Then** the operation calls the fingerprint count endpoint for that site and field.
2. **Given** the endpoint returns rows, **When** the operation exports the result, **Then** `data/ClientFingerprintCensus.csv` contains the field value and `count` columns.
3. **Given** the endpoint returns more than 20 rows, **When** the operation prints the table, **Then** the console table shows only the top 20 rows.

### User Story 2 - Handle an empty census (Priority: P1)

A NOC engineer runs the report for a quiet site and receives a header-only export plus a clear empty-census message.

**Why this priority**: An empty site is a valid result. The run must still leave an auditable file.

**Independent Test**: Mock an empty Mist count response. Verify that the exporter receives an empty row list with explicit field names and that the printed message says the census is empty.

**Acceptance Scenarios**:

1. **Given** the endpoint returns no `results`, **When** the operation writes the report, **Then** it writes a header-only `ClientFingerprintCensus.csv` file.
2. **Given** the endpoint returns no `results`, **When** the operation prints the result, **Then** it prints a message that says the census is empty.

### User Story 3 - Keep integration wiring deferred (Priority: P2)

The feature branch delivers the package, tests, specification, and wiring manifest without editing shared menu files.

**Why this priority**: Fleet work must avoid collisions in shared files.

**Independent Test**: Verify that `specs/3569-client-fingerprint-census/wiring.md` includes menu `289`, category `interactive_safe`, a site-prompt skip reason, the primary key strategy, and the deferred `MistHelper.py` import line.

## Requirements

### Functional Requirements

- **FR-001**: The operation MUST ask for the site and the distinct field, then run with no other prompt.
- **FR-002**: The distinct values MUST come from the OpenAPI enum for `countOrgClientFingerprints`.
- **FR-003**: A test MUST assert the OpenAPI distinct list used by the operation.
- **FR-004**: The operation MUST write `ClientFingerprintCensus.csv` under `data/` through the shared exporter.
- **FR-005**: The export MUST include the selected distinct field value and `count` for each result row.
- **FR-005A**: The export MUST use SDK pagination so it includes every count result page.
- **FR-006**: A response with no `results` MUST write a header-only file and print a message that says the census is empty.
- **FR-007**: The console table MUST print the top 20 rows sorted by count descending.
- **FR-008**: The operation MUST be registered in the wiring manifest as menu `289`, category `interactive_safe`.
- **FR-009**: The skip reason in the wiring manifest MUST name the site prompt.
- **FR-010**: The wiring manifest MUST define the primary key strategy for the export.
- **FR-011**: The release note fragment `changelog.d/issue-3569-client-fingerprint-census.md` MUST exist.

### Non-Functional Requirements

- **NFR-001**: The feature MUST use `SourceDependencyResolver` for the API session, site prompt, input prompt, and export path.
- **NFR-002**: The feature MUST log before and after each API call, transform, prompt, and export.
- **NFR-003**: The feature MUST not log tokens, passwords, passphrases, claim codes, keys, or certificate bodies.
- **NFR-004**: Unit tests MUST not make network calls.

## Key Entities

- **Fingerprint census row**: One exported row with `site_id`, `site_name`, `distinct`, `value`, and `count`.
- **Distinct field**: One allowed field from the OpenAPI enum: `family`, `model`, `os`, or `os_type`.
- **Census result**: The endpoint response with `distinct`, `results`, `total`, `start`, `end`, and `limit`.

## Assumptions

- The OpenAPI enum is authoritative. It does not include `mfg`, even though the issue text names it.
- The installed SDK exposes site-scoped aliases for the OpenAPI operation IDs.
- The integration pull request will apply the menu row and shared-file changes from `wiring.md`.
- The integration pull request will apply the README menu table update from `wiring.md`.
- The primary key strategy will use `site_id`, `distinct`, and `value` because the endpoint returns no Mist identifier.

## Success Criteria

- **SC-001**: A unit test proves that a populated response writes rows and prints the top 20 limit.
- **SC-002**: A unit test proves that an empty response writes a header-only file and prints the empty message.
- **SC-003**: A unit test proves that the distinct choices match the OpenAPI enum.
- **SC-004**: The package quality gates pass for compile, Ruff, Black, mypy, pydocstyle, pytest, vulture, and interrogate.
- **SC-005**: The client unit test proves that the SDK response passes through `mistapi.get_all`.
