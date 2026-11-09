# Research: Upgrade Lock Retention

## Decision

- Treat an HTTP 4xx response as a confirmed refusal. This matches the existing `OrgCancelLists` rule.
- Treat a server error, missing or invalid status, or a 2xx response without a valid upgrade identity as an uncertain submission.
- Keep uncertain submissions out of the settled state. Keep site locks and block retries until an existing rule proves the operation is safe.
- Apply the same confirmed-refusal test to new classification, cancellation evidence, and lock release of older records.
- Preserve cloud status reads, phase watches, post-checks, and the current lock lease.

## Rationale

The existing cancellation path treats only HTTP 4xx evidence as proof that no cloud job exists. The lock-release path instead trusts the `rejected` word alone. The shared refusal test makes these paths agree and protects records that already contain an ambiguous `rejected` result.

The aggregate service already stores `submission_unknown` when a transport exception occurs. Reuse that state for ambiguous HTTP responses. The settled-state and retry gates already treat uncertain submission states as unsettled.

## Alternatives Considered

- **Keep every unaccepted response as `rejected`**: Rejected because the current lock path treats that word as proof that no write can continue.
- **Release a lock after every failed submission**: Rejected because a server error or damaged success can hide a cloud job.
- **Add a new durable outcome field or database migration**: Rejected because the current state and raw HTTP status fields can represent this distinction.
- **Change the lease or add status polling**: Rejected because the issue provides no evidence to change the existing timing or read behavior.

## Evidence Boundary

The issue's source-export proof uses the actual classifier and route with callbacks intercepted. Implementation tests will use mocked results. No live Mist call, lock deletion, or database write is part of this design.
