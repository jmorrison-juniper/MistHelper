# Quickstart: Function and module size for Pylint limits (issue 4135)

Run these commands from the repository root in PowerShell. Use the worktree for the branch `chore/4135-pylint-size-refactor`. Do not change `main` in place.

## Prerequisites

1. Create the environment for a new worktree with the commands in `.github/copilot-instructions.md`, section "Language and environment".
2. Activate the environment with `.venv\Scripts\Activate.ps1`.
3. Authenticate `gh` with the repository account for read commands, for example `gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha`. Do not print a token.

## Scenario 1: Reproduce the findings (Task T002)

Run the issue command on the branch before any edit.

```powershell
.venv\Scripts\python.exe -m pylint --persistent=n --disable=all --enable=R0911,R0913,R0914,R0915,R0917,C0302,R0801 --output-format=json web_portal\services\operation.py MistHelper.py src\foundation\support\refactors\endpoint_primary_key_strategies.py src\operations\exporting\juniper_rma\workflows
```

Expected result before the change:

- R0911 at `_is_user_facing`.
- R0914 and R0915 at `_build_registry`.
- C0302 for `web_portal/services/operation.py`, `MistHelper.py`, and the endpoint module.
- R0801 for the two Juniper workflow modules.
- No R0913 and no R0917. If one appears, stop and record it in `analysis.md` before code changes.

## Scenario 2: Count lines by LF

Use this method for every line count. Do not use `Get-Content` for a count, because it undercounts.

```powershell
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
$text = [System.IO.File]::ReadAllText((Join-Path $repo 'MistHelper.py'))
($text -split "`n").Count - 1
```

Expected result on `main`: `8372`. After the change: 1,000 or fewer.

## Scenario 3: Capture the parity constants on main (Task T001)

Run each command before any edit. Each command prints one SHA-256 value. Store the three values in the three test modules named in `tasks.md`.

```powershell
@'
import hashlib
import json
from web_portal.services.operation import PARAMETER_REGISTRY
print(hashlib.sha256(json.dumps(PARAMETER_REGISTRY, sort_keys=True).encode("utf-8")).hexdigest())
'@ | .venv\Scripts\python.exe -
@'
import hashlib
import json
from src.foundation.support.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
print(hashlib.sha256(json.dumps(list(ENDPOINT_PRIMARY_KEY_STRATEGIES.items())).encode("utf-8")).hexdigest())
'@ | .venv\Scripts\python.exe -
@'
import hashlib
import MistHelper
print(hashlib.sha256("\n".join(MistHelper.menu_actions.keys()).encode("utf-8")).hexdigest())
'@ | .venv\Scripts\python.exe -
```

If `json.dumps` fails on a registry value, stop. Record the failing value in `analysis.md`.

## Scenario 4: Nested-package ratchet (Task T003)

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\test_nested_package_structure.py -s
```

Expected message: `nested_package_scope: 190 directories examined, 33 violations, 236 total excess`.

## Scenario 5: Symbol gate for each changed file (Task T046)

```powershell
symbol-diff --base origin/main MistHelper.py
symbol-diff --base origin/main web_portal\services\operation.py
symbol-diff --base origin/main src\foundation\support\refactors\endpoint_primary_key_strategies.py
```

Expected result: the tool lists only the names in the removed-name list of `plan.md`. The exit code is 1 for `MistHelper.py`, because the planned moves remove names. The pull request states this result. Do not report the gate as passed.

## Scenario 6: Parity and portal tests (Tasks T001, T012, T032, T044)

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\web_portal\test_portal_required_controls.py tests\guardrails\test_endpoint_catalog.py tests\guardrails\test_operation_registry_menu_coverage.py -q
```

## Scenario 7: Juniper writer tests (Task T022)

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\juniper_rma\workflows -q
```

## Scenario 8: Import smoke and cycle guard (Task T049)

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\test_move_module_guidance.py -q
.venv\Scripts\python.exe -c "import src.interfaces.cli.bootstrap.import_initializer"
```

## Scenario 9: Safe sweep (Task T046)

```powershell
.venv\Scripts\python.exe MistHelper.py --test
```

Expected result: each `safe` operation completes. Without a Mist API token, the API checks skip with a credential reason.

## Scenario 10: Menu reference (Task T053)

```powershell
.venv\Scripts\python.exe scripts\generate_menu_wiki.py
git diff --stat
.venv\Scripts\python.exe -m scripts.menu_api_map --check
```

Expected result: `generate_menu_wiki.py` writes no changed file. The last command fails with `No module named scripts.menu_api_map`. That failure is the blocked gate recorded in `analysis.md`.

## Scenario 11: Local gates (T-LOCAL-GATES)

Run each command from the table in `.github/copilot-instructions.md`, with the path list that applies to the changed files.

```powershell
.venv\Scripts\python.exe -m py_compile MistHelper.py
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
.venv\Scripts\python.exe -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
.venv\Scripts\python.exe -m radon cc src/interfaces/cli -j | complexity-gate --max 10
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r src/interfaces/cli src/foundation/support/portal_operations src/foundation/persistence/db/endpoint_strategies -q
.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5
.venv\Scripts\python.exe -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
.venv\Scripts\python.exe -m pydocstyle src/ wsgi.py web_portal
.venv\Scripts\python.exe -m interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md
diagram-refs --source-files MistHelper.py src/ --allowlist-file .github/diagram-refs-allowlist.txt
check-citations src tests
```

Caution: the `radon` command uses the path of each changed package. Repeat it for each package in the change map.

## Scenario 12: Full test shards (Task T048)

Run the two `pytest-chunks` commands from `.github/copilot-instructions.md`, section "Local gates". Each prints one summary line for each shard.

## Scenario 13: Test-quality analyzer (T-LOCAL-GATES)

Run the preflight and gate commands from `.github/copilot-instructions.md`, section "Test quality ratchet", in order. Stop at the first failure.
