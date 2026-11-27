# Quickstart: Integrate Mist Cisco Config Converter

This guide reproduces the current state of issue #4224 and lists the exact checks for each stage. It uses no Mist credential and no live Mist call.

## Prerequisites

- Use the repository root as the working folder.
- Use Python 3.15 or newer (R-67). Activate the project environment first.
- Use synthetic Cisco IOS samples only. Do not use a production credential or a real configuration.

## Step 1: Confirm the remote state of `main`

Run each command in PowerShell. Each command reads GitHub and changes nothing.

```powershell
gh api repos/jmorrison-juniper/MistHelper/contents/src/interfaces/portals/cisco_config_converter?ref=main --jq .[].name
gh api repos/jmorrison-juniper/MistHelper/contents/web_portal/app.py?ref=main --jq .sha
gh api repos/jmorrison-juniper/MistHelper/contents/web_portal/templates/base.html?ref=main --jq .sha
```

Expected result:

- The first command lists `__init__.py`, `conversion.py`, `models.py`, `presentation`, and `routes.py` (R-94).
- The second command prints `0fb25df1732815d18ff30d1823cbbdd30608aed6` (R-44).
- The third command prints `351cc44aeeae0a6fd61d4205af2de6777d066b2f` (R-23).

## Step 2: Confirm the portal has no converter tab

The portal has no converter tab until task T032 merges. Check the portal blueprint list and the navigation template for the converter name.

```powershell
Select-String -Path web_portal\app.py -Pattern "cisco|converter" -CaseSensitive:$false
Select-String -Path web_portal\templates\base.html -Pattern "cisco|converter" -CaseSensitive:$false
```

Expected result: Neither command prints a match on `main` (R-22, R-23).

## Step 3: Run the merged DNS slice tests

Activate the environment first.

```powershell
.venv\Scripts\Activate.ps1
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
python -m pytest tests/e2e/web_portal/test_portal_smoke.py
```

Expected result: Each command exits with code 0. The browser journeys use the isolated host. They need no Mist credential.

Inside the MistHelper container, run the same test file through the compose group (R-64):

```powershell
podman compose run --rm misthelper python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
```

## Step 4: Reproduce the operator journey (after gate G3)

Use this journey after T032 merges. Before that, use the isolated host route `/cisco-config-converter/`, as the browser test does.

1. Start the web portal on port 8055 (R-54).
2. Open the converter tab from the navigation bar.
3. Select a synthetic `.cfg` sample. Enter a template name of 1 to 120 visible characters. Select `standalone` or `spoke`.
4. Select a supported gateway role and hardware model (T012).
5. Review the parsed source and the unsupported lines.
6. Review the proposal. Confirm that the proposal shows the changes, the omissions, and the verification state.
7. Type EXPORT and export the reviewed proposal (FR-035).
8. Confirm that no Mist credential is needed for steps 1 to 7.

For apply, the operator confirms the organization, types APPLY, and runs the approved write (T022). The family must be enabled first, which needs the decision in D-15.

## Step 5: Reproduce the Mist contract facts

Read these lines in `documentation\mist-api-openapi31yaml.yaml` (R-73, R-75, R-77, R-80):

- Line 9727 defines `/api/v1/orgs/{org_id}/gatewaytemplates`.
- Line 9764 defines `operationId: createOrgGatewayTemplate`.
- Line 80782 lists `required` for `gateway_template`. Line 80783 lists `name`.
- Lines 80789 and 80790 list `spoke` and `standalone` as the only template types.

Read line 58 of `.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py`. It defines `createOrgGatewayTemplate(mist_session, org_id, body)`.

## Step 6: Verify this record

Run the STE gate on every Markdown file in the record (R-51, R-66).

```powershell
ste-linter --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\spec.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\plan.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\tasks.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\analysis.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\design\research.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\design\data-model.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\design\quickstart.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\design\contracts\portal-routes.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\design\contracts\mist-gateway-template.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\design\checklists\requirements.md specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter\design\checklists\security.md
```

Expected result: Each file scores 80 or above.

## Step 7: Verification command for each task

Each task in `tasks.md` names one command. Use the command for the task that you run. The first commands are these:

- T006: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_records.py`
- T007: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/input/test_input_contract.py`
- T011: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/hardware/test_hardware.py`
- T021: `python -m pytest tests/integration/web_portal/cisco_config_converter/operations/apply/test_apply_gates.py`
- T029: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
- T032: `python -m pytest tests/e2e/web_portal`

## Clean up

This record creates no temporary file. Remove any test artifact that a test run creates under `test-artifacts/` after the run ends.
