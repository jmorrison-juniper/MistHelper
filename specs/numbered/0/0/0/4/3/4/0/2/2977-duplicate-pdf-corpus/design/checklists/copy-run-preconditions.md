# Copy Run Preconditions Checklist: Duplicate PDF Corpus

**Purpose**: Record the owner inputs that FR-012 requires before the historical copy run starts (task T010).

**Created**: 2026-11-26

**Status**: Open. The agent checks no item. The owner records each value.

## Owner Inputs

- [ ] PRE-01 Source host. The owner records the host name that holds the historical corpus.
- [ ] PRE-02 Source root. The owner records the absolute path of the historical corpus on that host. The guard test names one candidate (R26, `tests/guardrails/test_juniper_corpus_paths.py` line 12). The owner confirms or replaces it.
- [ ] PRE-03 Copy root. The owner records an empty folder under `data\` on the owner machine. The folder must not overlap the source root.
- [ ] PRE-04 Output root. The owner records the folder for the verification report. The folder must not overlap the source root.
- [ ] PRE-05 Target free bytes. The owner records the free space on the copy-root volume in bytes. The value must exceed the total source size from the inventory.

## Operating Conditions

- [ ] PRE-06 Every harvest process on the owner machine is stopped before the inventory starts.
- [ ] PRE-07 The owner accepts the 2026-10-30 verification procedure: inventory, copy, compare, and source-unchanged check.
- [ ] PRE-08 The owner records the successor issue number for the copy run (D-11).

## Notes

- The verifier refuses a run when PRE-01 to PRE-05 are blank or overlapping (test `test_preconditions_refuse_missing_or_overlapping_paths`).
- The source corpus is not accessed until PRE-01 to PRE-08 are checked by the owner.
- Deletion of any redundant copy needs the separate approval of D-10. This checklist does not grant that approval.
