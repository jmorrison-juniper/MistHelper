# Security Checklist: Gated Converter Apply and Reconciliation

**Purpose**: Check the security and safety rules for the apply path before implementation starts.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Approval and Authorization

- [x] Writes need a verified operator. Decision D-5 keeps this rule open until a human decides the identity provider.
- [x] The approval word is exact. The check uses no trimming and no case folding (FR-003).
- [x] Each approval is single use and bound to the operator and both digests (FR-002, FR-008).
- [x] A cancel voids the approval and keeps the record (FR-022, Decision D-13).

## Write Safety

- [x] Each family starts disabled (FR-014, Decision D-3).
- [x] Zero write calls happen after any refusal (SC-001).
- [x] No write repeats in executor code. The SDK retry counts as one attempt (FR-015, Decision D-7).
- [x] Each write has a bound. The run has a deadline (FR-016, Decision D-8).
- [x] A partial or indeterminate outcome stops later writes (FR-018).

## Data Protection

- [x] Logs hold no payload value, no token, and no secret (FR-023, TST-18).
- [x] Responses hold no payload value and send `Cache-Control: no-store` (TST-26).
- [x] The approval seal depends on `PORTAL_SECRET_KEY`. The apply path refuses writes when the key is empty (Decision D-18).
- [x] Tests use a recording SDK double and no live credential (SC-006, Decision D-19).

## Residual Risks

- [x] The SDK offers no compare-and-set. Residual risk R-1 is recorded in `analysis.md`.
- [x] The PUT semantics are unverified. Unverified item U-1 is recorded in `design/research.md`.
- [x] HTTP 429 and 5xx meanings are unverified. Unverified items U-2 and U-3 are recorded in `design/research.md`.
