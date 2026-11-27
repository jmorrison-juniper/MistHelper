# Feature Specification: Gated Converter Apply and Reconciliation

**Feature Branch**: `feat/4644-gated-converter-apply`

**Created**: 2026-11-26

**Status**: Draft. Specification only. This record enables no Mist write.

**Input**: GitHub issue 4644, "[Spec]: Add gated converter apply and reconcile results". The record completes parent tasks T021 and T022 in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`, lines 76 and 77. Parent issue: 4224.

## Clarifications

### Session 2026-11-26

- Q: Does this issue enable a live Mist write? A: No. Issue 4644 authorizes no production operation. Issue 4633 keeps every write blocked. Decision D-17.
- Q: Which apply families does the first release register? A: Eight create, update, and assign families, F-01 to F-08. Each family starts disabled. Decision D-1.
- Q: Which word confirms an apply? A: The exact word `APPLY`. The check is case-sensitive, with no trimming. Parent FR-016. Decision D-4.
- Q: May the executor retry an unknown write? A: No. The executor never repeats a write. Decisions D-7 and D-9.
- Q: Which issue owns restore and partial-operation recovery? A: Issue 4646. This record classifies and reconciles outcomes. Decision D-16.
- Q: Does this record reuse the export approval in `ReviewState`? A: No. That approval lives in the Flask session and covers export only. Decision D-4.
- Q: Does the apply approval use a 15-minute lifetime? A: Yes. The lifetime is the proposed default from issue 4636, decision D-6 there. The owner may change it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review the exact change set before approval (Priority: P1)

An operator sees the exact organization, sites, gateways, and change set before approval. The operator reads each object and each field before the operator types the approval word.

**Why this priority**: Parent FR-015 requires an exact scope review before any cloud write.

**Independent Test**: Build a synthetic proposal and a synthetic scope. Request the apply view. Check that each organization, site, gateway, and change item appears once.

**Acceptance Scenarios**:

1. **Given** a reviewed proposal, **When** the operator requests the apply view, **Then** the response lists each scope item.
2. **Given** two sites share one name, **When** the operator requests the apply view, **Then** the response reports the conflict and refuses approval.

---

### User Story 2 - Execute only the approved change set (Priority: P1)

After the operator types `APPLY`, the system consumes the approval. The system then writes only the approved change items, in a fixed order.

**Why this priority**: A write outside the approved scope can change a production gateway.

**Independent Test**: Use a recording SDK double. Run one approved operation. Check each recorded write against the change set.

**Acceptance Scenarios**:

1. **Given** a valid approval and the exact word `APPLY`, **When** execution starts, **Then** the system writes each enabled change item once, in order.
2. **Given** a family that is disabled in the registry, **When** execution starts, **Then** the system makes zero SDK write calls.

---

### User Story 3 - Reconcile each result and stop after uncertainty (Priority: P1)

After each write, the system reads the object back. A failed, partial, or indeterminate outcome stops later writes. The system never repeats an unknown write.

**Why this priority**: Parent FR-018 and FR-019 require truthful outcomes and no unsafe retries.

**Independent Test**: Simulate each HTTP class and a timeout with the SDK double. Check the recorded outcome and the write count.

**Acceptance Scenarios**:

1. **Given** a timeout on one write, **When** the outcome is recorded, **Then** the outcome is indeterminate and no repeat write runs.
2. **Given** a final HTTP 429 after the SDK retries, **When** the outcome is recorded, **Then** the outcome is indeterminate.
3. **Given** a partial operation, **When** the operator requests reconciliation, **Then** the system uses read-only lookups and records each object outcome.

---

### User Story 4 - Refuse stale, duplicate, and unsafe submissions (Priority: P2)

The system refuses a stale proposal, a changed target, a duplicate submission, and an approval with no verified operator. Each refusal makes zero writes.

**Why this priority**: Parent FR-017 and FR-018 require protection against stale state and duplicate writes.

**Independent Test**: Use synthetic approvals and the SDK double. Check the write count after each refusal.

**Acceptance Scenarios**:

1. **Given** an approval with no verified operator, **When** the operator submits it, **Then** the system refuses it and makes zero writes.
2. **Given** a target digest that changed after approval, **When** execution starts, **Then** the system refuses the run before the first write.
3. **Given** a second submission for one approval, **When** the request arrives, **Then** the system refuses it because the approval is consumed.

### Edge Cases

- A write returns HTTP 429 after the SDK retries three times. The outcome is indeterminate.
- A write returns HTTP 500. The OpenAPI file does not document this status. The outcome is indeterminate.
- A create returns HTTP 200 with no natural ID. The outcome is indeterminate.
- A read-back differs from the approved fields. The outcome is partial, and later writes stop.
- The operator cancels after execution starts. The system refuses the cancel because the approval is consumed.
- An approval reaches exactly 15 minutes of age. The boundary is inclusive, so execution is refused.
- Another process holds the scope lock. The second run is refused without a write.
- The shared secret is missing. The store refuses every write, and no approval is issued.
- Mist changes an object between the re-read and the write. The SDK offers no compare-and-set. The residual risk is recorded in `analysis.md`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST show the organization, sites, gateways, and change set before approval. (Parent FR-015)
- **FR-002**: The system MUST issue one approval for each operation, bound to the operator, proposal digest, scope digest, and expiry. (Parent FR-016)
- **FR-003**: The system MUST accept approval only when the typed word equals `APPLY` exactly. (Parent FR-016)
- **FR-004**: The system MUST refuse approval and execution without a verified operator identity. (Decision D-5)
- **FR-005**: The system MUST refuse execution for an approval that is missing, consumed, expired, or bound to other digests. (Parent FR-016)
- **FR-006**: The system MUST refuse execution when the backup manifest for an object family is missing or incomplete. (Parent FR-016)
- **FR-007**: The system MUST invalidate approval when the input, proposal, target, role, model, or cloud state changes. (Parent FR-017)
- **FR-008**: The system MUST consume each approval once, under a lock, before the first write. (Parent FR-018)
- **FR-009**: The system MUST refuse a second run for one scope while another operation holds the scope lock. (Parent FR-018)
- **FR-010**: The system MUST read each target object before the run and before each write, and stop on any digest mismatch. (Parent FR-017)
- **FR-011**: The system MUST send only allow-listed fields for each enabled family. (Parent `mist-apply.md`)
- **FR-012**: The system MUST build each write body from the current object and the approved fields. (Parent FR-019)
- **FR-013**: The system MUST call mistapi methods with explicit arguments only. (Constitution, SDK compatibility gate)
- **FR-014**: The system MUST NOT call a write for a family that is disabled in the registry. (Decision D-3)
- **FR-015**: The system MUST NOT retry a write in its own code. (Parent FR-018)
- **FR-016**: The system MUST bound each write wait and the whole run with a deadline. (Decision D-8)
- **FR-017**: The system MUST classify each object outcome as verified, failed, partial, indeterminate, or not-applied. (Parent FR-019)
- **FR-018**: The system MUST stop later writes after a failed, partial, or indeterminate outcome. (Parent FR-019)
- **FR-019**: The system MUST reconcile with read-only lookups before any new approval after a partial or indeterminate outcome. (Parent FR-019)
- **FR-020**: The system MUST report an object as verified only after a read-back matches the approved fields and the unchanged unrelated fields. (Parent FR-019)
- **FR-021**: The system MUST treat a create response without a natural ID as indeterminate. (Parent FR-018)
- **FR-022**: The system MUST void an approval when the operator cancels before execution, and keep the operation in the `reviewed` phase. (Decision D-13)
- **FR-023**: The system MUST keep tokens, secret values, and payload values out of logs, responses, and exports. (Constitution, Principle III)
- **FR-024**: The system MUST log an info line before and a debug line after each action, with a summary only. (Constitution, Principle VII)
- **FR-025**: The system MUST leave the existing preview, review, and export behavior unchanged. (Issue 4636 FR-019)

### Mist Cloud Transport Requirements

- Each apply family uses one mistapi method. The table in `design/contracts/mist-write-families.md` names the eight write families, F-01 to F-08. Reconciliation uses the read methods R-a to R-e in the same contract.
- SDK insufficiency for writes: the SDK sets no timeout on write requests. The SDK repeats HTTP 429 writes three times. Tests TST-14 and TST-16 prove both behaviors with a mocked transport. This record proposes no owned transport.
- SDK authentication: the adapter receives the session object from the existing credential service. The adapter does not read a token or change `_apitoken`, `_apitoken_index`, `_session`, or `_cloud_uri`.
- SDK endpoint parity: test TST-12 compares the path that the adapter builds with the OpenAPI path for each family.
- Failure safety: `design/contracts/reconciliation.md` maps each status class to one outcome. Tests TST-13 to TST-17 cover each class.
- Secret redaction: tests TST-18 and TST-26 search logs and responses for payload values and secret values.

### Key Entities

- **ChangeSet**: The ordered change items for one proposal and one scope.
- **ChangeItem**: One family, one natural object ID or null for a create, one before digest, and one payload digest.
- **ApprovalRecord**: The approval record from issue 4636, checked by `ApprovalGate`.
- **OperationRecord**: The operation record from issue 4636, with the outcome `not-applied` added.
- **ReconciliationResult**: The read-only comparison for one object.
- **FamilyRegistry**: The default-disabled family list, with an allow-list of fields for each family.

## Success Criteria *(mandatory)*

- **SC-001**: Each refusal test proves zero SDK write calls.
- **SC-002**: Each simulated ambiguous write produces an indeterminate outcome and zero automatic repeats.
- **SC-003**: Each registered family has one positive test and one negative test.
- **SC-004**: Two concurrent processes consume one approval exactly once in 20 consecutive runs.
- **SC-005**: Reconciliation makes no write call.
- **SC-006**: No test uses a live credential or a live Mist request.
- **SC-007**: The apply test folder and the converter test root each hold five children or fewer.

## Assumptions

- Issue 4636 lands its state package before this record starts its code tasks.
- Issue 4634 supplies the field evidence for each enabled family.
- The owner keeps the 15-minute approval lifetime and the 10-minute run deadline until another value is approved.
- No operator identity provider exists on `main`. The apply path refuses every write until decision D-5 closes.
- The shipped container runs one Gunicorn worker. The file `container/scripts/start.sh` line 225 sets `--workers 1`.

## Dependencies

| Prerequisite | State on 2026-11-26 | Effect on this record |
| --- | --- | --- |
| Issue 4633, ownership handover | Closed. Shared-file work stays blocked by PR #4208, which is open. PR #4615 merged on 2026-11-13. | Route registration in `web_portal/app.py` waits for a separate integration change. |
| Issue 4634, API contracts | Open | Gate G2 blocks each family allow-list. |
| Issue 4635, licensing and authorship | Open | Gate G1 blocks release. The apply path uses independent authorship only. |
| Issue 4636, state model | Open. Draft only. Not on `main`. | Supplies the approval, operation, store, and transition types. |
| Issue 4642, read-only discovery | Open | Supplies current cloud reads and site and gateway lookups. |
| Issue 4643, private backup evidence | Open | Supplies complete backup manifests for `BackupGate`. |
| Issue 4646, recovery | Open. Draft only. | Reuses the reconciliation primitives from this record. |

## Out of Scope

- Delete, unassign, restore, and administrative writes. Issues 4645 and 4646 own them.
- Device inventory assignment and device-level updates, `updateOrgInventoryAssignment` and `updateSiteDevice`. They wait for field evidence from issue 4634.
- Shared portal route registration. Issue 4633 and parent task T032 own it.
- Browser controls and visual layout. Issue 4647 owns them.
- Legal reuse decisions. Issue 4635 owns them.
- Production enablement of any family. Decision D-17 governs it.

Warning: Enabling a write family can change a production Mist organization. This record cannot reverse that change. The owner must approve enablement first.
