# Quickstart: Dash pytest plugin marker warning

This file gives the exact steps to reproduce the warning and the exact verification commands. Run each command from the repository root. Each Windows block uses PowerShell. Each Linux and macOS block follows it.

## 1. Prepare the environment

Windows:

```powershell
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

Linux and macOS:

```bash
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
source .venv/bin/activate
```

The bootstrap command comes from `.github/copilot-instructions.md` lines 29 to 35 (remote check RC-15).

## 2. Reproduce the warning

Windows:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/refactors/test_app_context_session_state.py -q --no-cov
```

Linux and macOS:

```bash
.venv/bin/python -m pytest tests/unit/refactors/test_app_context_session_state.py -q --no-cov
```

Expected result: the warning summary names PytestRemovedIn10Warning and points to `dash/testing/plugin.py:104`. The issue quotes this text: `PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).` The issue states that the tests pass. This record did not run the command.

## 3. Confirm the source line in the installed package

Windows:

```powershell
Select-String -LiteralPath .venv\Lib\site-packages\dash\testing\plugin.py -Pattern "tryfirst"
```

Linux and macOS:

```bash
grep -n "tryfirst" .venv/lib/python3.15/site-packages/dash/testing/plugin.py
```

Expected result: line 104 holds `@pytest.mark.tryfirst` on `pytest_addhooks` (RC-43).

## 4. Confirm the upstream state (read only)

Read the latest release tag:

```powershell
gh api repos/plotly/dash/releases/latest --jq .tag_name
```

Read the plugin file at that tag. Replace `v4.5.1` with the tag from the previous command:

```powershell
$plugin = gh api "repos/plotly/dash/contents/dash/testing/plugin.py?ref=v4.5.1" | ConvertFrom-Json
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($plugin.content -replace '\s', '')))
($text -split "`n")[103]
```

Expected result at `v4.5.1`: `@pytest.mark.tryfirst` (RC-48). Expected result at `dev`: `@pytest.hookimpl(tryfirst=True)` (RC-49). The upgrade trigger in task T008 needs a release tag whose line 104 shows `pytest.hookimpl`.

## 5. Run the policy tests

Windows:

```powershell
.venv\Scripts\python.exe -m pytest tests/contract/test_pytest_coverage_gate.py -q --no-cov -k DashPytestPluginPolicy
```

Linux and macOS:

```bash
.venv/bin/python -m pytest tests/contract/test_pytest_coverage_gate.py -q --no-cov -k DashPytestPluginPolicy
```

Expected result: `6 passed`. The policy tests come from task T004.

## 6. Run the journey test

Windows:

```powershell
.venv\Scripts\python.exe -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py -q --no-cov
```

Linux and macOS:

```bash
.venv/bin/python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py -q --no-cov
```

Expected result: all tests pass. The owner reports that `-p no:dash` makes `test_complete_offline_journey` fail (RC-57). Confirm that report only with a run that is recorded in the issue.

## 7. Run the warning gate (upgrade change only)

Windows:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/refactors/test_app_context_session_state.py -q --no-cov -W error::pytest.PytestRemovedIn10Warning
$LASTEXITCODE
```

Linux and macOS:

```bash
.venv/bin/python -m pytest tests/unit/refactors/test_app_context_session_state.py -q --no-cov -W error::pytest.PytestRemovedIn10Warning
echo $?
```

Expected result after the upgrade: exit code 0. Before the upgrade, the command must fail. PR #4831 reported a failing exit code before its fix. This record did not run the command.

## 8. Confirm that the configuration holds no suppression

Windows:

```powershell
Select-String -LiteralPath pyproject.toml -Pattern "no:dash|filterwarnings"
```

Linux and macOS:

```bash
grep -n -E "no:dash|filterwarnings" pyproject.toml
```

Expected result: no output. The root configuration holds no such entry at remote main (RC-05, RC-06).

## 9. Confirm the manifest state

```powershell
git diff --name-only $(git merge-base origin/main HEAD) HEAD
```

Expected result for the interim change: the list holds no `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, or `uv.lock` (task T007).

## 10. Cleanup

No container starts for this change. No cleanup step applies. No volume or network is created.
