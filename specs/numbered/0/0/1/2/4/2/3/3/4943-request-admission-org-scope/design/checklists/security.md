# Security Checklist: Ship the preserved admission scope work

**Purpose**: Check each credential and logging rule of the change before the ship. A checked item means that the requirement exists in `spec.md` with a named test or check. Runtime proof comes from the tasks in `tasks.md`.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Credential Handling

- [x] The ledger stores only the SHA-256 hex digest of the authentication header (FR-010). The digest appears in `data-model.md` under Credential fingerprint.
- [x] A request with neither an `Authorization` header nor a `Cookie` header fails closed (FR-011). The contract `contracts/admission-scope.md` names the message.
- [x] The credential never appears in a rendered traceback. The frame-locals test checks this rule (FR-012 and SC-002).
- [x] The output on a non-terminal stream holds no ESC character (FR-013 and SC-003).
- [x] The organization scope refuses an empty identifier (FR-008).

## Logging

- [x] The new info line names the MSP identifier only. The new debug line names the status only (`contracts/operator-messages.md`).
- [x] The SDK error lines of the MSP call stay out of the handlers during the call (FR-016). The filter ends on every exit path (FR-017).
- [x] The client error line for a transport failure stays visible (FR-018).
- [x] Each new log line uses ASCII only (constitution Principle V).

## Repository Hygiene

- [x] The change adds no suppression comment (`#nosec`, `# noqa`, or `# type: ignore`). The plan's security rule forbids that form, and T-LOCAL-GATES checks the changed lines.
- [x] The record holds no token, password, or header value. The ship keeps the same rule for the tests and the fragment.
- [x] The live check uses an operator token from the owner secret store (`design/quickstart.md`, step 8). The record stores no token.

## Open Items

- [ ] The live menu 308 check with a real token is open. The owner runs it after the merge (decision D-13, unresolved item UR-3 in `analysis.md`). The unit tests cover the same paths with fake doubles.
- [ ] The traceback color defect is confirmed from source only. The red run in T007 confirms it at runtime (unverified item U-7 in `design/research.md`).
