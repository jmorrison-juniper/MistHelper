# Feature Specification: Check Every Operation Pair in the mistapi Spec Guard

**Feature Branch**: `fix/4935-mistapi-spec-pairs`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4935. The guard in `tests/guardrails/test_mistapi_spec_modules.py` checks only the last operation pair of each spec file.

## Clarifications

### Session 2026-11-26

- Q: Which operation pairs does the guard examine? → A: Each operation pair in each spec file, except the frozen spec files. The helper `_source_fields` returns every pair, not only the last one.
- Q: What does the guard do with an operation line that has no module line? → A: The guard reports the operation as missing its module line. The declared absences below are the only exception.
- Q: Which operations have a declared absence? → A: Two. `getOrg128TRegistrationCommands` in spec file 591 and `listOrgAuditLogsLegacy` in spec file 932. The installed SDK lacks both functions. The guard checks each absence on every run.
- Q: What happens to spec file 511, `specs/511-mist-count-org-client-fingerprints/spec.md`? → A: Its operation line has no module line. The installed SDK defines `countOrgClientFingerprints` in `mistapi.api.v1.orgs.insights`. The change adds that module line and corrects the stale status line.
- Q: Does a module line without an operation line fail the guard? → A: No. The survey on `main` found no such line. The guard ignores such a line, as the current helper does.
- Q: Does the change need a changelog fragment? → A: Yes. The constitution requires one fragment for each change. The changelog README allows none for an internal change, but the constitution prevails.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check every declared pair (Priority: P1)

A maintainer runs the guard. The guard checks each operation pair in each non-frozen spec file. The spec file of issue #4934 holds 25 pairs, and the guard checks all 25.

**Why this priority**: A guard that checks one pair in a 25-pair file gives false assurance. This defect is the reason for the issue.

**Independent Test**: Run the guard on a fixture spec file whose first pair names a wrong module. The guard reports the first pair as a defect.

**Acceptance Scenarios**:

1. **Given** two pairs and a wrong first module, **When** the guard runs, **Then** the guard reports the first pair.
2. **Given** the repository after the change, **When** the guard runs, **Then** the summary line reports 489 pairs and 0 defects.

---

### User Story 2 - Fail on an operation without a module line (Priority: P1)

A spec author adds an operation line and omits its module line. The guard fails and names the spec file and the operation. The author then adds the module line.

**Why this priority**: The old helper skipped such a file without a message. A skipped declaration gives no defect report.

**Independent Test**: Run the guard on a fixture with one operation line, a second operation line, and a module line.

**Acceptance Scenarios**:

1. **Given** an operation without a module line before the next operation, **When** the guard runs, **Then** it reports the operation.
2. **Given** an operation with no module at end of file, **When** the guard runs, **Then** it reports that operation.

---

### User Story 3 - Read the examined count (Priority: P2)

A maintainer reads one summary line from each guard run. The line gives the number of examined operation pairs and the number of defects. A run with zero pairs fails.

**Why this priority**: The repository rule requires each guard to show its examined scope. A zero count means that the guard examined no input.

**Independent Test**: Run the guard on a fixture spec tree that holds no operation line. The guard fails and reports that no pair was examined.

**Acceptance Scenarios**:

1. **Given** a spec tree with no operation line, **When** the guard runs, **Then** the guard fails with zero pairs.
2. **Given** any repository state, **When** the guard runs, **Then** the guard prints one summary line that begins with `mistapi spec module guard: examined`.

---

### User Story 4 - Verify each declared absence (Priority: P2)

A maintainer keeps two declared absences in the guard. The guard accepts each absence only while the installed SDK lacks that function. The guard fails when a later SDK release defines the function.

**Why this priority**: A declared absence can become stale after an SDK update. The guard must report a stale absence before a reader relies on it.

**Independent Test**: Run the absence check with a fixed SDK map that defines a declared operation. The guard reports one defect that names the module.

**Acceptance Scenarios**:

1. **Given** a declared absence and an SDK map without that operation, **When** the guard runs, **Then** it reports no defect.
2. **Given** an SDK map that defines a declared operation, **When** the guard runs, **Then** it reports one defect.

### Edge Cases

- An operation line is followed by a second operation line and then by one module line. The first operation has no module, so the guard reports it.
- A module line appears before any operation line. The guard ignores that line, as the current helper does.
- A prose line, such as one that says the module is not available, does not count as a module line. The operation then lacks a module line unless a declared absence applies.
- The frozen spec file `specs/595-mist-get-org-aos-register-cmd/spec.md` declares a module that the SDK lacks. The guard still skips that file.
- The spec file of issue #4934 holds 25 pairs. Each pair must match the installed SDK.
- Caution: a list line in this record that begins with the guard prefix adds a pair to the guard. This record avoids that prefix.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The guard MUST examine each operation pair in each spec file, except the frozen spec files.
- **FR-002**: The guard MUST pair each operation line with the next module line in the same spec file.
- **FR-003**: The guard MUST report each operation line that lacks a module line, unless FR-006 applies.
- **FR-004**: The guard MUST compare each module with the installed SDK definition and report each mismatch.
- **FR-005**: The guard MUST fail when it examines zero operation pairs.
- **FR-006**: The guard MUST accept a declared absence only for an `ABSENT_SDK_OPERATIONS` entry. The guard MUST report a defect when the SDK defines that operation.
- **FR-007**: The guard MUST print one summary line on each run. The summary line MUST give the examined pair count and the defect count.
- **FR-008**: The change MUST correct lines 14 to 16 of `specs/511-mist-count-org-client-fingerprints/spec.md`. Line 14 MUST name the module `mistapi.api.v1.orgs.insights`.
- **FR-009**: The change MUST keep `frozen_spec_files` and the frozen spec file unchanged.
- **FR-010**: The change MUST add a fixture test whose first pair names a wrong module. The fixture test MUST fail on the pre-change helper.
- **FR-011**: The change MUST edit only the guard file, spec file 511, one changelog fragment, and the record folder.
- **FR-012**: The record `spec.md` MUST NOT begin a line with the operation prefix or the module prefix. The guard reads every `spec.md` file.
- **FR-013**: Each changed executable line MUST carry an inline comment. The changed helper MUST log an `info` line before its file read and a `debug` line after it.
- **FR-014**: Each changed or new helper MUST keep five parameters or fewer. It MUST keep five logical blocks or fewer, and 25 lines or fewer.
- **FR-015**: The change MUST add one changelog fragment under `changelog.d/`, named for the issue.
- **FR-016**: The guard file MUST add no module-level name. The symbol gate then reports no module-level change.

### Key Entities

- **Operation pair**: One operation line and the next module line in the same spec file. A pair lacks a module line when the next operation line or the end of the file comes first.
- **Declared absence**: An operation pair whose spec path and operation match an `ABSENT_SDK_OPERATIONS` entry. It stays valid only while the installed SDK lacks the operation.
- **SDK definition**: A top-level function in the installed mistapi package. It maps a function name to its dotted module path.
- **Summary line**: The printed line that gives the examined pair count and the defect count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On `main` after the change, the guard prints `mistapi spec module guard: examined 489 operation pairs, 0 defects.`
- **SC-002**: The guard examines all 25 pairs in the spec file of issue #4934. Before the change, the guard examined one pair.
- **SC-003**: The fixture test for the wrong first pair fails on the pre-change helper and passes after the change.
- **SC-004**: Each applicable local gate in task T-LOCAL-GATES reports its expected result.
- **SC-005**: Each required check on the pull request reports success, including the guardrails shard.
- **SC-006**: No spec file outside the frozen set has an operation line without a module line, except the two declared absences.

## Assumptions

- The installed mistapi package is version 0.64.1. This version satisfies the pin `mistapi>=0.64.0,<0.65`.
- The guard reads the installed SDK source through the `ast` module. This record approximates that result with a regular expression. The gate run is the authority.
- Local spec files equal the files on `main`. Research R3 gives the evidence for each spec file.
- The guard runs in the guardrails shard of CI. The pytest shard definition in `.github/workflows/ci.yml` line 255 names `tests/guardrails`.

## Out of Scope

- Refreshing the other stale claims in spec file 511, including FR-001 and the lines that name `mistapi.api.v1.sites.insights`. A separate issue must cover them.
- Correcting `documentation/MIST_API_MISSING_ENDPOINTS.md`, which lists `listWebhookTopics` as missing. A separate issue must cover it.
- Changing the frozen spec file `specs/595-mist-get-org-aos-register-cmd/spec.md`, which declares a module that the SDK lacks.
- Deciding how the guard treats a module line without an operation line.
- Changing CI workflows, the mistapi pin, or any SDK file.
