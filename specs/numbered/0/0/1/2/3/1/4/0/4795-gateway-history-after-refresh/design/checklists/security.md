# Security Requirements Quality Checklist: Gateway History After an Ordinary Refresh

**Purpose**: Check that the security and tenant requirements are complete, clear, and testable.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Tenant and Identity Isolation

- [x] The foreign organization refusal is specified. FR-003 requires it, and N5 tests it.
- [x] The refusal occurs before any history read. FR-002, FR-003, and FR-007 require it, and N4 and N5 assert zero reads.
- [x] Site scope stays part of the identity. The natural key includes the site (data-model.md, R90).
- [x] The history store isolates identities by full identity. The existing isolation test covers the store (R36).

## Secret Handling and Logging

- [x] No secret, token, or password appears in a log line. FR-008 and the contract logging section require counts only.
- [x] The log text is ASCII. Principle V requires it, and the new messages follow it.
- [x] The storage error log uses the existing exception message. The change adds no new field to it.

## Mist Cloud Boundary

- [x] The read path sends no Mist request. FR-007 requires it, and the spec states the boundary.
- [x] The snapshot cache is not changed by the read. FR-007 requires it, and N1 and N4 assert no publish.

## Input and Route Behavior

- [x] A gateway page with no matching record returns HTTP 404 as before (R95).
- [x] The route adds no POST route and no state-changing input. The refresh routes stay unchanged.

## Notes

- Review date: 2026-11-26. All items pass for the change described in `spec.md`.
- The text of each refusal message is fixed by FR-009, so a change in wording cannot weaken an isolation message without a failing test.
- The exception log can include a traceback from a storage library. That text is outside this change. U-5 records the open review of the storage changes.
