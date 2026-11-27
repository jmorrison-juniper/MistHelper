# Feature Specification: Reviewed Restore and Partial-Operation Recovery

**Feature Branch**: `feat/4646-restore-recovery`

**Created**: 2026-11-26

**Status**: Draft. Offline design only. Production restore stays blocked.

**Input**: GitHub issue 4646, "[Spec]: Add reviewed restore and partial-operation recovery". The record completes tasks T027 and T028 of the full-parity task map in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`, lines 92 and 93.

## Clarifications

### Session 2026-11-26

- Q: Does this issue authorize a production restore? A: No. The issue states that no production recovery operation is authorized. Source: issue 4646, section Security and Secrets.
- Q: Which object families does a restore cover? A: Network, service, and service policy. Source: parity `spec.md` line 128 (FR-022) and `design/research.md` line 112 (row C28). Decision D-1.
- Q: Which typed word confirms a restore? A: `CONFIRM`. Source: parity `spec.md` line 130 (FR-024). Menu 306 uses `RESTORE`, in `.github/copilot-instructions.md` line 324. Decision D-6.
- Q: Can a restore delete an object that the backup omits? A: No. Source: parity `design/contracts/mist.md` line 150. Decision D-8.
- Q: Who builds the restore user interface? A: Issue 4647 builds it. This record supplies the response fields. Decision D-23.
- Q: Can an approval start before the operator identity is verified? A: No. Issue 4636 decision D-10 refuses write-capable approvals. Decision D-14 is HUMAN-DECISION-REQUIRED.
- Q: Is the 15-minute approval lifetime final? A: No. It is the default until the owner approves another value. Issue 4636 decision D-6. Decision D-21.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify the backup and review each decision (Priority: P1)

An operator selects one private backup. The system verifies the backup. The system then shows one decision for each object before any write.

**Why this priority**: A restore without a verified backup or a reviewed decision list can change production objects without evidence.

**Independent Test**: Use synthetic backups and a fake gateway. Confirm one decision per object and zero write calls.

**Acceptance Scenarios**:

1. **Given** a verified backup with complete pagination, **When** the operator proposes a restore, **Then** the proposal lists one decision for each object.
2. **Given** a damaged seal or a count mismatch, **When** the operator proposes a restore, **Then** the proposal is refused before any cloud call.
3. **Given** a current object that differs from the backup and has no override, **When** the proposal runs, **Then** the object receives the conflict decision.
4. **Given** a current object that the backup omits, **When** the proposal runs, **Then** the object receives the preserve decision and is not deleted.

---

### User Story 2 - Approve and run a reviewed restore (Priority: P1)

An operator reviews the exact scope and confirms it. The operator then types `CONFIRM`. The system writes only the approved objects, one at a time.

**Why this priority**: Two confirmations and one approval limit each write to the reviewed scope.

**Independent Test**: Use a fake gateway. Refuse each invalid approval and confirm zero writes. Run one valid restore and check the read-back of each object.

**Acceptance Scenarios**:

1. **Given** an approval that is 15 minutes old, **When** execution starts, **Then** execution is refused and no write occurs.
2. **Given** a valid approval and the typed word `CONFIRM`, **When** execution starts, **Then** a recovery backup is verified before the first write.
3. **Given** a successful write, **When** the read-back matches the target digest, **Then** the object outcome is verified.
4. **Given** an unverified operator identity, **When** an approval is requested, **Then** the approval is refused.

---

### User Story 3 - Stop safely and reconcile partial or unknown results (Priority: P1)

A failed, partial, or indeterminate write stops later writes. The system reads the cloud state and reports each object outcome. The system never retries an unknown write.

**Why this priority**: The cloud writes cannot run as one transaction. The operator must see the exact state of each object.

**Independent Test**: Simulate a timeout, an HTTP 429 response, a create response without an ID, and a read-back mismatch. Check each outcome and the number of write calls.

**Acceptance Scenarios**:

1. **Given** a timeout on one write, **When** the outcome is recorded, **Then** the outcome is indeterminate and no repeat write runs.
2. **Given** an indeterminate create, **When** reconciliation finds one object with the expected name, **Then** the system records the natural ID and verifies the outcome.
3. **Given** a partial apply, **When** the next object would start, **Then** the system stops and reports the earlier changes as present.

---

### User Story 4 - Propose and approve a recovery (Priority: P2)

After a partial or indeterminate operation, the operator reviews reverse changes. Each reverse change needs its own approval. A reverse update runs only when the current object matches the state that this operation wrote.

**Why this priority**: Recovery writes production objects a second time. It needs proof of ownership and a fresh approval.

**Independent Test**: Simulate a changed object, a created object, and a delete request without owner permission. Confirm each reverse change and each refusal.

**Acceptance Scenarios**:

1. **Given** an update whose current digest equals the recorded after-digest, **When** recovery is proposed, **Then** the reverse update is listed.
2. **Given** an object that another operator changed, **When** recovery is proposed, **Then** the reverse update is a conflict.
3. **Given** a created object and no owner permission for deletion, **When** recovery is proposed, **Then** the object is kept and no delete is listed.

### Edge Cases

- A backup object that changed after the backup receives the conflict decision. Warning: An override replaces a change that another operator made after the backup.
- Two current objects share the name of a backup object. The proposal excludes the backup object and reports a duplicate-name conflict.
- A referenced service name is absent from the current state. The proposal reports an unresolved reference and blocks execution.
- A lookup fails during review. The object becomes a conflict. The system never creates an object from a failed lookup.
- A write times out. The outcome is indeterminate. The system does not repeat the write.
- The SDK returns HTTP 429 after its internal retries. The outcome is indeterminate until reconciliation completes.
- A create response has no new natural ID. The outcome is indeterminate.
- A read-back differs from the target digest. The outcome is partial. Later writes stop.
- Caution: A partial restore leaves the earlier changes in place. The operator reviews each recorded outcome before recovery.
- The administrative gate is closed. Every restore route returns not found.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Requirement |
| --- | --- |
| FR-001 | A restore proposal MUST use only a backup manifest that passes every verification check. |
| FR-002 | The system MUST refuse a damaged seal, count mismatch, digest mismatch, pagination gap, wrong organization, or wrong object family before any cloud call. |
| FR-003 | The system MUST assign each backup object one decision: create, update, conflict, unchanged, or preserve. |
| FR-004 | The system MUST assign create only when the natural ID is absent and no current object has the same name. |
| FR-005 | The system MUST assign update only when an operator records an override for that object. |
| FR-006 | The system MUST assign conflict for duplicate names, unrecorded changes, unresolved references, failed lookups, and wrong organizations. |
| FR-007 | The system MUST NOT delete an object because the backup omits it. Such objects receive the preserve decision. |
| FR-008 | The system MUST verify a recovery backup of every target object before the first write. |
| FR-009 | Each approval MUST bind one operator, one proposal digest, one scope digest, one expiry time, and one use. |
| FR-010 | Execution MUST require a scope confirmation at approval and the exact typed word CONFIRM at execution. |
| FR-011 | The system MUST refuse each write-capable approval while the operator identity is unverified. |
| FR-012 | The system MUST refuse execution after an expired, consumed, changed, or missing approval and perform zero writes. |
| FR-013 | The system MUST read each target again immediately before its write and stop when the target changed. |
| FR-014 | The system MUST write one object at a time in the order network, service, and service policy. |
| FR-015 | The system MUST read back each written object and compare its normalized digest with the target digest. |
| FR-016 | The system MUST stop later writes after a failed, partial, or indeterminate outcome. |
| FR-017 | The system MUST NOT retry an indeterminate write. The system MUST reconcile with read-only lookups first. |
| FR-018 | Each object outcome MUST be verified, failed, partial, indeterminate, or not-applied. The system MUST NOT claim atomic rollback. |
| FR-019 | Recovery MUST propose a reverse update only when the current digest equals the recorded after-digest. |
| FR-020 | Each recovery action MUST need a new approval and a new recovery backup. |
| FR-021 | The system MUST delete a created object only with owner permission and through the deletion path of issue 4645. |
| FR-022 | The proposal response MUST show natural IDs, proposed changes, conflicts, outcomes, and recovery status. |
| FR-023 | Responses and logs MUST NOT contain backup bodies, credentials, or secret values. |
| FR-024 | The feature MUST call mistapi functions with explicit arguments only. Direct HTTP to a Mist REST endpoint is prohibited. |
| FR-025 | Every restore route MUST return not found while the administrative gate from issue 4645 is closed. |
| FR-026 | Existing converter routes and their responses MUST remain unchanged. |
| FR-027 | Each new directory MUST hold five children or fewer. Each touched module MUST hold five top-level names or fewer. |
| FR-028 | The system MUST log an info line before and a debug line after each write, read-back, and reconciliation step. |

### Mist Cloud Transport Requirements

This feature uses these mistapi functions from the pinned SDK version 0.64.1:

- Lists: `listOrgNetworks`, `listOrgServices`, and `listOrgServicePolicies`.
- Reads: `getOrgNetwork`, `getOrgService`, and `getOrgServicePolicy`.
- Creates: `createOrgNetwork`, `createOrgService`, and `createOrgServicePolicy`.
- Updates: `updateOrgNetwork`, `updateOrgService`, and `updateOrgServicePolicy`.

Delete calls stay outside this feature. Decision D-20 sends a reviewed delete through the path of issue 4645.

Contract tests must prove these points:

- SDK insufficiency: the SDK sets no timeout on writes and repeats HTTP 429 writes. Tests prove that the gateway bounds each wait and treats HTTP 429 as indeterminate.
- SDK authentication: the session comes from the existing portal credential service. Tests prove that the session passes as `mist_session` and that no token reaches a log.
- SDK endpoint parity: each call maps to one OpenAPI path and method. The mapping is in `design/contracts/restore-mist.md`.
- Failure safety: tests cover 4xx, 5xx, HTTP 429, timeout, missing create ID, and read-back mismatch.
- Secret redaction: tests cover logs and responses for backup bodies and credentials.

### Key Entities

- **BackupManifest**: A verified backup of one object family. It holds the natural IDs, normalized digests, and a private body for each object.
- **ObjectDecision**: The decision for one backup object. It names the family, the backup ID, the current ID, the decision, and the reason.
- **OperationRecord**: One restore operation. It holds the phase, decisions, outcomes, recovery actions, and approval reference.
- **ApprovalRecord**: One use of one operator approval. It binds the proposal digest, the scope digest, and the expiry time.
- **RecoveryAction**: One proposed reverse change. It names the object, the action, and the expected current digest.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every refused approval and every refused backup produces zero write calls in the tests.
- **SC-002**: Every backup object receives exactly one decision in each proposal test.
- **SC-003**: Every simulated ambiguous write produces an indeterminate outcome and zero automatic repeats.
- **SC-004**: Unrelated objects keep their normalized digests in every success and failure simulation.
- **SC-005**: Every recovery test proves ownership before it lists a reverse update.
- **SC-006**: Every test uses a fake gateway. No test opens a network socket.
- **SC-007**: No response and no captured log line in the tests holds a backup body or a credential value.
- **SC-008**: Every new directory holds five children or fewer, as the guard test reports.

## Assumptions

- The owner accepts the 15-minute approval lifetime as the default until another value is approved (issue 4636 decision D-6).
- Each operation holds at most 100 write decisions. Each write waits at most 60 seconds.
- Issue 4636 moves `lifecycle/backup.py` into `lifecycle/recovery/` before this feature starts (dependency R-4636-1).
- Issue 4643 stores the full normalized body of each backup object in the private store.
- Issue 4645 supplies the administrative gate and the delete path.
- The Mist update call replaces the whole object body. This assumption is unverified and the read-back check detects a merge.

## Out of Scope

- Production restore, live Mist calls, real credentials, and live backups. Warning: A live restore can change production Mist objects that operators depend on.
- Presentation files, which issue 4647 owns.
- Identity provider design, which issue 4636 decision D-10 owns.
- Apply, delete, and unassign operations, which issues 4644 and 4645 own.
- Changes to the shared portal files `web_portal/app.py` and `web_portal/templates/base.html`, which open draft pull request 4208 owns.
