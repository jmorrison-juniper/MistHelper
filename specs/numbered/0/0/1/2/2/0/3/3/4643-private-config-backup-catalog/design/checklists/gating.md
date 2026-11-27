# Gating Checklist: Private Configuration Backup and Verified Catalog

**Purpose**: Record which gates block each step of this change. A step never starts before its gate passes.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Owner Gates

- [x] G1 (source reuse and legal basis, issue 4635): this change reuses no external source or asset. The record cites none.
- [ ] G2 (contract evidence, issue 4634): open. The list operations need header evidence, item evidence, and relationship rows (T003). Blocks T009 and every enablement.
- [x] G3 (shared-file ownership, issue 4633): the coordinator decision names the rule. PR 4615 merged on 2026-11-13T06:20:12Z. No open PR touches `output_scan.py` or `data_browser.py` at drafting time. The integration owner repeats the check before T013.
- [ ] G3 handover (integration owner): the integration owner records the handover in issue 4633 before T013 starts.
- [x] G4 (storage policy, issue 4643 comment IC_kwDOQltU8c8AAAABkRDV7A): the local storage policy is approved on 2026-11-08.
- [ ] G4 (implementation evidence): restart, multiworker, and refusal tests must pass. Blocks enablement.
- [ ] G5 (operator and production authorization): not authorized. The owner authorized live testing only in the Mist portal NVMM lab, for named bounded tests.

## Issue Dependencies

- [ ] Issue 4636 merged. Its `state/` package, `BackupManifest`, `CanonicalDigest`, `RecordSeal`, `PersistenceUnavailable`, and `StateRefused` must exist before T004 to T011 start.
- [ ] Issue 4636 amendment for E-03 and E-04: the kind directory and the two added manifest fields.
- [ ] Issue 4636 approval of the operator identity design. Blocks any catalog endpoint (D-10).
- [x] Issue 4633 closed. Its decisions allow offline code and synthetic tests.

## Enablement

- [ ] Persistence enabled only after G2, G3 handover, G4 implementation evidence, and the issue 4636 gate pass.
- [ ] Catalog reads enabled only after the same gates pass and issue 4636 approves the operator view.
- [x] This change adds no production caller (D-17, FR-026). The writer and the catalog run only from tests.
