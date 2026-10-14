# Guard Requirements Checklist: Backup restoration

**Purpose**: Reviewer assessment of destructive restoration requirements.

**Created**: 2026-10-14

**Feature**: [Specification](../spec.md)

These markers belong to the reviewer.
A checked marker means requirement-quality approval, not completed implementation.

## Completeness

- [ ] CHK001 Are complete writable restoration and server-managed exclusions explicitly bounded? [Completeness, Spec FR-004, FR-005]
- [ ] CHK002 Are absent fields, deletion, inheritance, and unknown fields defined without silent omission? [Clarity, Spec FR-006, FR-007]
- [ ] CHK003 Are cloud provenance limits and checksum authenticity limits explicit? [Clarity, Spec FR-003]
- [ ] CHK004 Are saved site ownership, current membership, and selection dependencies defined? [Completeness, Spec FR-008, FR-009]

## Failure safety

- [ ] CHK005 Is verified recovery coverage required for every target before any write? [Consistency, Spec FR-012]
- [ ] CHK006 Are stale settings, stale membership, and changed source bundles addressed? [Coverage, Spec FR-013]
- [ ] CHK007 Are failed writes, failed saved-state checks, and remaining targets distinguished? [Clarity, Spec FR-014, FR-015]
- [ ] CHK008 Are cancellation, dry run, and exact confirmation requirements measurable? [Measurability, Spec FR-011, SC-001]

## Privacy and acceptance

- [ ] CHK009 Are hostile files, private ownership, and original-file preservation requirements explicit? [Completeness, Spec FR-002, FR-017]
- [ ] CHK010 Are browser, log, and output secret boundaries consistent? [Consistency, Spec FR-010, FR-017]
- [ ] CHK011 Are CLI and graphical acceptance scenarios defined independently? [Coverage, Spec SC-005]
- [ ] CHK012 Does acceptance distinguish offline evidence from actual user approval and production restoration? [Clarity, Spec Assumptions]

## Notes

The implementation command reads these markers but does not change them.
Autonomous development continues under the explicit user authorization.
Optional checklist commit hooks are deferred.
