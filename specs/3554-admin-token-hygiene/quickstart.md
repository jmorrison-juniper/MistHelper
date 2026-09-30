# Quickstart: Admin Token Hygiene

## Purpose

Use this guide to validate menu 273 after implementation. This planning step
does not implement the code.

## Prerequisites

1. Use the worktree `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene`.
2. Activate the worktree virtual environment.
3. Use a Mist API token only when a live integration run is required.
4. Do not write token keys to test output, logs, or fixtures.

## Unit Validation

Run the targeted unit tests:

```powershell
Set-Location "C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene"
rtk .venv\Scripts\python.exe -m pytest tests\unit\reports\admin_token_hygiene
```

Expected result:

- All tests pass.
- The redaction test uses a sentinel token key.
- The sentinel token key does not appear in captured logs, console output, or
  written CSV content.

## Syntax and Lint Validation

Run the smallest checks that cover the changed implementation files:

```powershell
Set-Location "C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene"
rtk .venv\Scripts\python.exe -m py_compile src\reports\admin_token_hygiene\client.py
rtk .venv\Scripts\python.exe -m py_compile src\reports\admin_token_hygiene\model.py
rtk .venv\Scripts\python.exe -m py_compile src\reports\admin_token_hygiene\operation.py
rtk .venv\Scripts\python.exe -m ruff check src\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene
rtk .venv\Scripts\python.exe -m black --check src\reports\admin_token_hygiene tests\unit\reports\admin_token_hygiene
```

Expected result:

- Each compile command returns no output.
- Ruff reports no findings.
- Black reports that formatting is unchanged.

## Test Mode Validation

Run menu 273 in test mode after menu wiring exists:

```powershell
Set-Location "C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene"
rtk .venv\Scripts\python.exe MistHelper.py --test
```

Expected result:

- Test mode does not prompt for input.
- The menu 273 test path completes.
- `data\AdminHygiene.csv` exists.
- `data\TokenHygiene.csv` exists.
- The console summary counts Super Users, local admins with no two-factor
  authentication, idle tokens, and unrestricted write tokens.

## Report Contract Validation

Inspect the generated CSV headers:

```powershell
Set-Location "C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene"
rtk .venv\Scripts\python.exe -c "from pathlib import Path; print(Path('data/AdminHygiene.csv').read_text().splitlines()[0]); print(Path('data/TokenHygiene.csv').read_text().splitlines()[0])"
```

Expected admin header:

```text
admin_id,email,name,role_summary,site_scope,two_factor_state,sso_state,password_age_days,invite_expiry,findings
```

Expected token header:

```text
id,name,created_by,created_time,last_used,idle_days,privilege_summary,source_ip_restriction_present,findings
```

## Live Run Notes

Only run a live Mist API validation with an approved read-only token. If the
token has broad access, store it in the normal local environment and never copy
it into a command line, a fixture, or a log.
