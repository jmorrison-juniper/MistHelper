# Security Checklist: Upgrade Portal Session Recovery

**Purpose**: Check the security controls of the recovery design before implementation.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Credential Handling

- [x] CHK-S01 No credential value persists in the store. Browser token and provider login sessions write no record (D-1, FR-002, FR-009).
- [x] CHK-S02 Each store record is encrypted and authenticated with MultiFernet (D-5, FR-004).
- [x] CHK-S03 The encryption key differs from the signing key (D-5, `design/contracts/settings.md`).
- [x] CHK-S04 The browser cookie holds only the owner key (FR-005).
- [x] CHK-S05 The feature reads the token value only inside the mistapi constructor call. The new code adds no name that holds the value.
- [x] CHK-S06 The feature reads no private SDK attribute (D-20, RC-55).

## Failure and Lifetime

- [x] CHK-S07 A failed validation deletes the record and returns 401 (FR-008, FR-024).
- [x] CHK-S08 A store outage fails closed, with no local fallback (D-9, FR-010, FR-011).
- [x] CHK-S09 Sign-out deletes the record and clears the browser session (FR-012).
- [x] CHK-S10 The absolute and idle lifetimes bound every record (D-6, FR-013).

## Logging and Responses

- [x] CHK-S11 Logs and responses exclude credentials, the encryption key, the browser identifier, and the raw owner key (FR-014).
- [x] CHK-S12 The feature adds no suppression comment for any finding (constitution Principle III, security findings).

## Open Controls

- [ ] CHK-S13 Redis password refusal. Explained: this control waits for the approval of decision D-2 (task T001). The compose default remains in place (RC-12) until approval.
- [ ] CHK-S14 Pattern-only log redaction for unlabeled secrets. Explained: the gap remains by design (D-13, RC-16). Test TP-22 covers the synthetic values only.
- [ ] CHK-S15 Redis ACL hardening. Explained: out of scope (spec.md, Out of Scope). The image support was not verified (U-5 in research.md).
