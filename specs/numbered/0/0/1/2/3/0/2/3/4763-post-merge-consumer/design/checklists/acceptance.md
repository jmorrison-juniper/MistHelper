# Closure Checklist: Issue #4763

**Purpose**: Gate the closure of issue #4763. The orchestrator closes the issue only after all items show a checked box.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

- [x] AC-01 Immediate path: eight merges log a confirmed merge and four starts (RC-56 to RC-63).
- [x] AC-02 Merged-close path: closed runs dispatch for human merges (RC-49, RC-64).
- [ ] AC-03 Delayed path: a labeled run logs `enabled` and skips the dispatch job (task T011, query H-01).
- [ ] AC-04 Delayed path: a closed or scheduled run covers a later merge within six hours (task T011, query H-04).
- [ ] AC-05 The orchestrator approves the closure (task T012).
- [x] AC-06 Test-only merges and manual starts do not count as evidence (FR-009, RC-93).
- [x] AC-07 Workflow-file changes do not count as evidence (FR-011, RC-55).
