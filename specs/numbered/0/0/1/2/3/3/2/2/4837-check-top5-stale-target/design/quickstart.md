# Quickstart: Top-Five Complexity Target Map

## Prerequisites

- Windows 11 with the `.venv` of the main checkout. Radon 6.0.1 is installed (R22).
- The repository root is the working directory for every command.

Caution: run each command from the repository root. The utility resolves its paths from the working directory.

## Scenario 1: Reproduce the defect before the change

```powershell
.venv\Scripts\python.exe scripts\check_top5_complexity.py
$LASTEXITCODE
```

Expected output: a traceback that ends with `RuntimeError: Target function not found in radon output: _execute_site_capture_loop`. The exit code is non-zero. This output matches the issue report.

## Scenario 2: Run the guard tests before the change

```powershell
.venv\Scripts\python.exe -m pytest tests\integration\test_top5_compatibility_paths.py -q
```

Expected output: the mapping guard test and the real-run guard test fail. The exit-code guard test passes. The two existing tests pass.

## Scenario 3: Run the utility after the change

```powershell
.venv\Scripts\python.exe scripts\check_top5_complexity.py
$LASTEXITCODE
```

Expected output: the header line `Target cyclomatic complexity results:`. Then five rows in target order, each in the form `- <name>: CC=<n> Rank=<letter> (<file>:<line>)`. Then one line. The line reads `PASS: All target functions are CC <= 10` with exit code 0. Otherwise, the line reads `FAIL: One or more target functions exceed CC 10` with exit code 1. The contract in `design\contracts\top5-cli.md` defines each line.

## Scenario 4: Run the guard tests after the change

```powershell
.venv\Scripts\python.exe -m pytest tests\integration\test_top5_compatibility_paths.py -q
```

Expected output: five tests pass.

## Scenario 5: Run the timeout regression test

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\prod_readiness\operations\execution\prod_readiness\test_subprocess_timeouts.py -q -k Complexity
```

Expected output: two tests pass.

## Scenario 6: Lint, format, and compile

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m py_compile scripts\check_top5_complexity.py
```

Expected output: ruff prints `All checks passed`. Black reports that no file needs a change. The compile step prints nothing.

## Scenario 7: Symbol and security checks

```powershell
.venv\Scripts\Activate.ps1
symbol-diff --base origin/main scripts\check_top5_complexity.py
bandit -c pyproject.toml -r scripts -q
```

Expected output: `symbol-diff` prints `no module-level name changed` and exits with code 0. Bandit prints no finding.

## Scenario 8: Complexity check for the changed utility

```powershell
.venv\Scripts\Activate.ps1
python -m radon cc scripts\check_top5_complexity.py -j | complexity-gate --max 10
```

Expected output: the command reports the actual result. The CI radon job does not cover this file (R18). The estimate for `main()` is CC 13 (U-2), so the command may report a block above 10. Record the output in the pull request body.

## Scenario 9: Test-quality ratchet after the commit

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected output: the preflight passes. The analyzer prints `gate: 0 new findings vs baseline`.

## Scenario 10: Read the remote map entry (read-only)

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api repos/jmorrison-juniper/MistHelper/contents/scripts/check_top5_complexity.py?ref=main --jq .sha
```

Expected output before the change: `7e13d7f70518c21621535e7732b901ab800af765` (R01). Expected output on the pull request branch: the new blob SHA.

## Scenario 11: Watch the remote checks

```powershell
gh pr checks fix/4837-check-top5-stale-target --watch
```

Expected output: each required check ends green. The integration shard runs the guard tests.
