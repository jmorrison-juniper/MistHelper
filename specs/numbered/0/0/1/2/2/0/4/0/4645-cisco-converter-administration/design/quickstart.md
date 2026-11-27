# Quickstart: Gated Converter Administration and Unassignment

This quickstart reproduces the evidence in this record and lists the exact commands for each gate. Run each command from the repository root in Windows PowerShell. The repository checkout is read-only for this record. Scenarios 1 to 5 read evidence only.

Warning: Do not run a live Mist delete or unassign command. This record authorizes none. Scenario 9 explains the boundary.

## Prerequisites

1. Open PowerShell in the repository root: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.
2. Activate the virtual environment: `.venv\Scripts\Activate.ps1`.
3. Set the GitHub host and the account token for each `gh` command. Run these two lines before each `gh` command. The lines set variables only. They print no value.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Scenario 1: Confirm the remote absence of administration code

Run the tree query. Expected result: no output. Each matching path would show that code exists on `main`.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '.tree[] | select(.path | test("cisco_config_converter/(engine|state)|tests/contract/cisco_config_converter|specs/numbered/0/0/1/2/2/0/4/0/4645")) | .path'
```

## Scenario 2: Confirm the converter root holds five children

Expected result: the five names `__init__.py`, `conversion.py`, `models.py`, `presentation`, and `routes.py`. A cache folder can appear. Ignore a cache folder.

```powershell
Get-ChildItem -LiteralPath 'src\interfaces\portals\cisco_config_converter' | Select-Object -ExpandProperty Name
```

## Scenario 3: Confirm the installed SDK function lines

Expected result: one match for each command. The line numbers are 117, 117, 117, 214, and 67.

```powershell
Select-String -LiteralPath '.venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py' -Pattern '^def deleteOrgNetwork\('
Select-String -LiteralPath '.venv\Lib\site-packages\mistapi\api\v1\orgs\services.py' -Pattern '^def deleteOrgService\('
Select-String -LiteralPath '.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py' -Pattern '^def deleteOrgGatewayTemplate\('
Select-String -LiteralPath '.venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py' -Pattern '^def unassignOrgDeviceProfile\('
Select-String -LiteralPath '.venv\Lib\site-packages\mistapi\api\v1\sites\sites.py' -Pattern '^def updateSiteInfo\('
```

## Scenario 4: Confirm the OpenAPI operation lines

Expected result: the operation lines 15279, 18566, 9909, 8405, and 26004. The local file hash equals the remote blob (RC-22). Each line number applies to `main`.

```powershell
Select-String -LiteralPath 'documentation\mist-api-openapi31yaml.yaml' -Pattern '^      operationId: (deleteOrgNetwork|deleteOrgService|deleteOrgGatewayTemplate|unassignOrgDeviceProfile|updateSiteInfo)$'
```

## Scenario 5: Confirm the site-template link and the null example

Expected result: line 20349 names the `sitetemplate_id` field for site template assignment. Line 56559 shows `sitetemplate_id: null` in a site example. The example does not define an unassignment.

```powershell
Select-String -LiteralPath 'documentation\mist-api-openapi31yaml.yaml' -Pattern '`sitetemplate_id` field of|sitetemplate_id: null'
```

## Scenario 6: Run the local gates after implementation

Run each command in the order below. Stop at the first failed command. Record the result of each command in the pull request body. Each gate path comes from `.github/workflows/ci.yml` (RC-17 to RC-20).

Not applicable: the safe sweep, menu reference gates, operation registry guards, dependency audit, ops portal gate, and ops platform gate. This change adds no menu row, registry entry, or dependency.

```powershell
python -m py_compile src\interfaces\portals\cisco_config_converter\routes.py
python -m py_compile src\interfaces\portals\cisco_config_converter\engine\administration\executor.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/integration/web_portal/cisco_config_converter -q
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py -q
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/routes.py
symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/engine/conversion.py
python -m pytest tests/guardrails/test_move_module_guidance.py
python -m pytest tests/guardrails/test_process_folder_structure.py
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py
python -m pytest tests/unit/web_portal/test_output_scan_runtime_files.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
Get-ChildItem -LiteralPath 'specs\numbered\0\0\1\2\2\0\4\0\4645-cisco-converter-administration' -Recurse -Filter '*.md' | ForEach-Object { ste-linter --config .ste-linter.toml --min-score 80 --quiet $_.FullName }
```

The full-test shards run in CI. Run them locally when the CI result is unclear:

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

## Scenario 7: Confirm that the page is hidden by default

Expected result: one test passes. The test asserts a 404 response with the mode unset.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/administration/test_administration_page.py::test_page_is_hidden_by_default -q
```

## Scenario 8: Confirm that the shared portal does not expose the routes

Expected result: no output until issue 4648 completes. A match means that the shared portal registered a converter route before the handover.

```powershell
Select-String -LiteralPath 'web_portal\app.py' -Pattern 'cisco|converter'
```

## Scenario 9: Live operations stay blocked

No command in this record starts a live Mist operation. The boundary has four parts.

1. Issue 4634 must verify each contract row in `design/contracts/mist-administration.md`.
2. The owner must record decisions D-1, D-2, and D-3 in issue 4645.
3. The variables `CISCO_CONVERTER_ADMIN_MODE` and `CISCO_CONVERTER_ADMIN_FAMILIES` must enable one family for a run.
4. A person must type `CONFIRM` and echo the scope digest for each run.
