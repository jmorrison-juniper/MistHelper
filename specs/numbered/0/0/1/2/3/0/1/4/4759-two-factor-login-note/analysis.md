# Analysis: Correct interactive two-factor login notes

This review compares `spec.md`, `plan.md`, `tasks.md`, and the remote evidence in `design/research.md`. Each remote check uses the identifier RC-nn from that file.

## Consistency Review

| Area | Result | Evidence |
| - | - | - |
| Spec and tasks | Consistent. Each FR maps to at least one task. | Requirement Coverage table in `tasks.md`. Traceability below. |
| Plan and tasks | Consistent. The file change map matches the task files. | `plan.md` File Change Map. |
| Spec and remote code | Consistent for the 2FA note. The note names paths that exist on `main`. | RC-02, RC-07 to RC-17. |
| Two login notes | Consistent on ports, prompts, and the browser login. | RC-13, RC-14, RC-15, RC-24, RC-34. |
| Operator guide | Consistent with both notes. The guide describes the same prompts and the same port roles. | RC-25, RC-26. |
| README | Consistent. The README already says MistHelper prompts for a verification code. No change is needed. | RC-52. |
| Count reconciliation | 67 remote checks in `research.md`, 67 entries in `STATUS.json`, and 67 checks in `summary.md`. | RC-01 to RC-67. |

## Defects In Existing Work

- **A-1 Stale issue evidence**: Owner comment IC_kwDOQltU8c8AAAABlGYtEA cites blob `f897a85e` as the state on `main`. Current `main` holds blob `98aeb3e8` (RC-01, RC-02). The comment is stale. Owner action: annotate the comment or close the issue through the fragment pull request.
- **A-2 Unlinked change**: Commit `4e81b2a4` (pull request #4924, merged 2026-11-26) changed both login notes (RC-33, RC-34). The pull request closes #4920, #4926, #4927, #4928, #4929, #4931, #4932, and #4933. It does not name #4759 (RC-60). The merge came after the owner hold comment of 2026-11-16 (RC-56). Owner action: review D-1 and D-2, and confirm the status of the hold.
- **A-3 Wrong SDK path on the two-factor page**: Line 68 names `mistapi.api.v1.admins.login.twoFactor()` (RC-03). The installed `mistapi` 0.64.1 has no `admins/login.py` (RC-04). It defines `twoFactor` in `mistapi.api.v1.login.two_factor` (RC-05). This defect is outside the MistHelper note. Owner action: file a separate issue (D-4). This change does not repair it.
- **A-4 Moved test path**: Pull request #4757 lists `tests/unit/auth/interactive/test_login_orchestrator.py`. That path is absent on `main` (RC-31). The test now sits at `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` (RC-27). This record cites the current path. No code change is needed.
- **A-5 Missing fragment**: `main` holds no release-note fragment for issue #4759 (RC-40). T003 adds it.
- **A-6 Missing candidate**: The owner comment IC_kwDOQltU8c8AAAABlEXN1g describes a candidate fragment. The candidate is absent from the repository tree, the local working tree, and `main`. T003 writes a new fragment from `spec.md`.
- **A-7 Partial signature**: The note lists `login_with_return(email, password, two_factor)`. The SDK signature starts with `apitoken` (RC-06). The note omits it. The three named parameters match the SDK. D-5 keeps the text.
- **A-8 Pre-existing wording outside the note**: Line 14 of `documentation/api/admins/POST_login.md` at `HEAD` reads "login with email/password, generate the token, and use /login/two_factor with the token". This text predates the MistHelper note. It is out of scope. Owner action: decide whether to file a separate issue.

## Positive Findings

- **A-9 Operator guide agrees**: Line 505 says the MSP sign-in section covers two-factor authentication (RC-26). Lines 575, 587 to 588, 617, and 626 at `HEAD` agree with the note. They say the terminal asks for the code, a token never asks for it, and the browser page of port 8056 has the code page.
- **A-10 No open pull request overlap**: Seven open pull requests exist. None touches the note paths or the fragment name (RC-55).
- **A-11 Cited commit exists**: Commit `c9aa2bb` is on `main` (RC-32). It is the merge commit of pull request #4757.

## Constraints And Debt

- **A-12 Owner hold**: The latest owner comment, IC_kwDOQltU8c8AAAABm4cmpA, holds commit, push, pull request, rebase, merge, and feature-hook runs (RC-56). T-PR, T-REMOTE-CI, and T-MERGE stay blocked until a new owner instruction arrives.
- **A-13 Changelog debt**: `changelog.d/` holds 335 entries on `main` (RC-51 and RC-59). The constitution permits unique records. A separate remediation issue handles the debt. This change does not.
- **A-14 Unrun gates**: The owner reports STE scores and a guard result (U-1 and U-2 in `design/research.md`). This specification step runs no gate. T-LOCAL-GATES reruns each gate.
- **A-15 STE workflow scope**: The STE workflow checks only the instruction files and the README (RC-61). The changed documentation pages rely on the local STE gate, which AGENTS.md requires for each Markdown file (RC-49). T-REMOTE-CI does not claim STE coverage for the changed pages.
- **A-16 README rule not triggered**: The constitution requires README updates only for new operations or behavior changes (RC-66). This change adds neither. The README stays unchanged, as FR-006 requires.
- **A-17 Wrong-account push risk**: A stale `GH_TOKEN` or `GITHUB_TOKEN` once pushed under another account (RC-67). T-PR clears both variables and switches to the correct account before the push.

## Unresolved Items

- **U-A (owner)**: Review the changes that pull request #4924 made to both login notes (D-1, D-2).
- **U-B (owner)**: Decide whether the hold in comment IC_kwDOQltU8c8AAAABm4cmpA still applies (D-7).
- **U-C (owner or orchestrator)**: File the separate issue for the SDK path (D-4). Agents in this session cannot create GitHub issues.
- **U-D (owner)**: Annotate the comment that cites blob `f897a85e` (A-1).
- **U-E (owner)**: Accept or reject the patch SHA-256 claim, which cannot be reproduced from remote data (U-3 in `design/research.md`).
- **U-F (owner)**: File the remediation issue for the changelog debt (A-13).

## Traceability

| Requirement | Task | Test or check |
| - | - | - |
| FR-001 | T001, T-LOCAL-GATES | Check: RC-02, RC-06 to RC-09, RC-11 to RC-17. Test: `test_two_factor_login_resends_credentials_with_installed_sdk` (RC-27) and `test_success_calls_login_with_return_with_two_factor` (RC-29). |
| FR-002 | T001 | Check: RC-07 (token branch in the SDK). Check: RC-17 and quickstart step 5 (only two callers). |
| FR-003 | T001 | Check: RC-54 (no operations portal code page). |
| FR-004 | T001 | Check: quickstart step 4 (old phrase absent at `HEAD`). |
| FR-005 | T003 | Test: the changelog guard file, 18 test functions (RC-36). |
| FR-006 | T004, T-PR | Test: `test_pull_request_does_not_edit_changelog_directly` at line 253. Check: quickstart step 9 (complete file list). |
| FR-007 | T002, T-LOCAL-GATES | Check: RC-13, RC-14, RC-15, RC-24, RC-34. Test: `test_prompt_two_factor_returns_trimmed_value` (RC-30). |
