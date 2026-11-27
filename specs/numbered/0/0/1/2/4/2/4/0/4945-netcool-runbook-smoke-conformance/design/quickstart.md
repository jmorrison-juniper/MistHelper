# Quickstart: Netcool Runbook Smoke Package Conformance

Use these steps to reproduce the baseline and to verify the change. Run each command from the repository root. Keep every generated file outside the repository.

## Prerequisites

1. Use the `.venv` at the repository root. The package needs Python 3.15 (`ci.yml` line 77, row R43).
2. Install the gate tools with `pip install -r requirements-dev.txt` (`ci.yml` line 163, row R42).
3. Set the GitHub account for `gh` reads. Run each line in order:

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario 1: Confirm the remote baseline

Read the issue and the linked records. These commands only read data.

```powershell
gh issue view 4945 -R jmorrison-juniper/MistHelper --json number,title,state,labels,comments
gh pr list -R jmorrison-juniper/MistHelper --state all --search "4945" --json number,title,state,headRefName,url,mergedAt
gh api "repos/jmorrison-juniper/MistHelper/contents/scripts/netcool_runbook_smoke/client.py?ref=main" --jq ".sha"
```

The first command shows state `OPEN` and labels `refactor`, `tests`, and `in-progress`. The second command returns an empty list. The third command returns the blob SHA `da54b0c22449362ff84a8e2766b2942037283c26` (row R03).

## Scenario 2: Confirm that the record folders are absent

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" ls-files -- specs/numbered/0/0/1/2/4/2/4/0
```

The command returns no line before the change. The route folder is new, so the command proves the absence (rows R72 and R73).

## Scenario 3: Record the baseline (T003)

Collect the test count before the first edit:

```powershell
python -m pytest tests/unit/scripts/netcool_runbook_smoke --collect-only -q
python -m pytest tests/unit/scripts/netcool_runbook_smoke -q
```

Record the collected count and the pass count. Record the console lines of the fixed fake-session run:

```powershell
python -m pytest tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py -q
```

The contract in `design/contracts/cli-output.md` lists the lines to compare.

## Scenario 4: Measure each gate on the untouched package (T004)

```powershell
python -m mypy scripts/netcool_runbook_smoke/__init__.py --config-file pyproject.toml
python -m ruff check scripts/netcool_runbook_smoke
bandit -c pyproject.toml -r scripts/netcool_runbook_smoke -q
radon cc scripts/netcool_runbook_smoke -a -nb
vulture scripts/netcool_runbook_smoke --min-confidence 70
pydocstyle scripts/netcool_runbook_smoke
interrogate scripts/netcool_runbook_smoke --fail-under 90 -v
```

Record each result. A first run can show many findings. The change repairs each finding in Phase 5.

## Scenario 5: Measure the package coverage (T005 and T-LOCAL-GATES)

```powershell
python -m pytest tests/unit/scripts/netcool_runbook_smoke --cov=scripts.netcool_runbook_smoke --cov-report=term
```

The `TOTAL` line of the report gives the value. The value must reach 95 percent after the change (FR-020).

## Scenario 6: Run the structure guard (T006 and T026)

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py -q
```

Before Phase 4, the guard fails with the fourteen function names. After Phase 4, the guard passes and prints the examined counts.

## Scenario 7: Run the gate guard and the injected-violation tests (T007 and T008)

```powershell
python -m pytest tests/guardrails/test_ci_gate_triggers.py -q
```

The guard fails on the untouched `ci.yml` and passes after Phase 5.

## Scenario 8: Check each moved name for old import paths (move gate)

Run each command. Each command must print no line after the change:

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.client import"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.command import"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.documents import"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.checks import"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.checks.scope import"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.checks.searches import"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.checks.identity import"
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "from scripts.netcool_runbook_smoke.checks.support import"
```

## Scenario 9: Seeded comment sample (T035, decision D-24)

The script reads every line of the package that holds a comment. It draws 40 lines with the seed 4945. Run it from the repository root:

```powershell
$pool = @(
    Get-ChildItem -Recurse -Filter '*.py' -LiteralPath 'scripts\netcool_runbook_smoke' |
    Sort-Object FullName |
    ForEach-Object {
        $path = $_.FullName
        $number = 0
        foreach ($line in [System.IO.File]::ReadAllLines($path)) {
            $number++
            if ($line -match '\S\s+#\s') {
                [pscustomobject]@{
                    Path = $path
                    Line = $number
                    Text = $line.Trim()
                }
            }
        }
    }
)
$random = New-Object System.Random 4945
$sample = $pool | Sort-Object { $random.Next() } | Select-Object -First 40
$sample | Format-List Path, Line, Text
```

The reviewer grades each line. A line passes when its comment states a cause and a purpose. A line that only restates the operation fails. The change passes when at least 36 of the 40 lines pass (FR-012).

## Scenario 10: Check the symbols of each changed file (symbol gate)

Run this command for each changed file that remains on disk. Record the result in the pull request body:

```powershell
symbol-diff --base origin/main scripts/netcool_runbook_smoke/__main__.py
```

For a deleted file, record each name that moved, with its new path. The tool reports each removed name. The pull request body lists the new path of each name (FR-025).

## Scenario 11: Run the unit tests and the guard tests

```powershell
python -m pytest tests/unit/scripts/netcool_runbook_smoke -q
python -m pytest tests/guardrails/test_nested_package_structure.py tests/guardrails/test_ci_gate_triggers.py tests/guardrails/test_changelog_fragment_policy.py -q
```

The pass count after the change equals the collected count of Scenario 3 (FR-021, decision D-15).

## Scenario 12: Confirm the runbook command

```powershell
python -m scripts.netcool_runbook_smoke --help
```

The command prints the option list and exits. It sends no request to Mist, because `--help` stops the parser first (FR-010).

## Scenario 13: Run the full local gate sequence (T-LOCAL-GATES)

Run each command. Record each result in the pull request body.

```powershell
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py scripts/netcool_runbook_smoke/__init__.py --config-file pyproject.toml
python -m pytest tests/unit/scripts/netcool_runbook_smoke -q
python -m pytest tests/guardrails -q
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
radon cc scripts/netcool_runbook_smoke -j | complexity-gate --max 10
bandit -c pyproject.toml -r scripts/netcool_runbook_smoke -q
vulture scripts/netcool_runbook_smoke --min-confidence 70
pydocstyle scripts/netcool_runbook_smoke
interrogate scripts/netcool_runbook_smoke --fail-under 90 -v
```

## Scenario 14: Confirm the remote gate counts (T-REMOTE-CI)

After the pull request runs, read each count line of the seven gate jobs:

```powershell
gh pr checks <number> -R jmorrison-juniper/MistHelper --watch
gh run view <run-id> -R jmorrison-juniper/MistHelper --log
```

Each count step prints the number of Python files of the package. The count is above zero in each job (SC-003).
