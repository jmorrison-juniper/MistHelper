# Approval and Verification Gates: Guest authorization workflows

**Purpose**: List each gate that blocks a task, the evidence that clears it, and the owner of that evidence.
**Created**: 2026-11-26
**Record**: [spec.md](../../spec.md)

## Gate Status

| Gate | Condition | Evidence that clears it | Owner | State on 2026-11-26 | Tasks blocked |
| --- | --- | --- | --- | --- | --- |
| G1 Rights | Clean-room path, or a recorded compatible path | Decision D-3 and the owner comment of 2026-11-06 | Owner | Resolved by D-3. Owner to record on issue 4278 (UR-7) | T002 |
| G2 Access | Trusted identity and allowed scopes, with cross-scope tests | Decision D-4 and its human approval | Maintainers | Open. HUMAN-DECISION-REQUIRED | Every read and write task, T004 onward |
| G3 Bounds | Approved byte and row limits | Decision D-13 and an owner record on issue 4278 | Maintainers | Proposed in D-13. Approval open (UR-5) | T008, CSV run |
| G4 Audit | Approved attribution, durable sink, failure handling | Decisions D-14 and D-15 and an owner record on issue 4278 | Maintainers | Proposed in D-14 and D-15. Approval open (UR-5) | T006, T007, T008 |
| G5 Contracts | Verified grant, extension, read-back, client fields, and paging | Live evidence from one approved run for each open item (U01 to U05) | Implementer and owner | Open. No live call made in this run | FR-011, FR-012, FR-008, T007 writes |
| PR 4208 | Handover of two shared files | Owner record on issue 4278 or closed PR 4208 | Owner | Open (R093) | T010, T011 |

## Gate Rules

- A gate clears only when its evidence exists and the owner records it on issue 4278.
- A task starts only when each gate it lists has cleared.
- Warning: a write enabled before G5 can change access with no verified result. Keep the write controls disabled until G5 clears.
- Live verification runs need owner approval for each run (UR-9). The owner comment of 2026-11-08 approves live tests in general. It does not set a run limit (U16).

## Blocking Summary

- While G2 is open, the page shows the disabled state. No record appears.
- While G2 and G5 are open, no write control becomes active.
- While G3 is open, the import control stays disabled.
- While G4 is open, no write control becomes active, because each write needs an intent row.
- While PR 4208 is open, no task edits `web_portal/app.py` or `web_portal/templates/base.html`.
