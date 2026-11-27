# Quickstart: Gateway History After an Ordinary Refresh

## Prerequisites

1. Create the Python environment with the steps in the "Language and environment" section of `.github/copilot-instructions.md`. Use Python 3.15.2.
2. Activate the environment with `.venv\Scripts\Activate.ps1`.
3. Install the Chromium browser that the end-to-end tests use.
4. Run each command from the root of the repository worktree that holds the publication branch.

## Scenario 1: Prove the Defect on the Parent Commit (Red Proof, T008)

Create a worktree for the parent commit. Use the main checkout's environment to run the tests.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" worktree add "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4795-parent" 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc
```

Copy the test file from the publication worktree into the parent worktree. Then run the tests with the main environment.

```powershell
& "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Scripts\python.exe" -m pytest tests/unit/wan_performance/test_gateway_insights.py
```

Expected result: N1, N2, N4, N5, N6, and N8 fail. N3, N7, and N9 pass.

Caution: remove the parent worktree when the proof ends. Removing a worktree does not delete the commit.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" worktree remove "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper-4795-parent"
```

## Scenario 2: Confirm the Repair and the Unit Tests at the Publication Head

```powershell
python -m pytest tests/unit/wan_performance/test_gateway_insights.py
```

Expected result: every test in the file passes.

## Scenario 3: Confirm the Route Regressions Under the Strict Environment

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
python -m pytest tests/e2e/web_portal/test_wan_performance_live.py
```

Expected result: E1 and E2 pass. The browser tests in the same file need the Chromium browser from the prerequisites.

## Scenario 4: Check the Remote Evidence Again (Read Only)

Set the account variables before each `gh` command.

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr view 4208 -R jmorrison-juniper/MistHelper --json headRefOid,state,mergedAt
```

Expected result: the head is `843be63bc837513b4442dae69da9f0db922e0ed1`, or a later commit that keeps the blob in the next command.

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/contents/src/interfaces/wan_performance/presentation/live_routes.py?ref=843be63bc837513b4442dae69da9f0db922e0ed1" --jq .sha
```

Expected result: `98827fc73a3d241859f539a03451d5cccf4d2e48`. A different value means the repair changed. Run Scenarios 2 and 3 again on the new head.

## Scenario 5: Run the Local Gates for the Changed Files (T-LOCAL-GATES)

Run each command once. Stop at the first failure, repair it, and run the command again. Record each count.

```powershell
python -m py_compile src/interfaces/wan_performance/presentation/live_routes.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/unit/wan_performance/test_gateway_insights.py
python -m pytest tests/e2e/web_portal/test_wan_performance_live.py
radon cc src/interfaces/wan_performance -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/interfaces/wan_performance -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src/interfaces/wan_performance/presentation/live_routes.py
symbol-diff --base origin/main tests/unit/wan_performance/test_gateway_insights.py
ste-linter --config .ste-linter.toml --min-score 80 documentation/wan-performance.md
check-citations src tests
```

The values of `MYPY_PATHS`, `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` come from `.github/workflows/ci.yml` (R73 to R76). Keep the values equal to those lines.

Run the test quality check after the intended tests are committed. Use the command from the "Test quality ratchet" procedure in `.github/copilot-instructions.md`.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Run the coverage command and the two `pytest-chunks` commands from the "Full tests" and "Coverage" rows of the local gates table when the runtime allows.

Not applicable to this change: the pip audit, the safe sweep, the menu reference, the ops portal, and the ops platform. The change touches no requirements file, no menu operation, and no portal in those folders.

## Scenario 6: Check the Publication Body (T-PR)

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr view 4208 -R jmorrison-juniper/MistHelper --json body --jq .body
```

Expected result after the owner authorizes publication: the body contains the line `Closes #4795` and the line that keeps `Refs #4200`. The body does not close #4200.
