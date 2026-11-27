# Migration Requirements Checklist: Guest parity refresh

**Purpose**: Review the completeness, clarity, safety, and evidence quality of the migration requirements.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

**Ownership**: This is a reviewer-owned checklist. A checked box records reviewer approval of a criterion. It does not record completed implementation. Generated items stay unchecked. Implementation tools must not change their state.

## Requirement Completeness

- [ ] CHK001 Does the inventory account for every source page, dialog, control, route, and workflow? [Completeness, Spec FR-030]
- [ ] CHK002 Are the source and target commits immutable, distinct, and dated? [Traceability, Spec FR-030]
- [ ] CHK003 Are layout, color, typography, spacing, icons, and responsive rules separate from target evidence? [Completeness, Spec FR-027, FR-028]
- [ ] CHK004 Is each guest field classified, including the privacy-dependent fields? [Completeness, Spec FR-007, FR-010]
- [ ] CHK005 Do connection, site, WLAN assignment, client search, and review requirements cover each state? [Coverage, Spec FR-002, FR-003, FR-008]
- [ ] CHK006 Do grant, edit, extension, revoke, and notification requirements have an owner decision? [Coverage, Spec FR-009, FR-012, FR-013, FR-014, FR-034]
- [ ] CHK007 Are the CSV headers, aliases, preview, mapping, progress, duplicate rules, and accounting defined? [Completeness, Spec FR-015 to FR-019]
- [ ] CHK008 Is the absence of a source database or Redis migration explicit? [Assumption, Spec FR-025]

## Requirement Clarity

- [ ] CHK009 Do the scope requirements forbid implicit organization selection and broader fallback? [Clarity, Spec FR-002, FR-022]
- [ ] CHK010 Do write requirements separate schema validity, SDK availability, and observed cloud behavior? [Clarity, Spec FR-011, FR-014, FR-022]
- [ ] CHK011 Are the five-year claim, the zero-minute revoke, the read-only name, and the notification conflict explicit? [Conflict, Spec FR-011, FR-012, FR-014, FR-034]
- [ ] CHK012 Are unknown authorization, missing expiry, failure, unavailable, and true-empty results defined separately? [Clarity, Spec FR-005, FR-006, FR-023, FR-033]
- [ ] CHK013 Are the confirmation actor, payload, scope, revision, reuse, and cancellation rules specific? [Clarity, Spec FR-020, FR-021]
- [ ] CHK014 Are visual comparator tolerances gated on reviewer approval rather than set in advance? [Ambiguity, Spec FR-027]

## Requirement Consistency

- [ ] CHK015 Does the future scope keep the offline projection as the only current implementation? [Consistency, Spec FR-029]
- [ ] CHK016 Does the source license remain CC BY-NC-SA 4.0 without an invented relicense? [Consistency, Spec FR-032, D-5]
- [ ] CHK017 Do read and write access, field disclosure, audit privacy, and screenshot retention agree? [Consistency, Spec FR-007, FR-020, FR-024]
- [ ] CHK018 Do all stories use one approved scope contract and one shared store? [Consistency, Spec FR-017, FR-022, FR-025, FR-026]

## Acceptance Criteria Quality

- [ ] CHK019 Does every inventory row have a disposition, a requirement, a task, and a named test family? [Measurability, Spec FR-030]
- [ ] CHK020 Does every remaining requirement have explicit task dependencies and measurable acceptance? [Traceability, Spec FR-030]
- [ ] CHK021 Do paired screenshots require commits, viewports, themes, fixtures, and hashes? [Measurability, Spec FR-027]
- [ ] CHK022 Is target visual and runtime evidence labeled UNVERIFIED until real evidence exists? [Evidence, Spec FR-027, FR-030]
- [ ] CHK023 Are the gate counts and the rule against hidden failures explicit? [Measurability, Spec FR-030, FR-035]

## Scenario and Edge Case Coverage

- [ ] CHK024 Are stale scope, delayed responses, concurrent tabs, and invalid confirmations specified? [Coverage, Spec FR-004, FR-021, FR-033]
- [ ] CHK025 Are denied, 4xx, 429, 5xx, timeout, partial, and ambiguous outcomes specified? [Coverage, Spec FR-022, FR-023]
- [ ] CHK026 Are CSV quoting, BOM and CRLF, formula text, malformed rows, aliases, and ambiguous names covered? [Coverage, Spec FR-016, FR-017]
- [ ] CHK027 Are the CSV limit boundaries, duplicates, canceled rows, unknown rows, and restart rules defined? [Coverage, Spec FR-018, FR-019, FR-024]
- [ ] CHK028 Are duration and time-badge boundaries measurable without treating expiry as authorization? [Coverage, Spec FR-006, FR-011]
- [ ] CHK029 Are keyboard, focus, announcements, contrast, long values, and reduced-motion rules specified? [Coverage, Spec FR-028]

## Non-Functional Requirements

- [ ] CHK030 Are bounded API work and the no-ambiguous-write-retry rule explicit? [Safety, Spec FR-018, FR-022, FR-023]
- [ ] CHK031 Are credential protection, log redaction, external text handling, and actor evidence defined? [Safety, Spec FR-020, FR-024]
- [ ] CHK032 Are the shared health check, ports, session, storage isolation, dependencies, and release status preserved? [Reliability, Spec FR-025, FR-026, FR-035]
- [ ] CHK033 Are complete private backups, restart, cutover, and return to the offline mode specified? [Recovery, Spec FR-024, FR-031, FR-035]

## Dependencies and Assumptions

- [ ] CHK034 Are the decisions D-1 to D-15 recorded with alternatives, approvers, and blocking tasks? [Dependency, Spec Assumptions]
- [ ] CHK035 Are the test hierarchy, shared-file ownership, projection move, and call-site updates gated? [Dependency, Spec FR-029, FR-030]
- [ ] CHK036 Does the final original-versus-target review require approved differences and operator approval? [Dependency, Spec FR-027, FR-030, FR-031]

## Notes

- The scope is reviewer preparation for the complete future migration.
- These 36 questions grade requirements. They do not grade product behavior.
- No checkbox in this file is checked by the planning run. The reviewer owns each state change.
- The [spec quality checklist](requirements.md) is a separate file. It grades the planning quality.
