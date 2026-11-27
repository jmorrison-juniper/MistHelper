# Security Requirements Checklist: Add independently authored converter visual journeys

**Purpose**: Confirm that the secret, input, storage, and cloud requirements are complete and testable before implementation starts.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

- [x] SEC001 No credential or environment value is read or printed by a test (FR-012, D-13). The rule is testable by review of the test module.
- [x] SEC002 Browser traffic stays on the loopback address (FR-011, D-11). A route guard aborts other hosts and counts them (T013).
- [x] SEC003 User text renders through `textContent` only (FR-010, RC-12, RC-15). The residual risk is the content security policy, which allows inline script (RC-42). The DOM rule is the control. Explained.
- [x] SEC004 Export needs the typed word `EXPORT` and a current review. The server checks the review on each request (D-2, D-6, RC-17).
- [x] SEC005 The converter writes no browser storage key. Only the host key `misthelper-theme` may exist (D-4, RC-15, RC-32).
- [x] SEC006 The browser script writes no log line that carries user content (U-2). The server logging stays unchanged.
- [x] SEC007 Traces and screenshots hold synthetic input only. The output folder is ignored by Git (RC-60).
- [x] SEC008 No browser test sends a cloud write or a live credential (FR-011, FR-012).
- [x] SEC009 The session secret policy stays unchanged. Issue #4636 (D-5 and D-15) owns the policy. Explained.
