# Migration Requirements Checklist: Guest parity

**Purpose**: Review the completeness, clarity, safety, and evidence quality of the full migration requirements.
**Created**: 2026-11-05
**Feature**: [spec.md](../../spec.md)

**Ownership**: This is a reviewer-owned requirements-quality checklist.
`[x]` means reviewer approval of a requirement criterion, not completed implementation.
Generated items remain unchecked. Implementation tools must not change their state.

## Requirement Completeness

- [ ] CHK001 Does the inventory account for every source page, dialog, control, route, and workflow? [Completeness, Spec FR-030]
- [ ] CHK002 Are source and target commits immutable, distinct, and clearly dated? [Traceability, Spec FR-030]
- [ ] CHK003 Are layout, color, typography, spacing, icons, and responsive requirements identified separately from target evidence? [Completeness, Spec FR-027/028]
- [ ] CHK004 Are all guest fields and privacy-dependent details explicitly classified? [Completeness, Spec FR-007/010]
- [ ] CHK005 Are connection, site, WLAN assignment, client search, and authorization review requirements complete? [Coverage, Spec FR-002/003/008]
- [ ] CHK006 Are grant, edit, extension, revoke, and backend-only notification requirements accounted for? [Coverage, Spec FR-009/012/013/014/034]
- [ ] CHK007 Are CSV headers, aliases, preview, mapping, progress, duplicate, and final accounting requirements defined? [Completeness, Spec FR-015/016/017/018/019]
- [ ] CHK008 Is the absence of a source database or Redis migration explicit? [Assumption, Spec FR-025]

## Requirement Clarity

- [ ] CHK009 Do approved scope requirements prohibit implicit organization selection and broader fallback? [Clarity, Spec FR-002/022]
- [ ] CHK010 Do write semantics distinguish schema validity, SDK method availability, and proven cloud behavior? [Clarity, Spec FR-011/014/022]
- [ ] CHK011 Are the five-year duration, zero-minute revoke, read-only name, and notification conflicts explicit? [Conflict, Spec FR-011/012/014/034]
- [ ] CHK012 Are unknown authorization, missing expiry, failure, unavailable, and true-empty results separately defined? [Clarity, Spec FR-005/006/023/033]
- [ ] CHK013 Are confirmation actor, payload, scope, revision, reuse, and cancellation constraints specific? [Clarity, Spec FR-020/021]
- [ ] CHK014 Are visual comparator tolerances and permitted differences gated on approval rather than invented? [Ambiguity, Spec FR-027]

## Requirement Consistency

- [ ] CHK015 Does full future specification scope preserve the offline-only current implementation boundary? [Consistency, Spec FR-029]
- [ ] CHK016 Does source authorship authorization remain resolved without an invented relicense? [Consistency, Spec FR-032]
- [ ] CHK017 Do read/write access, field disclosure, audit privacy, and screenshot retention align? [Consistency, Spec FR-007/020/024]
- [ ] CHK018 Do all stories use one approved scope contract and shared application/store ownership? [Consistency, Spec FR-017/022/025/026]

## Acceptance Criteria Quality

- [ ] CHK019 Does every inventory row have a disposition, requirement, task, and named acceptance family? [Measurability, Spec FR-030]
- [ ] CHK020 Does every remaining requirement have explicit task dependencies and measurable acceptance? [Traceability, Spec FR-030]
- [ ] CHK021 Are paired source/target screenshot commits, viewports, themes, fixtures, and hashes required? [Measurability, Spec FR-027]
- [ ] CHK022 Is target visual/runtime evidence labeled UNVERIFIED until actual evidence exists? [Evidence, Spec FR-027/030]
- [ ] CHK023 Are required gate counts and absence of hidden failure explicit? [Measurability, Spec FR-030/035]

## Scenario and Edge Case Coverage

- [ ] CHK024 Are stale scope, delayed responses, concurrent tabs, and invalid confirmation scenarios specified? [Coverage, Spec FR-004/021/033]
- [ ] CHK025 Are denied, 4xx, 429, 5xx, timeout, partial, and ambiguous outcomes specified? [Coverage, Spec FR-022/023]
- [ ] CHK026 Are CSV quoting, BOM/CRLF, formula strings, malformed rows, aliases, and ambiguous names covered? [Coverage, Spec FR-016/017]
- [ ] CHK027 Are CSV limit boundaries, duplicates, canceled rows, unknown rows, and restart rules defined or gated? [Coverage, Spec FR-018/019/024]
- [ ] CHK028 Are duration and time badge boundaries measurable without equating expiry to authorization? [Coverage, Spec FR-006/011]
- [ ] CHK029 Are keyboard, focus, announcements, contrast, long values, and reduced-motion requirements specified? [Coverage, Spec FR-028]

## Non-Functional Requirements

- [ ] CHK030 Are bounded API work and no-ambiguous-write-retry requirements explicit? [Safety, Spec FR-018/022/023]
- [ ] CHK031 Are token protection, log redaction, external-text handling, and actor evidence requirements defined? [Safety, Spec FR-020/024]
- [ ] CHK032 Are shared health, ports, session, storage isolation, dependencies, and release status requirements preserved? [Reliability, Spec FR-025/026/035]
- [ ] CHK033 Are complete private backups, restart, cutover, and return to offline mode requirements specified? [Recovery, Spec FR-024/031/035]

## Dependencies & Assumptions

- [ ] CHK034 Are D1-D7 alternatives, approvers, blocking tasks, and non-enabling defaults explicit? [Dependency, Spec Assumptions]
- [ ] CHK035 Are package/test hierarchy, shared-file ownership, projection move, and call-site requirements gated? [Dependency, Spec FR-029/030]
- [ ] CHK036 Does final original-versus-target review require approved differences and operator approval? [Dependency, Spec FR-027/030/031]

## Notes

The scope is formal reviewer preparation for the complete future migration.
These 36 questions grade requirements, not product behavior.
No new policy question was necessary because the user permitted explicit implementation gates.
The built-in [requirements checklist](requirements.md) is separate from this reviewer-owned checklist.
