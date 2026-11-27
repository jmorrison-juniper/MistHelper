# Quickstart: Site export write results

Run each command from the root of a git worktree that holds a `.venv`. Use `pwsh` version 7 for the route check. Do not run `python MistHelper.py --menu 213` for this issue, because that run calls Mist.

## Prerequisites

1. Activate the environment with `.venv\Scripts\Activate.ps1`.
2. Confirm the SDK version with the next command. The expected line is `Version: 0.64.1`.

```powershell
python -m pip show mistapi
```

3. Set the GitHub environment before each `gh` command. Use the account variable of this workstation.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario Q-01: Confirm the repair on remote main

Each command reads one blob SHA from `main`. The expected value follows each command.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/src/operations/exporting/export/site_application_list_exporter.py?ref=main" --jq .sha
```

Expected: `01cba0e52d5a3a6ced43d3e4b8c2d949cd76a31b`.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/src/operations/exporting/export/site_system_events_exporter.py?ref=main" --jq .sha
```

Expected: `12dcaccad3a704231f66127e6ed1f60e2414d27d`.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/tests/unit/export/test_site_asset_and_events_exporters.py?ref=main" --jq .sha
```

Expected: `a2aa37e006a3265a70422c2bbca32faecacf030c`.

## Scenario Q-02: Reproduce the defect on the base commit (expected result, not run)

This scenario shows that the base commit fails the failed-write cases. The expected result comes from reading the test assertions. It was not run during authoring.

1. Create a sibling worktree at the base commit.

```powershell
git worktree add ..\MistHelper-4717-base 3964d21d03f9f5717cb8eafb7272ecff21f5362a
```

2. Copy the `main` version of the shared test module into the base worktree.

```powershell
git -C ..\MistHelper-4717-base show origin/main:tests/unit/export/test_site_asset_and_events_exporters.py > ..\MistHelper-4717-base\tests\unit\export\test_site_asset_and_events_exporters.py
```

3. Create the environment in the base worktree. Follow the bootstrap steps in `.github/copilot-instructions.md` lines 26-30.
4. Run the failed-write cases in the base worktree.

```powershell
python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k test_failed_write_reports_error_without_success
```

Expected: four failed cases. The four case IDs are `applications-direct`, `applications-menu`, `system-events-direct`, and `system-events-menu`.

## Scenario Q-03: Run the focused reproduction on main

```powershell
python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py -k TestSiteWriteOutcomes
```

Expected: 16 passed. The class holds four tests, and each test runs four cases.

## Scenario Q-04: Run the offline harness (after T010)

The harness lives in `test-artifacts\offline-guard`. Git ignores that folder. The harness patches these entry points: `socket.socket.connect`, `socket.socket.connect_ex`, `socket.getaddrinfo`, `socket.create_connection`, and `sqlite3.connect`. Each patched entry point records each attempt and raises.

```powershell
$env:PYTHONPATH = 'test-artifacts\offline-guard'
python -m pytest -p offline_guard test-artifacts\offline-guard\test_offline_guard_self.py
```

Expected: three passed. The three cases prove that the socket, DNS, and SQLite blocks each raise.

```powershell
python -m pytest -p offline_guard tests/unit/export/test_site_asset_and_events_exporters.py
```

Expected: all tests pass. The harness prints `offline attempts: socket=0 dns=0 sqlite=0`.

## Scenario Q-05: Route check (after T011)

Run these two lines in `pwsh` 7.

```powershell
. .specify\scripts\powershell\spec-route.ps1
Resolve-SpecFeaturePath -SpecsDir specs -BranchName 4717-site-export-writer-results -Number 4717
```

Expected: `specs\numbered\0\0\1\2\2\3\3\2\4717-site-export-writer-results`.

Then run the route guard.

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py
```

Expected: all tests pass.

## Scenario Q-06: Inline comment scan (after T007 to T009)

This scan prints each line in the touched range that lacks a `#` comment. Blank lines, closing lines, and continuation lines are exempt. The scan also prints docstring, decorator, and definition lines in the test class. Review each printed line against those categories.

```powershell
$exporterFiles = @('src\operations\exporting\export\site_application_list_exporter.py', 'src\operations\exporting\export\site_system_events_exporter.py')
foreach ($file in $exporterFiles) {
    $lines = Get-Content -LiteralPath $file
    foreach ($index in 54..71) {
        $text = $lines[$index].Trim()
        if ($text -ne '' -and -not $text.Contains('#') -and $text -notmatch '^[\)\]\},]+$') {
            '{0}:{1}: {2}' -f $file, ($index + 1), $text
        }
    }
}
```

Expected for each exporter: only lines 64 and 70 print. Both lines continue a statement that carries its comment on the first line.

```powershell
$lines = Get-Content -LiteralPath 'tests\unit\export\test_site_asset_and_events_exporters.py'
foreach ($index in 321..434) {
    $text = $lines[$index].Trim()
    if ($text -ne '' -and -not $text.Contains('#') -and $text -notmatch '^[\)\]\},]+$') {
        '{0}: {1}' -f ($index + 1), $text
    }
}
```

Expected after the repair: each printed line is a docstring, a decorator line, a definition line, a continuation line, or a closing line. No printed line is a statement.

## Scenario Q-07: Symbol gate

```powershell
symbol-diff --base origin/main src/operations/exporting/export/site_application_list_exporter.py
symbol-diff --base origin/main src/operations/exporting/export/site_system_events_exporter.py
symbol-diff --base origin/main tests/unit/export/test_site_asset_and_events_exporters.py
```

Expected: `no module-level name changed`, exit code 0, for each command. The base is `origin/main`, which already holds the test class.

## Scenario Q-08: Record guards

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

Expected: each command passes. The output reports the examined counts. The changelog guard can skip its diff test outside a pull request event.

## Scenario Q-09: Local gates for the changed files

Run each command, then record its result in the pull request body. The commands match the local gates table in `.github/copilot-instructions.md` lines 57-74.

```powershell
python -m py_compile src\operations\exporting\export\site_application_list_exporter.py src\operations\exporting\export\site_system_events_exporter.py tests\unit\export\test_site_asset_and_events_exporters.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/unit/export/test_site_asset_and_events_exporters.py
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
radon cc src -j | complexity-gate --max 10
bandit -c pyproject.toml -r src -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
```

Expected results:

- Compile: no output.
- Lint: `All checks passed`.
- Format: no file needs a change.
- Types: `Success`.
- Tests: all tests pass.
- Coverage: 80 percent or above.
- Complexity: no block above 10.
- Security: no finding.
- Code quality: score 9.5 or above.
- Dead code: no finding.
- Docstrings: no violation, and coverage at 90 percent or above.
- Menu reference: no changed file after the two generator commands.

The test quality gate follows `.github/copilot-instructions.md` lines 95-125. Commit the intended tests first. Then run the preflight and the gate.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: the preflight passes, and the gate reports `gate: 0 new findings vs baseline`.

The two `pytest-chunks` commands in `.github/copilot-instructions.md` lines 87-88 run the full unit and contract trees on Windows.

## Scenario Q-10: Remote checks before merge

```powershell
gh pr checks <number> --watch
gh pr view <number> --json title,body,headRefName
```

Expected: each required check reports SUCCESS on the latest commit. The pull request body contains `Closes #4717`.
