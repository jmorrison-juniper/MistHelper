# Migration Requirements Checklist: MistDSW

**Purpose**: Review source contracts, reuse limits, and integration requirements.
**Created**: 2026-10-15
**Feature**: [Specification](../../spec.md)

**Ownership**: These 12 items belong to the PR reviewer.
An approved item means that its requirements are complete, not that product implementation is complete.

## Requirement Completeness

- [ ] CHK001 Are all four source workflows bounded explicitly? [Completeness, Spec FR-001]
- [ ] CHK002 Are all supported input formats and rejection rules documented? [Coverage, Spec FR-002]
- [ ] CHK003 Are template replacement and preservation limits explicit? [Clarity, Spec FR-006, FR-007]
- [ ] CHK004 Are network and service output counts specified? [Completeness, Spec FR-008]

## Requirement Consistency

- [ ] CHK005 Are Guest and Realo conflicts treated as approval conditions rather than defaults? [Consistency, Spec FR-010]
- [ ] CHK006 Is one authoritative database required without a feature-specific service? [Consistency, Spec FR-013]
- [ ] CHK007 Are CLI and portal workflows required to share generation behavior? [Consistency, Spec FR-012]
- [ ] CHK008 Is automatic deployment clearly outside the feature? [Coverage, Spec FR-016]

## Acceptance Criteria Quality

- [ ] CHK009 Are performance limits, batch size, and reference-host conditions quantified? [Measurability, Spec SC-003]
- [ ] CHK010 Are privacy, retention, and ownership outcomes measurable? [Coverage, Spec FR-014, SC-005, SC-007]
- [ ] CHK011 Are source reuse permissions tied to the exact material and revision? [Dependency, Spec FR-017]
- [ ] CHK012 Are planning completion and implementation authorization distinguished? [Clarity, Spec FR-018]

## Notes

All 12 items have traceability references.
The author evaluated their written criteria in [analysis](../analysis.md).
The author leaves reviewer checkboxes unchanged.
