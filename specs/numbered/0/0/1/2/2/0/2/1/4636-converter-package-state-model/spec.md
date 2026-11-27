# Feature Specification: Compliant Converter Package and State Model

**Feature Branch**: `feat/4636-converter-state-model`

**Created**: 2026-11-26

**Status**: Draft. Offline types and synthetic tests only. Cloud writes stay blocked.

**Input**: GitHub issue 4636, "[Spec]: Define compliant converter package and state model". Complete tasks T004 and T006 from the full-parity task map in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`.

## Clarifications

### Session 2026-11-26

- Q: Does this issue enable a cloud write? A: No. The coordinator denied cloud-write enablement until the portal proves operator identity, authorization, and durable operation state. Source: issue 4636, comment of 2026-11-08.
- Q: Does this issue register the converter in the shared portal? A: No. Open PR #4208 owns `web_portal/app.py` and `web_portal/templates/base.html`. Integration needs a separate handover. Source: issue 4633, coordinator decision.
- Q: Which store holds private state? A: No operational store is declared on `main`. The plan uses a private file store under `data/`. Decision D-3.
- Q: Does the models move keep a compatibility shim? A: No. Each call site changes in the same change. Source: `AGENTS.md`, section Code quality.
- Q: Is the 15-minute lifetime final? A: No. It is a proposed default until an owner approves another value. Decision D-6.
- Q: Does this issue change the role values? A: No. The values `standalone` and `spoke` stay until tasks T011 and T012. Decision D-11.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the converter package compliant (Priority: P1)

A maintainer checks the package layout before any source child is added. Every touched level keeps five children or fewer.

**Why this priority**: The constitution forbids a new direct child in a full level. The task map needs this inventory first.

**Independent Test**: Run the nested package guard and count each touched directory. Each count is five or fewer.

**Acceptance Scenarios**:

1. **Given** the converter package has five children, **When** this change lands, **Then** the package still has five children and `models.py` is gone.
2. **Given** a new test directory, **When** it is added, **Then** its parent gains one child and stays at five or fewer.

---

### User Story 2 - Bind private records to content (Priority: P1)

A developer creates each record type from synthetic data. Each record carries a digest. Each stored record carries a seal.

**Why this priority**: The digest stops an old review from approving a changed proposal.

**Independent Test**: Create each record type. Change one field. Check that the digest changes.

**Acceptance Scenarios**:

1. **Given** a proposal, **When** the new digest and the existing review digest are computed, **Then** both values match.
2. **Given** a stored record with one edited byte, **When** the store reads it, **Then** the seal check fails.

---

### User Story 3 - Refuse unsafe approvals (Priority: P1)

An approval binds one operator, one proposal digest, one scope digest, one expiry time, and one use.

**Why this priority**: Reuse or a missing identity can repeat or allow a cloud write.

**Independent Test**: Issue, change, expire, and consume synthetic approvals. Check each refusal.

**Acceptance Scenarios**:

1. **Given** no verified operator identity, **When** an approval is issued, **Then** the issue is refused.
2. **Given** an approval that is 15 minutes old, **When** execution starts, **Then** execution is refused.
3. **Given** a changed proposal digest, **When** the approval is checked, **Then** the check fails.
4. **Given** a consumed approval, **When** a second use starts, **Then** the second use is refused.

---

### User Story 4 - Survive restart and fail closed (Priority: P2)

The store writes a record, reads it back, and refuses each write that it cannot verify. A new store instance reads the same record.

**Why this priority**: The current review state lives in the browser session and does not survive a restart.

**Independent Test**: Write records with one store instance. Read them with a new instance. Change the secret and read again.

**Acceptance Scenarios**:

1. **Given** no portal secret, **When** a write starts, **Then** the write is refused and no file is created.
2. **Given** a read-back mismatch, **When** a write finishes, **Then** the store reports failure.
3. **Given** a changed secret, **When** a stored record is read, **Then** the seal check fails.

---

### User Story 5 - Prevent duplicate consumption across workers (Priority: P2)

Two worker processes compete for one approval. Exactly one process consumes it.

**Why this priority**: A second consumption can repeat a write.

**Independent Test**: Start two processes against one approval file. Count the successful consumptions.

---

### User Story 6 - Fail closed for backup manifests (Priority: P2)

A manifest with incomplete pagination, a count or checksum mismatch, a wrong organization, or a wrong object family is refused.

**Why this priority**: Recovery needs a complete backup. A partial backup can cause data loss.

**Independent Test**: Validate synthetic manifests. Use one defect in each manifest.

---

### Edge Cases

- A review at exactly 15 minutes is refused. The expiry boundary is inclusive.
- A naive timestamp without a UTC offset is refused.
- A rotated secret makes every sealed record unreadable.
- A process that exits while it holds a lock releases the lock. Another process can then acquire it.
- The data path is a file, not a directory. The store refuses writes.
- A record identifier with a path separator is refused.
- An operation in the `indeterminate` phase cannot start execution.
- A changed target after approval returns the operation to `proposed`.
- The 16 MiB source limit and its one-byte refusal stay unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The converter package MUST keep five direct children or fewer.
- **FR-002**: The plan MUST record package capacity and compliant paths before any child is added.
- **FR-003**: The change MUST replace `models.py` with the `state/` package and MUST NOT keep a shim.
- **FR-004**: The `state/` package MUST define source, review, proposal, approval, operation, and backup records.
- **FR-005**: Each record MUST carry a SHA-256 digest in the canonical JSON form of the existing review digest.
- **FR-006**: Each stored record MUST carry an HMAC-SHA256 seal with a key derived from `PORTAL_SECRET_KEY`.
- **FR-007**: Public views, logs, and exports MUST omit source text and secret values.
- **FR-008**: A review and an approval MUST expire 15 minutes after creation, using inclusive UTC expiry.
- **FR-009**: An approval MUST bind one operator, one proposal digest, one scope digest, and one use.
- **FR-010**: Issuing a write-capable approval MUST fail when no verified operator identity exists.
- **FR-011**: The transition table MUST accept documented transitions and refuse every other transition.
- **FR-012**: An indeterminate operation MUST NOT start execution without reconciliation and a fresh approval.
- **FR-013**: The store MUST refuse writes when the secret, directory, lock, or disk write is unavailable.
- **FR-014**: The store MUST NOT report success before a read-back verifies the seal and the digest.
- **FR-015**: A new store instance MUST read records from an earlier instance, and a changed secret MUST refuse them.
- **FR-016**: Two processes MUST NOT consume the same approval.
- **FR-017**: A backup manifest MUST fail closed on defects in pagination, count, checksum, organization, or family.
- **FR-018**: This change MUST NOT add a Mist REST call, a route registration, or a shared portal change.
- **FR-019**: Existing DNS preview, review, and export behavior and tests MUST remain unchanged.
- **FR-020**: Each new or moved executable line MUST carry an inline comment, and each store action MUST log before and after.
- **FR-021**: Private state MUST stay under the git-ignored `data/` directory, and production writes MUST stay disabled.
- **FR-022**: Tests MUST use synthetic data, `tmp_path`, and no live credential.
- **FR-023**: Each new test directory MUST hold five children or fewer.

### Mist Cloud Transport Requirements

This change names no mistapi method for the feature. It calls no Mist REST endpoint and opens no WebSocket transport. The 21 candidate write operations in the full-parity cloud contract stay blocked. Their payload and failure evidence remains pending under issue 4634.

### Key Entities

- **SourceRecord**: Private metadata for one validated source. It holds a digest, a byte count, a suffix, and an owner. It holds no source text.
- **ReviewRecord**: Durable review that binds one source and one proposal digest. It expires after 15 minutes.
- **ProposalRecord**: Proposal shape with a digest, mappings, omissions, and target references.
- **ApprovalRecord**: One-use operator approval bound to a proposal digest, a scope digest, and an expiry time.
- **OperationRecord**: Phase, approval reference, object references, backup references, and outcomes.
- **BackupManifest**: Verified inventory of one backup, with object digests and relationships.
- **PrivateStateStore**: Writes, reads, and consumes records under the data directory. It uses a seal, a lock, and a read-back.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The converter package keeps five direct children. The nested package guard counts three direct modules and directories.
- **SC-002**: All 25 planned test functions pass, and no test is skipped.
- **SC-003**: The state test run makes no network request and no Mist call.
- **SC-004**: Every undocumented transition in the transition table is refused.
- **SC-005**: Two-process consumption gives exactly one success in 20 consecutive runs.
- **SC-006**: The restart and secret-change tests pass in every run.
- **SC-007**: The coverage gate for `src` stays at 80 percent or above.

## Assumptions

- The owner accepts the 15-minute lifetime as the default until another value is approved.
- The shipped container runs one Gunicorn worker. `container/scripts/start.sh` line 225 sets `--workers 1`.
- Windows and POSIX both release a native lock when the holding process exits.
- UID 1000 can write the data directory in the container. `documentation/container-deployment.md` line 114 names UID 1000.
- No operator identity provider exists in this repository, so write-capable approvals stay refused.

## Out of Scope

- Cloud writes, apply, restore, delete, and unassign.
- Shared portal route registration and changes to `web_portal/` files.
- Identity provider selection and the shared `PORTAL_SECRET_KEY` policy.
- Source reuse and the license decision under issue 4635.
- Role, hardware, and model mappings under tasks T011 to T016.
- Discovery, backup capture, administration, and browser journeys under tasks T019 to T031.

Warning: A write without a verified approval can change a production gateway. Keep every write path blocked until decision D-10 closes.
