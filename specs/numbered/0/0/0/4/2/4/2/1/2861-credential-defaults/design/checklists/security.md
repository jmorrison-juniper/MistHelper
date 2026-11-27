# Security Checklist: Credential default audit

**Purpose**: Check that the credential requirements are clear and complete.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

- [x] CHK001 The record names no credential value. Each literal stays masked in research.md.
- [x] CHK002 Prompted tokens stay in process memory and never reach logs (FR-008, TST-14).
- [x] CHK003 Prompts use hidden input and handle end of file and interrupts (FR-007, TST-13).
- [x] CHK004 No default database account is selected silently (FR-001, FR-004, TST-06, TST-09).
- [x] CHK005 Conflicting token values are refused before any Mist call (FR-009).
- [x] CHK006 The allowlist test blocks a new implicit SDK environment read (FR-017, TST-16).
- [x] CHK007 The plan adds no suppression comment such as `# nosec`, `# noqa`, or `# type: ignore`.
- [ ] CHK008 Container credential defaults remain open. Explanation: decision D-7 is a human decision (FR-018).
- [ ] CHK009 The configured-token fallback remains open. Explanation: decision D-6 is a human decision (FR-013).
- [ ] CHK010 The legacy token name remains readable. Explanation: decision D-5 is a human decision (FR-009).
