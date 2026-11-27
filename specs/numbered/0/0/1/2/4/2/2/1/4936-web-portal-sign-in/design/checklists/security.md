# Security checklist: Browser sign-in with 2FA for the web portal

**Purpose**: Check each credential rule of the browser sign-in before implementation.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Credential handling

- [x] The password comes only from the request body. Evidence: FR-004, task T007, test T018.
- [x] The password and the 2FA code never reach a log record, a response, a cookie, or a file. Evidence: FR-004, FR-017, test T020, and `design/contracts/log-records.md`.
- [x] The SDK never prompts in a request. Evidence: FR-015, tests T018 (the prompt contract) and T007.
- [x] The browser flow never calls `APISession.login()` or `login_with_return()`. Evidence: FR-005, test T018, and `design/contracts/sdk-calls.md`.
- [x] The SDK token list is empty and the retry count is 0 before the first call. Evidence: FR-011, test T018.
- [x] The password step keeps no password after the call. Evidence: `plan.md` risk table and `research.md` D-4.
- [x] The exception record carries the class name only. Evidence: `design/contracts/log-records.md` and test T020.

## Request protection

- [x] Every POST uses the CSRF protection. Evidence: FR-014, test T019.
- [x] The allowlist covers every sign-in page. Evidence: FR-014, test T022.
- [x] Each sign-in response carries `Cache-Control: no-store`. Evidence: FR-014, test T019.
- [x] The browser identifier cookie is HttpOnly and SameSite Lax. Evidence: task T009 and `design/contracts/http-api.md`.
- [x] The cloud host comes from the catalog only. Evidence: FR-002, test T019 (unknown cloud).

## Session control

- [x] The process session changes only under one lock. Evidence: FR-007, test T020 (holders share one value).
- [x] A session change is refused while an operation runs. Evidence: D-17, test T019.
- [x] Pending sign-ins expire after 300 seconds and are bounded to 64 records. Evidence: FR-010, test T017.
- [x] The session lifetime accepts 10 to 20160 minutes only. Evidence: FR-009, test T017.
- [x] A missing lifetime sets no timer and logs one warning. Evidence: test T020.

## Open items

- [x] Explained, open: D-1 (credential policy for browser password entry) needs a human decision before the pull request merges.
- [x] Explained, open: D-3 (one process session) needs a human decision before implementation.
- [x] Explained, open: the live 2FA path needs the owner check that issue #4925 tracks (U-1).
