# Security Checklist: MSP Profile Lookup Failure

**Purpose**: Review the fail-closed and redaction rules before implementation

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

- [x] Fail closed: a failed lookup never selects the single-organization callback (FR-010, FR-011).
- [x] Redaction: no response body and no exception message reaches a log (FR-013, SC-006, T004 case 6, T010).
- [x] Token handling: the change reads the session and never prints or stores the token.
- [x] Input validation: the status check and the body checks run before any value is used (FR-001).
- [x] No new endpoint: the change adds no REST method and no direct HTTP call.
- [x] No persistence: the change writes no file and no database row.
- [x] ASCII logs: each new message uses ASCII text (`design/contracts/profile-lookup.md` and `design/contracts/menu-13-dispatch.md`).
- [x] No exception reaches the caller: a failed lookup returns a result (`design/contracts/profile-lookup.md`, rule 1).
- [x] Static security check: bandit runs on the two changed packages in T-LOCAL-GATES step 11.
