# Feature Specification: Close Full-Parity Evidence Gaps with Approved Dispositions

**Issue**: #4649
**Parent Issue**: #4224
**Feature Branch**: `docs/4649-converter-parity-evidence`
**Record Path**: `specs\numbered\0\0\1\2\2\0\4\4\4649-converter-parity-evidence`
**Parity Task Map**: PR #4596, `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`
**Created**: 2026-11-26
**Status**: Specified. Evidence closure, implementation, and cloud use are not approved.
**Input**: User description: "Close full-parity evidence gaps with approved dispositions." Task coverage: parity T033.

## Clarifications

- Q: Which T033 does this issue name? A: Parity task T033 in the full-parity task list, `tasks.md` line 114. It does not name the DNS task list of issue 4224, which ends at T030.
- Q: Does merging this record complete parity T033? A: No. This record defines how T033 closes. Parity T033 stays partial until FR-008 passes.
- Q: Which open issues block the completion claim? A: The open program issues 4634 to 4648 and the gates in the gate table. Decision D-12 lists them.
- Q: Can the agent approve an unsupported disposition? A: No. An owner approves each disposition. Decision D-7 is a human decision.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register evidence for each comparison row (Priority: P1)

A reviewer needs one register. The register shows the state, evidence, and disposition of each comparison row.

**Why this priority**: Full parity needs proof for each observed capability. A row without proof is an open gap.

**Independent Test**: Run the register audit on the parity record. The audit reports 40 rows with one disposition each.

**Acceptance Scenarios**:

1. **Given** comparison rows C01 to C40, **When** the register refresh completes, **Then** each row appears once with one disposition.
2. **Given** a row without a current check or owner decision, **When** the audit runs, **Then** the row stays open.
3. **Given** an accepted row whose blob SHA changed on main, **When** the audit runs, **Then** the audit fails and the row returns to open.

### User Story 2 - Keep each gate decision separate (Priority: P1)

Legal, API, integration owner, cloud owner, operator, and visual gates each need their own evidence and decision.

**Why this priority**: A decision for one gate does not authorize another gate. Mixed gates allow an unsafe cloud write.

**Independent Test**: Record one gate decision in a fixture. Confirm that only the work blocked by that gate changes.

**Acceptance Scenarios**:

1. **Given** gate G1 without a decision, **When** the audit runs, **Then** source reuse and release stay blocked.
2. **Given** a G2 decision for one operation family, **When** the audit runs, **Then** gates G4 and G5 stay open for that family.

### User Story 3 - Refresh evidence after implementation (Priority: P1)

After implementation work, the parity record needs a refresh. The refresh covers the comparison, the analysis, the decisions, and the test evidence.

**Why this priority**: Parity status changes only with new evidence. Stale evidence allows a false completion claim.

**Independent Test**: Run the audit on a fixture where every row, gate, and task passes. Remove one row decision and confirm the claim is refused.

**Acceptance Scenarios**:

1. **Given** 40 rows accepted or unsupported-approved, all gates decided, and 33 tasks verified-present, **When** the audit runs, **Then** the completion claim is allowed.
2. **Given** any open row, gate, or task, **When** the audit runs, **Then** the completion claim is refused.

### User Story 4 - Record owner-approved unsupported dispositions (Priority: P2)

An owner approves each capability that the converter cannot support. The approval states the reason and the limit that operators see.

**Why this priority**: Operators must see each unsupported capability. A silent omission is a parity defect.

**Independent Test**: Mark one fixture row unsupported-approved without an owner decision. Confirm that the audit fails.

**Acceptance Scenarios**:

1. **Given** a row with disposition unsupported-approved and an owner decision ID, **When** the audit runs, **Then** the row shows its limit text.
2. **Given** an unsupported row without an owner decision, **When** the audit runs, **Then** the audit fails.

### User Story 5 - Gate the converter guide (Priority: P3)

A converter guide is written only after documentation ownership approval and a passed legal gate.

**Why this priority**: A guide that copies source text creates a licensing defect.

**Independent Test**: Run the audit with no guide approval. Confirm that no converter guide file exists under `documentation/`.

**Acceptance Scenarios**:

1. **Given** no documentation approval, **When** the audit runs, **Then** no converter guide file exists.
2. **Given** approval and a passed legal gate, **When** the guide is written, **Then** its text does not copy source documents.

### Edge Cases

- A parity path differs from main. The register cites the path on main and marks the parity path stale.
- Legal approval arrives after implementation starts. Rows that depend on reuse stay open until the decision applies.
- The source repository changes after revision `d9be92f9`. Rows that cite the source become stale.
- The mistapi pin changes from 0.64.1. SDK evidence becomes stale and needs a new check.
- An issue closes without evidence. The completion claim stays refused.
- A gate reads zero files. The audit fails. It never skips silently.
- A local worktree differs from main. The register uses main only.
- Warning: a committed secret stays in the git history after a later revert. The audit rejects secret-like values before commit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The register MUST list each comparison row C01 to C40 once.
- **FR-002**: Each row MUST have one disposition: accepted, unsupported-approved, or open.
- **FR-003**: An accepted row MUST cite a repository path, a blob SHA on main, a line, and a passing check.
- **FR-004**: An unsupported-approved row MUST cite an owner decision ID, an approval date, and the limit text.
- **FR-005**: An open row MUST cite the parity task that remains.
- **FR-006**: Each gate MUST have a status, an owner, and evidence. No gate MAY pass by inference.
- **FR-007**: Each parity task from T001 to T033 MUST have one status: open, verified-present, partial, or absent.
- **FR-008**: The completion claim MUST be refused until every row, gate, and parity task passes.
- **FR-009**: The audit MUST fail when its input is missing or when it examines zero rows.
- **FR-010**: Each local Markdown link in the parity record and in this record MUST resolve.
- **FR-011**: Refreshed artifacts MUST NOT claim full parity while FR-008 fails.
- **FR-012**: Evidence MUST use public or synthetic content. Evidence MUST NOT contain a secret, a credential, or customer configuration.
- **FR-013**: This work MUST NOT authorize a converter guide, a cloud write, or a live Mist request.

### Mist Cloud Transport Requirements

This record adds no Mist call. The parity cloud contract names 21 candidate write operations. It omits `deleteOrgServicePolicy`, which the OpenAPI file and the installed SDK both expose. Each future write uses a mistapi method from the contract. Each future write also passes gates G2 and G4 first.

### Key Entities

- **Comparison row**: One observed capability with a state, evidence, a disposition, and parity tasks. Key: row ID C01 to C40.
- **Parity task status**: One parity task with one status and its evidence. Key: task ID T001 to T033.
- **Gate**: One approval gate with an owner, a status, and a decision ID. Key: gate ID G1 to G5 or GV.
- **Owner decision**: One approval record for a disposition or a gate. Key: decision ID in the form OD-number.
- **Audit report**: The counts and the result of one audit run. Key: UTC run time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The register lists 40 of 40 comparison rows with one disposition each.
- **SC-002**: At the baseline in this record, 0 rows are accepted and 40 rows are open.
- **SC-003**: Each audit run reports the number of rows, tasks, gates, and links that it examined.
- **SC-004**: Zero gates pass without a recorded owner decision or a named evidence source.
- **SC-005**: Zero cloud writes and zero live Mist requests occur during an audit run.
- **SC-006**: Zero secret-like values appear in the register, the audit output, or the test logs.

## Assumptions

- The parity record from PR #4596 is the authority for rows C01 to C40 and tasks T001 to T033.
- Main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26T07:15:01Z, is the baseline for this record.
- Source revision `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c` is the observation revision for the upstream converter source.
- The pinned mistapi version 0.64.1 is the SDK baseline. A pin change makes SDK evidence stale.
- Parity T033 execution starts after the open program issues deliver their evidence.
- The Spec Kit route for issue 4649 is `0\0\1\2\2\0\4\4`. That route is the base-5 representation of 4649, padded to eight digits.

## Out of Scope

- Converter behavior for parity tasks T001 to T032.
- Legal text, licensing decisions, and reuse approval. A human owner decides these.
- Cloud writes, live Mist requests, and production changes.
- Shared portal integration under parity T032. This work needs integration-owner handover, gate G3.
- The independently written converter guide, until documentation ownership approval exists.
- Changes to the parity record or to the parent record of issue 4224 in this pull request.
- A changelog fragment. Decision D-14 explains the omission.
