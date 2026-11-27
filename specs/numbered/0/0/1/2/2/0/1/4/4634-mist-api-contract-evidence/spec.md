# Feature Specification: Mist API Contract Evidence for the Cisco Converter

**Feature Branch**: `feat/4634-mist-api-contract-evidence`

**Record path**: `specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Verify Mist API contracts for Cisco converter mappings (issue 4634)."

**Parent**: Issue 4224. This issue is task T003 of the Cisco converter full-parity map in PR 4596.

## Problem

The parity map lists candidate Mist write operations. A method name does not prove field meaning or safe use. This record collects offline evidence for each operation. Each operation keeps its own status. Missing evidence blocks only the operation that lacks it.

Each write operation stays disabled in this change. No live Mist request runs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review write operation evidence (Priority: P1)

A reviewer reads one contract row for each Mist write operation. Each row gives the OpenAPI location, the SDK location, and the statuses.

**Why this priority**: Gate G2 blocks each write family until its evidence exists. Records 4644 and 4645 depend on this evidence.

**Independent Test**: Open `design\contracts\mist-write-operations.md`. Confirm 22 rows. Each row cites an OpenAPI location and an SDK line.

**Acceptance Scenarios**:

1. **Given** the record, **When** a reviewer reads the write contract, **Then** each of the 22 write operations has one row.
2. **Given** a row with incomplete field evidence, **When** a reviewer reads it, **Then** the row shows `partial` and no other row changes.

### User Story 2 - Review read and reference evidence (Priority: P1)

A reviewer checks the read operations that the program uses for reference checks and read-back. Each read operation has an identity row and a role.

**Why this priority**: Record 4645 asks this issue for verified reads before network and service deletion scope review.

**Independent Test**: Open `design\contracts\mist-read-operations.md`. Confirm 18 rows. Each row has a role and a status.

**Acceptance Scenarios**:

1. **Given** the record, **When** a reviewer checks the reference reads, **Then** each read names the write operations that use it.

### User Story 3 - Run offline contract tests (Priority: P2)

A developer runs three test modules. The tests use the bundled OpenAPI file, the pinned mistapi source, and mocked SDK responses. The tests open no network connection.

**Why this priority**: The tests keep the evidence true after a dependency or document change.

**Independent Test**: Run `python -m pytest tests\contract\web_portal\cisco_config_converter`. All 32 planned tests pass. No socket opens.

**Acceptance Scenarios**:

1. **Given** a positive synthetic fixture, **When** the schema check runs, **Then** the fixture passes.
2. **Given** a negative synthetic fixture, **When** the schema or the allowlist check runs, **Then** the fixture fails as expected.
3. **Given** a mocked HTTP 429 response on a write, **When** the SDK call runs, **Then** the test records the SDK retry count.

### User Story 4 - Keep unverified writes disabled (Priority: P1)

A reviewer confirms that the change adds no production write and no enablement setting. The Cisco converter keeps its offline behavior.

**Why this priority**: The issue states that this work does not authorize cloud writes.

**Independent Test**: List the changed paths on the branch. No path under `src\` appears.

**Acceptance Scenarios**:

1. **Given** the branch, **When** the reviewer lists the changed paths, **Then** no path under `src\` appears.
2. **Given** a test that scans the converter source, **When** the test runs, **Then** no write operation name appears in production source.

### Edge Cases

- A row where the OpenAPI file and the SDK disagree has the status `absent`. It blocks only that operation.
- A schema that allows an unknown top-level field is documented. The local allowlist rejects that field.
- A create response without `id` is indeterminate in the executor. The schema does not require `id`.
- The SDK repeats HTTP 429 for writes up to three times. Each repeat counts as one attempt.
- A null `sitetemplate_id` stays refused. The schema allows null, but its meaning is not documented.
- A list request body stays refused. The OpenAPI file declares object bodies only.
- A service or service policy body with no fields passes the schema. The local rule requires `name`.
- A mistapi version change makes the signature and retry tests fail. The evidence then needs a new review.

### Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST list the 21 write operations in the parity inventory and `deleteOrgServicePolicy`.
- **FR-002**: The record MUST list the 18 read operations used for reference checks, read-back, and candidate discovery.
- **FR-003**: Each contract row MUST cite the OpenAPI path, verb, operation ID, object location, and YAML line.
- **FR-004**: Each contract row MUST cite the pinned mistapi module, the function line, and the SDK call line.
- **FR-005**: Each contract row MUST carry an identity status, a field status, and a behavior status.
- **FR-006**: The contract tests MUST accept each positive synthetic fixture against the bundled OpenAPI schema.
- **FR-007**: The contract tests MUST reject each negative synthetic fixture through the schema or the local allowlist.
- **FR-008**: The contract tests MUST cover HTTP 400, 403, 404, 500, and 429 responses and a transport failure for each write family.
- **FR-009**: The contract tests MUST pin the SDK retry count and the wait times for HTTP 429 on POST, PUT, and DELETE.
- **FR-010**: The contract tests MUST show that each SDK wrapper forwards the request body unchanged and makes one call.
- **FR-011**: The gateway template fixtures MUST use only `name`, `type`, and `dns_servers`.
- **FR-012**: This change MUST NOT add a production write call, a live Mist request, or an enablement setting.
- **FR-013**: The contract tests MUST block socket connections and MUST NOT read a Mist credential variable.
- **FR-014**: Each write operation with incomplete field evidence MUST stay disabled and list its unverified items.
- **FR-015**: The record MUST exclude `deleteOrgServicePolicy` from converter scope and cite decision 4645 D-13.
- **FR-016**: The record MUST keep null site-template unassignment refused and cite decision 4645 D-3.
- **FR-017**: The record MUST report the same remote check count in the STATUS file, the research file, and the summary.
- **FR-018**: The tests MUST live under `tests\contract\web_portal\cisco_config_converter`. This keeps each directory within five children.
- **FR-019**: The change MUST add one changelog fragment named for issue 4634.
- **FR-020**: The record MUST flag incorrect or stale evidence in the issue comments and in the sibling records.
- **FR-021**: The record MUST align the family IDs with issue 4644 and the read needs with issue 4645.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature names 22 write operations and 18 read operations through mistapi methods. No product code calls them in this change.
- Direct HTTP to a Mist REST endpoint is prohibited. The tests use mistapi signatures and a mocked session only.
- This feature owns no WebSocket transport. The record names no WebSocket path.
- SDK insufficiency evidence: mistapi 0.64.1 repeats HTTP 429 for writes and sets no timeout on writes. The tests pin both behaviors (FR-009).
- SDK authentication evidence: the tests use a synthetic token constant and no credential variable (FR-013).
- SDK endpoint parity: each SDK verb and path must match the OpenAPI verb and path.
- Failure safety: the tests cover HTTP 400, 403, 404, 429, and 500 responses and a transport failure (FR-008).
- Secret redaction: mistapi logs write request bodies at DEBUG level. Secret-bearing families stay disabled until redaction evidence exists.

### Key Entities *(include if feature involves data)*

- **Write operation**: One Mist write operation with its identity, body schema, and statuses. Defined in `design\data-model.md`.
- **Read operation**: One Mist read operation with a role in a reference check or a read-back.
- **Synthetic fixture**: One test body written from the schema, with an accept or reject expectation.
- **Remote check**: One comparison of a repository path or commit with GitHub `main`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The write contract lists 22 of 22 write operations. The read contract lists 18 of 18 read operations.
- **SC-002**: Each of the 40 contract rows cites one OpenAPI location and one SDK line.
- **SC-003**: The contract tests report zero socket connections and zero reads of Mist credential variables.
- **SC-004**: No write operation reaches enabled status in this change.
- **SC-005**: The remote check count is the same in the STATUS file, the research file, and the summary.
- **SC-006**: Each directory that this change adds or changes holds five children or fewer.
- **SC-007**: Each local gate in the task T-LOCAL-GATES passes on the changed files.

## Out of Scope

- Live Mist API calls and cloud writes of any kind.
- Enablement of any write family. Gates G2, G4, and G5 remain open.
- Production code under `src\`. Production write paths belong to issues 4644 and 4645.
- Operator identity, approval seals, and backup design. These belong to issues 4636, 4643, 4644, and 4645.
- Correction of the pin text in the constitution and in `.github\copilot-instructions.md`. A separate issue owns this work.
- Correction of the parity record, the sibling records, and the issue comments. Their owners correct them.
- Menu changes and operation count changes.
- An upgrade of the mistapi package.

## Assumptions

- The bundled OpenAPI JSON file equals GitHub `main` blob `5f9f4ce94f812f0e818ee65f99f032118a28f56c`. The local file matches by blob SHA.
- The runtime pin is `mistapi==0.64.1` in `requirements.txt`. The `pyproject.toml` range is `>=0.64.1,<0.65`.
- The declared `jsonschema` 4.26.0 package validates OpenAPI 3.1 schemas. No new package is needed.
- The OpenAPI file describes the service as documented. This change does not verify service behavior.
- Records 4636, 4644, and 4645 use the families and reads named in this record.

## Clarifications

### Session 2026-11-26

- Q: Does the converter need `deleteOrgServicePolicy`? A: No. Exclude it. Decision D-4 records this. Decision 4645 D-13 also excludes it.
- Q: Should read operations be in scope? A: Yes. Record 4645 asks this issue for reference reads. Gate G2 covers reads and read-back.
- Q: May this work call the live Mist API? A: No. The issue and the operator instruction forbid it.
- Q: Which OpenAPI file is authoritative? A: The JSON file, as the parity contract names it. The YAML file is a cross-check.
- Q: Which mistapi version applies? A: Version 0.64.1, the exact pin in `requirements.txt`.
- Q: May a list request body be sent? A: Not verified. Refuse list bodies. Decision D-7 records this.
