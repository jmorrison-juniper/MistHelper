# Security Checklist: Offline Dynamic JVD Labs Preview

**Purpose**: Check the security controls of the Labs routes before implementation review.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Request Handling

- [x] SEC-01 Each POST route is protected by the shared CSRF hook. Evidence: L-3 and R-15. Test TR-05 and TR-06.
- [x] SEC-02 The shared CSRF answer is reused. No Labs CSRF handler exists (D-8). Evidence: R-16.
- [x] SEC-03 The form accepts two fields only. Extra and repeated fields return HTTP 400 (FR-008, FR-009). Tests TR-08 and TR-09.
- [x] SEC-04 The run name matches the ASCII pattern before any planner call (FR-010). Tests TU-01, TU-02, and TR-10.
- [x] SEC-05 The field set and the run-name pattern are checked before the planner runs (`data-model.md`, "Validation Order").
- [x] SEC-06 The GET routes change no state. The capability route reads no body (`contracts/capability-response.md`).

## Output and Data Handling

- [x] SEC-07 Jinja autoescape stays on for the Labs template. Evidence: L-6. Test TU-14 checks ASCII output and TR-03 checks the page.
- [x] SEC-08 The page shows only devices, links, and the fingerprint (FR-012). Test TU-03.
- [x] SEC-09 The page never shows raw planner output (`contracts/labs-page.md`, "Forbidden Content").
- [x] SEC-10 A plan result with an unexpected or authority key shows the unavailable state (FR-015, FR-016). Tests TU-04 and TU-05.

## Authority and Scope

- [x] SEC-11 Provider access, deployment, and execution authority report `disabled` (FR-003). Test TR-01.
- [x] SEC-12 The feature adds three routes only (FR-019). Test TR-12.
- [x] SEC-13 The package imports no Mist or provider module (FR-020). Test TU-13.
- [x] SEC-14 The package does not import the private framework at load (FR-017). Test TU-12.
- [x] SEC-15 The public tests use synthetic values only (FR-018). Review item UI-02 in `ui.md`.

## Logging and Secrets

- [x] SEC-16 Logs omit raw run names and raw form values (FR-022). Test TU-14.
- [x] SEC-17 Logs use ASCII only (FR-022). Test TU-14.
- [x] SEC-18 No secret, token, or credential appears in markup, logs, or fixtures. Review item UI-02 and the bandit gate.
- [x] SEC-19 The planner failure logs the error with full context (D-14). Test TU-10.

## Open Items

- [ ] SEC-20 The owner confirms that the private framework stays local (D-16). This item stays open because it needs a human answer.
