# Quickstart: Interactive Login Output

This guide proves the change end to end. Run each scenario from the worktree root with the Python 3.15 environment of the repository. The scenarios 1 to 5 need no network and no credential. Scenario 6 is a manual check for an operator with a live account. It uses a read-only account, and it shows the terminal output of a real login.

## Prerequisites

- The worktree for branch `fix/4863-interactive-login-output`, created from `origin/main`.
- The environment from `scripts/bootstrap_worktree.py`, or the `.venv` of the main checkout. Remote check RC-65 gives the Windows entry point.
- For scenario 6 only: the account, the cloud, and the 2FA device of the operator. Keep the password and the code out of shared screens and out of recorded sessions.

## Scenario 1: Reproduce the defect before the change

Run the new cloud menu tests on the untouched branch.

```powershell
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_clouds.py -q
```

Expected before the change: the tests fail. The failures show a warning record for the banner and the menu lines. This proves that the defect exists (FR-001, FR-002).

## Scenario 2: Login sequence, 2FA success, redaction, and SDK console level

```powershell
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -q
```

Expected after the change: every test passes. The 2FA success test shows the success line in the captured output. The sentinel test finds no password value and no code value in the output or in the log records. The real-SDK test finds no SDK success line in the output and finds the SDK error line for a refused password.

## Scenario 3: MSP picker

```powershell
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py -q
```

Expected after the change: every test passes. The invalid input tests still find their warning records.

## Scenario 4: Cancel record of the switch flow

```powershell
python -m pytest tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py -q -k cancel_logs_info
```

Expected after the change: the test passes. The cancel record is an info record, and no warning record exists.

## Scenario 5: Failure and validation lines keep their records

```powershell
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py -q
```

Expected: every test passes without any edit to `test_credential_prompter.py`. The validation assertions still find their warning records.

## Scenario 6: Manual terminal check with a live account (operator)

Use a read-only account that requires 2FA. Set `CONSOLE_LOG_LEVEL=30` in the git-ignored `.env` file of the checkout.

1. Run `python MistHelper.py --login`.
2. Press Enter at the cloud prompt, or type the cloud number.
3. Type the email, the password, and the 2FA code when the prompt appears.
4. Confirm that the cloud menu, the 2FA banner, and the two success lines show no warning label. The contract lists the exact text.
5. Confirm the terminal shows no line that starts with the SDK label `[  INFO   ]` for the login.
6. Type `0` at the menu prompt to exit.

Expected: each step matches the list. A failure of step 4 or step 5 stops the check. Record the result in the pull request, without the password and without the code.

## Scenario 7: MSP picker in the switch flow (operator)

1. Start the tool with an API token in `.env`.
2. Choose menu 143, which is the switch to interactive login.
3. Type `y` at the confirmation prompt.
4. Complete the login with an account that has two or more MSP grants.
5. Confirm the banner `SELECT MSP AND ORGANIZATION` and the MSP menu appear as plain text.
6. Type `q` at the organization picker to skip, then type `0` to exit.

Expected: the banner and the menu show no warning label. An invalid MSP number still shows a warning label.

## Full local gate list

The complete list of gates and the expected results is in `tasks.md`, task T-LOCAL-GATES. The list follows the local gates table of `.github/copilot-instructions.md`.
