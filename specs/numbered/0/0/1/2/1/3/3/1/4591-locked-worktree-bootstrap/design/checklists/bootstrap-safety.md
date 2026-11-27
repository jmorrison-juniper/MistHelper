# Bootstrap Safety Checklist: Locked Worktree Bootstrap

**Purpose**: Check the safety, secret, and logging requirements of the change before review.
**Created**: 2026-11-26
**Feature**: `spec.md` and `design/contracts/bootstrap-lock-cause.md`

## Secrets and Output

- [x] SAF-001 No cause message prints an index URL, a host name, or a credential (FR-003, SC-004). TC-02 checks it.
- [x] SAF-002 Index variable names appear in output, and values do not (FR-004). TC-03 and TC-05 check it.
- [x] SAF-003 Output uses ASCII characters only (Constitution Principle V).
- [x] SAF-004 Secrets never reach a test fixture. The tests use the fixed public index and the example mirror name only.

## Lock Enforcement

- [x] SAF-005 The locked sync uses `--locked` and never a frozen sync (FR-002).
- [x] SAF-006 The lock check uses the same child environment as the locked sync (contract section 6).

## Configuration Safety

- [x] SAF-007 The bootstrap never writes the pip configuration (FR-005). The contract names this invariant.
- [x] SAF-008 Index variables change only in the child environment. The caller environment stays unchanged (existing `_install_environment` behavior, lines 636 to 650).
- [x] SAF-009 The public index serves the locked sync only through `--public-lock-index` or the existing probe (contract section 6).

## Process Safety

- [x] SAF-010 No shell string is built. Every subprocess call uses an argument list (existing behavior).
- [x] SAF-011 No suppression comment is added. A security finding is fixed, not hidden (Constitution, "Security Findings").
- [x] SAF-012 Each new log line has an info line before the action and a debug line after it (Constitution Principle VII). The review checks this rule.
- [x] SAF-013 Each changed line has an inline comment (Constitution Principle VI). The review checks this rule.
- [x] SAF-014 The change adds no destructive action. The only file write is the changelog fragment and the documentation edit.
