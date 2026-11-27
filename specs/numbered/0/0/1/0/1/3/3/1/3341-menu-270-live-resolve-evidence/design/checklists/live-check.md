# Live Check Checklist: Menu 270 Owner Run

**Purpose**: Gate the owner before and after the one approved live resolve request.
**Created**: 2026-11-26
**Feature**: `spec.md`, FR-001 to FR-011

## Before the Run

- [ ] CHK101 The owner approves in writing one lab organization label and one Marvis Action topic.
- [ ] CHK102 The preview of mode 3 lists exactly one action. The count reads 1.
- [ ] CHK103 Issue #4389 names a cause, or the owner approves a new run after the 2026-10-21 refusal.
- [ ] CHK104 The owner's Mist access is configured outside the repository. No credential is written in a file or in the issue.
- [ ] CHK105 The acknowledge answer is planned as blank.

## During the Run

- [ ] CHK106 The operator types `RESOLVE 1` exactly, and types nothing else at the confirmation prompt.
- [ ] CHK107 The operator leaves the acknowledge answer blank.

## After the Run

- [ ] CHK108 The results file shows one row. The row shows the outcome, the HTTP status, and the verified status.
- [ ] CHK109 The owner evidence record follows `design\contracts\live-evidence-record.md`.
- [ ] CHK110 If the outcome is `error`, the owner does not retry. The owner adds the message to issue #4389.
