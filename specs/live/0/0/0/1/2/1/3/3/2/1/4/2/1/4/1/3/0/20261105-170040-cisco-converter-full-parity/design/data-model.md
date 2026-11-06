# Data Model and State Safety

## Source and Review

**SourceConfiguration** contains an opaque identifier, digest, safe display name, byte count, encoding, and private transient content.
Stored inputs also contain a verified contained path and owner.
The upload suffix does not establish valid content.
Do not place source text or credentials in signed session cookies or browser storage.

**ParsedReview** contains typed family observations, source locations, confidence, redacted display values, and unsupported reasons.
Keep observations separate from generated settings.
Unknown syntax remains visible without exposing its secret values.

## Role, Hardware, and Proposal

**HardwareSelection** contains role, family, verified model identifier, supported ports, and explicit interface assignments.
Changing any field creates a new proposal version.
Unknown models and conflicting assignments block apply.

**Proposal** contains source digest, version, target IDs, hardware selection, contract versions, ordered object changes, omissions, and unresolved checks.
Each object change distinguishes create, update, assignment, deletion, unassignment, or no change.
Use natural IDs from Mist for existing objects.
Names are display and matching hints, not safe unique keys.

**Approval** contains operator identity, permission evidence, proposal digest, scope digest, timestamp, expiry, and one-use authorization state.
Use an assumed 15-minute review lifetime until the owner approves another value.
Exact typed confirmation must accompany the current operation.
Do not keep the confirmation word after cancel, completion, expiry, or scope change.

## Operation and Recovery

**OperationRecord** contains operation identity, object IDs, before-state digests, backup references, phase, and each response outcome.
A duplicate request resolves to the same operation record.
Record object IDs immediately after confirmed creation.
Do not store credentials or unnecessary source content in the audit summary.

**BackupManifest** contains schema version, object family, organization, capture time, pagination completeness, object count, checksums, and relationships.
Full private recovery content may contain sensitive settings.
Restrict access through the existing private storage policy.
Never send the full backup to logs or ordinary proposal exports.
A failed page, missing relationship, wrong organization, or checksum mismatch makes recovery evidence invalid.

## State Transitions

```text
selected -> validated -> parsed -> proposed -> reviewed -> approved
approved -> backup-verified -> executing -> verified
executing -> failed | partial | indeterminate
partial | indeterminate -> reconciled -> recovery-proposed
recovery-proposed -> reviewed -> approved -> recovering -> recovery-verified
```

Rejected input returns to selection and invalidates prior review.
Any proposal or target change returns to proposed state.
An expired or consumed approval cannot return directly to execution.
An indeterminate result cannot enter execution again without read-only reconciliation and fresh approval.
A failed recovery remains visible as failed or partial.
No state implies transaction-level atomicity across cloud objects.
