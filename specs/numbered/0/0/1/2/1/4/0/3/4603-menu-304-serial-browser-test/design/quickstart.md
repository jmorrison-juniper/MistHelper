# Quickstart: Menu 304 serial number browser test

This file gives the exact reproduction steps and the verification commands for issue #4603. Run each command from the repository root unless a step says otherwise.

## Prerequisites

- Windows 11 or Linux, with Git and the GitHub CLI (`gh`).
- Python 3.15.2 for combinations C and D. Python 3.13.18 for combinations A and B. Install each with `uv python install 3.15.2` and `uv python install 3.13.18`.
- Chromium for Playwright. On Linux, run `python -m playwright install --with-deps chromium`. On Windows, run `python -m playwright install chromium`.
- `pytest-timeout`. Without it, `tests/e2e/conftest.py` line 209 skips the E2E tests.

Caution: install each experiment in its own environment. Do not edit a requirements file for an experiment.

## Scenario 1: Read the CI evidence (read-only)

Set the GitHub host and token from the approved account variable. Do not print the token.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh run view 42173674615 -R jmorrison-juniper/MistHelper --log-failed
```

Expected result: the output contains a line with `FAILED tests/e2e/web_portal/test_juniper_menus_browser.py::TestTheJuniperMenusAreReadableInTheBrowser::test_menu_304_waits_for_serial_numbers_then_saves_each_asset[chromium]`.

Read the pytest plugin line from the job log for the Dash version:

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh run view 42173674615 -R jmorrison-juniper/MistHelper --job 127747809271 --log
```

Expected result: the line that starts with `plugins:` names `dash-4.5.0`.

## Scenario 2: Run the browser module once

```powershell
python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -v
```

Expected result after T002 to T004: 19 tests pass. Before the change: 18 tests pass.

## Scenario 3: Repeat the menu 304 test (matrix run)

Run this loop in each combination environment. Record the printed count in `design/research.md`.

```powershell
$results = 1..20 | ForEach-Object {
    python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -k test_menu_304_waits -q | Out-Host
    $LASTEXITCODE -eq 0
}
Write-Output ("passes=" + @($results | Where-Object { $_ -eq $true }).Count + " of " + @($results).Count)
```

For combinations B and C, replace `1..20` with `1..10`.

## Scenario 4: Build the four combinations

Each combination uses the same requirements file, then overrides only Dash and Playwright. Create one environment folder for each combination. Do not commit any environment folder.

| Combination | Python | Dash | Playwright | Runs | Override after the requirements install |
| - | - | - | - | - | - |
| A (failing run) | 3.13.18 | 4.5.0 | 1.64.1 | 20 | `uv pip install dash==4.5.0 playwright==1.64.1` |
| B (passing PR run) | 3.13.18 | 4.4.1 | 1.64.1 | 10 | `uv pip install dash==4.4.1 playwright==1.64.1` |
| C (main Python, older Dash) | 3.15.2 | 4.5.0 | 1.65.2 | 10 | `uv pip install dash==4.5.0` |
| D (current main) | 3.15.2 | 4.5.1 | 1.65.2 | 20 | none |

Common steps for each combination:

```powershell
uv venv --python 3.13.18 .venv-combination-a
.venv-combination-a\Scripts\Activate.ps1
uv pip install -r requirements-dev.txt
uv pip install dash==4.5.0 playwright==1.64.1
python -m playwright install chromium
pip show dash playwright pytest-playwright mistapi
```

Replace the Python version, the environment folder name, and the override line for each row of the table. The `pip show` output records the installed versions for the results section.

## Scenario 5: Confirm the failure message (TC-2)

```powershell
python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -k test_menu_304_names -v
```

Expected result: the test passes. The test itself asserts that the failure text contains `/api/operations/parameters/304` and `503`.

## Scenario 6: Local gates before the commit

Run each command from the table in `tasks.md`, section T-LOCAL-GATES.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py
symbol-diff --base origin/main tests/e2e/web_portal/test_juniper_menus_browser.py
python -m pytest tests/guardrails/test_e2e_shard_partition.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

Run the test quality gate after the local commit:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected results appear in `tasks.md`, section T-LOCAL-GATES.

## Scenario 7: Delete the environments

After the matrix, delete the four environment folders by their exact names:

```powershell
Remove-Item -LiteralPath .venv-combination-a -Recurse -Force
Remove-Item -LiteralPath .venv-combination-b -Recurse -Force
Remove-Item -LiteralPath .venv-combination-c -Recurse -Force
Remove-Item -LiteralPath .venv-combination-d -Recurse -Force
```

Only the four named folders are removed. The browser screenshots in `test-artifacts/juniper-portal/` are git-ignored and stay in place.

## Expected Outcomes

- Combination D: 20 of 20 passes, required by SC-002.
- Combination A: the pass count and the failure count are recorded, required by SC-003.
- Combinations B and C: recorded for analysis. No pass count is required.
