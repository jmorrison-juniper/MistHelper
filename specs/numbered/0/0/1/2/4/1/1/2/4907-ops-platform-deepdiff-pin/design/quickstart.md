# Quickstart: Ops Platform Deepdiff Pin

## Reproduce the failure (read only)

Run these commands in PowerShell. The token line follows the brief. Each command uses GET requests only.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh run view 45064277976 -R jmorrison-juniper/MistHelper --log-failed
```

Expected lines in the log, in order:

- `Collecting deepdiff==9.2.1 (from -r requirements.txt (line 56))`
- `ERROR: Cannot install None and deepdiff==9.2.1 because these package versions have conflicting dependencies.`
- `mist-ops-platform 0.1.0 depends on deepdiff<9.0 and >=8.6.2`
- `ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts`
- `##[error]Process completed with exit code 1.`

No line of the log shows `test session starts` or `collected`. The failing check is `pytest (ops platform)`, and its failing step is `Install dependencies`.

Read the job table of the same run:

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh run view 45064277976 -R jmorrison-juniper/MistHelper --json jobs
```

## Confirm the main baseline (read only)

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh run view 45774119357 -R jmorrison-juniper/MistHelper --json jobs
```

Expected: the job `pytest (ops platform)` reports conclusion `success`.

## Verify the local change (after T003 and T004)

Run these commands from the worktree root of the change branch, with the `.venv` of the checkout.

```powershell
python -m pytest tests/guardrails/test_dependency_export.py -q -s
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
python -m ruff check .
python -m black --check .
symbol-diff --base origin/main tests/guardrails/test_dependency_export.py
```

Expected results:

- The `-s` output holds the line `ops platform pins: examined 22 pins, 0 defects`.
- The changelog policy test passes.
- Ruff prints `All checks passed`.
- Black reports that no file needs a change.
- Symbol diff prints `no module-level name changed`.

## Verify the negative case

The test method builds the negative case in memory. It replaces the deepdiff pin with `deepdiff==9.2.1` and requires exactly one defect, `deepdiff`. No repository file changes during the check.
