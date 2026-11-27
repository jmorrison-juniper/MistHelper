# Quickstart: WAN Duplicate Sample Coverage

## Prerequisites

- Task T002 is complete. PR #4208 released both affected files.
- Create a worktree for branch `fix/4681-wan-duplicate-sample-coverage` from the new `main`. Do not change the shared checkout.
- Activate the environment with `.venv\Scripts\Activate.ps1`.
- Before each `gh` command, set the host and the token from the account variable. The token value is never printed.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario 1: Confirm the Defect on the PR Head

Run this read-only check before you change code. It confirms the PR #4208 head blob for the snapshot client.

```text
gh api "repos/jmorrison-juniper/MistHelper/contents/src/interfaces/wan_performance/collection/snapshot_client.py?ref=843be63bc837513b4442dae69da9f0db922e0ed1" --jq .sha
```

Expected result: `88899eecece6666c6c3a7b377fe1e3d703ee1bd4`.

The defect path is the set of lines that accept a repeated timestamp and count it. Lines 266, 285, 322, 357, and 435 hold that path at the PR head.

## Scenario 2: Reproduce the Defect with Unit Tests

Run this after task T003 adds the in-response duplicate tests. Before the fix, these tests fail.

Reproduction steps:

1. Build a 10-minute response with six timestamps.
2. Repeat one timestamp.
3. Omit another expected interval.
4. Pass the response through `GatewayInsights._metrics` and the summary path.
5. Observe `sample_count` 6 and `coverage_fraction` 1.0 on the defective code.

```text
python -m pytest tests/unit/wan_performance/test_gateway_insights.py -k duplicate
```

Expected result before the fix: the duplicate tests fail. The repeated and missing case reports `sample_count` 6.

## Scenario 3: Verify the Fix

Run this after tasks T006 and T008 are complete.

```text
python -m pytest tests/unit/wan_performance/test_gateway_insights.py
python -m pytest tests/unit/wan_performance/test_calendar_summaries.py
```

Expected result: each command reports all tests passed. The repeated and missing case reports `sample_count` 5 and `coverage_fraction` 5/6. The five-sample hour adds no congestion minutes.

## Scenario 4: Confirm Zero Live Mist Calls

Remove the Mist token variable names from the test shell. Then run Scenario 3 again.

```text
Remove-Item Env:MIST_APITOKEN -ErrorAction SilentlyContinue
Remove-Item Env:MIST_API_TOKEN -ErrorAction SilentlyContinue
```

Expected result: all tests still pass. The tests use mocked SDK responses and need no token.

## Scenario 5: Confirm the Changelog and the Documentation

```text
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
git grep -n "Each expected interval counts once" -- documentation/wan-performance.md
```

Expected result: the guard test passes. The `git grep` command prints the updated line in `documentation/wan-performance.md`.

## Local gates

Run each command on the changed files. The list follows the local gates table in `.github/copilot-instructions.md` at line 50 (RC-27). The path values come from `.github/workflows/ci.yml` (RC-37 and RC-38).

```text
python -m py_compile src\interfaces\wan_performance\collection\snapshot_client.py
python -m py_compile src\interfaces\wan_performance\domain\summary.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/unit/wan_performance/test_gateway_insights.py
python -m pytest tests/unit/wan_performance/test_calendar_summaries.py
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
radon cc src/interfaces/wan_performance -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/interfaces/wan_performance -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
symbol-diff --base origin/main src\interfaces\wan_performance\collection\snapshot_client.py
symbol-diff --base origin/main src\interfaces\wan_performance\domain\summary.py
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

| Gate | Expected result |
| - | - |
| Compile | No output for each changed file |
| Lint | `All checks passed` |
| Format | No file needs a change |
| Types | `Success` |
| Unit tests | All tests pass |
| Coverage | 80 percent or above |
| Complexity | No block above cyclomatic complexity 10 |
| Security lint | No finding at any severity |
| Code quality | Score 9.5 or above |
| Dead code | No finding |
| Docstrings | No violation. Coverage 90 percent or above |
| Symbols | `no module-level name changed`, exit code 0 |
| Test quality preflight | All tests pass |
| Test quality analyzer | `gate: 0 new findings vs baseline`. Run after the local commit. |
| Full tests | One summary line for each shard |

Gates that do not apply are these. The safe sweep and the menu reference have no menu change. The dependency audit has no manifest change. The STE gate has no listed Markdown file change. The ops portal and ops platform gates have no change. The Playwright job runs in CI, and task T-REMOTE-CI checks it.
