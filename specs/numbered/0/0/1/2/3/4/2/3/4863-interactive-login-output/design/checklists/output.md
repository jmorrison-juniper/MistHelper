# Output Checklist: Interactive Login Output

**Purpose**: Check each printed line and each log record of the interactive login against the channel rules in `design/contracts/operator-output.md`

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Channel Rules

- [x] Each direct output line of the contract has a source line in the remote file of `main`, as the research table shows.
- [x] Each progress line writes an info record, and no direct output duplicates it.
- [x] Each deleted progress line has an info record that stays (lines 84, 137, 170, 198, and 237 of `login_orchestrator.py`).
- [x] Each failure line keeps its warning or error record (RC-04, RC-17, RC-21, RC-26).
- [x] The 2FA success line follows the debug record of the 2FA result, and it appears only when `authenticated` is true (RC-13, RC-75).
- [x] The cancel record is an info record, and the direct output line "Cancelled." stays (RC-01, RC-02).
- [x] The MSP picker lines follow the cloud menu rules, and only the switch flow shows them (RC-31).

## Text Rules

- [x] Prompt wording is unchanged for the cloud, email, password, 2FA, MSP, and organization prompts.
- [x] No new printed line uses an ellipsis or a placeholder.
- [ ] Explained: each new printed line uses ASCII text. This check runs in T017 after the change, because the file content does not exist yet.
- [ ] Explained: each changed line carries an inline comment that states its channel. This check runs in T017 after the change, because the file content does not exist yet.

## Verification Links

- [x] Each contract row maps to a test in `design/quickstart.md` or to a manual step in scenario 6 or scenario 7.
- [ ] Explained: the manual terminal check (scenario 6) runs after the pull request exists, with a live account. The operator records the result in the pull request.
