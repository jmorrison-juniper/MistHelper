# Write Safety Requirements Quality Checklist: Reviewed Restore and Partial-Operation Recovery

**Purpose**: Check that each cloud write has a complete safety rule and a test.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Approval and Freshness

- [x] CHK001 Each write needs a usable approval. The approval is unused, unexpired, and bound to the digests. Covered by FR-009, FR-012, and tests E1, E2, and E6.
- [x] CHK002 Each target is read again immediately before its write. The write stops when the target changed. Covered by FR-013 and test E9.
- [x] CHK003 The execution lock refuses a second run on the same organization. Covered by decision D-26 and by task T012, which adds the lock refusal test.

## Attempts and Outcomes

- [x] CHK004 Each write has one attempt from the executor view. No automatic repeat runs. Covered by FR-017 and tests E11 and E12.
- [x] CHK005 Each successful write has a read-back before its outcome is verified. Covered by FR-015 and test E8.
- [x] CHK006 A timeout yields an indeterminate outcome. The wait is bounded at 60 seconds. Covered by decisions D-15 and D-16 and test E11.
- [x] CHK007 A final HTTP 429 yields an indeterminate outcome, and reconciliation runs before the next write. Covered by decision D-17 and test E12.
- [x] CHK008 A create without a new natural ID yields an indeterminate outcome. Covered by `design/contracts/restore-mist.md`, section Status mapping for writes.

## Stop Policy and Reconciliation

- [x] CHK009 The first failed, partial, or indeterminate outcome stops later writes. Covered by FR-016 and test E10.
- [x] CHK010 Reconciliation uses read-only lookups only. Covered by the `reconcile` command in `design/contracts/restore-api.md` and by test E13.
- [x] CHK011 No automatic rollback runs. The outcome names each object that changed. Covered by FR-018, decision D-13, and test R5.

## Recovery

- [x] CHK012 A reverse update runs only when the current digest equals the recorded after-digest. Covered by FR-019, decision D-18, and tests R1 and R2.
- [x] CHK013 Unrelated objects keep their digests in each success and failure simulation. Covered by FR-007 and test E14.
- [x] CHK014 An object that the backup omits is never deleted. Covered by FR-007, decision D-8, and test R7.

## Notes

- Item CHK003 depends on the lock refusal test that task T012 adds.
