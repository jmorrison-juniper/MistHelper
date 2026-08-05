# Quickstart: Validate the clear-text logging work

**Feature**: 1034-codeql-cleartext-logging

**Date**: 2026-08-05

This guide states the runnable checks that prove the feature works. Run every check before
you open the final pull request. Each check names the requirement that it proves.

---

## Prerequisites

Activate the project virtual environment. The global Python interpreter in this workspace
is broken, so always use the virtual environment path.

```powershell
.venv\Scripts\Activate.ps1
```

Confirm that the GitHub command-line tool holds a token with the `security_events` scope.

```powershell
gh auth status
```

---

## Check 1: The open alert count reaches zero

**Proves**: SC-001 and SC-008.

```powershell
gh api "repos/:owner/:repo/code-scanning/alerts?state=open&per_page=100" `
  --jq '[.[] | select(.rule.id==\"py/clear-text-logging-sensitive-data\")] | length'
```

**Expected output at the start**: `19`.

**Expected output at the end**: `0`.

**Limit**: This count reflects the last completed scan of `main`. A pull request branch
shows a different count. Run the check again after the merge.

---

## Check 2: The register holds nineteen complete rows

**Proves**: SC-002 and FR-002.

```powershell
Select-String -Path specs\1034-codeql-cleartext-logging\verdict-register.md `
  -Pattern '^\| 1[78][0-9] \|' | Measure-Object | Select-Object -ExpandProperty Count
```

**Expected output**: `19`.

Then read the table and confirm that no `Verdict` cell is blank and no `Reason` cell is
blank. Contract clause C-3 and clause C-4 state the rule.

---

## Check 3: The dismissal reasons match the register

**Proves**: SC-003 and contract clause C-8.

```powershell
gh api "repos/:owner/:repo/code-scanning/alerts?state=dismissed&per_page=100" `
  --jq '.[] | select(.rule.id==\"py/clear-text-logging-sensitive-data\")
        | \"\(.number)|\(.dismissed_reason)|\(.dismissed_comment)\"'
```

Compare each output line against the matching register row. A line with no matching row
fails the check. A register row with no matching line fails the check.

---

## Check 4: The ZTP credential stays out of a redirected stream

**Proves**: SC-005, FR-009, and FR-010.

Run menu 144 with the output stream redirected to a file.

```powershell
python MistHelper.py --menu 144 > data\ztp_redirect_test.txt
```

Then search the file for the credential.

```powershell
Select-String -Path data\ztp_redirect_test.txt -Pattern 'ZTP Password:'
```

**Expected result**: The file holds the label and the withhold notice. The file holds no
credential value.

Delete the test file after the check.

```powershell
Remove-Item data\ztp_redirect_test.txt
```

**Warning**: This check calls the live Mist API and returns a real credential. Run the check
against a laboratory device. Do not run the check against a production device.

---

## Check 5: The ZTP credential still reaches an interactive terminal

**Proves**: FR-011 and acceptance scenario 1 of user story 1.

Run menu 144 on an interactive terminal with no redirection.

```powershell
python MistHelper.py --menu 144
```

**Expected result**: The screen shows the recording warning first. The screen then shows the
credential.

**Limit**: This check needs a human. No automated test can prove the interactive path,
because a test harness has no terminal. The unit test in check 8 covers the branch logic
with a fake terminal answer.

---

## Check 6: The SSH plan echo keeps every line

**Proves**: SC-010 and acceptance scenario 1 of user story 6.

Start a bulk SSH run and stop at the plan echo.

```powershell
python MistHelper.py --menu 60
```

**Expected result**: The screen shows the target hosts, the user name, and the command
count. The text matches the earlier text.

Then read the log and confirm the level.

```powershell
Select-String -Path data\script.log -Pattern 'Target hosts' | Select-Object -Last 3
```

**Expected result**: The matching lines carry the `INFO` level and not the `WARNING` level.

---

## Check 7: The address audit log holds no street address

**Proves**: FR-018 and acceptance scenario 2 of user story 3.

Run the address audit at the default log level. Then search the log.

```powershell
Select-String -Path data\script.log -Pattern 'Resolving address \(key='
```

**Expected result**: No match. The replacement line names the site identifier.

**Limit**: A raise of the log level to debug returns the address to the log. The recorded
decision states that condition, so the check runs at the default level only.

---

## Check 8: The unit tests pass

**Proves**: The branch logic of every code change.

```powershell
.venv\Scripts\python.exe -m pytest tests\unit -q
```

**Expected result**: Every test passes.

The new tests are as follows.

| Test file | Covers |
| - | - |
| `tests/unit/test_credential_console_contract.py` | Contract clause C-2, C-6, and C-8 |
| `tests/unit/test_credential_console_behavior.py` | The reveal branch and the withhold branch |
| `tests/unit/test_ssh_runner_echo_plan.py` | The `echo()` conversion of user story 6 |
| `tests/unit/test_address_resolver_log_redaction.py` | The address policy of user story 3 |
| `tests/unit/test_starlink_location_dump_guard.py` | The expiry guard of user story 4 |

---

## Check 9: The quality gates pass

**Proves**: The merge readiness of every pull request.

Run the gates exactly as the continuous integration workflow runs them. The scope of each
command matters. A narrower scope hides a failure.

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check --diff .
.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml
.venv\Scripts\python.exe -m radon cc src/ -n C
.venv\Scripts\python.exe -m bandit -r src/ MistHelper.py starlink_dashboard.py
.venv\Scripts\python.exe -m pytest --cov --cov-fail-under=80
```

**Expected result**: Every command exits with the code `0`.

**Warning**: The `radon` tool honors no suppression marker. A block above the complexity
value of 10 fails the gate. Decompose the block. Do not annotate it.

---

## Check 10: The documents meet the writing standard

**Proves**: SC-009 and FR-027.

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 `
  specs\1034-codeql-cleartext-logging\plan.md `
  specs\1034-codeql-cleartext-logging\research.md `
  specs\1034-codeql-cleartext-logging\data-model.md `
  specs\1034-codeql-cleartext-logging\quickstart.md `
  specs\1034-codeql-cleartext-logging\verdict-register.md `
  specs\1034-codeql-cleartext-logging\contracts\verdict-register.md `
  specs\1034-codeql-cleartext-logging\contracts\credential_console.md
```

**Expected result**: Every file scores 80 or above.

**Limit**: The `STE compliance` job grades a fixed file list under `documentation/`. A
document under `specs/` never reaches that job, so this check runs by hand.

---

## Check 11: The `!?` sweep matches the register

**Proves**: SC-006 and FR-017.

```powershell
Select-String -Path src\ssh\*.py, src\ssh\**\*.py -Pattern '!\?' |
  ForEach-Object { "$($_.Path):$($_.LineNumber)" }
```

Compare the output against the sweep table in `research.md` under note R-009. Every listed
line holds a recorded disposition. A new line with no disposition fails the check.

---

## Check 12: No concurrent edit collides with issue #1721

**Proves**: FR-023.

Run this check immediately before any edit to `starlink_dashboard.py`.

```powershell
gh pr list --state open --json number,title,headRefName,files `
  --jq '.[] | select(.files[].path==\"starlink_dashboard.py\")
        | \"#\(.number) \(.headRefName) \(.title)\"'
```

**Expected result**: No output.

If the command prints a pull request, stop. Wait for that pull request to merge. Record the
observed state and the date in the register.
