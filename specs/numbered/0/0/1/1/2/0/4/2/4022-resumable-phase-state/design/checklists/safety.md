# Safety Requirements Quality Checklist: Persist resumable firmware phase state

**Purpose**: Check the safety and security requirements of the resume before implementation.
**Created**: 2026-11-26
**Feature**: `spec.md`, `plan.md`, `design/contracts/`

## Confirmation and command safety

- [x] CHK101 The resume needs the exact typed word RESUME before any Mist request (FR-007, FR-008).
- [x] CHK102 A resume refuses another operator's site lock (FR-009).
- [x] CHK103 The route refuses a run that is not stopped or has no recovery point (FR-006, FR-009).
- [x] CHK104 The route refuses a live driver thread (FR-009).

## Firmware write protection

- [x] CHK105 A device at its target version receives no firmware (FR-011).
- [x] CHK106 A settled or skipped phase receives no firmware and no wait (FR-012).
- [x] CHK107 At most one firmware call runs for the recovery phase in each attempt (FR-013).
- [x] CHK108 An unknown reply stops the write until reconciliation proves the outcome (FR-014, FR-021).
- [x] CHK109 A later phase waits for the recovery phase to settle (FR-016).

## Lock and hold protection

- [x] CHK110 The site hold stays active while a phase is unknown or unsettled (FR-017).
- [x] CHK111 The lock does not release at stopped or failed while the hold stays active (FR-018).
- [x] CHK112 The start, pre-check, takeover, and retry routes refuse during a hold (FR-022).

## Persistence and evidence

- [x] CHK113 Each recovery point and attempt has a verified write (FR-003).
- [x] CHK114 A failed verified write keeps the hold and reports no clean stop (FR-004).

## Logging and secrets

- [x] CHK115 Each resume action writes an info line before it runs and a debug line after it runs (FR-029).
- [x] CHK116 Logs and records hold no secret and no actor email (contract resume-route.md, Logging).

## Mist access

- [x] CHK117 Each Mist request uses a named mistapi function (FR-028). The guard test runs in the delivery gates.
- [ ] CHK118 Not checked: live Mist behavior of the job listing after an unknown reply. Research U-02 records this item. The operator reviews the evidence (FR-014).

## Review gate

- [x] CHK119 The pull request carries the needs-human-review label and no auto-merge label (T-PR, T-MERGE).
- [x] CHK120 The owner approves the start before implementation (T000, D-11).

## Notes

- CHK118 remains open because no live request ran during this record.
