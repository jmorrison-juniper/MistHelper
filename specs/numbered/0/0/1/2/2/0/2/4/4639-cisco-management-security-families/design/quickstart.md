# Quickstart: Review management and security configuration families

These steps reproduce the current state and verify each change. Run each command from the repository root unless a step names another folder. Repository root: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.

## 1. Confirm the issue is open

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh issue view 4639 -R jmorrison-juniper/MistHelper --json number,state,title
```

Expected result: `"state":"OPEN"` and the title `[Spec]: Review management and security configuration families`.

## 2. Confirm the local and remote base

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" rev-parse HEAD
```

Expected result: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. This value matches remote `main` (research evidence boundary).

## 3. Reproduce the current DNS-only behavior

```powershell
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter/test_routes.py
```

Expected result before implementation: all tests pass. The DNS unit test asserts one unsupported item for each unsupported line (R31, R32). Unsupported lines carry the generic label from `IOSDnsConverter._label` (R28).

## 4. Re-check the Mist evidence pointers

```powershell
Select-String -LiteralPath "documentation\mist-api-openapi31yaml.yaml" -Pattern "^    remote_syslog:"
Select-String -LiteralPath "documentation\mist-api-openapi31yaml.yaml" -Pattern "^        remote_syslog:"
Select-String -LiteralPath "documentation\mist-api-openapi31yaml.yaml" -Pattern "^    snmp_config:"
```

Expected results: the first command reports a match at line 92510. The second command reports several matches, and line 101532 is the site settings match. The third command reports a match at line 103999. Compare the results with rows R42, R43, and R49 in `design/research.md`.

## 5. Confirm the installed SDK signatures

```powershell
Select-String -LiteralPath ".venv\Lib\site-packages\mistapi\api\v1\sites\setting.py" -Pattern "^def updateSiteSettings"
Select-String -LiteralPath ".venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py" -Pattern "^def updateOrgGatewayTemplate"
```

Expected results: the first command reports line 42. The second command reports line 145. Compare them with rows R68 and R70.

## 6. Confirm the absence of a flow export and HSRP property

```powershell
Select-String -LiteralPath "documentation\mist-api-openapi31yaml.yaml" -Pattern "netflow|ipfix|jflow|flow_export|flow_collector|hsrp" -CaseSensitive:$false
```

Expected result: no output. This matches rows R61 and R62.

## 7. Confirm that the process folder guard still passes

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py
```

Expected result: the guard passes for the managed route. The route check reads `specs/numbered/0/0/1/2/2/0/2/4` (R16).

## 8. Verification after implementation

Run these commands during T-LOCAL-GATES. Each command names the gate from the local gates table (R04).

| Gate | Command | Expected result |
| --- | --- | --- |
| Compile | `python -m py_compile src/interfaces/portals/cisco_config_converter/conversion.py tests/integration/web_portal/cisco_config_converter/management/test_management.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy $MYPY_PATHS --config-file pyproject.toml` | `Success`. Copy `MYPY_PATHS` from `.github/workflows/ci.yml` (R11). |
| Management tests | `python -m pytest tests/integration/web_portal/cisco_config_converter/management/test_management.py` | All 17 tests pass |
| DNS and route tests | `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter/test_routes.py` | All tests pass |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | The coverage report meets 80 percent or above |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src/interfaces/portals/cisco_config_converter -j \| complexity-gate --max 10` | No block above complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q` | No finding |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture $VULTURE_PATHS --min-confidence 70` | No finding. Copy `VULTURE_PATHS` from `.github/workflows/ci.yml`. |
| Docstrings | `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90` | No violation and coverage of 90 percent or above |
| Symbols | `symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/conversion.py` | No existing module-level name removed. The two new names appear in the pull request body. |
| Process folder | `python -m pytest tests/guardrails/test_process_folder_structure.py` | The guard passes |
| STE | `ste-linter --config .ste-linter.toml --min-score 80` with every Markdown file of this record | Each file scores 80 or above |

Gates that do not apply: safe sweep, menu reference, dependency audit, ops portal, and ops platform. The pull request body gives the reason for each.

## 9. Confirm the changed-file scope

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --name-only origin/main
```

Expected result: `src/interfaces/portals/cisco_config_converter/conversion.py`, files under `tests/integration/web_portal/cisco_config_converter/management/`, and one fragment under `changelog.d/`. `CHANGELOG.md` does not appear.
