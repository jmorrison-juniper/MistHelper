# Quickstart: Site Variable Audit

## Purpose

Use this guide to validate the Site Variable Audit implementation after the
task workflow creates the source files.

## Prerequisites

1. Open the feature worktree.

   ```powershell
   Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
   ```

2. Use the worktree virtual environment.

   ```powershell
   C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe --version
   ```

3. Confirm that the source package exists after implementation.

   ```powershell
   Test-Path -LiteralPath 'src\reports\site_variable_audit'
   ```

## Unit validation

Run the model and client fixture tests. These tests must not use the network.

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m pytest tests\unit\reports\site_variable_audit
```

Expected result:

- The scanner finds tokens in nested dictionaries.
- The scanner finds tokens in lists.
- The scanner normalizes `{{ name }}` to `name`.
- The scanner ignores malformed brace text.
- The client tests use fixtures and no network.
- The report rows use deterministic order.

## Local syntax and style validation

Run the smallest gates for the new package and tests.

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m py_compile src\reports\site_variable_audit\client.py src\reports\site_variable_audit\model.py src\reports\site_variable_audit\operation.py
```

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m ruff check src\reports\site_variable_audit tests\unit\reports\site_variable_audit
```

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m black --check src\reports\site_variable_audit tests\unit\reports\site_variable_audit
```

Expected result:

- Syntax validation returns no output.
- Ruff reports no findings.
- Black reports that files would remain unchanged.

## Operation validation

Run the safe test mode after integration adds Menu 275.

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe MistHelper.py --test
```

Expected result:

- The operation does not prompt.
- `data\SiteVariableAudit.csv` exists.
- `data\SiteVariableSummary.csv` exists.
- The console summary prints the count of sites with missing variables.

## Manual report inspection

Inspect the CSV outputs after a fixture or dry-run path creates them.

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
Import-Csv -LiteralPath 'data\SiteVariableAudit.csv' | Select-Object -First 5
```

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3556-site-variable-audit'
Import-Csv -LiteralPath 'data\SiteVariableSummary.csv' | Select-Object -First 5
```

Expected result:

- Each audit row names the site, template type, template name, variable name,
  and field path.
- Each summary row names counts for required, defined, missing, and unused
  variables.

## Deferred integration checks

The integration pull request must prove these items:

- Menu 275 calls `SiteVariableAudit.run()`.
- `SiteVariableAudit.run()` takes no positional argument.
- The `OperationRegistry` entry marks Menu 275 as safe.
- The generated menu references include Menu 275.
- `specs\3556-site-variable-audit\wiring.md` names each changed integration
  surface.
- `changelog.d\issue-3556-site-variable-audit.md` exists.
